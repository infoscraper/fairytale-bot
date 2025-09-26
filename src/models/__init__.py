"""Models package for proper SQLAlchemy relationships"""

# Import Base first
from ..core.database import Base

# Import models in dependency order to avoid circular import issues
from .user import User
from .child import Child
from .story import Story
from .story_series import StorySeries
from .child_preferences import ChildPreferences

__all__ = [
    "Base",
    "User", 
    "Child",
    "Story",
    "StorySeries", 
    "ChildPreferences"
]