"""User service"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import User as TelegramUser

from ..repositories.user_repository import UserRepository
from ..models import User


class UserService:
    """Service for user operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
    
    async def get_or_create_user(self, telegram_user: TelegramUser) -> User:
        """Get existing user or create new one from Telegram user"""
        return await self.user_repo.get_or_create_from_telegram(telegram_user)
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID"""
        return await self.user_repo.get_by_telegram_id(telegram_id)
    
    async def can_create_free_story(self, user_id: int) -> bool:
        """Check if user can create free story (3 story limit)"""
        return await self.user_repo.can_create_free_story(user_id, free_limit=3)
    
    async def use_free_story(self, user_id: int) -> bool:
        """Use one free story"""
        return await self.user_repo.increment_free_stories(user_id)
    
    async def get_user_stats(self, user_id: int) -> dict:
        """Get user statistics"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return {}
        
        return {
            "user_id": user.id,
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "free_stories_used": user.free_stories_used,
            "children_count": len(user.children) if user.children else 0,
            "is_active": user.is_active,
            "created_at": user.created_at
        }
