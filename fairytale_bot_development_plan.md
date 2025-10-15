# План разработки Сказочного бота

## 🎯 Общая стратегия

**Цель:** Создать MVP сказочного бота с полной инфраструктурой для дальнейшего масштабирования  
**Окружение:** Локальная разработка с Docker Desktop + Railway для продакшена  
**Исключения:** Платежи и подписки (интеграция позже)

---

## 📋 ЭТАП 0: Подготовка инфраструктуры

### 0.1 Настройка базового окружения

#### 0.1.1 Структура проекта
```bash
mkdir fairytale_bot && cd fairytale_bot
```

Создаем базовую структуру:
```
fairytale_bot/
├── .env.example
├── .env
├── .gitignore
├── docker-compose.yml
├── docker-compose.dev.yml
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── Procfile                    # Railway deployment
├── railway.json               # Railway configuration
├── railway.toml               # Railway environment config
├── nixpacks.toml              # Railway build optimization
├── RAILWAY_DEPLOYMENT.md      # Railway deployment guide
├── src/
│   ├── __init__.py
│   ├── main.py
│   └── core/
│       ├── __init__.py
│       ├── config.py
│       └── database.py
└── tests/
    └── __init__.py
```

#### 0.1.2 Базовые конфигурационные файлы

**Создаем `.env.example`:**
```env
# Database (Railway автоматически создаст PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:password@containers-us-west-xxx.railway.app:5432/railway
# Для локальной разработки:
# DATABASE_URL=postgresql+asyncpg://fairytale_user:fairytale_pass@localhost:5432/fairytale_db
# POSTGRES_USER=fairytale_user
# POSTGRES_PASSWORD=fairytale_pass
# POSTGRES_DB=fairytale_db

# Redis (Railway автоматически создаст Redis)
REDIS_URL=redis://default:password@containers-us-west-xxx.railway.app:6379
# Для локальной разработки:
# REDIS_URL=redis://localhost:6380/0

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# OpenAI
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4o-mini

# ElevenLabs Text-to-Speech (ОБЯЗАТЕЛЬНО для TTS функций)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=XB0fDUnXU5powFXDhCwa
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
ELEVENLABS_STABILITY=0.75
ELEVENLABS_SIMILARITY_BOOST=0.85
ELEVENLABS_STYLE=0.2
ELEVENLABS_USE_SPEAKER_BOOST=True

# Google Text-to-Speech (альтернатива ElevenLabs)
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
GOOGLE_CLOUD_PROJECT_ID=your-gcp-project-id
GOOGLE_TTS_VOICE_NAME=ru-RU-Standard-A
GOOGLE_TTS_VOICE_GENDER=FEMALE
GOOGLE_TTS_AUDIO_ENCODING=MP3

# Environment
ENVIRONMENT=development
DEBUG=True
```

**Создаем `docker-compose.yml`:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: fairytale_postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: fairytale_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: fairytale_pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@fairytale.local
      PGADMIN_DEFAULT_PASSWORD: admin123
    ports:
      - "8080:80"
    depends_on:
      - postgres
    profiles:
      - tools

volumes:
  postgres_data:
  redis_data:
```

#### 0.1.3 Тестирование базовой инфраструктуры

**Команды для Docker Desktop:**
```bash
# Запуск базовых сервисов
docker-compose up -d postgres redis

# Проверка статуса
docker-compose ps

# Проверка логов
docker-compose logs postgres
docker-compose logs redis

# Тест подключения к PostgreSQL
docker-compose exec postgres psql -U fairytale_user -d fairytale_db -c "SELECT version();"

# Тест подключения к Redis
docker-compose exec redis redis-cli ping
```

**Ожидаемый результат:**
- PostgreSQL отвечает с версией
- Redis отвечает "PONG"
- Все контейнеры в статусе "healthy"

### 0.2 Настройка Python окружения

#### 0.2.1 Создание requirements.txt
```txt
# Core
aiogram>=3.13.0
aiohttp==3.9.1
asyncpg==0.29.0
psycopg2-binary==2.9.9
sqlalchemy[asyncio]==2.0.25
alembic==1.13.1
pydantic>=2.9.0
pydantic-settings>=2.5.0

# Redis & Caching
redis[hiredis]==4.6.0
aioredis==2.0.1

# Celery
celery[redis]==5.3.4
flower==2.0.1

# TTS
elevenlabs==0.2.2

# OpenAI
openai==1.10.0

# Google Cloud
google-cloud-texttospeech==2.16.0
google-auth-oauthlib==1.2.0

# Database
psycopg2-binary==2.9.9

# Utilities
python-dateutil==2.8.2
structlog==23.2.0

# Production Server
gunicorn==21.2.0

# Development
pytest==7.4.4
pytest-asyncio==0.23.2
black==23.12.1
isort==5.13.2
```

#### 0.2.2 Базовый Python контейнер

**Создаем `Dockerfile`:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY src/ ./src/
COPY alembic.ini .
COPY alembic/ ./alembic/

# Создаем пользователя
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

CMD ["python", "-m", "src.main"]
```

#### 0.2.3 Тестирование Python окружения

**Обновляем `docker-compose.yml`:**
```yaml
  app:
    build: .
    container_name: fairytale_app
    environment:
      - DATABASE_URL=postgresql+asyncpg://fairytale_user:fairytale_pass@postgres:5432/fairytale_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./src:/app/src
    profiles:
      - app
```

