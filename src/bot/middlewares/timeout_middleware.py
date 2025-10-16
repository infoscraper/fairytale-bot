"""
Middleware для предотвращения зависания бота
"""
import asyncio
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

logger = logging.getLogger(__name__)

class TimeoutMiddleware(BaseMiddleware):
    """
    Middleware для ограничения времени обработки запросов
    """
    
    def __init__(self, timeout: int = 30):
        """
        Args:
            timeout: Максимальное время обработки в секундах
        """
        self.timeout = timeout
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Обработка события с таймаутом
        """
        
        # Получаем информацию о пользователе для логов
        user_info = "unknown"
        chat_id = None
        
        if isinstance(event, (Message, CallbackQuery)):
            if hasattr(event, 'from_user') and event.from_user:
                user_info = f"@{event.from_user.username or event.from_user.id}"
            
            if isinstance(event, Message):
                chat_id = event.chat.id
            elif isinstance(event, CallbackQuery) and event.message:
                chat_id = event.message.chat.id
        
        try:
            # Запускаем обработчик с таймаутом
            result = await asyncio.wait_for(
                handler(event, data),
                timeout=self.timeout
            )
            return result
            
        except asyncio.TimeoutError:
            logger.warning(
                f"⏰ Handler timeout ({self.timeout}s) for user {user_info}"
            )
            
            # Отправляем сообщение о таймауте
            if chat_id:
                try:
                    if isinstance(event, Message):
                        await event.answer(
                            "⏰ Запрос обрабатывается слишком долго.\n"
                            "Попробуйте еще раз через несколько секунд."
                        )
                    elif isinstance(event, CallbackQuery):
                        await event.answer(
                            "⏰ Обработка заняла слишком много времени",
                            show_alert=True
                        )
                        if event.message:
                            await event.message.edit_text(
                                "⏰ Запрос обрабатывается слишком долго.\n"
                                "Попробуйте еще раз через несколько секунд."
                            )
                except Exception as e:
                    logger.error(f"Error sending timeout message: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error in handler for user {user_info}: {e}")
            
            # Отправляем сообщение об ошибке
            if chat_id:
                try:
                    if isinstance(event, Message):
                        await event.answer(
                            "❌ Произошла ошибка при обработке запроса.\n"
                            "Попробуйте еще раз."
                        )
                    elif isinstance(event, CallbackQuery):
                        await event.answer(
                            "❌ Произошла ошибка",
                            show_alert=True
                        )
                        if event.message:
                            await event.message.edit_text(
                                "❌ Произошла ошибка при обработке запроса.\n"
                                "Попробуйте еще раз."
                            )
                except Exception as send_error:
                    logger.error(f"Error sending error message: {send_error}")
            
            raise e
