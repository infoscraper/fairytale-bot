"""FSM states for story series management"""
from aiogram.fsm.state import State, StatesGroup


class SeriesCreationStates(StatesGroup):
    """States for creating new story series"""
    awaiting_setting = State()
    awaiting_characters = State()
    awaiting_description = State()
    confirm_series = State()


class SeriesManagementStates(StatesGroup):
    """States for managing existing series"""
    awaiting_episode_prompt = State()
    confirm_complete_series = State()
    confirm_deactivate_series = State()
