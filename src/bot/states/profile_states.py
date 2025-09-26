"""FSM states for profile editing"""
from aiogram.fsm.state import State, StatesGroup


class ProfileEditStates(StatesGroup):
    """States for profile editing"""
    awaiting_new_name = State()
    awaiting_new_age = State()
    awaiting_new_characters = State()
    awaiting_new_interests = State()
    awaiting_new_length = State()