**Команды тестирования:**
```bash
# Сборка образа
docker-compose build app

# Тест импортов Python
docker-compose run --rm app python -c "import aiogram, sqlalchemy, redis; print('All imports OK')"

# Тест подключения к БД
docker-compose run --rm app python -c "
import asyncio
import asyncpg
async def test():
    conn = await asyncpg.connect('postgresql://fairytale_user:fairytale_pass@postgres:5432/fairytale_db')
    version = await conn.fetchval('SELECT version()')
    print(f'DB Version: {version[:50]}...')
    await conn.close()
asyncio.run(test())
"
```

### 0.3 Настройка системы миграций

#### 0.3.1 Инициализация Alembic

**Создаем базовую конфигурацию:**

```python
# src/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # ElevenLabs Text-to-Speech
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "XB0fDUnXU5powFXDhCwa"
    ELEVENLABS_MODEL_ID: str = "eleven_multilingual_v2"
    ELEVENLABS_STABILITY: float = 0.75
    ELEVENLABS_SIMILARITY_BOOST: float = 0.85
    ELEVENLABS_STYLE: float = 0.2
    ELEVENLABS_USE_SPEAKER_BOOST: bool = True
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields in .env

settings = Settings()
```

```python
# src/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings

# Async SQLAlchemy engine
# Ensure we use asyncpg driver for PostgreSQL
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif database_url.startswith("postgresql+psycopg2://"):
    database_url = database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    future=True
)

async_session_maker = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_async_session():
    async with async_session_maker() as session:
        yield session
```

**Настраиваем `alembic.ini`:**
```ini
[alembic]
script_location = alembic
sqlalchemy.url = driver://user:pass@localhost/dbname

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

#### 0.3.2 Тестирование миграций

**Команды:**
```bash
# Инициализация Alembic в контейнере
docker-compose run --rm app alembic init alembic

# Создание первой миграции
docker-compose run --rm app alembic revision --autogenerate -m "Initial migration"

# Применение миграций
docker-compose run --rm app alembic upgrade head

# Проверка статуса
docker-compose run --rm app alembic current
```

### 0.4 Настройка Celery

#### 0.4.1 Базовая конфигурация Celery

```python
# src/core/celery_app.py
from celery import Celery
from .config import settings

celery_app = Celery(
    "fairytale_bot",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
)

# Автоматическое обнаружение задач
celery_app.autodiscover_tasks(['src.tasks'])
```

#### 0.4.2 Добавляем Celery в docker-compose

```yaml
  celery_worker:
    build: .
    container_name: fairytale_celery
    command: celery -A src.core.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://fairytale_user:fairytale_pass@postgres:5432/fairytale_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./src:/app/src
    profiles:
      - celery

  flower:
    build: .
    container_name: fairytale_flower
    command: celery -A src.core.celery_app flower
    environment:
      - REDIS_URL=redis://redis:6379/0
    ports:
      - "5555:5555"
    depends_on:
      - redis
    profiles:
      - tools
```

#### 0.4.3 Тестирование Celery

**Создаем тестовую задачу:**
```python
# src/tasks/test_tasks.py
from ..core.celery_app import celery_app
import time

@celery_app.task
def test_task(duration: int = 5):
    """Тестовая задача для проверки Celery"""
    time.sleep(duration)
    return f"Task completed after {duration} seconds"
```

**Команды тестирования:**
```bash
# Запуск Celery worker
docker-compose --profile celery up -d celery_worker

# Запуск Flower (веб-интерфейс)
docker-compose --profile tools up -d flower

# Тест задачи через Python
docker-compose run --rm app python -c "
from src.tasks.test_tasks import test_task
result = test_task.delay(3)
print(f'Task ID: {result.id}')
print(f'Result: {result.get(timeout=10)}')
"
```

**Проверки:**
- Flower доступен на http://localhost:5555
- Задача выполняется и возвращает результат
- Логи Celery показывают обработку задач

---

## 📋 ЭТАП 0.5: Railway Deployment Setup

### 0.5.1 Railway Configuration Files

**Создаем `Procfile`:**
```
web: python -m src.main
worker: celery -A src.core.celery_app worker --loglevel=info
```

**Создаем `railway.json`:**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python -m src.main",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Создаем `railway.toml`:**
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "python -m src.main"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[environments.production]
variables = { ENVIRONMENT = "production", DEBUG = "False" }
```

**Создаем `nixpacks.toml`:**
```toml
[phases.setup]
nixPkgs = ["ffmpeg"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[phases.build]
cmds = [
    "ls -la",
    "echo 'Build completed'"
]

[start]
cmd = "python -m src.main"
```

### 0.5.2 Railway Environment Variables

**Обязательные переменные для Railway:**
```env
# Database (Railway автоматически создаст)
DATABASE_URL=postgresql+asyncpg://postgres:password@containers-us-west-xxx.railway.app:5432/railway

# Redis (Railway автоматически создаст)
REDIS_URL=redis://default:password@containers-us-west-xxx.railway.app:6379

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_production_bot_token

# OpenAI
OPENAI_API_KEY=your_openai_key

# ElevenLabs
ELEVENLABS_API_KEY=your_elevenlabs_key

# Environment
ENVIRONMENT=production
DEBUG=False
```

### 0.5.3 Railway Deployment Process

