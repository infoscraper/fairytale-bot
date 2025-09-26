"""Profile management handlers"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from ..states.profile_states import ProfileEditStates
from ..keyboards.inline import (
    get_profile_management_keyboard, 
    get_profile_actions_keyboard,
    get_edit_profile_keyboard,
    get_confirm_keyboard
)
from ...services.child_service import ChildService
from ...models import User
import re

router = Router()


@router.callback_query(F.data == "back_to_profiles")
async def back_to_profiles_handler(
    callback: CallbackQuery,
    session: AsyncSession,
    current_user: User
):
    """Handle back to profiles action"""
    child_service = ChildService(session)
    children = await child_service.get_user_children(current_user.id)
    
    keyboard = get_profile_management_keyboard(children)
    
    await callback.message.edit_text(
        "👨‍👩‍👧‍👦 **Управление профилями детей**\n\n"
        f"У вас {len(children)} профил{'ь' if len(children) == 1 else ('я' if len(children) < 5 else 'ей')}.\n"
        "Выберите ребенка для управления:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("manage_profile_"))
async def manage_profile_handler(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Handle profile management for specific child"""
    child_id = int(callback.data.split("_")[2])
    
    child_service = ChildService(session)
    child = await child_service.get_child_by_id(child_id)
    
    if not child:
        await callback.answer("❌ Профиль не найден", show_alert=True)
        return
    
    # Get child statistics
    stats = await child_service.get_child_statistics(child_id)
    
    stats_text = (
        f"👶 **{child.name}** ({child.age} лет)\n\n"
        f"📊 **Статистика:**\n"
        f"• Сказок создано: {stats['story_count']}\n"
        f"• Любимые персонажи: {', '.join(child.favorite_characters[:3]) or 'не указаны'}\n"
        f"• Интересы: {', '.join(child.interests[:3]) or 'не указаны'}\n"
        f"• Длина сказок: {child.preferred_story_length} мин\n\n"
        "**Что хотите сделать?**"
    )
    
    keyboard = get_profile_actions_keyboard(child_id)
    
    await callback.message.edit_text(stats_text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("profile_stats_"))
