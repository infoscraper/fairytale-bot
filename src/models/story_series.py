"""Story series model"""
from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime, ForeignKey, func, Text
from sqlalchemy.orm import relationship

from ..core.database import Base


class StorySeries(Base):
    """Story series model for continuing stories"""
    __tablename__ = "story_series"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False, index=True)
    
    series_name = Column(String(200), nullable=False)  # "Приключения Савы"
    description = Column(Text)  # Описание серии
    main_character = Column(String(100), nullable=False)  # имя ребенка
    setting = Column(String(200), nullable=False)  # "Волшебный лес", "Подводное царство"
    world_details = Column(JSON, default=dict)  # Детали мира серии
    recurring_characters = Column(JSON, default=list)  # постоянные персонажи серии
    
    total_episodes = Column(Integer, default=0)
    current_episode = Column(Integer, default=0)
    last_episode_date = Column(DateTime, nullable=True)
    
    is_completed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="story_series")
    child = relationship("Child", back_populates="story_series")
    stories = relationship("Story", back_populates="series", order_by="Story.episode_number")
    
    def __repr__(self):
        return f"<StorySeries(id={self.id}, name='{self.series_name}', episodes={self.total_episodes})>"
