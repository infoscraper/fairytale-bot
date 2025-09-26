"""Database middleware for Aiogram"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import async_session_maker


class DatabaseMiddleware(BaseMiddleware):
    """Middleware to provide database session for handlers"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Provide async database session"""
        async with async_session_maker() as session:
            data["session"] = session
            return await handler(event, data)
