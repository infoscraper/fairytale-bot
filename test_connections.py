#!/usr/bin/env python3
"""
Test script for production connections
"""
import asyncio
import os
import sys
import json

async def test_database():
    """Test database connection"""
    print("🔍 Testing database connection...")
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        
        database_url = os.getenv('DATABASE_URL')
        print(f"   URL: {database_url}")
        
        if not database_url:
            print("❌ DATABASE_URL not set")
            return False
            
        # Ensure asyncpg driver
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            print(f"   Fixed URL: {database_url}")
            
        engine = create_async_engine(database_url)
        async with engine.begin() as conn:
            result = await conn.execute("SELECT version()")
            version = await result.fetchone()
            print(f"✅ Database OK: {version[0]}")
        await engine.dispose()
        return True
    except Exception as e:
        print(f"❌ Database failed: {e}")
        return False

async def test_redis():
    """Test Redis connection"""
    print("🔍 Testing Redis connection...")
    try:
        import redis.asyncio as redis
        
        redis_url = os.getenv('REDIS_URL')
        print(f"   URL: {redis_url}")
        
        if not redis_url:
            print("❌ REDIS_URL not set")
            return False
            
        r = redis.from_url(redis_url, decode_responses=True)
        await r.ping()
        info = await r.info()
        print(f"✅ Redis OK: version {info.get('redis_version')}")
        await r.close()
        return True
    except Exception as e:
        print(f"❌ Redis failed: {e}")
        return False

async def test_gemini_json():
    """Test Gemini JSON parsing"""
    print("🔍 Testing Gemini credentials...")
    try:
        creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        if not creds_json:
            print("❌ GOOGLE_APPLICATION_CREDENTIALS_JSON not set")
            return False
            
        # Try to parse JSON
        creds = json.loads(creds_json)
        project_id = creds.get('project_id')
        client_email = creds.get('client_email')
        
        print(f"   Project ID: {project_id}")
        print(f"   Client Email: {client_email}")
        
        if project_id and client_email:
            print("✅ Gemini credentials JSON OK")
            return True
        else:
            print("❌ Gemini credentials incomplete")
            return False
    except json.JSONDecodeError as e:
        print(f"❌ Gemini JSON parse error: {e}")
        return False
    except Exception as e:
        print(f"❌ Gemini credentials failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Testing production connections...")
    print("=" * 50)
    
    tests = [
        test_database(),
        test_redis(), 
        test_gemini_json()
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    success_count = sum(1 for result in results if result is True)
    total_tests = len(results)
    
    print("=" * 50)
    print(f"📊 Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! Bot should work.")
        sys.exit(0)
    else:
        print("⚠️ Some tests failed. Fix issues above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
