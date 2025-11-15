#!/bin/bash

echo "🔍 ДИАГНОСТИКА DOKPLOY - МНОЖЕСТВЕННЫЕ ЭКЗЕМПЛЯРЫ БОТА"
echo "=================================================="

echo ""
echo "1️⃣ Проверяем все контейнеры с ботом:"
docker ps -a | grep -E "(fairytale|bot)" || echo "❌ Контейнеры не найдены"

echo ""
echo "2️⃣ Проверяем Docker Swarm сервисы:"
docker service ls 2>/dev/null || echo "ℹ️ Docker Swarm не используется"

echo ""
echo "3️⃣ Проверяем процессы Python:"
ps aux | grep -E "(python|main.py)" | grep -v grep || echo "❌ Python процессы не найдены"

echo ""
echo "4️⃣ Проверяем Redis блокировки:"
REDIS_CONTAINER=$(docker ps -q --filter "name=redis" | head -1)
if [ ! -z "$REDIS_CONTAINER" ]; then
    echo "Redis контейнер: $REDIS_CONTAINER"
    docker exec $REDIS_CONTAINER redis-cli KEYS "bot:poller_lock:*" 2>/dev/null || echo "❌ Не удалось подключиться к Redis"
    docker exec $REDIS_CONTAINER redis-cli GET "bot:poller_lock:*" 2>/dev/null || echo "ℹ️ Блокировки не найдены"
else
    echo "❌ Redis контейнер не найден"
fi

echo ""
echo "5️⃣ Проверяем логи последних контейнеров:"
BOT_CONTAINERS=$(docker ps -q --filter "ancestor=fairytalebot" 2>/dev/null)
if [ ! -z "$BOT_CONTAINERS" ]; then
    for container in $BOT_CONTAINERS; do
        echo "--- Логи контейнера $container ---"
        docker logs $container --tail 10 2>/dev/null
        echo ""
    done
else
    echo "❌ Активные контейнеры бота не найдены"
fi

echo ""
echo "🛠️ ЭКСТРЕННОЕ ИСПРАВЛЕНИЕ:"
echo "========================="

read -p "Хотите остановить ВСЕ контейнеры бота? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🛑 Останавливаем все контейнеры бота..."
    docker stop $(docker ps -q --filter "name=fairytale" 2>/dev/null) 2>/dev/null || echo "ℹ️ Нет активных контейнеров для остановки"
    
    echo "🗑️ Удаляем старые контейнеры..."
    docker rm $(docker ps -aq --filter "name=fairytale" 2>/dev/null) 2>/dev/null || echo "ℹ️ Нет контейнеров для удаления"
    
    echo "🧹 Очищаем Redis блокировки..."
    if [ ! -z "$REDIS_CONTAINER" ]; then
        docker exec $REDIS_CONTAINER redis-cli DEL "bot:poller_lock:*" 2>/dev/null || echo "⚠️ Не удалось очистить блокировки"
    fi
    
    echo "✅ Очистка завершена!"
    echo ""
    echo "📋 СЛЕДУЮЩИЕ ШАГИ:"
    echo "1. Проверьте конфигурацию Dokploy: Replicas = 1"
    echo "2. Перезапустите сервис в Dokploy"
    echo "3. Проверьте логи на наличие одного активного экземпляра"
fi

echo ""
echo "📖 DOKPLOY КОНФИГУРАЦИЯ:"
echo "======================="
echo "В настройках сервиса должно быть:"
echo '{'
echo '  "Mode": {'
echo '    "Replicated": {'
echo '      "Replicas": 1'
echo '    }'
echo '  }'
echo '}'
echo ""
echo "❌ НЕ должно быть:"
echo "- Replicas > 1"
echo "- Global mode"
echo "- Автомасштабирование"