async def profile_stats_handler(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Show detailed profile statistics"""
    child_id = int(callback.data.split("_")[2])
    
    child_service = ChildService(session)
    stats = await child_service.get_child_statistics(child_id)
    
    if not stats:
        await callback.answer("❌ Профиль не найден", show_alert=True)
        return
    
    # Format top themes
    top_themes_text = "не определены"
    if stats['top_themes']:
        top_themes_text = "\n".join([f"   • {theme} ({count} раз)" for theme, count in stats['top_themes']])
    
    stats_text = (
        f"📊 **Подробная статистика для {stats['name']}**\n\n"
        f"👶 **Базовая информация:**\n"
        f"• Имя: {stats['name']}\n"
        f"• Возраст: {stats['age']} лет\n"
        f"• Профиль создан: {stats['created_at'].strftime('%d.%m.%Y')}\n\n"
        f"📚 **Сказки:**\n"
        f"• Всего создано: {stats['story_count']}\n"
        f"• Любимые темы:\n{top_themes_text}\n\n"
        f"🎭 **Предпочтения:**\n"
        f"• Персонажи: {', '.join(stats['favorite_characters']) or 'не указаны'}\n"
        f"• Интересы: {', '.join(stats['interests']) or 'не указаны'}\n"
        f"• Длина сказок: {stats['preferred_story_length']} мин"
    )
    
    keyboard = get_profile_actions_keyboard(child_id)
    
    await callback.message.edit_text(stats_text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("edit_profile_"))
async def edit_profile_handler(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Show profile editing options"""
    child_id = int(callback.data.split("_")[2])
    
    child_service = ChildService(session)
    child = await child_service.get_child_by_id(child_id)
    
    if not child:
        await callback.answer("❌ Профиль не найден", show_alert=True)
        return
    
    edit_text = (
        f"✏️ **Редактирование профиля {child.name}**\n\n"
        f"**Текущие данные:**\n"
        f"• Имя: {child.name}\n"
        f"• Возраст: {child.age} лет\n"
        f"• Персонажи: {', '.join(child.favorite_characters) or 'не указаны'}\n"
        f"• Интересы: {', '.join(child.interests) or 'не указаны'}\n"
        f"• Длина сказок: {child.preferred_story_length} мин\n\n"
        "**Что хотите изменить?**"
    )
    
    keyboard = get_edit_profile_keyboard(child_id)
    
    await callback.message.edit_text(edit_text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("edit_name_"))
async def edit_name_handler(
    callback: CallbackQuery,
    state: FSMContext
):
    """Start name editing process"""
    child_id = int(callback.data.split("_")[2])
    
    await state.update_data(child_id=child_id)
    await state.set_state(ProfileEditStates.awaiting_new_name)
    
    await callback.message.edit_text(
        "📝 **Изменение имени**\n\n"
        "Введите новое имя для ребенка:"
    )
    await callback.answer()


@router.message(StateFilter(ProfileEditStates.awaiting_new_name))
async def process_new_name(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Process new name input"""
    data = await state.get_data()
    child_id = data.get("child_id")
    
    new_name = message.text.strip()
    
    if not new_name or len(new_name) < 2:
        await message.answer("❌ Имя должно содержать минимум 2 символа. Попробуйте еще раз:")
        return
    
    if len(new_name) > 50:
        await message.answer("❌ Имя слишком длинное (максимум 50 символов). Попробуйте еще раз:")
        return
    
    child_service = ChildService(session)
    success = await child_service.update_child_name(child_id, new_name)
    
    if success:
        await message.answer(
            f"✅ Имя успешно изменено на **{new_name}**!",
            reply_markup=get_profile_actions_keyboard(child_id)
        )
    else:
        await message.answer("❌ Ошибка при сохранении. Попробуйте позже.")
    
    await state.clear()


@router.callback_query(F.data.startswith("edit_age_"))
async def edit_age_handler(
    callback: CallbackQuery,
    state: FSMContext
):
    """Start age editing process"""
    child_id = int(callback.data.split("_")[2])
    
    await state.update_data(child_id=child_id)
    await state.set_state(ProfileEditStates.awaiting_new_age)
    
    await callback.message.edit_text(
        "🎂 **Изменение возраста**\n\n"
        "Введите новый возраст (от 2 до 8 лет):"
    )
    await callback.answer()


@router.message(StateFilter(ProfileEditStates.awaiting_new_age))
async def process_new_age(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Process new age input"""
    data = await state.get_data()
    child_id = data.get("child_id")
    
    try:
        new_age = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите число от 2 до 8:")
        return
    
    child_service = ChildService(session)
    success = await child_service.update_child_age(child_id, new_age)
    
    if success:
        await message.answer(
            f"✅ Возраст успешно изменен на **{new_age} лет**!",
            reply_markup=get_profile_actions_keyboard(child_id)
        )
    else:
        await message.answer("❌ Возраст должен быть от 2 до 8 лет. Попробуйте еще раз:")
        return
    
    await state.clear()


@router.callback_query(F.data.startswith("edit_characters_"))
async def edit_characters_handler(
    callback: CallbackQuery,
    state: FSMContext
):
    """Start characters editing process"""
    child_id = int(callback.data.split("_")[2])
    
    await state.update_data(child_id=child_id)
    await state.set_state(ProfileEditStates.awaiting_new_characters)
    
    await callback.message.edit_text(
        "🎭 **Изменение персонажей**\n\n"
        "Введите любимых персонажей через запятую:\n"
        "*(например: принцесса, дракон, единорог)*"
    )
    await callback.answer()


@router.message(StateFilter(ProfileEditStates.awaiting_new_characters))
async def process_new_characters(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Process new characters input"""
    data = await state.get_data()
    child_id = data.get("child_id")
    
    characters_text = message.text.strip()
    characters = [char.strip() for char in characters_text.split(',') if char.strip()]
    
    if not characters:
        await message.answer("❌ Введите хотя бы одного персонажа:")
        return
    
    child_service = ChildService(session)
    success = await child_service.update_child_characters(child_id, characters)
    
    if success:
        await message.answer(
            f"✅ Персонажи успешно обновлены!\n\n"
            f"**Новые персонажи:** {', '.join(characters[:5])}",
            reply_markup=get_profile_actions_keyboard(child_id)
        )
    else:
        await message.answer("❌ Ошибка при сохранении. Попробуйте позже.")
    
    await state.clear()


@router.callback_query(F.data.startswith("edit_interests_"))
async def edit_interests_handler(
    callback: CallbackQuery,
    state: FSMContext
):
    """Start interests editing process"""
    child_id = int(callback.data.split("_")[2])
    
    await state.update_data(child_id=child_id)
    await state.set_state(ProfileEditStates.awaiting_new_interests)
    
    await callback.message.edit_text(
        "💫 **Изменение интересов**\n\n"
        "Введите интересы ребенка через запятую:\n"
        "*(например: животные, космос, спорт)*"
    )
    await callback.answer()


@router.message(StateFilter(ProfileEditStates.awaiting_new_interests))
async def process_new_interests(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Process new interests input"""
    data = await state.get_data()
    child_id = data.get("child_id")
    
    interests_text = message.text.strip()
    interests = [interest.strip() for interest in interests_text.split(',') if interest.strip()]
    
    if not interests:
        await message.answer("❌ Введите хотя бы один интерес:")
        return
    
    child_service = ChildService(session)
    success = await child_service.update_child_interests(child_id, interests)
    
    if success:
        await message.answer(
            f"✅ Интересы успешно обновлены!\n\n"
            f"**Новые интересы:** {', '.join(interests[:5])}",
            reply_markup=get_profile_actions_keyboard(child_id)
        )
    else:
        await message.answer("❌ Ошибка при сохранении. Попробуйте позже.")
    
    await state.clear()


@router.callback_query(F.data.startswith("edit_length_"))
async def edit_length_handler(
    callback: CallbackQuery,
    state: FSMContext
):
    """Start story length editing process"""
    child_id = int(callback.data.split("_")[2])
    
    await state.update_data(child_id=child_id)
    await state.set_state(ProfileEditStates.awaiting_new_length)
    
    await callback.message.edit_text(
        "⏱️ **Изменение длины сказок**\n\n"
        "Введите желаемую длину сказок в минутах (от 1 до 10):\n\n"
        "💡 **Рекомендации:**\n"
        "• 2-3 мин - для малышей 2-4 года\n"
        "• 5-7 мин - для дошкольников 5-6 лет\n"
        "• 8-10 мин - для школьников 7-8 лет"
    )
    await callback.answer()


@router.message(StateFilter(ProfileEditStates.awaiting_new_length))
async def process_new_length(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Process new story length input"""
    data = await state.get_data()
    child_id = data.get("child_id")
    
    try:
        new_length = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите число от 1 до 10:")
        return
    
    child_service = ChildService(session)
    success = await child_service.update_child_story_length(child_id, new_length)
    
    if success:
        await message.answer(
            f"✅ Длина сказок успешно изменена на **{new_length} минут**!",
            reply_markup=get_profile_actions_keyboard(child_id)
        )
    else:
        await message.answer("❌ Длина должна быть от 1 до 10 минут. Попробуйте еще раз:")
        return
    
    await state.clear()


@router.callback_query(F.data.startswith("deactivate_profile_"))
async def deactivate_profile_handler(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Show deactivation confirmation"""
    child_id = int(callback.data.split("_")[2])
    
    child_service = ChildService(session)
    child = await child_service.get_child_by_id(child_id)
    
    if not child:
        await callback.answer("❌ Профиль не найден", show_alert=True)
        return
    
    confirm_text = (
        f"⚠️ **Деактивация профиля**\n\n"
        f"Вы уверены, что хотите деактивировать профиль **{child.name}**?\n\n"
        f"После деактивации:\n"
        f"• Профиль будет скрыт из списка\n"
        f"• Нельзя будет создавать новые сказки\n"
        f"• Старые сказки сохранятся\n"
        f"• Профиль можно будет восстановить"
    )
    
    keyboard = get_confirm_keyboard("deactivate", str(child_id))
    
    await callback.message.edit_text(confirm_text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_deactivate_"))
async def confirm_deactivate_handler(
    callback: CallbackQuery,
    session: AsyncSession,
    current_user: User
):
    """Confirm profile deactivation"""
    child_id = int(callback.data.split("_")[2])
    
    child_service = ChildService(session)
    child = await child_service.get_child_by_id(child_id)
    
    if not child:
        await callback.answer("❌ Профиль не найден", show_alert=True)
        return
    
    success = await child_service.deactivate_child(child_id)
    
    if success:
        # Return to profiles list
        children = await child_service.get_user_children(current_user.id)
        keyboard = get_profile_management_keyboard(children)
        
        await callback.message.edit_text(
            f"✅ Профиль **{child.name}** успешно деактивирован.\n\n"
            "👨‍👩‍👧‍👦 **Управление профилями детей**\n\n"
            f"У вас {len(children)} активных профил{'ь' if len(children) == 1 else ('я' if len(children) < 5 else 'ей')}.",
            reply_markup=keyboard
        )
    else:
        await callback.answer("❌ Ошибка при деактивации", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_"))
async def cancel_action_handler(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Cancel any confirmation action"""
    # Extract child_id if present in the context
    await callback.message.edit_text(
        "❌ Действие отменено.\n\n"
        "Используйте /profile для управления профилями."
    )
    await callback.answer()
