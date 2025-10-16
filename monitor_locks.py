#!/usr/bin/env python3
"""
Monitor and cleanup bot locks
"""
import asyncio
import os
import sys
import redis.asyncio as redis
from datetime import datetime

async def monitor_locks():
    """Monitor bot locks and cleanup dead ones"""
    
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    r = redis.from_url(redis_url, decode_responses=True)
    
    try:
        # Get all bot locks
        lock_keys = await r.keys("bot:poller_lock:*")
        
        print(f"🔍 Found {len(lock_keys)} bot locks:")
        print("-" * 50)
        
        for key in lock_keys:
            try:
                value = await r.get(key)
                ttl = await r.ttl(key)
                
                if value:
                    print(f"🔒 {key}")
                    print(f"   Value: {value}")
                    print(f"   TTL: {ttl}s")
                    
                    if ttl < 0:
                        print(f"   ⚠️  Lock has no expiration!")
                    elif ttl < 30:
                        print(f"   ⏰ Lock expires soon ({ttl}s)")
                    else:
                        print(f"   ✅ Lock is healthy")
                else:
                    print(f"❌ {key} - No value (cleaning up)")
                    await r.delete(key)
                    
                print()
                
            except Exception as e:
                print(f"❌ Error checking {key}: {e}")
        
        # Check for processes
        print("🔍 Checking running processes:")
        print("-" * 50)
        
        import subprocess
        try:
            result = subprocess.run(
                ["ps", "aux"], 
                capture_output=True, 
                text=True
            )
            
            bot_processes = []
            for line in result.stdout.split('\n'):
                if 'src.main' in line and 'grep' not in line:
                    bot_processes.append(line.strip())
            
            print(f"Found {len(bot_processes)} bot processes:")
            for i, proc in enumerate(bot_processes, 1):
                print(f"{i}. {proc}")
                
            if len(bot_processes) > 1:
                print("\n⚠️  WARNING: Multiple bot processes detected!")
                print("   This may cause conflicts.")
                
        except Exception as e:
            print(f"❌ Error checking processes: {e}")
            
    except Exception as e:
        print(f"❌ Error connecting to Redis: {e}")
        sys.exit(1)
    finally:
        await r.close()

async def cleanup_dead_locks():
    """Cleanup locks that have no corresponding process"""
    
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    r = redis.from_url(redis_url, decode_responses=True)
    
    try:
        lock_keys = await r.keys("bot:poller_lock:*")
        
        for key in lock_keys:
            ttl = await r.ttl(key)
            if ttl < 10:  # Lock expires in less than 10 seconds
                print(f"🧹 Cleaning up expiring lock: {key}")
                await r.delete(key)
                
    except Exception as e:
        print(f"❌ Error cleaning locks: {e}")
    finally:
        await r.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        asyncio.run(cleanup_dead_locks())
    else:
        asyncio.run(monitor_locks())
