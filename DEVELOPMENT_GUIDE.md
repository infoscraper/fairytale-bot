# 🎭 Руководство по разработке Fairytale Bot

## 📚 Обзор архитектуры

Этот документ поможет вам быстро найти нужные файлы для внесения изменений в различные части бота.

---

## 🎯 **ГЕНЕРАЦИЯ ТЕКСТА СКАЗОК**

### 📝 **Основной файл:**
- **`src/services/openai_service.py`** - сервис генерации сказок через OpenAI

### 🔧 **Что можно изменить:**

#### 1. **Системные промпты для сказок**
```python
# Файл: src/services/openai_service.py
# Метод: _get_storyteller_system_prompt()

def _get_storyteller_system_prompt(self) -> str:
    return """
    Ты - волшебный рассказчик сказок для детей...
    # ЗДЕСЬ ИЗМЕНИТЬ ОСНОВНОЙ ПРОМПТ
    """
```

#### 2. **Адаптация по возрасту**
```python
# Файл: src/services/openai_service.py
# Метод: _get_age_appropriate_guidance()

def _get_age_appropriate_guidance(self, age: int) -> str:
    # ЗДЕСЬ ИЗМЕНИТЬ ЛОГИКУ АДАПТАЦИИ ПОД ВОЗРАСТ
```

#### 3. **Морали сказок**
```python
# Файл: src/services/openai_service.py
# Метод: _extract_moral_from_story()

def _extract_moral_from_story(self, story_text: str) -> str:
    # ЗДЕСЬ ДОБАВИТЬ НОВЫЕ МОРАЛИ
```

#### 4. **Длина и структура сказок**
```python
# Файл: src/services/openai_service.py
# Метод: _get_age_adaptations()

def _get_age_adaptations(self, age: int) -> Dict[str, str]:
    # ЗДЕСЬ ИЗМЕНИТЬ ДЛИНУ И СЛОЖНОСТЬ
```

---

## 🎙️ **ГЕНЕРАЦИЯ АУДИО**

### 📝 **Основные файлы:**
- **`src/services/tts_service.py`** - ElevenLabs TTS (текущий)
- **`test_gemini_tts.py`** - тестовый скрипт для Gemini TTS
- **`src/services/gemini_tts_service.py`** - будущий Gemini TTS сервис

### 🔧 **Что можно изменить:**

#### 1. **ElevenLabs настройки**
```python
# Файл: src/services/tts_service.py
# Метод: _get_emotion_settings()

def _get_emotion_settings(self, mood: str) -> dict:
    # ЗДЕСЬ ИЗМЕНИТЬ НАСТРОЙКИ ГОЛОСА
```

#### 2. **Выбор голоса по возрасту**
```python
# Файл: src/services/tts_service.py
# Метод: _get_child_appropriate_voice()

def _get_child_appropriate_voice(self, child_age: int) -> str:
    # ЗДЕСЬ ИЗМЕНИТЬ ЛОГИКУ ВЫБОРА ГОЛОСА
```

#### 3. **Gemini TTS настройки**
```python
# Файл: test_gemini_tts.py
# Переменные для настройки:

MODEL = "gemini-2.5-flash-tts"  # или "gemini-2.5-pro-tts"
VOICE = "Algieba"  # Выбор из 30 голосов
LANGUAGE_CODE = "ru-ru"  # Русский язык
PROMPT = "Расскажи сказку спокойным добрым голосом для ребенка..."
```

#### 4. **Промпты для озвучки**
```python
# Файл: test_gemini_tts.py
# Функция: generate_fairytale_audio()

PROMPT = "Расскажи сказку спокойным добрым голосом для ребенка. Используй интонации."
# ЗДЕСЬ ИЗМЕНИТЬ СТИЛЬ ОЗВУЧКИ
```

---

## 🎨 **ИНТЕРФЕЙС БОТА (КНОПКИ, ТЕКСТЫ, МЕНЮ)**

### 📝 **Основные файлы:**
- **`src/bot/keyboards/inline.py`** - все inline кнопки
- **`src/bot/handlers/start.py`** - главное меню и приветствие
- **`src/bot/handlers/story_creation.py`** - интерфейс создания сказок
- **`src/bot/handlers/history.py`** - интерфейс истории

### 🔧 **Что можно изменить:**

#### 1. **Кнопки и меню**
```python
# Файл: src/bot/keyboards/inline.py

def get_main_menu_keyboard():
    # ЗДЕСЬ ИЗМЕНИТЬ ГЛАВНОЕ МЕНЮ
    
def get_theme_keyboard(child_id: int, interests: list):
    # ЗДЕСЬ ИЗМЕНИТЬ КНОПКИ ВЫБОРА ТЕМ
    
def get_feedback_keyboard(story_id: int, child_id: int):
    # ЗДЕСЬ ИЗМЕНИТЬ КНОПКИ ОБРАТНОЙ СВЯЗИ
```