**Шаги деплоя:**
1. Создать проект в Railway Dashboard
2. Добавить PostgreSQL и Redis сервисы
3. Настроить переменные окружения
4. Подключить GitHub репозиторий
5. Настроить автоматический деплой

**Команды для деплоя:**
```bash
# Подготовка к деплою
git add .
git commit -m "Prepare for Railway deployment"
git push origin main

# Проверка деплоя
railway logs
railway status
```

### 0.5.4 Railway Lessons Learned

**Критические ошибки и их решения:**

1. **TokenValidationError**: 
   - Проблема: Неправильный или отсутствующий TELEGRAM_BOT_TOKEN
   - Решение: Проверить токен в Railway Dashboard, убедиться в отсутствии пробелов

2. **TelegramConflictError**:
   - Проблема: Несколько экземпляров бота работают одновременно
   - Решение: Остановить все локальные экземпляры, проверить webhook в BotFather

3. **Database Connection Issues**:
   - Проблема: Неправильный DATABASE_URL формат
   - Решение: Использовать postgresql+asyncpg:// вместо postgresql://

4. **Redis Compatibility Issues**:
   - Проблема: Redis 5.x vs 4.x API различия
   - Решение: Использовать redis[hiredis]==4.6.0 для совместимости

5. **Alembic Migration Issues**:
   - Проблема: Миграции не применяются на Railway
   - Решение: Интегрировать создание таблиц в main.py для Railway

6. **Dependency Conflicts**:
   - Проблема: Конфликт между celery[redis] и redis[hiredis]
   - Решение: Использовать совместимые версии пакетов

---

## 📋 ЭТАП 1: MVP Telegram бота

### 1.1 Базовая структура бота

#### 1.1.1 Создание моделей данных

```python
# src/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from ..core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=False)
    language_code = Column(String(10), default="ru")
    is_active = Column(Boolean, default=True)
    free_stories_used = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

```python
# src/models/child.py
from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..core.database import Base

class Child(Base):
    __tablename__ = "children"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    favorite_characters = Column(JSON, default=list)
    interests = Column(JSON, default=list)
    preferred_story_length = Column(Integer, default=10)  # minutes
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="children")
```

#### 1.1.2 Создание базового бота

```python
# src/main.py
#!/usr/bin/env python3
"""
Fairytale Bot - Entry point
"""
import asyncio
import logging
import os
import sys
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
logger = logging.getLogger(__name__)


async def init_database():
    """Initialize database with migrations"""
    logger.info("🔄 Initializing database...")
    
    try:
        # Check if we're in Railway environment
        if os.getenv("RAILWAY_ENVIRONMENT"):
            logger.info("🚂 Running in Railway environment, creating tables...")
            
            # Import database components
            from .core.database import engine
            from .models import Base
            
            # Create all tables
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("✅ Database tables created successfully!")
        else:
            logger.info("🏠 Running locally, skipping automatic migrations")
            
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        # Don't exit in production, just log the error
        if not os.getenv("RAILWAY_ENVIRONMENT"):
            raise


