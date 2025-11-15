#!/usr/bin/env python3
"""
Health check script for production deployment
"""
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
import redis.asyncio as redis
import aiohttp

async def check_database():
    """Check database connection"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not set")
            return False
            
        engine = create_async_engine(database_url)
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            await result.fetchone()
        await engine.dispose()
        print("✅ Database connection OK")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def check_redis():
    """Check Redis connection"""
    try:
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            print("❌ REDIS_URL not set")
            return False
            
        r = redis.from_url(redis_url)
        await r.ping()
        await r.close()
        print("✅ Redis connection OK")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

async def check_telegram():
    """Check Telegram Bot API"""
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            print("❌ TELEGRAM_BOT_TOKEN not set")
            return False
            
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        bot_info = data.get('result', {})
                        print(f"✅ Telegram Bot API OK - @{bot_info.get('username')}")
                        return True
        print("❌ Telegram Bot API failed")
        return False
    except Exception as e:
        print(f"❌ Telegram Bot API failed: {e}")
        return False

async def check_gemini_credentials():
    """Check Gemini TTS credentials"""
    try:
        creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        
        if not creds or not project_id:
            print("❌ Gemini TTS credentials not set")
            return False
            
        import json
        creds_data = json.loads(creds)
        if creds_data.get('project_id') == project_id:
            print("✅ Gemini TTS credentials OK")
            return True
        else:
            print("❌ Gemini TTS project ID mismatch")
            return False
    except Exception as e:
        print(f"❌ Gemini TTS credentials failed: {e}")
        return False

async def main():
    """Run all health checks"""
    print("🔍 Running health checks...")
    print("-" * 40)
    
    checks = [
        check_database(),
        check_redis(),
        check_telegram(),
        check_gemini_credentials()
    ]
    
    results = await asyncio.gather(*checks, return_exceptions=True)
    
    success_count = sum(1 for result in results if result is True)
    total_checks = len(results)
    
    print("-" * 40)
    print(f"📊 Health check results: {success_count}/{total_checks} passed")
    
    if success_count == total_checks:
        print("🎉 All checks passed! Bot should work correctly.")
        sys.exit(0)
    else:
        print("⚠️ Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
