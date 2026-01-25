#!/bin/bash
# Скрипт для синхронизации фронтенда на несколько серверов
# Использование: ./sync_frontend_servers.sh

set -e

# ⚙️ НАСТРОЙКИ - ИЗМЕНИТЕ ПОД ВАШИ СЕРВЕРЫ
# Формат: "user@server-ip:/path/to/frontend"
SERVERS=(
    "user@server1-ip:/opt/stealthnet-frontend"
    "user@server2-ip:/opt/stealthnet-frontend"
)

MAIN_SERVER_PATH="/opt/remnawave-STEALTHNET-Panel"
FRONTEND_BUILD_PATH="$MAIN_SERVER_PATH/frontend/build"

echo "🔨 Сборка фронтенда..."
cd "$MAIN_SERVER_PATH/admin-panel"
npm run build

if [ ! -d "$FRONTEND_BUILD_PATH" ]; then
    echo "❌ Ошибка: Директория $FRONTEND_BUILD_PATH не найдена"
    exit 1
fi

echo "📤 Синхронизация с серверами..."

for server in "${SERVERS[@]}"; do
    echo "  → Синхронизация с $server..."
    
    # Определяем, это удаленный сервер или локальный путь
    if [[ "$server" == *"@"* ]]; then
        # Удаленный сервер через SSH/rsync
        USER_HOST="${server%%:*}"
        REMOTE_PATH="${server#*:}"
        
        # Копируем файлы через rsync
        rsync -avz --delete \
            --exclude='*.map' \
            "$FRONTEND_BUILD_PATH/" \
            "$USER_HOST:$REMOTE_PATH/"
        
        # Перезагружаем nginx на удаленном сервере
        ssh "$USER_HOST" "sudo systemctl reload nginx" 2>/dev/null || echo "    ⚠️  Не удалось перезагрузить nginx (может потребоваться ручная перезагрузка)"
    else
        # Локальный путь
        rsync -avz --delete \
            --exclude='*.map' \
            "$FRONTEND_BUILD_PATH/" \
            "$server/"
        
        # Перезагружаем nginx локально
        sudo systemctl reload nginx 2>/dev/null || echo "    ⚠️  Не удалось перезагрузить nginx"
    fi
    
    echo "    ✅ Готово"
done

echo ""
echo "✅ Фронтенд успешно синхронизирован на все серверы!"
echo ""
echo "📋 Проверка доступности серверов:"
for server in "${SERVERS[@]}"; do
    if [[ "$server" == *"@"* ]]; then
        USER_HOST="${server%%:*}"
        SERVER_IP="${USER_HOST#*@}"
        echo "  → Проверка $SERVER_IP..."
        if curl -s -f -o /dev/null -w "%{http_code}" "http://$SERVER_IP/api/public/health" | grep -q "200"; then
            echo "    ✅ Сервер доступен"
        else
            echo "    ⚠️  Сервер недоступен или health check не работает"
        fi
    fi
done
