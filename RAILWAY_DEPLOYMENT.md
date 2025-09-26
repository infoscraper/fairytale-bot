# Railway Deployment Guide

## 🚀 Деплой Fairytale Bot на Railway

### Предварительные требования

1. **Аккаунт Railway**: Зарегистрируйтесь на [railway.app](https://railway.app)
2. **GitHub репозиторий**: Код должен быть в GitHub
3. **API ключи**: Подготовьте все необходимые ключи

### Шаги деплоя

#### 1. Подключение репозитория

1. Войдите в Railway Dashboard
2. Нажмите "New Project"
3. Выберите "Deploy from GitHub repo"
4. Выберите репозиторий `fairytale-bot`

#### 2. Настройка переменных окружения

В Railway Dashboard → Settings → Variables добавьте:

```env
# Database (Railway автоматически создаст PostgreSQL)
DATABASE_URL=postgresql://postgres:password@containers-us-west-xxx.railway.app:5432/railway

# Redis (Railway автоматически создаст Redis)
REDIS_URL=redis://default:password@containers-us-west-xxx.railway.app:6379

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# OpenAI
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4o-mini

# ElevenLabs TTS
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=XB0fDUnXU5powFXDhCwa
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
ELEVENLABS_STABILITY=0.75
ELEVENLABS_SIMILARITY_BOOST=0.85
ELEVENLABS_STYLE=0.2
ELEVENLABS_USE_SPEAKER_BOOST=True

# Environment
ENVIRONMENT=production
DEBUG=False
```

#### 3. Добавление сервисов

1. **PostgreSQL**: Add Service → Database → PostgreSQL
2. **Redis**: Add Service → Database → Redis

#### 4. Настройка базы данных

После создания PostgreSQL сервиса:

1. Railway автоматически создаст переменную `DATABASE_URL`
2. Скопируйте её в переменные окружения основного сервиса
3. При первом деплое миграции применятся автоматически

#### 5. Деплой

1. Railway автоматически начнет деплой при push в main ветку
2. Следите за логами в Railway Dashboard
3. Проверьте статус деплоя

### Мониторинг

- **Логи**: Railway Dashboard → Deployments → View Logs
- **Метрики**: Railway Dashboard → Metrics
- **Переменные**: Railway Dashboard → Settings → Variables

### Troubleshooting

#### Проблемы с базой данных
```bash
# Проверка подключения
railway run python -c "from src.core.database import engine; print('DB OK')"
```

#### Проблемы с миграциями
```bash
# Применение миграций вручную
railway run alembic upgrade head
```

#### Проблемы с Redis
```bash
# Проверка Redis
railway run python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"
```

### Автоматический деплой

Railway автоматически деплоит при:
- Push в main ветку
- Merge Pull Request в main
- Ручной деплой через Dashboard

### Масштабирование

- **Web процесс**: Автоматически масштабируется Railway
- **Worker процесс**: Настройте отдельный сервис для Celery worker

### Стоимость

- **Hobby Plan**: $5/месяц - достаточно для MVP
- **Pro Plan**: $20/месяц - для продакшена

### Безопасность

- Все переменные окружения зашифрованы
- Railway автоматически обновляет SSL сертификаты
- Рекомендуется использовать Railway Secrets для чувствительных данных

## 🎯 Готово!

После деплоя ваш бот будет доступен 24/7 на Railway инфраструктуре!
