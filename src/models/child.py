"""Child model"""
from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from ..core.database import Base


class Child(Base):
    """Child profile model"""
    __tablename__ = "children"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    favorite_characters = Column(JSON, default=list)
    interests = Column(JSON, default=list)
    preferred_story_length = Column(Integer, default=5)  # minutes (оптимально для детей)
    preferred_voice_id = Column(String(50), default="XB0fDUnXU5powFXDhCwa")  # Charlotte по умолчанию
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="children")
    stories = relationship("Story", back_populates="child", lazy="selectin")
    story_series = relationship("StorySeries", back_populates="child", lazy="selectin")
    
    def __repr__(self):
        return f"<Child(id={self.id}, name='{self.name}', age={self.age}, user_id={self.user_id})>"
