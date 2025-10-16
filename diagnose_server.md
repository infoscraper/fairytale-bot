# 🔍 Диагностика проблемы на сервере

## Команды для проверки на сервере:

### 1. Проверить все контейнеры с ботом:
```bash
docker ps -a | grep fairytale
docker ps -a | grep bot
```

### 2. Проверить Docker Swarm сервисы:
```bash
docker service ls
docker service ps <service_name>
```

### 3. Проверить процессы Python:
```bash
ps aux | grep python
ps aux | grep main.py
```

### 4. Проверить Redis блокировки:
```bash
docker exec <redis_container> redis-cli KEYS "bot:poller_lock:*"
docker exec <redis_container> redis-cli GET "bot:poller_lock:*"
docker exec <redis_container> redis-cli TTL "bot:poller_lock:*"
```

### 5. Проверить логи всех контейнеров:
```bash
docker logs <container_name> --tail 50
```

## Ожидаемые результаты:

### ✅ Правильно (должно быть):
- 1 контейнер с ботом в статусе "running"
- 1 Redis контейнер
- 1 PostgreSQL контейнер
- (опционально) 1 Celery worker

### ❌ Проблема (если видите):
- 2+ контейнера с ботом
- Контейнеры в статусе "restarting"
- Множественные процессы python с main.py
- Блокировки в Redis с TTL > 60s

## Решения:

### Немедленные действия:
```bash
# Остановить ВСЕ контейнеры бота
docker stop $(docker ps -q --filter "name=fairytale")

# Удалить старые контейнеры
docker rm $(docker ps -aq --filter "name=fairytale")

# Очистить Redis блокировки
docker exec <redis_container> redis-cli DEL "bot:poller_lock:*"

# Перезапустить только ОДИН экземпляр
docker-compose up -d
```

### Настройка Dokploy:
В конфигурации сервиса установить:
```json
{
  "Mode": {
    "Replicated": {
      "Replicas": 1
    }
  }
}
```

**КРИТИЧНО: Replicas ДОЛЖНО быть = 1!**
