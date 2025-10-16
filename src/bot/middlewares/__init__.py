"""Middlewares package"""
from .database import DatabaseMiddleware
from .user_context import UserContextMiddleware
from .content_safety import ContentSafetyMiddleware, ThemeValidationMiddleware
from .timeout_middleware import TimeoutMiddleware


def setup_middlewares(dp):
    """Setup all middlewares"""
    
    # Timeout middleware (should be first to wrap everything)
    dp.message.middleware(TimeoutMiddleware(timeout=30))
    dp.callback_query.middleware(TimeoutMiddleware(timeout=30))
    
    # Database session middleware (should be second)
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    
    # User context middleware (after database)
    dp.message.middleware(UserContextMiddleware())
    dp.callback_query.middleware(UserContextMiddleware())
    
    # Content safety middleware (after user context)
    dp.message.middleware(ContentSafetyMiddleware())
    dp.callback_query.middleware(ContentSafetyMiddleware())
    
    # Theme validation middleware (for callback queries)
    dp.callback_query.middleware(ThemeValidationMiddleware())
