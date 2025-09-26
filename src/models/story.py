"""Story model"""
from sqlalchemy import Column, Integer, String, Text, JSON, Boolean, DateTime, ForeignKey, Float, func
from sqlalchemy.orm import relationship

from ..core.database import Base


class Story(Base):
    """Story model"""
    __tablename__ = "stories"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False, index=True)
    series_id = Column(Integer, ForeignKey("story_series.id"), nullable=True, index=True)
    child_name = Column(String(100), nullable=False)
    child_age = Column(Integer, nullable=False)
    
    # Story content
    theme = Column(String(200), nullable=True)
    characters = Column(JSON, default=list)
    story_text = Column(Text, nullable=False)
    moral = Column(String(500), nullable=True)
    
    # Audio files
    audio_file_id = Column(String(255), nullable=True)  # Telegram file ID
    music_file_id = Column(String(255), nullable=True)  # Music file ID
    full_audio_file_id = Column(String(255), nullable=True)  # Final mixed audio
    
    # Series information (temporarily disabled)
    # series_id = Column(Integer, ForeignKey("story_series.id"), nullable=True)
    episode_number = Column(Integer, nullable=True)
    
    # Generation metadata
    generation_time = Column(Float, nullable=True)  # seconds
    tokens_used = Column(Integer, nullable=True)
    
    # Feedback
    child_feedback = Column(String(20), nullable=True)  # loved, liked, neutral, disliked
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="stories")
    child = relationship("Child", back_populates="stories")
    series = relationship("StorySeries", back_populates="stories")
    
    def __repr__(self):
        return f"<Story(id={self.id}, child_name='{self.child_name}', theme='{self.theme}')>"
