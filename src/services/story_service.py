"""Story service for managing story creation and logic"""
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from .openai_service import OpenAIService
from .child_service import ChildService
from ..repositories.base import BaseRepository
from ..models import Story, Child


class StoryService:
    """Service for story creation and management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.openai_service = OpenAIService()
        self.child_service = ChildService(session)
        self.story_repo = BaseRepository(session, Story)
    
    async def create_story(
        self,
        child_id: int,
        theme: Optional[str] = None,
        custom_theme: Optional[str] = None
    ) -> Story:
        """Create a new story for child"""
        
        # Get child information
        child = await self.child_service.get_child_by_id(child_id)
        if not child:
            raise ValueError(f"Ребенок с ID {child_id} не найден")
        
        # Generate story using OpenAI
        story_data = await self.openai_service.generate_story(
            child=child,
            theme=theme,
            custom_theme=custom_theme
        )
        
        # Create story record in database
        story = await self.story_repo.create(
            user_id=child.user_id,
            child_id=child.id,
            child_name=child.name,
            child_age=child.age,
            theme=story_data["theme"],
            characters=story_data["characters"],
            story_text=story_data["story_text"],
            moral=story_data["moral"],
            tokens_used=story_data["tokens_used"],
            generation_time=story_data.get("generation_time", 0.0)
        )
        
        return story
    
    async def get_user_stories(self, user_id: int, limit: int = 10) -> List[Story]:
        """Get recent stories for user"""
        from sqlalchemy import select, and_
        
        result = await self.session.execute(
            select(Story)
            .where(Story.user_id == user_id)
            .order_by(Story.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_child_stories(self, child_id: int, limit: int = 10) -> List[Story]:
        """Get recent stories for specific child"""
        from sqlalchemy import select
        
        result = await self.session.execute(
            select(Story)
            .where(Story.child_id == child_id)
            .order_by(Story.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_story_by_id(self, story_id: int) -> Story:
        """Get specific story by ID"""
        from sqlalchemy import select
        
        result = await self.session.execute(
            select(Story)
            .where(Story.id == story_id)
        )
        return result.scalar_one_or_none()
    
    async def create_story_for_series(
        self,
        child_id: int,
        series_id: int,
        episode_number: int,
        theme: str,
        story_text: str = "",
        moral: str = "",
        tokens_used: int = 0,
        generation_time: float = 0.0
    ) -> Story:
        """Create story as part of a series"""
        from sqlalchemy import select
        
        # Get child
        child_result = await self.session.execute(
            select(Child).where(Child.id == child_id)
        )
        child = child_result.scalar_one_or_none()
        if not child:
            raise ValueError("Child not found")
        
        # Create story
        story = Story(
            user_id=child.user_id,
            child_id=child.id,
            series_id=series_id,
            child_name=child.name,
            child_age=child.age,
            theme=theme,
            characters=child.favorite_characters or [],
            story_text=story_text,
            moral=moral,
            episode_number=episode_number,
            generation_time=generation_time,
            tokens_used=tokens_used
        )
        
        self.session.add(story)
        await self.session.commit()
        await self.session.refresh(story)
        
        # Update user's free story count
        user_result = await self.session.execute(
            select(User).where(User.id == child.user_id)
        )
        user = user_result.scalar_one_or_none()
        if user and user.free_stories_used < 3:
            user.free_stories_used += 1
            await self.session.commit()
        
        return story
    
    async def update_story_feedback(self, story_id: int, feedback: str) -> bool:
        """Update story feedback from child"""
        valid_feedback = ["loved", "liked", "neutral", "disliked"]
        
        if feedback not in valid_feedback:
            return False
        
        story = await self.story_repo.update(story_id, child_feedback=feedback)
        return story is not None
    
    async def get_story_by_id(self, story_id: int) -> Optional[Story]:
        """Get story by ID"""
        return await self.story_repo.get_by_id(story_id)
    
    async def get_story_stats(self, user_id: int) -> Dict[str, int]:
        """Get story statistics for user"""
        from sqlalchemy import select, func
        
        # Total stories count
        total_result = await self.session.execute(
            select(func.count(Story.id)).where(Story.user_id == user_id)
        )
        total_stories = total_result.scalar_one()
        
        # Stories with feedback
        feedback_result = await self.session.execute(
            select(func.count(Story.id))
            .where(Story.user_id == user_id, Story.child_feedback.isnot(None))
        )
        stories_with_feedback = feedback_result.scalar_one()
        
        # Loved stories
        loved_result = await self.session.execute(
            select(func.count(Story.id))
            .where(Story.user_id == user_id, Story.child_feedback == "loved")
        )
        loved_stories = loved_result.scalar_one()
        
        return {
            "total_stories": total_stories,
            "stories_with_feedback": stories_with_feedback,
            "loved_stories": loved_stories,
            "feedback_rate": round(stories_with_feedback / total_stories * 100) if total_stories > 0 else 0
        }
    
    async def close(self):
        """Close OpenAI service"""
        await self.openai_service.close()
