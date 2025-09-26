"""Content Safety Middleware - проверка безопасности контента"""
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from ...services.content_safety_service import content_safety, SafetyLevel

logger = logging.getLogger(__name__)


class ContentSafetyMiddleware(BaseMiddleware):
    """Middleware для проверки безопасности контента"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Проверка безопасности контента перед обработкой
        """
        
        # Проверяем только сообщения пользователей
        if isinstance(event, Message) and event.text:
            user_data = data.get('current_user')
            if not user_data:
                return await handler(event, data)
            
            # Получаем информацию о детях пользователя
            child_service = data.get('child_service')
            if not child_service:
                return await handler(event, data)
            
            children = await child_service.get_user_children(user_data.id)
            if not children:
                return await handler(event, data)
            
            # Проверяем безопасность текста для всех детей пользователя
            text = event.text.strip()
            
            for child in children:
                safety_level, violations = content_safety.validate_input(text, child.age)
                
                if safety_level == SafetyLevel.BLOCKED:
                    logger.warning(f"Blocked content from user {user_data.id}: {text[:50]}...")
                    
                    await event.answer(
                        "🚫 Извините, но этот контент содержит неподходящие для детей материалы.\n\n"
                        "Пожалуйста, используйте только добрые и позитивные темы для сказок.",
                        show_alert=True
                    )
                    return  # Блокируем обработку
            
            # Для предупреждений отправляем уведомление, но разрешаем
            if safety_level == SafetyLevel.WARNING:
                logger.info(f"Warning content from user {user_data.id}: {text[:50]}...")
                
                await event.answer(
                    "⚠️ Внимание: эта тема может быть сложной для детей младшего возраста.\n"
                    "Убедитесь, что сказка будет подходящей для вашего ребенка.",
                    show_alert=True
                )
        
        return await handler(event, data)


class ThemeValidationMiddleware(BaseMiddleware):
    """Middleware для валидации тем сказок"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Валидация тем сказок
        """
        
        if isinstance(event, CallbackQuery) and event.data:
            # Проверяем callback с темой
            if event.data.startswith("theme_"):
                user_data = data.get('current_user')
                if not user_data:
                    return await handler(event, data)
                
                # Извлекаем тему из callback
                theme = event.data.split("_", 1)[1]
                if theme == "random":
                    return await handler(event, data)
                
                # Получаем информацию о выбранном ребенке
                child_service = data.get('child_service')
                if not child_service:
                    return await handler(event, data)
                
                # Нужно получить ID ребенка из callback или состояния
                # Для упрощения проверяем для всех детей пользователя
                children = await child_service.get_user_children(user_data.id)
                
                for child in children:
                    safety_level, message = content_safety.validate_theme(theme, child.age)
                    
                    if safety_level == SafetyLevel.BLOCKED:
                        logger.warning(f"Blocked theme '{theme}' for child {child.id}")
                        
                        await event.answer(
                            f"🚫 {message}\n\n"
                            f"Попробуйте выбрать другую тему из предложенных.",
                            show_alert=True
                        )
                        return  # Блокируем обработку
                    
                    elif safety_level == SafetyLevel.WARNING:
                        logger.info(f"Warning theme '{theme}' for child {child.id}")
                        
                        await event.answer(
                            f"⚠️ {message}\n\n"
                            f"Вы уверены, что хотите продолжить с этой темой?",
                            show_alert=True
                        )
        
        return await handler(event, data)
