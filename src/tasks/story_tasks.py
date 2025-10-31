"""
Celery tasks for story generation and TTS
"""
import asyncio
from typing import Optional
from ..core.celery_app import celery_app
from ..services.story_service import StoryService
from ..services.tts_service import TTSService
from ..core.database import async_session_maker
from ..models.story import Story
from aiogram import Bot
from aiogram.types import BufferedInputFile
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)

def _run_async(coro):
    """
    Safely run async coroutine in Celery worker context.
    Handles event loop creation/cleanup properly for prefork workers.
    """
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Loop is closed")
    except RuntimeError:
        # No event loop exists, create new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(coro)
    finally:
        # Clean up if we created the loop
        if not loop.is_running():
            pending = asyncio.all_tasks(loop)
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()

@celery_app.task(bind=True, max_retries=3)
def generate_story_async(self, child_id: int, theme: str, message_id: int, chat_id: int):
    """
    Асинхронная генерация сказки
    """
    try:
        # Запускаем асинхронную функцию безопасно для Celery
        return _run_async(_generate_story_internal(child_id, theme, message_id, chat_id))
    except Exception as exc:
        logger.error(f"Story generation failed: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

async def _generate_story_internal(child_id: int, theme: str, message_id: int, chat_id: int):
    """
    Внутренняя функция генерации сказки
    """
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    
    try:
        # Обновляем статус
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="🎨 Создаю сказку... (это может занять 30-60 секунд)"
        )
        
        # Генерируем сказку
        async with async_session_maker() as session:
            story_service = StoryService(session)
            story = await story_service.create_story(
                child_id=child_id,
                theme=theme
            )
            
            if not story:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text="❌ Не удалось создать сказку. Попробуйте еще раз."
                )
                return
            
            # Отправляем текст сказки
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"📖 **{story.theme.title()}**\n\n{story.story_text}\n\n💭 *{story.moral}*"
            )
            
            # Генерируем аудио в фоне
            generate_audio_async.delay(story.id, chat_id)
            
    except Exception as e:
        logger.error(f"Error in story generation: {e}")
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="❌ Произошла ошибка при создании сказки. Попробуйте позже."
        )
    finally:
        await bot.session.close()

@celery_app.task(bind=True, max_retries=2)
def generate_audio_async(self, story_id: int, chat_id: int):
    """
    Асинхронная генерация аудио
    """
    try:
        return _run_async(_generate_audio_internal(story_id, chat_id))
    except Exception as exc:
        logger.error(f"Audio generation failed: {exc}")
        # Don't retry audio generation too aggressively
        if self.request.retries < 1:
            raise self.retry(exc=exc, countdown=30)

async def _generate_audio_internal(story_id: int, chat_id: int):
    """
    Внутренняя функция генерации аудио
    """
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    
    try:
        # Получаем сказку
        async with async_session_maker() as session:
            from sqlalchemy import select
            from ..models.child import Child
            
            result = await session.execute(
                select(Story).where(Story.id == story_id)
            )
            story = result.scalar_one_or_none()
            if not story:
                return
            
            # Получаем настройки ребёнка для voice_id
            child_result = await session.execute(
                select(Child).where(Child.id == story.child_id)
            )
            child = child_result.scalar_one_or_none()
            voice_id = child.preferred_voice_id if child else None
            
            # Генерируем аудио
            tts_service = TTSService()
            audio_buffer = await tts_service.generate_audio_for_story(
                story_text=story.story_text,
                child_name=story.child_name,
                child_age=story.child_age,
                voice_id=voice_id
            )
            
            if audio_buffer:
                # Читаем данные из BytesIO
                audio_data = audio_buffer.read()
                audio_buffer.seek(0)  # Reset for potential retry
                
                # Создаём InputFile для aiogram
                audio_input = BufferedInputFile(
                    file=audio_data,
                    filename=f"story_{story_id}.mp3"
                )
                
                # Отправляем аудио
                await bot.send_voice(
                    chat_id=chat_id,
                    voice=audio_input,
                    caption=f"🎧 Аудиосказка: {story.theme.title()}"
                )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text="🔇 Не удалось создать аудиоверсию сказки, но текст доступен выше."
                )
                
    except Exception as e:
        logger.error(f"Error in audio generation: {e}")
    finally:
        await bot.session.close()