async def main():
    """Main function to start the bot"""
    
    # Initialize database first (only in Railway)
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
        
        # Start polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        raise
    finally:
        await bot.session.close()
        await close_redis()
        logger.info("🛑 Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
```

#### 1.1.3 Тестирование MVP бота

**Команды:**
```bash
# Создание и применение миграций
docker-compose run --rm app alembic revision --autogenerate -m "Add user and child models"
docker-compose run --rm app alembic upgrade head

# Запуск бота
docker-compose --profile app up -d app

# Проверка логов
docker-compose logs -f app
```

**Тесты:**
1. Отправить `/start` боту
2. Проверить создание пользователя в БД
3. Пройти процесс создания профиля ребенка
4. Проверить сохранение данных ребенка

### 1.2 Интеграция с OpenAI

#### 1.2.1 Сервис генерации сказок

```python
# src/services/openai_service.py
from openai import AsyncOpenAI
from ..core.config import settings

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate_simple_story(self, child_name: str, age: int, characters: list, theme: str = None):
        prompt = f"""
        Создай короткую добрую сказку для ребенка {age} лет по имени {child_name}.
        Любимые персонажи: {', '.join(characters)}
        Тема: {theme or 'любая подходящая для возраста'}
        
        Требования:
        - Ребенок должен быть главным героем
        - История должна быть позитивной и поучительной
        - Длина: примерно 2-3 минуты чтения
        - Возрастная адаптация под {age} лет
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты - опытный детский писатель сказок."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.8
        )
        
        return response.choices[0].message.content
```

#### 1.2.2 Тестирование генерации

**Создаем тестовую задачу:**
```python
# src/tasks/story_tasks.py
from ..core.celery_app import celery_app
from ..services.openai_service import OpenAIService

@celery_app.task
def generate_story_task(child_name: str, age: int, characters: list, theme: str = None):
    service = OpenAIService()
    story = await service.generate_simple_story(child_name, age, characters, theme)
    return {"story_text": story, "status": "completed"}
```

**Команды тестирования:**
```bash
# Тест генерации сказки
docker-compose run --rm app python -c "
import asyncio
from src.services.openai_service import OpenAIService

async def test():
    service = OpenAIService()
    story = await service.generate_simple_story('Алиса', 5, ['единорог', 'принцесса'], 'волшебный лес')
    print('Story generated:', len(story), 'characters')
    print(story[:200] + '...')

asyncio.run(test())
"
```

---

## 📋 ЭТАП 2: Полная функциональность сказок

### 2.1 Серии и память

**Модели:**
- StorySeries
- ChildPreferences
- Story (расширенная)

### 2.2 Аудио-производство

**Интеграции:**
- ElevenLabs TTS (приоритет)
- Google Cloud TTS (альтернатива)
- Suno AI для музыки
- pydub для микширования

### 2.3 Система рекомендаций

**Компоненты:**
- Анализ предпочтений
- ML рекомендации
- Обратная связь

---

## 📋 ЭТАП 3: Продакшн готовность

### 3.1 Railway Production Deployment
### 3.2 Мониторинг и логирование
### 3.3 Тестирование и CI/CD

---

## ✅ Чеклист готовности инфраструктуры

- [x] PostgreSQL запущен и доступен ✅
- [x] Redis запущен и доступен ✅  
- [x] Python контейнер собирается ✅
- [x] Alembic создает миграции ✅
- [x] Celery worker запускается ✅
- [x] Flower доступен на localhost:5555 ✅
- [x] Базовый бот отвечает на /start ✅
- [x] OpenAI API работает ✅
- [x] Тестовая сказка генерируется ✅
- [x] Railway деплой настроен ✅
- [x] Production бот работает на Railway ✅

**Статус: ИНФРАСТРУКТУРА ГОТОВА! 🎉**

---

## 🎯 ТЕКУЩИЙ СТАТУС ПРОЕКТА (26.09.2024)

### ✅ ЗАВЕРШЕНО:

#### Инфраструктура (100%)
- PostgreSQL + Redis работают в Docker
- Python контейнер с Aiogram 3.13.0+
- Alembic миграции настроены
- Celery + Flower для фоновых задач
- **НОВОЕ**: Railway деплой настроен и работает

#### MVP Бот (100%)
- **Модели данных**: User, Child, Story реализованы
- **FSM состояния**: Создание профилей детей работает
- **Handlers**: /start, /story, /profile, создание профилей
- **Middlewares**: Database session, User context
- **OpenAI интеграция**: Генерация персонализированных сказок
- **База данных**: Все CRUD операции работают

#### Функциональность (100%)
- ✅ Регистрация пользователей
- ✅ Создание профилей детей (имя, возраст, персонажи, интересы)
- ✅ Генерация сказок через OpenAI GPT-4o-mini (обновлено!)
- ✅ Сохранение сказок в БД
- ✅ Система обратной связи (❤️👍😐👎)
- ✅ Счетчик бесплатных сказок
- ✅ Выбор ребенка для сказки
- ✅ Выбор темы сказки
- ✅ **НОВОЕ**: Интерфейс с кнопками вместо текстовых команд
- ✅ **НОВОЕ**: Система безопасности контента (многоуровневая фильтрация)
- ✅ **НОВОЕ**: Валидация имен, персонажей и интересов детей
- ✅ **НОВОЕ**: Ограничение длины сказок (1-10 минут)
- ✅ **НОВОЕ**: Исправление timeout ошибок при создании сказок
- ✅ **НОВОЕ**: Разделение длинных сообщений на части
- ✅ **НОВОЕ**: История сказок с фильтрацией и поиском
- ✅ **НОВОЕ**: Экспорт сказок в текстовые файлы

### 🔧 ТЕХНИЧЕСКИЕ РЕШЕНИЯ:
- **OpenAI SDK**: 1.10.0+ (обновлено для поддержки новых моделей)
- **Aiogram**: 3.13.0+ (обновлено для совместимости)
- **Pydantic**: 2.9.0+ (обновлено для совместимости)
- **ElevenLabs**: 0.2.2 (интегрирован для TTS)
- **Redis**: 4.6.0 (совместимость с Celery)
- **PostgreSQL**: psycopg2-binary + asyncpg для Railway
- **Railway**: Полная настройка деплоя
- **Foreign Keys**: Восстановлены и работают
- **Relationships**: Настроены правильно
- **Content Safety**: Многоуровневая система валидации контента
- **Message Splitting**: Автоматическое разделение длинных сообщений
- **Database Initialization**: Автоматическое создание таблиц на Railway

### 🚨 КРИТИЧЕСКИЕ УРОКИ RAILWAY ДЕПЛОЯ:

1. **Dependency Management**:
   - Использовать совместимые версии Redis (4.6.0) и Celery
   - Добавить psycopg2-binary для PostgreSQL совместимости
   - Тестировать все зависимости локально перед деплоем

2. **Environment Variables**:
   - Все переменные должны быть установлены в Railway Dashboard
   - Проверять отсутствие пробелов в токенах
   - Использовать правильные форматы URL (postgresql+asyncpg://)

3. **Database Initialization**:
   - Интегрировать создание таблиц в main.py для Railway
   - Не полагаться на Alembic миграции в production
   - Использовать SQLAlchemy Base.metadata.create_all

4. **Redis Compatibility**:
   - Проверять версию Redis API (aclose vs close)
   - Использовать hasattr для проверки методов
   - Тестировать с разными версиями Redis

5. **Bot Token Management**:
   - Создавать отдельные боты для staging и production
   - Проверять webhook настройки в BotFather
   - Останавливать все локальные экземпляры перед деплоем

---

## 📋 СЛЕДУЮЩИЕ ШАГИ РАЗРАБОТКИ

### ЭТАП 2А: Критические исправления и улучшения (3-4 дня) 🚀 ВЫСОКИЙ ПРИОРИТЕТ

#### 2А.1 Создание Staging окружения (День 1)
```bash
# Задачи:
- [ ] Создать staging бота в BotFather
- [ ] Создать отдельный Railway проект для staging
- [ ] Настроить staging переменные окружения (отдельная БД)
- [ ] Создать staging branch в Git
- [ ] Настроить автоматический деплой staging → production
- [ ] Создать deployment скрипты
- [ ] Добавить staging логирование
```

#### 2А.2 Починка функционала ограничений (День 1-2)
```bash
# КРИТИЧЕСКАЯ ПРОБЛЕМА: can_create_free_story() не вызывается!
- [ ] Добавить проверку лимитов перед созданием сказки
- [ ] Реализовать тестовый режим (список telegram_id в конфиге)
- [ ] Создать UI для превышения лимита (3 сказки)
- [ ] Добавить предложение об оплате с заглушкой
- [ ] Протестировать ограничения на staging
```

#### 2А.3 Интеграция Gemini-TTS (День 2-3)
```bash
# Замена ElevenLabs на Gemini-TTS
- [ ] Создать GeminiTTSService (30 голосов, 80+ языков)
- [ ] Протестировать голоса для детей разных возрастов
- [ ] Настроить промпты для детской озвучки (2-8 лет)
- [ ] Интегрировать в story_creation.py
- [ ] Обновить requirements.txt (google-cloud-texttospeech>=2.31.0)
- [ ] Протестировать качество аудио на staging
```

#### 2А.4 Система платежей (День 2)
```bash
# Заглушка для будущей интеграции
- [ ] Создать payment keyboards и handlers
- [ ] Добавить предложение подписки (299₽/месяц)
- [ ] Реализовать заглушку платежей
- [ ] Добавить информацию о преимуществах подписки
- [ ] Протестировать flow превышения лимитов
```

### ЭТАП 2Б: Улучшение UX и стабильности (1-2 дня) ✅ ЗАВЕРШЕН

#### 2Б.1 Починка архитектуры БД ✅ ЗАВЕРШЕНО
```bash
# Задачи:
- [x] Восстановить Foreign Keys правильно
- [x] Настроить правильные relationships в SQLAlchemy
- [x] Создать миграцию для FK constraints
- [x] Протестировать все связи между таблицами
```

#### 2Б.2 Расширение функций профилей ✅ ЗАВЕРШЕНО
```bash
# Задачи:
- [x] Редактирование профилей детей
- [x] Деактивация/удаление профилей
- [x] Просмотр статистики ребенка (сколько сказок)
- [x] Валидация возраста (1-16 лет)
```

#### 2Б.3 Улучшение генерации сказок ✅ ЗАВЕРШЕНО
```bash
# Задачи:
- [x] Добавить больше тем сказок
- [x] Кастомная тема (свободный ввод)
- [x] Адаптация длины по возрасту
- [x] Сохранение времени генерации
- [x] Обработка ошибок OpenAI
```

### ЭТАП 2В: История и память (2-3 дня) ✅ ЗАВЕРШЕН

#### 2В.1 История сказок ✅ ГОТОВО
```bash
# Задачи:
- [x] Команда /history - просмотр всех сказок
- [x] Фильтрация по ребенку
- [x] Повторное чтение сказки
- [x] Экспорт сказки в текстовый файл
- [x] Пагинация для большого количества сказок
- [x] Поиск по названию/теме сказки
- [x] Создание похожих сказок
- [x] Интеграция с главным меню
```

#### 2В.2 Система серий (StorySeries)
```bash
# Задачи:
- [ ] Восстановить модель StorySeries
- [ ] Создание многосерийных сказок
- [ ] Связь между эпизодами
- [ ] Продолжение истории по запросу
```

#### 2В.3 Память и контекст
```bash
# Задачи:
- [ ] Запоминание любимых персонажей
- [ ] Адаптация под предыдущие сказки
- [ ] Система тегов интересов
- [ ] Эволюция предпочтений
```

### ЭТАП 2Г: Аудио-производство (ОБНОВЛЕНО) 🚀 ВЫСОКИЙ ПРИОРИТЕТ

#### 2Г.1 Gemini-TTS интеграция (ПРИОРИТЕТ)
```bash
# Задачи:
- [x] Интеграция с ElevenLabs TTS (базовая) - ЗАМЕНИТЬ НА GEMINI
- [ ] Создать GeminiTTSService с 30 голосами
- [ ] Протестировать голоса: Aoede, Charon, Kore, Fenrir для детей
- [ ] Настроить русскоязычные промпты для озвучки (2-8 лет)
- [ ] Интеграция в story_creation.py
- [ ] Обработка ошибок Gemini TTS API
- [ ] Сохранение аудио файлов в БД
```

#### 2Г.2 Фоновая музыка (ОТЛОЖЕНО)
```bash
# Задачи - ОТЛОЖЕНЫ НА БУДУЩЕЕ:
- [ ] Интеграция с royalty-free музыкой
- [ ] pydub для микширования аудио
- [ ] Разные стили музыки по жанрам сказок
- [ ] Настройка громкости фоновой музыки
```

#### 2Г.3 Полное аудио (ОТЛОЖЕНО)
```bash
# Задачи - ОТЛОЖЕНЫ НА БУДУЩЕЕ:
- [ ] Создание полного аудио (речь + музыка)
- [ ] Опции воспроизведения в Telegram
- [ ] Сохранение как голосовое сообщение
- [ ] Экспорт MP3 файлов
```

### ЭТАП 3: Система мониторинга и аналитики (3-4 дня) 🚀 ВЫСОКИЙ ПРИОРИТЕТ

#### 3.1 Event Tracking System
```bash
# Задачи:
- [ ] Создать AnalyticsService для трекинга событий
- [ ] Определить ключевые события (регистрация, создание сказки, подписка)
- [ ] Настроить очередь событий в Redis
- [ ] Создать модели для аналитических данных
- [ ] Интегрировать трекинг в существующие handlers

# Техническая архитектура:
# src/analytics/
# ├── __init__.py
# ├── service.py          # AnalyticsService
# ├── events.py           # Event definitions
# ├── models.py           # Analytics models
# ├── middleware.py       # Analytics middleware
# └── dashboard.py        # Admin dashboard

# Ключевые события для трекинга:
# - user_registered
# - child_profile_created
# - story_generated
# - story_rated
# - subscription_started
# - payment_completed
# - user_churned
# - feature_used
```

#### 3.2 User Analytics
```bash
# Задачи:
- [ ] Трекинг источников пользователей (Telegram, рефералы)
- [ ] Анализ воронки конверсии (регистрация → профиль → сказка)
- [ ] Retention анализ (возвращаются ли пользователи)
- [ ] География пользователей
- [ ] Время активности (пики использования)
```

#### 3.3 Content Analytics
```bash
# Задачи:
- [ ] Популярные темы сказок
- [ ] Анализ по возрастным группам
- [ ] Любимые персонажи
- [ ] Длина сказок (предпочтения)
- [ ] Рейтинг сказок (лайки/дизлайки)
- [ ] Время генерации сказок
```

#### 3.4 Business Metrics
```bash
# Задачи:
- [ ] Воронка подписок (бесплатные → платные)
- [ ] Конверсия в платных пользователей
- [ ] ARPU (средний доход с пользователя)
- [ ] Churn rate (отток пользователей)
- [ ] LTV (пожизненная ценность)
- [ ] Cohort analysis
```

#### 3.5 Real-time Dashboard
```bash
# Задачи:
- [ ] Создать админ панель с метриками
- [ ] Real-time счетчики в Redis
- [ ] Ежедневные/еженедельные отчеты
- [ ] Алерты при критических изменениях
- [ ] Экспорт данных для анализа

# Технические детали:
# - Web интерфейс на FastAPI + Jinja2
# - Real-time обновления через WebSocket
# - Графики с Chart.js или Plotly
# - Экспорт в CSV/JSON
# - Алерты через Telegram/Email
# - Кеширование метрик в Redis
# - Автоматические отчеты по расписанию
```

### ЭТАП 4: Продвинутые функции (4-5 дней)

#### 4.1 Персонализация
```bash
# Задачи:
- [ ] ML анализ предпочтений
- [ ] Автоматические рекомендации тем
- [ ] Система рейтингов
- [ ] Любимые сказки
```

#### 4.2 Социальные функции
```bash
# Задачи:
- [ ] Поделиться сказкой с другом
- [ ] Семейные аккаунты
- [ ] Совместное создание сказок
- [ ] Коллекции сказок
```

#### 4.3 Администрирование
```bash
# Задачи:
- [ ] Расширенная админ панель
- [ ] A/B тестирование
- [ ] Управление пользователями
- [ ] Система уведомлений
```

---

## 🎯 РЕКОМЕНДУЕМЫЙ ПЛАН НА БЛИЖАЙШИЕ 3 НЕДЕЛИ:

### Неделя 1: Критические исправления (ПРИОРИТЕТ)
1. **День 1**: Этап 2А.1-2А.2 (Staging + Ограничения)
   - Создание staging бота и Railway проекта
   - Исправление критической ошибки с лимитами
   - Добавление тестового режима
   - Создание UI для превышения лимитов
2. **День 2-3**: Этап 2А.3-2А.4 (Gemini TTS + Платежи)
   - Создание GeminiTTSService
   - Тестирование голосов для детей
   - Интеграция в story_creation.py
   - Создание заглушки платежей
3. **День 4-5**: Тестирование и деплой
   - Тестирование на staging
   - Деплой в production
   - Мониторинг работы

### Неделя 2: Серии и расширения  
1. **День 6-8**: Этап 2В.2 (система серий)
   - Восстановление модели StorySeries
   - Создание многосерийных сказок
   - Активация отключенных handlers
2. **День 9-10**: Этап 2В.3 (память и контекст)
   - Запоминание предпочтений
   - Адаптация под предыдущие сказки
3. **День 11-12**: Дополнительные улучшения
   - Оптимизация производительности
   - Улучшение UX

### Неделя 3: Мониторинг и аналитика 🚀 НОВОЕ
1. **День 13-15**: Этап 3.1-3.2 (Event Tracking + User Analytics)
   - Создание AnalyticsService
   - Трекинг ключевых событий
   - Анализ воронки конверсии
   - Retention анализ
2. **День 16-17**: Этап 3.3-3.4 (Content + Business Analytics)
   - Анализ контента и предпочтений
   - Бизнес-метрики и воронка подписок
   - Cohort analysis
3. **День 18-21**: Этап 3.5 (Real-time Dashboard)
   - Создание админ панели
   - Real-time метрики
   - Алерты и отчеты

### 🎯 НЕМЕДЛЕННЫЕ СЛЕДУЮЩИЕ ШАГИ (НА ЭТОЙ НЕДЕЛЕ):
1. **Staging окружение** - создать тестовый контур на Railway
2. **КРИТИЧЕСКОЕ: Исправить ограничения** - метод can_create_free_story() не вызывается!
3. **Gemini TTS** - заменить ElevenLabs на Google Gemini-TTS
4. **Система платежей** - создать заглушку для подписок
5. **Система мониторинга** - начать с базового трекинга событий

**После этого у вас будет полноценный продукт с качественным аудио готовый к первым пользователям! 🚀**

---

## 🎯 ТЕКУЩИЕ ПРИОРИТЕТЫ (СЕГОДНЯ-ЗАВТРА)

### 🚀 КРИТИЧЕСКИЙ ПРИОРИТЕТ:
1. **Исправить ограничения** - метод can_create_free_story() не вызывается!
2. **Staging Environment** - создать тестовый контур на Railway
3. **Gemini TTS** - заменить ElevenLabs на Google Gemini-TTS
4. **Система платежей** - создать заглушку для подписок

### 🔧 ТЕХНИЧЕСКИЕ УЛУЧШЕНИЯ:
1. **Тестовый режим** - список telegram_id без ограничений
2. **Gemini TTS интеграция** - 30 голосов, промпты для детей
3. **Сохранение аудио в БД** - не терять сгенерированные файлы
4. **Event Tracking** - система сбора аналитических данных

### 📱 UX УЛУЧШЕНИЯ:
1. **UI для лимитов** - показать когда сказки закончились
2. **Предложение подписки** - 299₽/месяц с преимуществами
3. **Качественная озвучка** - Gemini TTS для детей 2-8 лет
4. **Аналитический дашборд** - понимание поведения пользователей

---

## 📊 СТАТИСТИКА ПРОЕКТА

### ✅ ЗАВЕРШЕНО: 90%
- **Инфраструктура**: 100% ✅
- **MVP Бот**: 100% ✅  
- **Безопасность**: 100% ✅
- **UX/UI**: 100% ✅
- **История**: 100% ✅
- **Railway Deploy**: 100% ✅
- **Ограничения**: 0% ❌ (КРИТИЧЕСКАЯ ОШИБКА!)
- **TTS**: 70% 🔄 (ElevenLabs → Gemini)
- **Платежи**: 0% ❌
- **Серии**: 0% ❌
- **Мониторинг**: 0% ❌

### 🎯 ЦЕЛЬ: 95% готовности к релизу
**Осталось**: Исправить ограничения + Gemini TTS + платежи + система серий + мониторинг

### 🚨 КРИТИЧЕСКИЕ ЗАДАЧИ:
1. **ИСПРАВИТЬ ОГРАНИЧЕНИЯ** - can_create_free_story() не вызывается!
2. **Staging Environment** - для безопасной разработки
3. **Gemini TTS** - заменить ElevenLabs на Google TTS
4. **Система платежей** - заглушка для подписок
5. **Series System** - многосерийные сказки
6. **Analytics System** - мониторинг пользователей и бизнес-метрик

**Проект требует критических исправлений перед production! 🚨**

---

## 📊 СИСТЕМА МОНИТОРИНГА И АНАЛИТИКИ

### 🎯 Ключевые метрики для отслеживания:

#### 1. **User Acquisition Metrics**
```python
# Источники пользователей
- telegram_direct        # Прямой поиск в Telegram
- telegram_share         # Поделились ссылкой
- referral_code          # Реферальная программа
- external_ad            # Внешняя реклама

# География
- country_code           # ISO код страны
- timezone              # Часовой пояс
- language_preference   # Предпочитаемый язык
```

#### 2. **User Engagement Metrics**
```python
# Активность
- daily_active_users     # DAU
- weekly_active_users    # WAU  
- monthly_active_users   # MAU
- session_duration       # Время в боте
- stories_per_user       # Сказок на пользователя
- return_rate           # Процент возвращающихся

# Воронка конверсии
- registration_rate      # Регистрация / старт
- profile_completion     # Профиль / регистрация
- first_story_rate       # Первая сказка / профиль
- subscription_rate      # Подписка / активность
```

#### 3. **Content Performance Metrics**
```python
# Популярность контента
- top_story_themes       # Популярные темы
- age_group_preferences  # Предпочтения по возрастам
- character_popularity   # Популярные персонажи
- story_length_prefs     # Предпочтения длины
- rating_distribution    # Распределение оценок

# Качество контента
- avg_generation_time    # Время генерации
- error_rate            # Процент ошибок
- user_satisfaction     # Удовлетворенность
- repeat_usage          # Повторное использование
```

#### 4. **Business Metrics**
```python
# Финансовые показатели
- revenue_per_user       # ARPU
- lifetime_value         # LTV
- conversion_funnel      # Воронка подписок
- churn_rate            # Отток пользователей
- retention_cohorts     # Когортный анализ

# Операционные метрики
- cost_per_story        # Стоимость генерации
- api_usage             # Использование API
- storage_usage         # Использование хранилища
- performance_metrics   # Производительность
```

### 🛠 Техническая реализация:

#### 1. **AnalyticsService**
```python
# src/analytics/service.py
class AnalyticsService:
    async def track_event(self, event_type: str, user_id: int, data: dict):
        """Трекинг события пользователя"""
        event = {
            'event_type': event_type,
            'user_id': user_id,
            'timestamp': datetime.utcnow(),
            'data': data,
            'session_id': await self.get_session_id(user_id)
        }
        
        # Отправка в очередь для обработки
        await self.event_queue.put(event)
        
        # Обновление real-time счетчиков
        await self.update_realtime_counters(event)
    
    async def get_user_metrics(self, user_id: int) -> dict:
        """Получение метрик пользователя"""
        return {
            'stories_count': await self.get_stories_count(user_id),
            'last_active': await self.get_last_active(user_id),
            'preferred_themes': await self.get_preferred_themes(user_id),
            'engagement_score': await self.calculate_engagement(user_id)
        }
```

#### 2. **Event Middleware**
```python
# src/analytics/middleware.py
class AnalyticsMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        # Трекинг всех действий пользователя
        user_id = data.get('user_id')
        if user_id:
            await analytics.track_event(
                'user_action',
                user_id,
                {'action': handler.__name__, 'timestamp': datetime.utcnow()}
            )
        
        return await handler(event, data)
```

#### 3. **Real-time Dashboard**
```python
# src/analytics/dashboard.py
@app.get("/analytics/dashboard")
async def get_dashboard():
    return {
        'users': {
            'total': await get_total_users(),
            'active_today': await get_active_today(),
            'new_today': await get_new_today()
        },
        'stories': {
            'generated_today': await get_stories_today(),
            'avg_rating': await get_avg_rating(),
            'popular_themes': await get_popular_themes()
        },
        'business': {
            'revenue_today': await get_revenue_today(),
            'conversion_rate': await get_conversion_rate(),
            'churn_rate': await get_churn_rate()
        }
    }
```

### 📈 Примеры аналитических запросов:

#### 1. **Воронка конверсии**
```sql
-- Анализ воронки от регистрации до подписки
WITH funnel AS (
    SELECT 
        DATE(created_at) as date,
        COUNT(*) as registered,
        COUNT(CASE WHEN child_count > 0 THEN 1 END) as with_profiles,
        COUNT(CASE WHEN story_count > 0 THEN 1 END) as with_stories,
        COUNT(CASE WHEN is_subscribed THEN 1 END) as subscribed
    FROM users 
    GROUP BY DATE(created_at)
)
SELECT 
    date,
    registered,
    with_profiles,
    with_stories,
    subscribed,
    ROUND(with_profiles::float / registered * 100, 2) as profile_rate,
    ROUND(with_stories::float / with_profiles * 100, 2) as story_rate,
    ROUND(subscribed::float / with_stories * 100, 2) as subscription_rate
FROM funnel
ORDER BY date DESC;
```

#### 2. **Cohort Analysis**
```sql
-- Анализ retention по когортам
WITH cohorts AS (
    SELECT 
        user_id,
        DATE_TRUNC('week', created_at) as cohort_week,
        DATE_TRUNC('week', last_active) as active_week
    FROM users
),
cohort_sizes AS (
    SELECT cohort_week, COUNT(*) as size
    FROM cohorts
    GROUP BY cohort_week
)
SELECT 
    c.cohort_week,
    cs.size as cohort_size,
    c.active_week,
    COUNT(*) as active_users,
    ROUND(COUNT(*)::float / cs.size * 100, 2) as retention_rate
FROM cohorts c
JOIN cohort_sizes cs ON c.cohort_week = cs.cohort_week
GROUP BY c.cohort_week, cs.size, c.active_week
ORDER BY c.cohort_week, c.active_week;
```

### 🚨 Алерты и мониторинг:

#### 1. **Критические алерты**
```python
# Алерты при критических изменениях
ALERTS = {
    'high_error_rate': {
        'threshold': 5,  # 5% ошибок
        'message': 'Высокий процент ошибок генерации сказок'
    },
    'low_conversion': {
        'threshold': 10,  # 10% конверсия
        'message': 'Низкая конверсия в подписки'
    },
    'high_churn': {
        'threshold': 20,  # 20% отток
        'message': 'Высокий отток пользователей'
    },
    'api_quota_exceeded': {
        'threshold': 90,  # 90% квоты
        'message': 'Приближается лимит API'
    }
}
```

#### 2. **Автоматические отчеты**
```python
# Еженедельные отчеты
WEEKLY_REPORTS = {
    'user_growth': 'Рост пользователей за неделю',
    'content_performance': 'Популярные темы и персонажи',
    'business_metrics': 'Финансовые показатели',
    'technical_health': 'Производительность и ошибки'
}
```

### 🎯 Приоритеты внедрения:

1. **Неделя 1**: Критические исправления (ограничения + Gemini TTS + платежи)
2. **Неделя 2**: Серии сказок + Базовый трекинг событий
3. **Неделя 3**: User Analytics и воронка конверсии  
4. **Неделя 4**: Content Analytics и Business Metrics
5. **Неделя 5**: Real-time Dashboard и алерты

**ВНИМАНИЕ: Сначала исправить критические ошибки, потом аналитику! 🚨**
