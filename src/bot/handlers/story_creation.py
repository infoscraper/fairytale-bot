"""Story creation handlers"""
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from ..states.story_states import StoryCreationStates
from ..keyboards.inline import get_theme_keyboard, get_feedback_keyboard
from ...services.story_service import StoryService
from ...services.child_service import ChildService
from ...services.tts_service import TTSService
from ...services.content_safety_service import content_safety, SafetyLevel
from ...models.user import User

router = Router()


@router.callback_query(F.data.startswith("new_story_"))
async def start_new_story(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Start creating new story"""
    child_id = int(callback.data.split("_")[2])
    
    child_service = ChildService(session)
    child = await child_service.get_child_by_id(child_id)
    
    if not child:
        await callback.answer("❌ Ребенок не найден", show_alert=True)
        return
    
    # Show theme selection based on child's interests
    keyboard = get_theme_keyboard(child_id, child.interests)
    
    await callback.message.edit_text(
        f"🎭 Создаем сказку для {child.name}!\n\n"
        f"Выберите тему из любимых интересов {child.name} "
        f"или предложите свою:",
        reply_markup=keyboard
    )
    # Do NOT answer the callback here again — it was already answered at the start
    # A repeated answer after long processing causes TelegramBadRequest: query is too old
    pass


@router.callback_query(F.data.startswith("theme_"))
async def handle_theme_selection(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    current_user: User
):
    """Handle theme selection for story"""
    # Answer callback immediately to prevent timeout
    await callback.answer()
    
    parts = callback.data.split("_")
    child_id = int(parts[1])
    theme = "_".join(parts[2:])  # Join back in case theme has underscores
    
    # Get child data for validation
    child_service = ChildService(session)
    child = await child_service.get_child_by_id(child_id)
    
    if not child:
        await callback.message.edit_text("❌ Ребенок не найден")
        return
    
    if theme == "random":
        theme = None  # Will be auto-selected from interests
    else:
        # Валидация темы на безопасность
        safety_level, message = content_safety.validate_theme(theme, child.age)
        
        if safety_level == SafetyLevel.BLOCKED:
            await callback.message.edit_text(
                f"🚫 {message}\n\n"
                f"Пожалуйста, выберите другую тему из предложенных."
            )
            return
        
        elif safety_level == SafetyLevel.WARNING:
            # Show warning but continue
            await callback.message.edit_text(
                f"⚠️ {message}\n\n"
                f"🔄 Продолжаю создание сказки..."
            )
            await asyncio.sleep(2)  # Brief pause to show warning
    
    # Save to state for story generation
    await state.update_data(
        child_id=child_id,
        selected_theme=theme
    )
    
    # Show immediate response and start background task
    progress_message = await callback.message.edit_text(
        f"🎭 Создаю волшебную сказку для {child.name}!\n\n"
        f"✨ Тема: {theme or 'сюрприз'}\n"
        f"⏱️ Это займет 30-60 секунд\n\n"
        f"🔮 Начинаю работу..."
    )
    
    # Try background story generation first
    celery_available = False
    
    try:
        from ...tasks.story_tasks import generate_story_async
        from ...core.celery_app import celery_app
        
        # Check if Celery is available by inspecting active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print(f"🔧 Celery workers found: {list(active_workers.keys())}")
            celery_available = True
        else:
            print("⚠️ No active Celery workers found")
            
    except Exception as e:
        print(f"⚠️ Celery not available: {e}")
    
    if celery_available:
        try:
            # Launch async task
            task_result = generate_story_async.delay(
                child_id=child_id,
                theme=theme if theme != "random" else None,
                user_id=current_user.id,
                message_id=progress_message.message_id,
                chat_id=callback.message.chat.id
            )
            
            print(f"🚀 Celery task launched: {task_result.id}")
            
            # Immediate response to user
            await callback.message.edit_text(
                f"✅ Сказка для {child.name} запущена в работу!\n\n"
                f"🎭 Тема: {theme or 'сюрприз'}\n"
                f"⏱️ Ожидайте 30-60 секунд\n\n"
                f"🤖 Я пришлю готовую сказку, как только закончу!\n"
                f"📱 Можете пользоваться ботом дальше."
            )
            
            # Clear state
            await state.clear()
            return
            
        except Exception as e:
            print(f"❌ Error launching Celery task: {e}")
            celery_available = False
    
    # Fallback to synchronous generation
    print("🔄 Using synchronous story generation (fallback)")
    
    progress_message = await callback.message.edit_text(
        f"🎭 Создаю волшебную сказку...\n"
        f"✨ Это займет около минуты\n\n"
        f"🔮 Придумываю историю..."
    )
    
    # Generate story synchronously as fallback
    print(f"🏗️ Starting story creation for child_id: {child_id}")
    story_service = StoryService(session)
    story = await story_service.create_story(
        child_id=child_id,
        theme=theme if theme != "random" else None
    )
    
    # Update progress
    print(f"📝 Story created successfully: {story.id}")
    await callback.bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=progress_message.message_id,
        text="🎭 Сказка готова! 🎙️ Создаю аудио..."
    )
    print(f"✅ Progress message updated")
    
    # Generate audio with Charlotte's voice
    print(f"🎙️ Starting TTS generation...")
    tts_service = TTSService()
    print(f"🔧 TTS service created, calling generate_audio_for_story...")
    audio_buffer = await tts_service.generate_audio_for_story(
        story_text=story.story_text,
        child_name=story.child_name,
        child_age=story.child_age,
        mood="cheerful"
    )
    print(f"✅ TTS result: {'Success' if audio_buffer else 'Failed'}")
    
    # Send the story
    keyboard = get_feedback_keyboard(story.id, child_id)
    
    # Отправляем заголовок отдельно
    header_message = (
        f"📖 **Сказка для {story.child_name}**\n\n"
        f"🎯 Тема: {story.theme}\n"
        f"🎭 Персонажи: {', '.join(story.characters[:3])}\n"
        f"💫 Мораль: {story.moral}\n\n"
        f"{'='*30}"
    )
    
    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=header_message,
        parse_mode="Markdown"
    )
    
    # Отправляем текст сказки (разбиваем если слишком длинный)
    max_message_length = 4000  # Оставляем запас для форматирования
    
    if len(story.story_text) <= max_message_length:
        # Короткая сказка - отправляем целиком
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=story.story_text
        )
    else:
        # Длинная сказка - разбиваем на части
        chunks = []
        current_chunk = ""
        sentences = story.story_text.split('. ')
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 2 <= max_message_length:
                current_chunk += sentence + '. '
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + '. '
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Отправляем каждую часть
        for i, chunk in enumerate(chunks, 1):
            part_message = f"**Часть {i}/{len(chunks)}**\n\n{chunk}"
            await callback.bot.send_message(
                chat_id=callback.message.chat.id,
                text=part_message,
                parse_mode="Markdown"
            )
    
    # Отправляем финальное сообщение с кнопками
    final_message = f"{'='*30}\n\nПонравилась ли сказка {story.child_name}?"
    
    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=final_message,
        reply_markup=keyboard
    )
    
    # Send audio if generated successfully
    if audio_buffer:
        print(f"🎧 Sending audio file...")
        audio_file = BufferedInputFile(
            audio_buffer.read(),
            filename=f"story_{story.id}_{story.child_name}.mp3"
        )
        
        await callback.bot.send_audio(
            chat_id=callback.message.chat.id,
            audio=audio_file,
            title=f"Сказка для {story.child_name}",
            performer="Charlotte - Сказочница",
            caption=f"🎧 Аудиоверсия сказки '{story.theme}' для {story.child_name}"
        )
        print(f"✅ Audio sent successfully!")
    else:
        print(f"❌ No audio to send")
    
    # Delete progress message
    await callback.bot.delete_message(
        chat_id=callback.message.chat.id,
        message_id=progress_message.message_id
    )
    
    # Update user's free stories counter
    from ...services.user_service import UserService
    user_service = UserService(session)
    await user_service.use_free_story(current_user.id)
    
    # Clear state
    await state.clear()


@router.callback_query(F.data.startswith("custom_theme_"))
async def start_custom_theme(
    callback: CallbackQuery,
    state: FSMContext
):
    """Start custom theme input"""
    # Answer callback immediately to prevent timeout
    await callback.answer()
    
    child_id = int(callback.data.split("_")[2])
    
    await state.update_data(child_id=child_id)
    
    await callback.message.edit_text(
        "✏️ Напишите свою тему для сказки:\n\n"
        "💡 Например:\n"
        "• Путешествие в космос\n"
        "• Подводное приключение\n"
        "• Волшебный лес\n"
        "• День в цирке\n\n"
        "Опишите что хотите в сказке:"
    )
    
    await state.set_state(StoryCreationStates.custom_theme_input)


@router.message(StateFilter(StoryCreationStates.custom_theme_input))
async def handle_custom_theme(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    current_user: User
):
    """Handle custom theme input"""
    custom_theme = message.text.strip()
    
    if not custom_theme:
        await message.answer(
            "❌ Пожалуйста, опишите тему для сказки.\n"
            "Например: 'приключение в волшебном лесу'"
        )
        return
    
    data = await state.get_data()
    child_id = data.get("child_id")
    
    if not child_id:
        await message.answer("❌ Ошибка: не выбран ребенок. Начните заново с /story")
        await state.clear()
        return
    
    # Show progress
    progress_message = await message.answer(
        f"🎭 Создаю сказку на тему: '{custom_theme}'...\n"
        "✨ Это займет около минуты\n\n"
        "🔮 Придумываю историю..."
    )
    
    try:
        # Generate story with custom theme
        story_service = StoryService(session)
        story = await story_service.create_story(
            child_id=child_id,
            custom_theme=custom_theme
        )
        
        # Update progress
        await progress_message.edit_text("🎭 Сказка готова! 🎙️ Создаю аудио...")
        
        # Generate audio with Charlotte's voice - TEMPORARILY DISABLED  
        print(f"🎙️ [CUSTOM] TTS generation temporarily disabled for debugging")
        audio_buffer = None  # Temporarily disabled
        
        # Send the story
        keyboard = get_feedback_keyboard(story.id, child_id)
        
        story_message = (
            f"📖 **Сказка для {story.child_name}**\n\n"
            f"🎯 Тема: {story.theme}\n"
            f"🎭 Персонажи: {', '.join(story.characters[:3])}\n"
            f"💫 Мораль: {story.moral}\n\n"
            f"{'='*30}\n\n"
            f"{story.story_text}\n\n"
            f"{'='*30}\n\n"
            f"Понравилась ли сказка {story.child_name}?"
        )
        
        await message.answer(
            story_message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        # Delete progress message
        await progress_message.delete()
        
        # Update user's free stories counter
        from ...services.user_service import UserService
        user_service = UserService(session)
        await user_service.use_free_story(current_user.id)
        
        # Clear state
        await state.clear()
        
    except Exception as e:
        await progress_message.edit_text(
            f"😔 Произошла ошибка при создании сказки:\n{str(e)}\n\n"
            "Попробуйте еще раз через минуту."
        )
        await state.clear()


@router.callback_query(F.data.startswith("custom_theme_"))
async def handle_custom_theme_request(
    callback: CallbackQuery,
    state: FSMContext
):
    """Handle custom theme request"""
    # Answer callback immediately to prevent timeout
    await callback.answer()
    
    child_id = int(callback.data.split("_")[2])
    
    await state.update_data(child_id=child_id)
    await state.set_state(StoryCreationStates.awaiting_custom_theme)
    
    await callback.message.edit_text(
        "✏️ **Создание сказки на свою тему**\n\n"
        "Напишите тему для сказки (например: 'про дракона и замок' или 'о путешествии в лес'):\n\n"
        "💡 Чем подробнее опишете тему, тем интереснее получится сказка!"
    )


@router.message(StateFilter(StoryCreationStates.awaiting_custom_theme))
async def handle_custom_theme_input(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    current_user: User
):
    """Handle custom theme input and create story"""
    data = await state.get_data()
    child_id = data.get("child_id")
    custom_theme = message.text.strip()
    
    if not custom_theme:
        await message.answer("❌ Тема не может быть пустой. Пожалуйста, опишите тему сказки:")
        return
    
    if len(custom_theme) < 3:
        await message.answer("❌ Тема слишком короткая. Опишите тему подробнее:")
        return
    
    if len(custom_theme) > 200:
        await message.answer("❌ Тема слишком длинная (максимум 200 символов). Сократите описание:")
        return
    
    # Get child details
    child_service = ChildService(session)
    child = await child_service.get_child_by_id(child_id)
    
    if not child or child.user_id != current_user.id:
        await message.answer("❌ Произошла ошибка. Попробуйте снова или выберите /start")
        await state.clear()
        return
    
    # Show progress message
    progress_message = await message.answer(
        f"✨ Создаю персональную сказку для {child.name}...\n"
        f"🎯 Тема: {custom_theme}\n\n"
        f"⏳ Это может занять несколько секунд..."
    )
    
    try:
        # Generate story with custom theme
        from ...services.openai_service import OpenAIService
        openai_service = OpenAIService()
        story_data = await openai_service.generate_story(child, custom_theme=custom_theme)
        
        # Save story
        story_service = StoryService(session)
        story = await story_service.create_story(
            user_id=current_user.id,
            child_id=child_id,
            child_name=child.name,
            child_age=child.age,
            theme=custom_theme,
            characters=child.favorite_characters,
            story_text=story_data["story_text"],
            moral=story_data["moral"],
            tokens_used=story_data.get("tokens_used", 0),
            generation_time=story_data.get("generation_time", 0.0)
        )
        
        # Create feedback keyboard
        keyboard = get_feedback_keyboard(story.id, child_id)
        
        story_message = (
            f"📖 **Персональная сказка для {story.child_name}**\n\n"
            f"🎯 Тема: {story.theme}\n"
            f"🎭 Персонажи: {', '.join(story.characters[:3])}\n"
            f"💫 Мораль: {story.moral}\n\n"
            f"{'='*30}\n\n"
            f"{story.story_text}\n\n"
            f"{'='*30}\n\n"
            f"Понравилась ли сказка {story.child_name}?"
        )
        
        await message.answer(
            story_message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        # Delete progress message
        await progress_message.delete()
        
        # Update user's free stories counter
        from ...services.user_service import UserService
        user_service = UserService(session)
        await user_service.use_free_story(current_user.id)
        
        # Clear state
        await state.clear()
        
    except Exception as e:
        await progress_message.edit_text(
            f"😔 Произошла ошибка при создании сказки:\n{str(e)}\n\n"
            "Попробуйте еще раз через минуту."
        )
        await state.clear()


@router.callback_query(F.data.startswith("feedback_"))
async def handle_story_feedback(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Handle story feedback"""
    parts = callback.data.split("_")
    story_id = int(parts[1])
    feedback = parts[2]
    
    story_service = StoryService(session)
    success = await story_service.update_story_feedback(story_id, feedback)
    
    if success:
        feedback_messages = {
            'loved': "🥰 Ура! Рад, что сказка так понравилась!",
            'liked': "😊 Здорово! Спасибо за отзыв!",
            'neutral': "😐 Понятно, в следующий раз попробую лучше!",
            'disliked': "😔 Жаль... В следующий раз сделаю лучше!"
        }
        
        await callback.answer(
            feedback_messages.get(feedback, "Спасибо за отзыв!"),
            show_alert=True
        )
        
        # Update keyboard to show only "new story" option
        from ..keyboards.inline import get_story_type_keyboard
        story = await story_service.get_story_by_id(story_id)
        if story:
            keyboard = get_story_type_keyboard(story.child_id)
            
            try:
                await callback.message.edit_reply_markup(reply_markup=keyboard)
            except:
                pass  # Message might be too old to edit
    else:
        await callback.answer("❌ Ошибка при сохранении отзыва", show_alert=True)




@router.callback_query(F.data.startswith("edit_profile_"))
async def handle_edit_profile(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Handle profile editing request (placeholder)"""
    child_id = int(callback.data.split("_")[2])
    
    child_service = ChildService(session)
    child = await child_service.get_child_by_id(child_id)
    
    if not child:
        await callback.answer("❌ Ребенок не найден", show_alert=True)
        return
    
    profile_text = (
        f"⚙️ Профиль {child.name}:\n\n"
        f"👶 Имя: {child.name}\n"
        f"🎂 Возраст: {child.age} лет\n"
        f"🎭 Персонажи: {', '.join(child.favorite_characters)}\n"
        f"💫 Интересы: {', '.join(child.interests)}\n"
        f"⏱️ Длина сказок: {child.preferred_story_length} мин\n\n"
        f"🔧 Редактирование профилей скоро будет доступно!"
    )
    
    await callback.message.edit_text(profile_text)
    await callback.answer()
