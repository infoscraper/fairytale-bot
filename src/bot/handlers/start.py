"""Start handler for the bot"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from ..keyboards.inline import get_children_keyboard, get_profile_management_keyboard, get_main_menu_keyboard
from ..states.story_states import StoryCreationStates
from ...services.child_service import ChildService
from ...models.user import User

router = Router()


@router.message(Command("start"))
async def start_handler(
    message: Message,
    session: AsyncSession,
    current_user: User
):
    """Handle /start command"""
    
    user_name = current_user.first_name
    user_stats = f"(ID: {current_user.id}, бесплатных сказок: {3 - current_user.free_stories_used}/3)"
    
    welcome_text = (
        f"🎭 Привет, {user_name}! Добро пожаловать в мир сказок!\n\n"
        "Я - твой персональный сказочник! ✨\n\n"
        "📚 Что я умею:\n"
        "• Создавать уникальные сказки специально для твоего ребенка\n"
        "• Делать его главным героем каждой истории\n"
        "• Адаптировать сказки под возраст и интересы\n"
        "• Запоминать предпочтения и создавать серии\n\n"
        f"👤 {user_stats}\n\n"
        "Выберите действие:"
    )
    
    keyboard = get_main_menu_keyboard()
    await message.answer(welcome_text, reply_markup=keyboard)


@router.message(Command("help"))
async def help_handler(message: Message):
    """Handle /help command"""
    
    help_text = (
        "🆘 Помощь по боту\n\n"
        "📖 Как создать сказку:\n"
        "1. Отправь команду /story\n"
        "2. Расскажи про своего ребенка\n"
        "3. Выбери любимых персонажей\n"
        "4. Жди волшебства! ✨\n\n"
        "💡 Советы:\n"
        "• Чем подробнее расскажешь про ребенка, тем лучше сказка\n"
        "• Сказки адаптируются под возраст (2-8 лет)\n"
        "• Каждая история уникальна и неповторима\n\n"
        "❓ Вопросы? Просто напиши мне!"
    )
    
    await message.answer(help_text)


@router.message(Command("story"))
async def story_handler(
    message: Message,
    session: AsyncSession,
    current_user: User,
    state: FSMContext
):
    """Handle /story command"""
    
    child_service = ChildService(session)
    children = await child_service.get_user_children(current_user.id)
    
    if not children:
        # No children - show add child button
        keyboard = get_children_keyboard([])  # Empty list shows "Add child" button
        await message.answer(
            "👶 У вас пока нет профилей детей.\n\n"
            "Создайте первый профиль:",
            reply_markup=keyboard
        )
    else:
        # Show children selection
        keyboard = get_children_keyboard(children)
        await message.answer(
            f"👶 У вас {len(children)} профил{'ь' if len(children) == 1 else ('я' if len(children) < 5 else 'ей')}.\n\n"
            "Для кого создаем сказку?",
            reply_markup=keyboard
        )


@router.message(Command("profile"))
async def profile_handler(
    message: Message,
    session: AsyncSession,
    current_user: User
):
    """Handle /profile command - enhanced version"""
    
    child_service = ChildService(session)
    children = await child_service.get_user_children(current_user.id)
    
    if not children:
        await message.answer(
            "👶 У вас пока нет профилей детей.\n\n"
            "Создайте первый профиль командой /story!",
            reply_markup=get_children_keyboard([])
        )
        return
    
    # Show enhanced profile management interface
    keyboard = get_profile_management_keyboard(children)
    
    await message.answer(
        "👨‍👩‍👧‍👦 **Управление профилями детей**\n\n"
        f"У вас {len(children)} профил{'ь' if len(children) == 1 else ('я' if len(children) < 5 else 'ей')}.\n"
        "Выберите ребенка для управления:",
        reply_markup=keyboard
    )


# Обработчики кнопок главного меню
@router.callback_query(F.data == "menu_create_story")
async def menu_create_story_handler(
    callback: CallbackQuery,
    session: AsyncSession,
    current_user: User
):
    """Handle create story menu button"""
    child_service = ChildService(session)
    children = await child_service.get_user_children(current_user.id)
    
    if not children:
        keyboard = get_children_keyboard([])
        await callback.message.edit_text(
            "👶 У вас пока нет профилей детей.\n\n"
            "Создайте первый профиль:",
            reply_markup=keyboard
        )
    else:
        keyboard = get_children_keyboard(children)
        await callback.message.edit_text(
            f"👶 У вас {len(children)} профил{'ь' if len(children) == 1 else ('я' if len(children) < 5 else 'ей')}.\n\n"
            "Для кого создаем сказку?",
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.callback_query(F.data == "menu_manage_profiles")
async def menu_manage_profiles_handler(
    callback: CallbackQuery,
    session: AsyncSession,
    current_user: User
):
    """Handle manage profiles menu button"""
    child_service = ChildService(session)
    children = await child_service.get_user_children(current_user.id)
    
    if not children:
        await callback.message.edit_text(
            "👶 У вас пока нет профилей детей.\n\n"
            "Создайте первый профиль командой /story!",
            reply_markup=get_children_keyboard([])
        )
    else:
        keyboard = get_profile_management_keyboard(children)
        await callback.message.edit_text(
            "👨‍👩‍👧‍👦 **Управление профилями детей**\n\n"
            f"У вас {len(children)} профил{'ь' if len(children) == 1 else ('я' if len(children) < 5 else 'ей')}.\n"
            "Выберите ребенка для управления:",
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.callback_query(F.data == "menu_story_history")
async def menu_story_history_handler(
    callback: CallbackQuery,
    session: AsyncSession,
    current_user: User
):
    """Handle story history menu button"""
    # TODO: Implement story history functionality
    await callback.message.edit_text(
        "📚 **История сказок**\n\n"
        "Эта функция пока в разработке.\n"
        "Скоро здесь будет отображаться история всех созданных сказок! 📖✨",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "menu_help")
async def menu_help_handler(callback: CallbackQuery):
    """Handle help menu button"""
    help_text = (
        "🆘 **Помощь по боту**\n\n"
        "📖 **Как создать сказку:**\n"
        "1. Нажмите кнопку 'Создать сказку'\n"
        "2. Расскажите про своего ребенка\n"
        "3. Выберите любимых персонажей\n"
        "4. Ждите волшебства! ✨\n\n"
        "💡 **Советы:**\n"
        "• Чем подробнее расскажете про ребенка, тем лучше сказка\n"
        "• Сказки адаптируются под возраст (2-8 лет)\n"
        "• Каждая история уникальна и неповторима\n\n"
        "❓ **Вопросы?** Просто напишите мне!"
    )
    
    await callback.message.edit_text(
        help_text,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def main_menu_handler(
    callback: CallbackQuery,
    session: AsyncSession,
    current_user: User
):
    """Handle main menu callback"""
    user_name = current_user.first_name
    user_stats = f"(ID: {current_user.id}, бесплатных сказок: {3 - current_user.free_stories_used}/3)"
    
    welcome_text = (
        f"🎭 Привет, {user_name}! Добро пожаловать в мир сказок!\n\n"
        "Я - твой персональный сказочник! ✨\n\n"
        "📚 Что я умею:\n"
        "• Создавать уникальные сказки специально для твоего ребенка\n"
        "• Делать его главным героем каждой истории\n"
        "• Адаптировать сказки под возраст и интересы\n"
        "• Запоминать предпочтения и создавать серии\n\n"
        f"👤 {user_stats}\n\n"
        "Выберите действие:"
    )
    
    keyboard = get_main_menu_keyboard()
    await callback.message.edit_text(welcome_text, reply_markup=keyboard)
    await callback.answer()


# Echo handler temporarily disabled to allow FSM states to work
# @router.message()
# async def echo_handler(message: Message):
#     """Handle all other messages"""
#     
#     echo_text = (
#         f"👋 Спасибо за сообщение!\n\n"
#         f"Пока что я учусь быть лучшим сказочником. 📚\n\n"
#         f"Попробуй команды:\n"
#         f"/start - главное меню\n"
#         f"/help - помощь\n"
#         f"/story - создать сказку\n\n"
#         f"Твое сообщение: «{message.text}»"
#     )
#     
#     await message.answer(echo_text)
