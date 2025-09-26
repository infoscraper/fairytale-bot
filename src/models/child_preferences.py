"""Child preferences model"""
from sqlalchemy import Column, Integer, JSON, DateTime, ForeignKey, func

from ..core.database import Base


class ChildPreferences(Base):
    """Child preferences for ML personalization"""
    __tablename__ = "child_preferences"
    
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False, unique=True)
    
    # Learned preferences
    preferred_themes = Column(JSON, default=list)  # темы которые нравятся
    avoided_themes = Column(JSON, default=list)   # темы которых избегать
    favorite_music_styles = Column(JSON, default=list)
    preferred_voices = Column(JSON, default=list)  # предпочтительные голоса
    
    # Behavioral patterns
    attention_span = Column(Integer, default=10)  # minutes, learned from usage
    interaction_count = Column(Integer, default=0)
    
    # Timestamps
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<ChildPreferences(child_id={self.child_id}, interactions={self.interaction_count})>"
