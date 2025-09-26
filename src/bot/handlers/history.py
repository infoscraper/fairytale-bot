"""Handlers for story history management"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, BufferedInputFile
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import io

from ..keyboards.inline import get_history_keyboard, get_story_actions_keyboard, get_children_filter_keyboard
from ...services.story_service import StoryService
from ...services.child_service import ChildService
from ...models import User, Story

router = Router()


@router.message(Command("history"))
async def history_command(
    message: Message,
    session: AsyncSession,
    current_user: User
):
    """Show user's story history"""
    story_service = StoryService(session)
    child_service = ChildService(session)
    
    # Get all user stories (recent first)
    stories = await story_service.get_user_stories(current_user.id, limit=20)
    children = await child_service.get_user_children(current_user.id)
    
    if not stories:
        await message.answer(
            "📚 **История сказок**\n\n"
            "У вас пока нет созданных сказок.\n"
            "Создайте первую сказку командой /story! ✨"
        )
        return
    
    # Create history message
    history_text = f"📚 **История сказок**\n\n"
    history_text += f"Всего сказок: {len(stories)}\n"
    history_text += f"Для детей: {len(children)}\n\n"
    
    # Show recent stories (last 5)
    history_text += "🔥 **Последние сказки:**\n"
    for i, story in enumerate(stories[:5], 1):
        feedback_emoji = "💖" if story.child_feedback == "loved" else "👍" if story.child_feedback == "liked" else "📖"
        date_str = story.created_at.strftime("%d.%m")
        history_text += f"{i}. {feedback_emoji} {story.child_name} • {story.theme} • {date_str}\n"
    
    if len(stories) > 5:
        history_text += f"\n... и еще {len(stories) - 5} сказок"
    
    keyboard = get_history_keyboard(len(children) > 1)
    await message.answer(history_text, reply_markup=keyboard)


@router.callback_query(F.data == "view_all_stories")
async def view_all_stories(
    callback: CallbackQuery,
    session: AsyncSession,
    current_user: User
):
    """Show all user stories with pagination"""
    story_service = StoryService(session)
    stories = await story_service.get_user_stories(current_user.id, limit=50)
    
    if not stories:
        await callback.answer("У вас нет сказок", show_alert=True)
        return
    
    # Create detailed stories list
    stories_text = f"📖 **Все сказки ({len(stories)})**\n\n"
    
    for i, story in enumerate(stories, 1):
        feedback_emoji = get_feedback_emoji(story.child_feedback)
        date_str = story.created_at.strftime("%d.%m.%Y")
        generation_time = f" ({story.generation_time}s)" if story.generation_time else ""
        
        stories_text += (
            f"{i}. {feedback_emoji} **{story.child_name}** ({story.child_age} лет)\n"
            f"   🎯 {story.theme} • 📅 {date_str}{generation_time}\n"
            f"   📝 {len(story.story_text)} символов\n\n"
        )
        
        # Split into pages if too long
        if len(stories_text) > 3500:
            stories_text += f"... и еще {len(stories) - i} сказок\n\n"
            stories_text += "Используйте фильтры для более детального просмотра."
            break
    
    keyboard = get_history_keyboard(len(await ChildService(session).get_user_children(current_user.id)) > 1)
    await callback.message.edit_text(stories_text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "filter_by_child")
