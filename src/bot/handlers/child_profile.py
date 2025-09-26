"""Child profile management handlers"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from ..states.story_states import StoryCreationStates, ProfileStates
from ..keyboards.inline import get_children_keyboard, get_story_type_keyboard
from ...services.child_service import ChildService
from ...services.content_safety_service import content_safety, SafetyLevel
from ...models.user import User

router = Router()


@router.callback_query(F.data == "add_new_child")
async def start_child_creation(
    callback: CallbackQuery, 
    state: FSMContext,
    session: AsyncSession
):
    """Start child profile creation"""
    await callback.message.edit_text(
        "👶 Давайте создадим профиль для вашего ребенка!\n\n"
        "Как зовут вашего малыша? 💝"
    )
    await state.set_state(StoryCreationStates.awaiting_child_name)
    await callback.answer()


# Alternative direct command for testing
@router.message(Command("add_child"))
async def add_child_command(
    message: Message,
    state: FSMContext
):
    """Direct command to add child (for testing)"""
    await message.answer(
        "👶 Создаем профиль ребенка!\n\n"
        "Как зовут вашего малыша? 💝"
    )
    await state.set_state(StoryCreationStates.awaiting_child_name)


@router.message(StateFilter(StoryCreationStates.awaiting_child_name))
async def handle_child_name(
    message: Message, 
    state: FSMContext,
    session: AsyncSession
):
    """Handle child name input"""
    child_name = message.text.strip()
    
    # Validation
    if not child_name:
        await message.answer(
            "❌ Имя не может быть пустым.\n"
            "Пожалуйста, введите имя ребенка:"
        )
        return
    
    if len(child_name) > 50:
        await message.answer(
            "❌ Имя слишком длинное (максимум 50 символов).\n"
            "Пожалуйста, введите более короткое имя:"
        )
        return
    
    # Валидация имени на безопасность
    try:
        # Проверяем имя на неподходящий контент
        safety_level, violations = content_safety.validate_input(child_name, 5)  # Default age for validation
        
        if safety_level == SafetyLevel.BLOCKED:
            alternatives = content_safety.get_safe_alternatives("name", 5)
            alt_text = f"\n\n💡 Попробуйте: {', '.join(alternatives[:3])}" if alternatives else "\n\n💡 Попробуйте: Анна, Максим, София"
            
            await message.answer(
                f"🚫 Имя '{child_name}' содержит неподходящий контент.\n\n"
                f"Пожалуйста, выберите другое имя.{alt_text}"
            )
            return
    except Exception as e:
        logger.error(f"Error validating child name: {e}")
        # Продолжаем без валидации в случае ошибки
    
    # Save to state
    await state.update_data(child_name=child_name)
    
    await message.answer(
        f"Замечательно! {child_name} - красивое имя! 😊\n\n"
        f"Сколько лет {child_name}?\n"
        "(введите цифрой от 2 до 8 лет)"
    )
    await state.set_state(StoryCreationStates.awaiting_child_age)


@router.message(StateFilter(StoryCreationStates.awaiting_child_age))
async def handle_child_age(
    message: Message, 
    state: FSMContext,
    session: AsyncSession
):
    """Handle child age input"""
    try:
        age = int(message.text.strip())
        
        if not 2 <= age <= 8:
            await message.answer(
                "❌ Возраст должен быть от 2 до 8 лет.\n"
                "Пожалуйста, введите корректный возраст:"
            )
            return
        
        # Save to state
        await state.update_data(child_age=age)
        
        data = await state.get_data()
        child_name = data['child_name']
        
        await message.answer(
            f"Отлично! 🎈\n\n"
            f"Теперь расскажите, кто любимые персонажи {child_name}?\n\n"
            f"💡 Например:\n"
            f"• единороги, принцессы\n"
            f"• супергерои, роботы\n"
            f"• динозавры, драконы\n"
            f"• животные, волшебники\n\n"
            f"Можете написать несколько через запятую:"
        )
        await state.set_state(StoryCreationStates.awaiting_characters)
        
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите возраст цифрой.\n"
            "Например: 5"
        )


@router.message(StateFilter(StoryCreationStates.awaiting_characters))
async def handle_child_characters(
    message: Message, 
    state: FSMContext,
    session: AsyncSession
):
    """Handle child favorite characters input"""
    characters_text = message.text.strip()
    
    if not characters_text:
        await message.answer(
            "❌ Пожалуйста, введите хотя бы одного персонажа.\n"
            "Например: единороги, принцессы"
        )
        return
    
    # Parse characters
    characters = [char.strip() for char in characters_text.split(',') if char.strip()]
    
    if not characters:
        await message.answer(
            "❌ Не удалось разобрать персонажей.\n"
            "Пожалуйста, перечислите их через запятую:"
        )
        return
    
    # Валидация персонажей на безопасность
    try:
        child_service = ChildService(session)
        # Временно создаем сервис для валидации (возраст получим из state)
        data = await state.get_data()
        child_age = data.get('child_age', 5)  # Default age for validation
        
        safety_level, problematic_chars = content_safety.validate_characters(characters, child_age)
        
        if safety_level == SafetyLevel.BLOCKED:
            alternatives = content_safety.get_safe_alternatives(problematic_chars[0], child_age)
            alt_text = f"\n\n💡 Попробуйте вместо этого: {', '.join(alternatives)}" if alternatives else ""
            
            await message.answer(
                f"🚫 Некоторые персонажи содержат неподходящий для детей контент: {', '.join(problematic_chars)}\n\n"
                f"Пожалуйста, выберите более подходящих персонажей.{alt_text}"
            )
            return
    except ValueError as e:
        await message.answer(f"🚫 {str(e)}")
        return
    
    # Save to state
    await state.update_data(characters=characters)
    
    data = await state.get_data()
    child_name = data['child_name']
    
    characters_list = '\n'.join([f"• {char}" for char in characters[:5]])
    
    await message.answer(
        f"Замечательный выбор! 🌟\n\n"
        f"Любимые персонажи {child_name}:\n"
        f"{characters_list}\n\n"
        f"А что еще интересно {child_name}?\n\n"
        f"💡 Например:\n"
        f"• космос, путешествия\n"
        f"• животные, природа\n"
        f"• магия, волшебство\n"
        f"• спорт, приключения\n\n"
        f"Можете написать несколько через запятую:"
    )
    await state.set_state(StoryCreationStates.awaiting_interests)


@router.message(StateFilter(StoryCreationStates.awaiting_interests))
async def handle_child_interests(
    message: Message, 
    state: FSMContext,
    session: AsyncSession,
    current_user: User
):
    """Handle child interests and create profile"""
    interests_text = message.text.strip()
    
    if not interests_text:
        await message.answer(
            "❌ Пожалуйста, введите хотя бы один интерес.\n"
            "Например: космос, животные"
        )
        return
    
    # Parse interests
    interests = [interest.strip() for interest in interests_text.split(',') if interest.strip()]
    
    if not interests:
        await message.answer(
            "❌ Не удалось разобрать интересы.\n"
            "Пожалуйста, перечислите их через запятую:"
        )
        return
    
    # Валидация интересов на безопасность
    try:
        child_service = ChildService(session)
        # Временно создаем сервис для валидации (возраст получим из state)
        data = await state.get_data()
        child_age = data.get('child_age', 5)  # Default age for validation
        
        safety_level, problematic_interests = content_safety.validate_interests(interests, child_age)
        
        if safety_level == SafetyLevel.BLOCKED:
            alternatives = content_safety.get_safe_alternatives(problematic_interests[0], child_age)
            alt_text = f"\n\n💡 Попробуйте вместо этого: {', '.join(alternatives)}" if alternatives else ""
            
            await message.answer(
                f"🚫 Некоторые интересы содержат неподходящий для детей контент: {', '.join(problematic_interests)}\n\n"
                f"Пожалуйста, выберите более подходящие интересы.{alt_text}"
            )
            return
    except ValueError as e:
        await message.answer(f"🚫 {str(e)}")
        return
    
    # Get data from state
    data = await state.get_data()
    child_name = data['child_name']
    child_age = data['child_age']
    characters = data['characters']
    
    try:
        # Create child profile
        child_service = ChildService(session)
        child = await child_service.create_child_profile(
            user_id=current_user.id,
            name=child_name,
            age=child_age,
            characters=characters,
            interests=interests
        )
        
        # Show success message with options
        keyboard = get_story_type_keyboard(child.id)
        
        characters_text = ', '.join(characters[:3])
        if len(characters) > 3:
            characters_text += f" и еще {len(characters) - 3}"
        
        interests_text = ', '.join(interests[:3])
        if len(interests) > 3:
            interests_text += f" и еще {len(interests) - 3}"
        
        await message.answer(
            f"🎉 Профиль {child_name} создан!\n\n"
            f"📋 Информация:\n"
            f"👶 Имя: {child_name}\n"
            f"🎂 Возраст: {child_age} лет\n"
            f"🎭 Любимые персонажи: {characters_text}\n"
            f"💫 Интересы: {interests_text}\n\n"
            f"Что будем создавать?",
            reply_markup=keyboard
        )
        
        # Clear state
        await state.clear()
        
    except ValueError as e:
        await message.answer(f"❌ Ошибка: {e}")
        await state.clear()
    except Exception as e:
        await message.answer(
            "😔 Произошла ошибка при создании профиля.\n"
            "Попробуйте еще раз с команды /story"
        )
        await state.clear()


@router.callback_query(F.data.regexp(r"^child_\d+$"))
async def handle_child_selection(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Handle child selection from list"""
    child_id = int(callback.data.split("_")[1])
    
    child_service = ChildService(session)
    child = await child_service.get_child_by_id(child_id)
    
    if not child:
        await callback.answer("❌ Ребенок не найден", show_alert=True)
        return
    
    # Show child options
    keyboard = get_story_type_keyboard(child_id)
    
    await callback.message.edit_text(
        f"👶 Выбран: {child.name} ({child.age} лет)\n\n"
        f"🎭 Персонажи: {', '.join(child.favorite_characters[:3])}\n"
        f"💫 Интересы: {', '.join(child.interests[:3])}\n\n"
        f"Что будем создавать?",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_children")
async def back_to_children_list(
    callback: CallbackQuery,
    session: AsyncSession,
    current_user: User
):
    """Go back to children selection"""
    child_service = ChildService(session)
    children = await child_service.get_user_children(current_user.id)
    
    if not children:
        await callback.message.edit_text(
            "👶 У вас пока нет профилей детей.\n"
            "Давайте создадим первый! Как зовут вашего малыша?"
        )
        return
    
    keyboard = get_children_keyboard(children)
    await callback.message.edit_text(
        "👶 Для кого создаем сказку?",
        reply_markup=keyboard
    )
    await callback.answer()
