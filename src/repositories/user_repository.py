"""User repository"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram.types import User as TelegramUser

from .base import BaseRepository
from ..models import User


class UserRepository(BaseRepository[User]):
    """Repository for User model"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID"""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def create_from_telegram_user(self, telegram_user: TelegramUser) -> User:
        """Create user from Telegram user object"""
        return await self.create(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name or "Unknown",
            language_code=telegram_user.language_code or "ru"
        )
    
    async def get_or_create_from_telegram(self, telegram_user: TelegramUser) -> User:
        """Get existing user or create new one"""
        user = await self.get_by_telegram_id(telegram_user.id)
        
        if user is None:
            user = await self.create_from_telegram_user(telegram_user)
        
        return user
    
    async def increment_free_stories(self, user_id: int) -> bool:
        """Increment free stories used counter"""
        user = await self.get_by_id(user_id)
        if user:
            await self.update(user_id, free_stories_used=user.free_stories_used + 1)
            return True
        return False
    
    async def can_create_free_story(self, user_id: int, free_limit: int = 3) -> bool:
        """Check if user can create free story"""
        user = await self.get_by_id(user_id)
        if user:
            return user.free_stories_used < free_limit
        return False
