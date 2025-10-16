#!/usr/bin/env python3
"""
Fairytale Bot - Entry point
"""
import asyncio
import uuid
import logging
import os
import sys
import signal
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from .core.config import settings
from .core.redis import get_redis, close_redis
from .bot.handlers import setup_routers
from .bot.middlewares import setup_middlewares

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Silence noisy third-party loggers in production
logging.getLogger("aiogram.dispatcher").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("elevenlabs").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def init_database():
    """Initialize database with migrations"""
    logger.info("🔄 Initializing database...")
    
    try:
        # Platform-agnostic auto-migration toggle (works for Dokploy, Railway, etc.)
        auto_migrate = os.getenv("AUTO_MIGRATE", "0") == "1"
        if auto_migrate:
            logger.info("🗄️ AUTO_MIGRATE=1 → creating tables if not exist...")
            
            # Import database components
            from .core.database import engine
            from .models import Base
            
            # Create all tables
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("✅ Database tables created successfully!")
        else:
            logger.info("⏭️ AUTO_MIGRATE is disabled — skipping automatic migrations")
            
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        # Don't exit in production, just log the error
        if not (os.getenv("AUTO_MIGRATE", "0") == "1"):
            raise


async def main():
    """Main function to start the bot"""
    
    # Initialize database first (when AUTO_MIGRATE=1)
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
        
        # Gate polling by environment and role to avoid conflicts
        should_poll = settings.BOT_ROLE == "poller" and settings.ENVIRONMENT in {"production", "staging", "development"}
        if not should_poll:
            logger.warning(f"🤚 Polling disabled. ENVIRONMENT={settings.ENVIRONMENT}, BOT_ROLE={settings.BOT_ROLE}")
            return

        # Acquire distributed lock to ensure a single poller
        lock_key = f"bot:poller_lock:{settings.TELEGRAM_BOT_TOKEN[:8]}"
        lock_value = str(uuid.uuid4())
        got_lock = await redis.set(lock_key, lock_value, ex=120, nx=True)
        
        if not got_lock:
            # Check if existing lock is expired or from a dead process
            logger.warning("🔒 Another instance holds poller lock. Checking if it's alive...")
            
            # Try to get the current lock value and TTL
            current_value = await redis.get(lock_key)
            ttl = await redis.ttl(lock_key)
            
            if current_value and ttl > 0:
                if ttl > 60:  # Lock was recently renewed, respect it
                    logger.warning(f"🔒 Lock is active (TTL: {ttl}s). Exiting without polling.")
                    logger.warning("💡 This usually means multiple bot instances are running!")
                    logger.warning("🔧 Check Dokploy configuration: Replicas should be = 1")
                    return
                else:
                    # Lock is expiring soon, might be from a dying process
                    logger.info(f"🕐 Lock expires soon (TTL: {ttl}s). Attempting to claim...")
                    
                    # More aggressive approach: try to claim immediately
                    await redis.delete(lock_key)
                    await asyncio.sleep(1)  # Brief pause
                    
                    got_lock = await redis.set(lock_key, lock_value, ex=120, nx=True)
                    if got_lock:
                        logger.info("✅ Successfully claimed expiring lock!")
                    else:
                        logger.warning("❌ Failed to claim expiring lock. Another instance got it first.")
                        return
            elif ttl <= 0:
                logger.info("🧹 Found expired lock, attempting to claim it...")
                # Force delete and claim
                await redis.delete(lock_key)
                got_lock = await redis.set(lock_key, lock_value, ex=120, nx=True)
                if got_lock:
                    logger.info("✅ Successfully claimed expired lock!")
                else:
                    logger.warning("❌ Failed to claim expired lock. Another instance got it first.")
                    return
            else:
                logger.warning("🔒 Lock exists but no TTL info. Attempting force claim...")
                # Force delete and try to claim
                await redis.delete(lock_key)
                await asyncio.sleep(2)
                got_lock = await redis.set(lock_key, lock_value, ex=120, nx=True)
                if not got_lock:
                    logger.warning("❌ Failed to force claim lock. Exiting.")
                    return

        # Background task to renew lock TTL
        renew_task = None
        async def _renew_lock():
            try:
                while True:
                    await asyncio.sleep(60)
                    try:
                        current = await redis.get(lock_key)
                        if current == lock_value:
                            await redis.expire(lock_key, 120)
                        else:
                            logger.warning("🔓 Poller lock lost to another instance. Stopping polling.")
                            await dp.stop_polling()
                            break
                    except Exception as e:
                        logger.error(f"❌ Error renewing poller lock: {e}")
            except asyncio.CancelledError:
                pass

        renew_task = asyncio.create_task(_renew_lock())

        # Setup signal handlers for graceful shutdown
        shutdown_event = asyncio.Event()
        
        def signal_handler(signum, frame):
            logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
            shutdown_event.set()
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            # Start polling with shutdown handling
            polling_task = asyncio.create_task(dp.start_polling(bot))
            shutdown_task = asyncio.create_task(shutdown_event.wait())
            
            # Wait for either polling to complete or shutdown signal
            done, pending = await asyncio.wait(
                [polling_task, shutdown_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                    
        finally:
            if renew_task:
                renew_task.cancel()
            # Release lock if still owned
            try:
                current = await redis.get(lock_key)
                if current == lock_value:
                    await redis.delete(lock_key)
            except Exception as e:
                logger.error(f"❌ Error releasing poller lock: {e}")
        
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        raise
    finally:
        await bot.session.close()
        await close_redis()
        logger.info("🛑 Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
