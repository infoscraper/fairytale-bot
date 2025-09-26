"""States for story creation flow"""
from aiogram.fsm.state import State, StatesGroup


class StoryCreationStates(StatesGroup):
    """States for creating a story"""
    
    # Child profile creation
    awaiting_child_name = State()
    awaiting_child_age = State()
    awaiting_characters = State()
    awaiting_interests = State()
    
    # Story customization
    awaiting_custom_theme = State()
    
    # Story creation
    selecting_child = State()
    selecting_theme = State()
    custom_theme_input = State()
    generating_story = State()
    
    # Story feedback
    awaiting_feedback = State()


class ProfileStates(StatesGroup):
    """States for managing child profiles"""
    
    # Profile editing
    editing_name = State()
    editing_age = State()
    editing_characters = State()
    editing_interests = State()
    editing_story_length = State()
    
    # Profile selection
    selecting_profile_to_edit = State()


class SeriesStates(StatesGroup):
    """States for managing story series"""
    
    # Series creation
    creating_new_series = State()
    selecting_series_theme = State()
    
    # Series management
    selecting_active_series = State()
    viewing_series_episodes = State()
