# Railway Deployment Guide

## Автоматическое развертывание

Railway может автоматически развернуть ваш проект из GitHub репозитория. Проект уже настроен для этого!

## Что нужно сделать:

### 1. Подключить репозиторий к Railway
1. Зайдите на [railway.app](https://railway.app)
2. Нажмите "New Project"
3. Выберите "Deploy from GitHub repo"
4. Выберите репозиторий `infoscraper/fairytale-bot`

### 2. Настроить переменные окружения
В Railway Dashboard добавьте следующие переменные:

**Обязательные:**
- `TELEGRAM_BOT_TOKEN` - токен вашего Telegram бота
- `DATABASE_URL` - URL PostgreSQL базы данных
- `REDIS_URL` - URL Redis для кеширования
- `OPENAI_API_KEY` - API ключ OpenAI

**Опциональные:**
- `ELEVENLABS_API_KEY` - для TTS (если используете)
- `ENVIRONMENT=production`
- `DEBUG=false`

### 3. Добавить базы данных
В Railway можно добавить:
- **PostgreSQL** - для основной базы данных
- **Redis** - для кеширования и FSM

### 4. Автоматическое развертывание
Railway автоматически:
- ✅ Соберет Docker образ
- ✅ Установит зависимости
- ✅ Запустит миграции (если настроены)
- ✅ Запустит бота
- ✅ Будет мониторить health check на `/health`

## Файлы конфигурации

Проект содержит все необходимые файлы:
- `railway.json` - основная конфигурация Railway
- `railway.toml` - дополнительные настройки
- `Procfile` - команда запуска
- `Dockerfile` - образ для контейнеризации
- Health check endpoint в `src/main.py`

## Мониторинг

После развертывания:
- Логи доступны в Railway Dashboard
- Health check: `https://your-app.railway.app/health`
- Метрики и мониторинг встроены

## Обновления

При push в main ветку Railway автоматически пересоберет и перезапустит приложение.
