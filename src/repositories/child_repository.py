"""Child repository"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from .base import BaseRepository
from ..models import Child


class ChildRepository(BaseRepository[Child]):
    """Repository for Child model"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Child)
    
    async def get_user_children(self, user_id: int) -> List[Child]:
        """Get all active children for user"""
        result = await self.session.execute(
            select(Child)
            .where(and_(Child.user_id == user_id, Child.is_active == True))
            .order_by(Child.created_at)
        )
        return list(result.scalars().all())
    
    async def get_children_by_age_range(self, min_age: int, max_age: int) -> List[Child]:
        """Get children by age range"""
        result = await self.session.execute(
            select(Child).where(
                and_(
                    Child.age.between(min_age, max_age),
                    Child.is_active == True
                )
            )
        )
        return list(result.scalars().all())
    
    async def create_child_profile(
        self, 
        user_id: int, 
        name: str, 
        age: int, 
        characters: List[str] = None,
        interests: List[str] = None,
        story_length: int = 5
    ) -> Child:
        """Create new child profile"""
        return await self.create(
            user_id=user_id,
            name=name.strip(),
            age=age,
            favorite_characters=characters or [],
            interests=interests or [],
            preferred_story_length=story_length
        )
    
    async def update_preferences(
        self, 
        child_id: int, 
        characters: List[str] = None,
        interests: List[str] = None,
        story_length: int = None
    ) -> Optional[Child]:
        """Update child preferences"""
        update_data = {}
        
        if characters is not None:
            update_data['favorite_characters'] = characters
        if interests is not None:
            update_data['interests'] = interests
        if story_length is not None:
            update_data['preferred_story_length'] = story_length
            
        if update_data:
            return await self.update(child_id, **update_data)
        return await self.get_by_id(child_id)
    
    async def deactivate_child(self, child_id: int) -> bool:
        """Deactivate child profile"""
        result = await self.update(child_id, is_active=False)
        return result is not None
