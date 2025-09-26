"""Handlers package"""
from .start import router as start_router
from .child_profile import router as child_profile_router
from .story_creation import router as story_creation_router
from .profile_management import router as profile_management_router
from .history import router as history_router
# from .series_management import router as series_router

def setup_routers(dp):
    """Setup all routers"""
    # FSM handlers should be first to catch state-specific messages
    dp.include_router(child_profile_router)
    dp.include_router(profile_management_router)
    dp.include_router(story_creation_router)
    # dp.include_router(series_router)
    dp.include_router(history_router)
    dp.include_router(start_router)
