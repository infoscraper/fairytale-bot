#!/usr/bin/env python3
"""
Тест асинхронной генерации сказок
"""
import asyncio
import os
import sys

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tasks.story_tasks import generate_story_async

def test_celery_task():
    """Тест запуска Celery задачи"""
    print("🧪 Testing Celery story generation...")
    
    try:
        # Запускаем задачу
        result = generate_story_async.delay(
            child_id=1,
            theme="космос",
            user_id=1,
            message_id=123,
            chat_id=456
        )
        
        print(f"✅ Task started: {result.id}")
        print(f"📊 Task state: {result.state}")
        
        # Ждем результат (максимум 2 минуты)
        try:
            final_result = result.get(timeout=120)
            print(f"🎉 Task completed: {final_result}")
        except Exception as e:
            print(f"⏰ Task timeout or error: {e}")
            
    except Exception as e:
        print(f"❌ Error starting task: {e}")
        print("💡 Make sure Redis and Celery worker are running!")

if __name__ == "__main__":
    test_celery_task()
