"""Child service"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.child_repository import ChildRepository
from ..models import Child
from .content_safety_service import content_safety, SafetyLevel


class ChildService:
    """Service for child operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.child_repo = ChildRepository(session)
    
    async def get_user_children(self, user_id: int) -> List[Child]:
        """Get all children for user"""
        return await self.child_repo.get_user_children(user_id)
    
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
        
        # Validate age
        if not 2 <= age <= 12:
            raise ValueError("Возраст должен быть от 2 до 12 лет")
        
        # Validate name
        if not name or len(name.strip()) == 0:
            raise ValueError("Имя не может быть пустым")
        
        if len(name.strip()) > 50:
            raise ValueError("Имя не может быть длиннее 50 символов")
        
        # Clean and validate characters
        clean_characters = []
        if characters:
            for char in characters:
                char_clean = char.strip()
                if char_clean:
                    # Проверяем безопасность персонажа
                    safety_level, problematic_chars = content_safety.validate_characters([char_clean], age)
                    if safety_level == SafetyLevel.SAFE:
                        clean_characters.append(char_clean)
                    else:
                        raise ValueError(f"Персонаж '{char_clean}' содержит неподходящий для детей контент")
        
        # Clean and validate interests
        clean_interests = []
        if interests:
            for interest in interests:
                interest_clean = interest.strip()
                if interest_clean:
                    # Проверяем безопасность интереса
                    safety_level, problematic_interests = content_safety.validate_interests([interest_clean], age)
                    if safety_level == SafetyLevel.SAFE:
                        clean_interests.append(interest_clean)
                    else:
                        raise ValueError(f"Интерес '{interest_clean}' содержит неподходящий для детей контент")
        
        return await self.child_repo.create_child_profile(
            user_id=user_id,
            name=name.strip(),
            age=age,
            characters=clean_characters,
            interests=clean_interests,
            story_length=story_length
        )
    
    async def get_child_by_id(self, child_id: int) -> Optional[Child]:
        """Get child by ID"""
        return await self.child_repo.get_by_id(child_id)
    
    async def update_child_interests(self, child_id: int, interests: List[str]) -> Optional[Child]:
        """Update child interests"""
        clean_interests = [interest.strip() for interest in interests if interest.strip()]
        return await self.child_repo.update_preferences(child_id, interests=clean_interests)
    
    async def update_child_characters(self, child_id: int, characters: List[str]) -> Optional[Child]:
        """Update child favorite characters"""
        clean_characters = [char.strip() for char in characters if char.strip()]
        return await self.child_repo.update_preferences(child_id, characters=clean_characters)
    
    async def get_child_summary(self, child_id: int) -> dict:
        """Get child profile summary"""
        child = await self.child_repo.get_by_id(child_id)
        if not child:
            return {}
        
        return {
            "child_id": child.id,
            "name": child.name,
            "age": child.age,
            "favorite_characters": child.favorite_characters,
            "interests": child.interests,
            "preferred_story_length": child.preferred_story_length,
            "created_at": child.created_at
        }
    
    async def update_child_name(self, child_id: int, new_name: str) -> bool:
        """Update child's name"""
        child = await self.child_repo.get_by_id(child_id)
        if not child:
            return False
        
        child.name = new_name.strip()
        await self.session.commit()
        return True
    
    async def update_child_age(self, child_id: int, new_age: int) -> bool:
        """Update child's age with validation"""
        if not (2 <= new_age <= 8):
            return False
            
        child = await self.child_repo.get_by_id(child_id)
        if not child:
            return False
        
        child.age = new_age
        await self.session.commit()
        return True
    
    async def update_child_characters(self, child_id: int, new_characters: List[str]) -> bool:
        """Update child's favorite characters"""
        child = await self.child_repo.get_by_id(child_id)
        if not child:
            return False
        
        # Clean and validate characters
        cleaned_characters = []
        for char in new_characters:
            char_clean = char.strip()
            if char_clean:
                # Проверяем безопасность персонажа
                safety_level, problematic_chars = content_safety.validate_characters([char_clean], child.age)
                if safety_level == SafetyLevel.SAFE:
                    cleaned_characters.append(char_clean)
                else:
                    raise ValueError(f"Персонаж '{char_clean}' содержит неподходящий для детей контент")
        
        child.favorite_characters = cleaned_characters[:10]  # Max 10 characters
        await self.session.commit()
        return True
    
    async def update_child_interests(self, child_id: int, new_interests: List[str]) -> bool:
        """Update child's interests"""
        child = await self.child_repo.get_by_id(child_id)
        if not child:
            return False
        
        # Clean and validate interests
        cleaned_interests = []
        for interest in new_interests:
            interest_clean = interest.strip()
            if interest_clean:
                # Проверяем безопасность интереса
                safety_level, problematic_interests = content_safety.validate_interests([interest_clean], child.age)
                if safety_level == SafetyLevel.SAFE:
                    cleaned_interests.append(interest_clean)
                else:
                    raise ValueError(f"Интерес '{interest_clean}' содержит неподходящий для детей контент")
        
        child.interests = cleaned_interests[:10]  # Max 10 interests
        await self.session.commit()
        return True
    
    async def update_child_story_length(self, child_id: int, new_length: int) -> bool:
        """Update child's preferred story length"""
        if not (1 <= new_length <= 10):  # 1-10 minutes (оптимально для детей)
            return False
            
        child = await self.child_repo.get_by_id(child_id)
        if not child:
            return False
        
        child.preferred_story_length = new_length
        await self.session.commit()
        return True
    
    async def deactivate_child(self, child_id: int) -> bool:
        """Deactivate child profile"""
        child = await self.child_repo.get_by_id(child_id)
        if not child:
            return False
        
        child.is_active = False
        await self.session.commit()
        return True
    
    async def get_child_statistics(self, child_id: int) -> Optional[dict]:
        """Get statistics for a child"""
        child = await self.child_repo.get_by_id(child_id)
        if not child:
            return None
        
        from sqlalchemy import select, func
        from ..models import Story
        
        # Count stories for this child
        story_count_query = select(func.count(Story.id)).where(Story.child_id == child_id)
        result = await self.session.execute(story_count_query)
        story_count = result.scalar() or 0
        
        # Get favorite themes
        themes_query = select(Story.theme).where(Story.child_id == child_id)
        result = await self.session.execute(themes_query)
        themes = [row[0] for row in result.fetchall() if row[0]]
        
        # Count theme frequency
        theme_counts = {}
        for theme in themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        # Get top 3 themes
        top_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "child_id": child.id,
            "name": child.name,
            "age": child.age,
            "story_count": story_count,
            "favorite_characters": child.favorite_characters,
            "interests": child.interests,
            "preferred_story_length": child.preferred_story_length,
            "top_themes": top_themes,
            "created_at": child.created_at
        }
