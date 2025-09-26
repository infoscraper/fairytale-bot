"""Story series service for managing story series"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from datetime import datetime

from ..models import StorySeries, Child, User, Story
from .openai_service import OpenAIService
from ..core.config import settings


class StorySeriesService:
    """Service for managing story series"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.openai_service = OpenAIService()
    
    async def create_series(
        self,
        user_id: int,
        child_id: int,
        child_name: str,
        setting: str,
        recurring_characters: List[str],
        description: Optional[str] = None
    ) -> StorySeries:
        """Create new story series"""
        
        series_name = f"Приключения {child_name}"
        if setting:
            series_name += f" в {setting.lower()}"
        
        series = StorySeries(
            user_id=user_id,
            child_id=child_id,
            series_name=series_name,
            description=description or f"Увлекательные приключения {child_name} в мире {setting}",
            main_character=child_name,
            setting=setting,
            world_details={
                "setting": setting,
                "mood": "добрый и волшебный",
                "created_at": datetime.now().isoformat()
            },
            recurring_characters=recurring_characters,
            total_episodes=0,
            current_episode=0
        )
        
        self.session.add(series)
        await self.session.commit()
        await self.session.refresh(series)
        
        return series
    
    async def get_user_series(self, user_id: int, active_only: bool = True) -> List[StorySeries]:
        """Get all series for user"""
        query = select(StorySeries).where(StorySeries.user_id == user_id)
        
        if active_only:
            query = query.where(StorySeries.is_active == True)
        
        query = query.order_by(desc(StorySeries.last_episode_date))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_child_series(self, child_id: int, active_only: bool = True) -> List[StorySeries]:
        """Get all series for specific child"""
        query = select(StorySeries).where(StorySeries.child_id == child_id)
        
        if active_only:
            query = query.where(StorySeries.is_active == True)
        
        query = query.order_by(desc(StorySeries.last_episode_date))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_series_by_id(self, series_id: int) -> Optional[StorySeries]:
        """Get series by ID"""
        result = await self.session.execute(
            select(StorySeries).where(StorySeries.id == series_id)
        )
        return result.scalar_one_or_none()
    
    async def create_next_episode(
        self,
        series_id: int,
        custom_prompt: Optional[str] = None
    ) -> Story:
        """Create next episode in series"""
        
        # Get series
        series = await self.get_series_by_id(series_id)
        if not series:
            raise ValueError("Series not found")
        
        # Get child
        child_result = await self.session.execute(
            select(Child).where(Child.id == series.child_id)
        )
        child = child_result.scalar_one_or_none()
        if not child:
            raise ValueError("Child not found")
        
        # Get previous episodes for context
        previous_episodes = await self.get_series_episodes(series_id, limit=3)
        
        # Generate story content
        story_data = await self._generate_series_episode(
            series=series,
            child=child,
            previous_episodes=previous_episodes,
            custom_prompt=custom_prompt
        )
        
        # Create story
        next_episode_num = series.current_episode + 1
        
        from .story_service import StoryService
        story_service = StoryService(self.session)
        
        story = await story_service.create_story_for_series(
            child_id=child.id,
            series_id=series.id,
            episode_number=next_episode_num,
            theme=story_data["theme"],
            story_text=story_data["story_text"],
            moral=story_data["moral"],
            tokens_used=story_data.get("tokens_used", 0),
            generation_time=story_data.get("generation_time", 0.0)
        )
        
        # Update series
        series.current_episode = next_episode_num
        series.total_episodes = max(series.total_episodes, next_episode_num)
        series.last_episode_date = datetime.now()
        
        await self.session.commit()
        
        return story
    
    async def get_series_episodes(self, series_id: int, limit: int = 10) -> List[Story]:
        """Get episodes from series"""
        result = await self.session.execute(
            select(Story)
            .where(Story.series_id == series_id)
            .order_by(Story.episode_number)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def complete_series(self, series_id: int) -> bool:
        """Mark series as completed"""
        series = await self.get_series_by_id(series_id)
        if not series:
            return False
        
        series.is_completed = True
        await self.session.commit()
        return True
    
    async def deactivate_series(self, series_id: int) -> bool:
        """Deactivate series"""
        series = await self.get_series_by_id(series_id)
        if not series:
            return False
        
        series.is_active = False
        await self.session.commit()
        return True
    
    async def _generate_series_episode(
        self,
        series: StorySeries,
        child: Child,
        previous_episodes: List[Story],
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate story content for series episode using OpenAI"""
        
        # Build context from previous episodes
        context = self._build_series_context(series, previous_episodes)
        
        # Determine theme
        if custom_prompt:
            theme = custom_prompt
        else:
            theme = f"Новое приключение в {series.setting}"
        
        # Build episode prompt
        prompt = self._build_episode_prompt(
            series=series,
            child=child,
            context=context,
            theme=theme,
            episode_number=series.current_episode + 1
        )
        
        # Generate with OpenAI
        try:
            # Use Chat Completions API with proper parameters for GPT-5
            request_params = {
                "model": settings.OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": self._get_series_system_prompt()},
                    {"role": "user", "content": prompt}
                ]
            }
            
            # Use correct parameters based on model
            if settings.OPENAI_MODEL.startswith('gpt-5'):
                request_params["max_completion_tokens"] = 800  # Для коротких эпизодов
                # GPT-5 uses default temperature=1.0 only
            else:
                request_params["max_tokens"] = 800  # Ограничиваем эпизоды серий
                request_params["temperature"] = 0.8
            
            response = await self.openai_service.client.chat.completions.create(**request_params)
            
            story_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            # Extract moral
            moral = self._extract_episode_moral(story_text)
            
            return {
                "story_text": story_text,
                "theme": theme,
                "moral": moral,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            raise Exception(f"Ошибка генерации эпизода серии: {str(e)}")
    
    def _build_series_context(self, series: StorySeries, previous_episodes: List[Story]) -> str:
        """Build context from series and previous episodes"""
        context_parts = [
            f"Серия: {series.series_name}",
            f"Мир: {series.setting}",
            f"Главный герой: {series.main_character}",
            f"Постоянные персонажи: {', '.join(series.recurring_characters)}"
        ]
        
        if previous_episodes:
            context_parts.append("\\nПредыдущие эпизоды:")
            for i, episode in enumerate(previous_episodes[-3:], 1):  # Last 3 episodes
                context_parts.append(f"Эпизод {episode.episode_number}: {episode.theme}")
                if episode.moral:
                    context_parts.append(f"Мораль: {episode.moral}")
        
        return "\\n".join(context_parts)
    
    def _build_episode_prompt(
        self,
        series: StorySeries,
        child: Child,
        context: str,
        theme: str,
        episode_number: int
    ) -> str:
        """Build prompt for series episode"""
        
        age_guidance = self._get_age_guidance(child.age)
        
        prompt = f"""Создай эпизод #{episode_number} для продолжающейся серии сказок.

{context}

Тема этого эпизода: {theme}
Возраст ребенка: {child.age} лет

Требования:
1. {age_guidance}
2. Используй постоянных персонажей серии и мир {series.setting}
3. Сохраняй преемственность с предыдущими эпизодами
4. История должна быть законченной, но оставлять возможность для продолжения
5. Включи элементы, связанные с интересами ребенка: {', '.join(child.interests or [])}
6. Длина сказки: примерно {child.preferred_story_length * 100} слов

Структура:
- Краткая связь с предыдущими событиями (если есть)
- Новое приключение с четкой завязкой, развитием и развязкой
- Мораль эпизода
- Намек на возможные будущие приключения

Начни рассказ и создай увлекательный эпизод!"""

        return prompt
    
    def _get_series_system_prompt(self) -> str:
        """Get system prompt for series generation"""
        return """Ты опытный сказочник, специализирующийся на создании продолжающихся серий сказок для детей. 

Твоя задача - создавать эпизоды, которые:
- Сохраняют единство мира и персонажей
- Развивают характеры и отношения между персонажами
- Каждый эпизод является законченной историей
- Поддерживают интерес к продолжению серии
- Адаптированы под возраст ребенка
- Содержат поучительные элементы

Стиль: добрый, увлекательный, с элементами волшебства и приключений."""
    
    def _get_age_guidance(self, age: int) -> str:
        """Get age-appropriate guidance for series"""
        if age <= 3:
            return "Простые слова, повторяющиеся элементы, знакомые ситуации"
        elif age <= 5:
            return "Понятные эмоции, простые конфликты, дружба и помощь"
        elif age <= 7:
            return "Более сложные приключения, решение проблем, храбрость"
        else:
            return "Командная работа, преодоление трудностей, ответственность"
    
    def _extract_episode_moral(self, story_text: str) -> str:
        """Extract moral from episode (enhanced with diverse morals)"""
        import random
        
        # Сначала ищем явные моральные указания в тексте
        moral_keywords = ["мораль:", "урок:", "запомни:", "главное:", "важно понимать:", "вывод:"]
        
        text_lower = story_text.lower()
        for keyword in moral_keywords:
            if keyword in text_lower:
                start_pos = text_lower.find(keyword)
                remaining_text = story_text[start_pos + len(keyword):].strip()
                
                # Take the sentence containing the moral
                sentences = remaining_text.split('.')
                if sentences and sentences[0].strip():
                    return sentences[0].strip() + '.'
        
        # Fallback: try to extract from last few sentences
        sentences = story_text.split('.')
        if len(sentences) >= 2:
            last_sentence = sentences[-2].strip()
            if len(last_sentence) > 10:  # Проверяем что это не случайный фрагмент
                return last_sentence + '.'
        
        # Если не можем извлечь - выбираем случайную подходящую мораль
        episode_morals = [
            "Дружба — это одно из самых важных сокровищ в жизни",
            "Важно быть добрым, смелым и помогать другим",
            "Даже маленькие поступки доброты делают мир лучше",
            "Настоящая смелость — не в силе, а в сердце",
            "Лучше вместе, чем поодиночке",
            "Честность всегда важнее обмана",
            "Труд и терпение помогают достичь мечты",
            "Маленькие герои тоже совершают большие дела",
            "Настоящий друг всегда рядом, когда трудно",
            "Каждый особенный по-своему, и это ценно"
        ]
        
        return random.choice(episode_morals)
    
    async def close(self):
        """Close the session"""
        await self.session.close()