#### 2. **Тексты сообщений**
```python
# Файл: src/bot/handlers/start.py
# Функция: start_handler()

welcome_text = (
    f"🎭 Привет, {user_name}! Добро пожаловать в мир сказок!\n\n"
    "Я - твой персональный сказочник! ✨\n\n"
    # ЗДЕСЬ ИЗМЕНИТЬ ПРИВЕТСТВИЕ
)
```

#### 3. **Темы сказок**
```python
# Файл: src/bot/keyboards/inline.py
# Функция: get_theme_keyboard()

# ЗДЕСЬ ДОБАВИТЬ НОВЫЕ ТЕМЫ СКАЗОК
```

#### 4. **Сообщения об ошибках**
```python
# Файл: src/bot/handlers/story_creation.py
# Различные функции

# ЗДЕСЬ ИЗМЕНИТЬ СООБЩЕНИЯ ОБ ОШИБКАХ
```

---

## 👤 **УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ И ПРОФИЛЯМИ**

### 📝 **Основные файлы:**
- **`src/bot/handlers/child_profile.py`** - создание профилей детей
- **`src/bot/handlers/profile_management.py`** - управление профилями
- **`src/services/user_service.py`** - логика пользователей
- **`src/services/child_service.py`** - логика профилей детей

### 🔧 **Что можно изменить:**

#### 1. **Создание профилей**
```python
# Файл: src/bot/handlers/child_profile.py
# Функция: handle_child_name()

# ЗДЕСЬ ИЗМЕНИТЬ ПРОЦЕСС СОЗДАНИЯ ПРОФИЛЯ
```

#### 2. **Валидация данных**
```python
# Файл: src/services/child_service.py
# Различные методы валидации

# ЗДЕСЬ ИЗМЕНИТЬ ПРАВИЛА ВАЛИДАЦИИ
```

#### 3. **Ограничения пользователей**
```python
# Файл: src/services/user_service.py
# Метод: can_create_free_story()

async def can_create_free_story(self, user_id: int) -> bool:
    # ЗДЕСЬ ИЗМЕНИТЬ ЛОГИКУ ОГРАНИЧЕНИЙ
```

---

## 🛡️ **БЕЗОПАСНОСТЬ И ВАЛИДАЦИЯ КОНТЕНТА**

### 📝 **Основной файл:**
- **`src/services/content_safety_service.py`** - проверка безопасности контента

### 🔧 **Что можно изменить:**

#### 1. **Фильтры небезопасного контента**
```python
# Файл: src/services/content_safety_service.py
# Метод: validate_input()

def validate_input(self, text: str, child_age: int) -> Tuple[SafetyLevel, List[str]]:
    # ЗДЕСЬ ДОБАВИТЬ НОВЫЕ ПРАВИЛА БЕЗОПАСНОСТИ
```

#### 2. **Возрастные ограничения**
```python
# Файл: src/services/content_safety_service.py
# Различные методы валидации

# ЗДЕСЬ ИЗМЕНИТЬ ВОЗРАСТНЫЕ ОГРАНИЧЕНИЯ
```

---

## 🗄️ **БАЗА ДАННЫХ И МОДЕЛИ**

### 📝 **Основные файлы:**
- **`src/models/user.py`** - модель пользователя
- **`src/models/child.py`** - модель профиля ребенка
- **`src/models/story.py`** - модель сказки
- **`src/models/story_series.py`** - модель серий сказок

### 🔧 **Что можно изменить:**

#### 1. **Структура пользователей**
```python
# Файл: src/models/user.py
class User(Base):
    # ЗДЕСЬ ДОБАВИТЬ НОВЫЕ ПОЛЯ ДЛЯ ПОЛЬЗОВАТЕЛЯ
```

#### 2. **Структура профилей детей**
```python
# Файл: src/models/child.py
class Child(Base):
    # ЗДЕСЬ ДОБАВИТЬ НОВЫЕ ПОЛЯ ДЛЯ ПРОФИЛЯ
```

#### 3. **Структура сказок**
```python
# Файл: src/models/story.py
class Story(Base):
    # ЗДЕСЬ ДОБАВИТЬ НОВЫЕ ПОЛЯ ДЛЯ СКАЗКИ
```

---

## ⚙️ **КОНФИГУРАЦИЯ И НАСТРОЙКИ**

### 📝 **Основные файлы:**
- **`src/core/config.py`** - основные настройки
- **`.env`** - переменные окружения
- **`requirements.txt`** - зависимости Python

### 🔧 **Что можно изменить:**

#### 1. **Основные настройки**
```python
# Файл: src/core/config.py
class Settings(BaseSettings):
    # ЗДЕСЬ ДОБАВИТЬ НОВЫЕ НАСТРОЙКИ
```

#### 2. **Переменные окружения**
```bash
# Файл: .env
# ЗДЕСЬ ДОБАВИТЬ НОВЫЕ ПЕРЕМЕННЫЕ
```

