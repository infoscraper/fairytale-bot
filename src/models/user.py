"""User model"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship

from ..core.database import Base


class User(Base):
    """User model for Telegram bot users"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=False)
    language_code = Column(String(10), default="ru")
    is_active = Column(Boolean, default=True)
    free_stories_used = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    children = relationship("Child", back_populates="user", lazy="selectin", cascade="all, delete-orphan")
    stories = relationship("Story", back_populates="user", lazy="selectin")
    story_series = relationship("StorySeries", back_populates="user", lazy="selectin")
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, first_name='{self.first_name}')>"
