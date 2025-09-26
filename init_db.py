#!/usr/bin/env python3
"""
Database initialization script for Railway deployment
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.database import engine
from src.core.config import settings
import alembic.command
import alembic.config


async def init_database():
    """Initialize database with migrations"""
    print("🔄 Initializing database...")
    
    try:
        # Run Alembic migrations
        alembic_cfg = alembic.config.Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        
        print("📦 Running database migrations...")
        alembic.command.upgrade(alembic_cfg, "head")
        print("✅ Database migrations completed successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)
    
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_database())