#### 3. **Зависимости**
```txt
# Файл: requirements.txt
# ЗДЕСЬ ДОБАВИТЬ НОВЫЕ БИБЛИОТЕКИ
```

---

## 🔄 **ФОНОВЫЕ ЗАДАЧИ И CELERY**

### 📝 **Основные файлы:**
- **`src/core/celery_app.py`** - конфигурация Celery
- **`src/tasks/`** - фоновые задачи

### 🔧 **Что можно изменить:**

#### 1. **Конфигурация Celery**
```python
# Файл: src/core/celery_app.py
celery_app.conf.update(
    # ЗДЕСЬ ИЗМЕНИТЬ НАСТРОЙКИ CELERY
)
```

#### 2. **Фоновые задачи**
```python
# Файл: src/tasks/test_tasks.py
# ЗДЕСЬ ДОБАВИТЬ НОВЫЕ ФОНОВЫЕ ЗАДАЧИ
```

---

## 🌐 **DEPLOYMENT И ИНФРАСТРУКТУРА**

### 📝 **Основные файлы:**
- **`docker-compose.yml`** - локальная разработка
- **`Dockerfile`** - контейнер приложения
- **`railway.json`** - настройки Railway
- **`railway.toml`** - конфигурация Railway

### 🔧 **Что можно изменить:**

#### 1. **Docker конфигурация**
```yaml
# Файл: docker-compose.yml
# ЗДЕСЬ ИЗМЕНИТЬ НАСТРОЙКИ КОНТЕЙНЕРОВ
```

#### 2. **Railway настройки**
```json
# Файл: railway.json
{
  // ЗДЕСЬ ИЗМЕНИТЬ НАСТРОЙКИ ДЕПЛОЯ
}
```

---

## 📊 **МИГРАЦИИ БАЗЫ ДАННЫХ**

### 📝 **Основные файлы:**
- **`alembic/`** - папка с миграциями
- **`alembic.ini`** - конфигурация Alembic

### 🔧 **Создание миграций:**
```bash
# Создать новую миграцию
docker-compose run --rm app alembic revision --autogenerate -m "Описание изменений"

# Применить миграции
docker-compose run --rm app alembic upgrade head
```

---

## 🧪 **ТЕСТИРОВАНИЕ**

### 📝 **Основные файлы:**
- **`test_gemini_tts.py`** - тест Gemini TTS
- **`src/tasks/test_tasks.py`** - тест Celery

### 🔧 **Запуск тестов:**
```bash
# Тест Gemini TTS
python test_gemini_tts.py

# Тест Celery
docker-compose run --rm app python -c "from src.tasks.test_tasks import test_task; test_task.delay(3)"
```

---

## 📈 **МОНИТОРИНГ И ЛОГИРОВАНИЕ**

### 📝 **Основные файлы:**
- **`src/main.py`** - основная логика и логирование
- **`src/bot/middlewares/`** - middleware для логирования

### 🔧 **Что можно изменить:**

#### 1. **Уровни логирования**
```python
# Файл: src/main.py
logging.basicConfig(
    level=logging.INFO,  # ЗДЕСЬ ИЗМЕНИТЬ УРОВЕНЬ ЛОГИРОВАНИЯ
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---

## 🚀 **БЫСТРЫЙ СТАРТ РАЗРАБОТКИ**

### 1. **Локальная разработка:**
```bash
# Запуск инфраструктуры
docker-compose up -d postgres redis

# Запуск бота
docker-compose --profile app up -d app

# Просмотр логов
docker-compose logs -f app
```

### 2. **Тестирование изменений:**
```bash
# Перезапуск бота после изменений
docker-compose restart app

# Проверка статуса
docker-compose ps
```

### 3. **Деплой на Railway:**
```bash
# Через Railway CLI
railway deploy

# Или через Git (автоматический деплой)
git push origin main
```

---

## 📞 **ПОМОЩЬ И ПОДДЕРЖКА**

Если у вас возникли вопросы по разработке:

1. **Проверьте логи:** `docker-compose logs -f app`
2. **Проверьте статус:** `docker-compose ps`
3. **Перезапустите сервисы:** `docker-compose restart`
4. **Обратитесь к документации** в соответствующих файлах

---

## 🎯 **ПОЛЕЗНЫЕ КОМАНДЫ**

```bash
# Просмотр всех контейнеров
docker-compose ps

# Просмотр логов
docker-compose logs -f [service_name]

# Перезапуск сервиса
docker-compose restart [service_name]

# Выполнение команд в контейнере
docker-compose exec app python -c "print('Hello')"

# Создание миграции
docker-compose run --rm app alembic revision --autogenerate -m "Description"

# Применение миграций
docker-compose run --rm app alembic upgrade head

# Тест подключения к БД
docker-compose exec postgres psql -U fairytale_user -d fairytale_db -c "SELECT version();"

# Тест Redis
docker-compose exec redis redis-cli ping
```

---

**Удачной разработки! 🎭✨**
