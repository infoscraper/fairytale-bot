#!/usr/bin/env python3
"""
Force start bot by clearing locks - emergency use only
"""
import asyncio
import os
import sys
import uuid
import redis.asyncio as redis

async def force_start():
    """Force clear locks and start bot"""
    
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    r = redis.from_url(redis_url, decode_responses=True)
    
    try:
        # Get bot token for lock key
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        if not bot_token:
            print("❌ TELEGRAM_BOT_TOKEN not set")
            return
        
        lock_key = f"bot:poller_lock:{bot_token[:8]}"
        
        # Check current lock
        current_value = await r.get(lock_key)
        ttl = await r.ttl(lock_key)
        
        if current_value:
            print(f"🔍 Found existing lock: {current_value} (TTL: {ttl}s)")
            
            # Force delete the lock
            deleted = await r.delete(lock_key)
            print(f"🧹 Deleted {deleted} locks")
        else:
            print("✅ No existing locks found")
        
        # Set new lock
        lock_value = str(uuid.uuid4())
        got_lock = await r.set(lock_key, lock_value, ex=120, nx=True)
        
        if got_lock:
            print(f"✅ Successfully claimed lock: {lock_value}")
            print("🚀 Bot can now start!")
        else:
            print("❌ Failed to claim lock - another instance beat us to it")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        await r.close()

if __name__ == "__main__":
    print("🚨 FORCE START: Clearing locks and claiming new one...")
    asyncio.run(force_start())