async def filter_by_child(
    callback: CallbackQuery,
    session: AsyncSession,
    current_user: User
):
    """Show children filter options"""
    child_service = ChildService(session)
    children = await child_service.get_user_children(current_user.id)
    
    if len(children) <= 1:
        await callback.answer("У вас только один ребенок", show_alert=True)
        return
    
    keyboard = get_children_filter_keyboard(children)
    await callback.message.edit_text(
        "👶 **Фильтр по детям**\n\n"
        "Выберите ребенка для просмотра его сказок:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("child_stories_"))
async def show_child_stories(
    callback: CallbackQuery,
    session: AsyncSession,
    current_user: User
):
    """Show stories for specific child"""
    child_id = int(callback.data.split("_")[2])
    
    story_service = StoryService(session)
    child_service = ChildService(session)
    
    # Get child and their stories
    child = await child_service.get_child_by_id(child_id)
    if not child or child.user_id != current_user.id:
        await callback.answer("Ребенок не найден", show_alert=True)
        return
    
    child_stories = await story_service.get_child_stories(child_id, limit=20)
    
    if not child_stories:
        await callback.message.edit_text(
            f"📚 **Сказки для {child.name}**\n\n"
            f"Пока нет созданных сказок для {child.name}.\n"
            "Создайте первую сказку командой /story! ✨"
        )
        return
    
    # Create child-specific stories list
    stories_text = f"📚 **Сказки для {child.name}** ({child.age} лет)\n\n"
    stories_text += f"Всего сказок: {len(child_stories)}\n\n"
    
    for i, story in enumerate(child_stories, 1):
        feedback_emoji = get_feedback_emoji(story.child_feedback)
        date_str = story.created_at.strftime("%d.%m.%Y")
        
        stories_text += (
            f"{i}. {feedback_emoji} **{story.theme}**\n"
            f"   📅 {date_str} • 📝 {len(story.story_text)} символов\n"
            f"   💭 {story.moral[:50]}...\n\n"
        )
        
        if len(stories_text) > 3500:
            stories_text += f"... и еще {len(child_stories) - i} сказок"
            break
    
    keyboard = get_history_keyboard(True)  # Show all filters
    await callback.message.edit_text(stories_text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("read_story_"))
async def read_story_again(
    callback: CallbackQuery,
    session: AsyncSession,
    current_user: User
):
    """Show specific story for re-reading"""
    story_id = int(callback.data.split("_")[2])
    
    story_service = StoryService(session)
    story = await story_service.get_story_by_id(story_id)
    
    if not story or story.user_id != current_user.id:
        await callback.answer("Сказка не найдена", show_alert=True)
        return
    
    # Format story for display
    feedback_emoji = get_feedback_emoji(story.child_feedback)
    date_str = story.created_at.strftime("%d.%m.%Y в %H:%M")
    
    story_text = (
        f"📖 **Сказка для {story.child_name}** {feedback_emoji}\n\n"
        f"🎯 **Тема:** {story.theme}\n"
        f"🎭 **Персонажи:** {', '.join(story.characters[:3])}\n"
        f"📅 **Создана:** {date_str}\n"
        f"💫 **Мораль:** {story.moral}\n\n"
        f"{'='*30}\n\n"
        f"{story.story_text}\n\n"
        f"{'='*30}"
    )
    
    keyboard = get_story_actions_keyboard(story.id, story.child_id)
    await callback.message.edit_text(story_text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "back_to_history")
async def back_to_history(
    callback: CallbackQuery,
    session: AsyncSession,
    current_user: User
):
    """Return to main history view"""
    # Re-run the main history command logic
    await history_command(callback.message, session, current_user)
    await callback.answer()


@router.callback_query(F.data.startswith("export_story_"))
async def export_story_to_file(
    callback: CallbackQuery,
    session: AsyncSession,
    current_user: User
):
    """Export story to text file"""
    story_id = int(callback.data.split("_")[2])
    
    story_service = StoryService(session)
    story = await story_service.get_story_by_id(story_id)
    
    if not story or story.user_id != current_user.id:
        await callback.answer("Сказка не найдена", show_alert=True)
        return
    
    # Create story file content
    date_str = story.created_at.strftime("%d.%m.%Y в %H:%M")
    
    file_content = f"""СКАЗКА ДЛЯ {story.child_name.upper()}
{'='*50}

Тема: {story.theme}
Возраст ребенка: {story.child_age} лет
Персонажи: {', '.join(story.characters)}
Дата создания: {date_str}
Мораль: {story.moral}

{'='*50}
ТЕКСТ СКАЗКИ
{'='*50}

{story.story_text}

{'='*50}
Создано ботом-сказочником 🎭
Специально для {story.child_name} ❤️
"""
    
    # Create file
    file_bytes = file_content.encode('utf-8')
    filename = f"Сказка_для_{story.child_name}_{story.id}.txt"
    
    # Send file
    file_obj = BufferedInputFile(file_bytes, filename=filename)
    
    await callback.message.answer_document(
        file_obj,
        caption=f"📥 **Экспорт сказки для {story.child_name}**\n\n"
                f"🎯 Тема: {story.theme}\n"
                f"📅 Создана: {date_str}\n"
                f"📝 Размер: {len(story.story_text)} символов"
    )
    
    await callback.answer("✅ Файл отправлен!")


@router.callback_query(F.data.startswith("similar_story_"))
async def create_similar_story(
    callback: CallbackQuery,
    session: AsyncSession,
    current_user: User
):
    """Create similar story based on existing one"""
    parts = callback.data.split("_")
    child_id = int(parts[2])
    story_id = int(parts[3])
    
    story_service = StoryService(session)
    original_story = await story_service.get_story_by_id(story_id)
    
    if not original_story or original_story.user_id != current_user.id:
        await callback.answer("Сказка не найдена", show_alert=True)
        return
    
    # Show progress message
    progress_message = await callback.message.edit_text(
        f"✨ Создаю похожую сказку на тему '{original_story.theme}'...\n"
        f"⏳ Это может занять несколько секунд..."
    )
    
    try:
        # Create new story with similar theme
        new_story = await story_service.create_story(
            child_id=child_id,
            theme=original_story.theme
        )
        
        # Format new story for display
        feedback_emoji = get_feedback_emoji(new_story.child_feedback)
        date_str = new_story.created_at.strftime("%d.%m.%Y в %H:%M")
        
        story_text = (
            f"📖 **Новая сказка для {new_story.child_name}** {feedback_emoji}\n\n"
            f"🎯 **Тема:** {new_story.theme}\n"
            f"🎭 **Персонажи:** {', '.join(new_story.characters[:3])}\n"
            f"📅 **Создана:** {date_str}\n"
            f"💫 **Мораль:** {new_story.moral}\n\n"
            f"{'='*30}\n\n"
            f"{new_story.story_text}\n\n"
            f"{'='*30}"
        )
        
        from ..keyboards.inline import get_feedback_keyboard
        keyboard = get_feedback_keyboard(new_story.id, child_id)
        await progress_message.edit_text(story_text, reply_markup=keyboard, parse_mode="Markdown")
        
    except Exception as e:
        await progress_message.edit_text(
            f"😔 Произошла ошибка при создании сказки:\n{str(e)}\n\n"
            "Попробуйте еще раз через минуту."
        )


def get_feedback_emoji(feedback: str) -> str:
    """Get emoji for story feedback"""
    return {
        "loved": "💖",
        "liked": "👍", 
        "disliked": "👎",
        None: "📖"
    }.get(feedback, "📖")
