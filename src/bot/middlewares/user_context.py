"""User context middleware"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from ...services.user_service import UserService


class UserContextMiddleware(BaseMiddleware):
    """Middleware to automatically get/create user context"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Provide user context"""
        session: AsyncSession = data.get("session")
        
        if session and hasattr(event, "from_user") and event.from_user:
            user_service = UserService(session)
            user = await user_service.get_or_create_user(event.from_user)
            data["current_user"] = user
            data["user_service"] = user_service
        
        return await handler(event, data)
