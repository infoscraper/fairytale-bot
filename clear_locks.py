#!/usr/bin/env python3
"""
Force clear all bot locks - emergency use only
"""
import asyncio
import os
import sys
import redis.asyncio as redis

async def clear_all_locks():
    """Clear all bot locks"""
    
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    r = redis.from_url(redis_url, decode_responses=True)
    
    try:
        # Get all bot locks
        lock_keys = await r.keys("bot:poller_lock:*")
        
        if not lock_keys:
            print("✅ No locks found")
            return
        
        print(f"🔍 Found {len(lock_keys)} locks:")
        for key in lock_keys:
            value = await r.get(key)
            ttl = await r.ttl(key)
            print(f"  - {key}: {value} (TTL: {ttl}s)")
        
        # Delete all locks
        if lock_keys:
            deleted = await r.delete(*lock_keys)
            print(f"🧹 Deleted {deleted} locks")
        
        print("✅ All bot locks cleared!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        await r.close()

if __name__ == "__main__":
    print("🚨 EMERGENCY: Clearing all bot locks...")
    asyncio.run(clear_all_locks())
