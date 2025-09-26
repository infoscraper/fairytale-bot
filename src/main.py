#!/usr/bin/env python3
"""
Fairytale Bot - Entry point
"""
import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from .core.config import settings
from .core.redis import get_redis
from .bot.handlers import setup_routers
from .bot.middlewares import setup_middlewares

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def init_database():
    """Initialize database with migrations"""
    logger.info("🔄 Initializing database...")
    
    try:
        # Check if we're in Railway environment
        if os.getenv("RAILWAY_ENVIRONMENT"):
            logger.info("🚂 Running in Railway environment, applying migrations...")
            
            # Import Alembic components
            import alembic.command
            import alembic.config
            
            # Run Alembic migrations
            alembic_cfg = alembic.config.Config("/app/alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
            
            logger.info("📦 Running database migrations...")
            alembic.command.upgrade(alembic_cfg, "head")
            logger.info("✅ Database migrations completed successfully!")
        else:
            logger.info("🏠 Running locally, skipping automatic migrations")
            
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        # Don't exit in production, just log the error
        if not os.getenv("RAILWAY_ENVIRONMENT"):
            raise


async def main():
    """Main function to start the bot"""
    
    # Initialize database first (only in Railway)
    await init_database()
    
    # Initialize bot with default properties
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Setup Redis storage for FSM
    redis = await get_redis()
    storage = RedisStorage(redis=redis)
    
    # Create dispatcher with FSM storage
    dp = Dispatcher(storage=storage)
    
    # Setup middlewares and routers
    setup_middlewares(dp)
    setup_routers(dp)
    
    try:
        logger.info("🚀 Starting Fairytale Bot...")
        logger.info(f"🤖 Bot token: {settings.TELEGRAM_BOT_TOKEN[:10]}...")
        logger.info(f"🌍 Environment: {settings.ENVIRONMENT}")
        
        # Start polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        raise
    finally:
        await bot.session.close()
        logger.info("🛑 Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
