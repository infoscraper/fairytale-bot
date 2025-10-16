#!/usr/bin/env python3
"""
Диагностика проблем с генерацией сказок
"""
import asyncio
import os
import sys
import logging

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_story_generation():
    """Тестируем генерацию сказок напрямую"""
    
    print("🧪 ДИАГНОСТИКА ГЕНЕРАЦИИ СКАЗОК")
    print("=" * 50)
    
    try:
        # 1. Проверяем подключение к базе данных
        print("\n1️⃣ Проверяем базу данных...")
        from core.database import async_session_maker, engine
        from sqlalchemy import text
        
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT 1"))
            print("✅ База данных доступна")
            
    except Exception as e:
        print(f"❌ Ошибка базы данных: {e}")
        return
    
    try:
        # 2. Проверяем Redis
        print("\n2️⃣ Проверяем Redis...")
        from core.redis import get_redis
        
        redis = await get_redis()
        await redis.ping()
        print("✅ Redis доступен")
        
    except Exception as e:
        print(f"❌ Ошибка Redis: {e}")
        return
    
    try:
        # 3. Проверяем Celery
        print("\n3️⃣ Проверяем Celery...")
        from tasks.story_tasks import generate_story_async
        
        # Пробуем запустить задачу
        result = generate_story_async.delay(
            child_id=1,
            theme="тест",
            user_id=1,
            message_id=999,
            chat_id=999
        )
        
        print(f"✅ Celery задача запущена: {result.id}")
        print(f"📊 Статус: {result.state}")
        
        # Ждем результат 10 секунд
        try:
            final_result = result.get(timeout=10)
            print(f"🎉 Celery работает: {final_result}")
        except Exception as e:
            print(f"⏰ Celery timeout или ошибка: {e}")
            print("💡 Возможно, Celery worker не запущен")
            
    except Exception as e:
        print(f"❌ Ошибка Celery: {e}")
        print("💡 Celery недоступен, проверяем fallback...")
        
        # 4. Тестируем прямую генерацию (fallback)
        try:
            print("\n4️⃣ Тестируем прямую генерацию...")
            from services.story_service import StoryService
            from services.child_service import ChildService
            
            async with async_session_maker() as session:
                # Проверяем, есть ли дети в базе
                child_service = ChildService(session)
                children = await child_service.get_children_by_user_id(1)
                
                if not children:
                    print("⚠️ Нет детей в базе для тестирования")
                    print("💡 Создайте профиль ребенка через бота сначала")
                    return
                
                child = children[0]
                print(f"👶 Найден ребенок: {child.name} ({child.age} лет)")
                
                # Генерируем сказку
                story_service = StoryService(session)
                story = await story_service.create_story(
                    child_id=child.id,
                    theme="тест"
                )
                
                if story:
                    print(f"✅ Сказка создана: {story.id}")
                    print(f"📖 Тема: {story.theme}")
                    print(f"📝 Длина текста: {len(story.story_text)} символов")
                    print(f"💭 Мораль: {story.moral}")
                else:
                    print("❌ Не удалось создать сказку")
                    
        except Exception as e:
            print(f"❌ Ошибка прямой генерации: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🎯 РЕКОМЕНДАЦИИ:")
    print("1. Если Celery не работает → запустите Celery worker")
    print("2. Если прямая генерация не работает → проверьте OpenAI API")
    print("3. Если нет детей → создайте профиль через бота")

async def test_openai_connection():
    """Тестируем подключение к OpenAI"""
    print("\n🤖 Тестируем OpenAI API...")
    
    try:
        from core.config import settings
        import openai
        
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": "Привет! Это тест."}],
            max_tokens=50
        )
        
        print("✅ OpenAI API работает")
        print(f"📝 Ответ: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ Ошибка OpenAI API: {e}")

if __name__ == "__main__":
    asyncio.run(test_story_generation())
    asyncio.run(test_openai_connection())
