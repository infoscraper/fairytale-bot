#!/usr/bin/env python3
"""
Fairytale Bot - Entry point
"""
import asyncio
import logging
from aiohttp import web
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


async def health_check(request):
    """Health check endpoint for Railway"""
    return web.json_response({"status": "healthy", "service": "fairytale-bot"})


async def main():
    """Main function to start the bot"""
    
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
    
    # Create web app for health checks
    app = web.Application()
    app.router.add_get('/health', health_check)
    
    # Start web server for health checks
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    
    try:
        logger.info("🚀 Starting Fairytale Bot...")
        logger.info(f"🤖 Bot token: {settings.TELEGRAM_BOT_TOKEN[:10]}...")
        logger.info(f"🌍 Environment: {settings.ENVIRONMENT}")
        logger.info("🏥 Health check available at /health")
        
        # Start polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        raise
    finally:
        await bot.session.close()
        await runner.cleanup()
        logger.info("🛑 Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
