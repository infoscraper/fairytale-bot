"""Middlewares package"""
from .database import DatabaseMiddleware
from .user_context import UserContextMiddleware
from .content_safety import ContentSafetyMiddleware, ThemeValidationMiddleware


def setup_middlewares(dp):
    """Setup all middlewares"""
    
    # Database session middleware (should be first)
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
