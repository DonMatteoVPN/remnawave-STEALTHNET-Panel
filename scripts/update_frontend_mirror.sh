#!/bin/bash
# Скрипт для обновления фронтенда на втором сервере
# Использование: ./update_frontend_mirror.sh user@mirror-server:/opt/stealthnet-frontend

set -e

MIRROR_PATH="${1:-}"
MAIN_SERVER_PATH="/opt/remnawave-STEALTHNET-Panel"

if [ -z "$MIRROR_PATH" ]; then
    echo "❌ Ошибка: Укажите путь к второму серверу"
    echo "Использование: $0 user@mirror-server:/opt/stealthnet-frontend"
    exit 1
fi

echo "🔨 Сборка фронтенда..."
cd "$MAIN_SERVER_PATH/admin-panel"
npm run build

echo "📦 Создание архива..."
cd "$MAIN_SERVER_PATH"
tar -czf /tmp/frontend-build-$(date +%Y%m%d-%H%M%S).tar.gz frontend/build

ARCHIVE_FILE=$(ls -t /tmp/frontend-build-*.tar.gz | head -1)
echo "📤 Копирование на второй сервер: $MIRROR_PATH"

# Определяем, это удаленный сервер или локальный путь
if [[ "$MIRROR_PATH" == *"@"* ]]; then
    # Удаленный сервер через SSH
    scp "$ARCHIVE_FILE" "$MIRROR_PATH/frontend-build.tar.gz"
    ssh "${MIRROR_PATH%%:*}" "cd ${MIRROR_PATH#*:} && rm -rf * && tar -xzf frontend-build.tar.gz && mv frontend/build/* . && rm -rf frontend frontend-build.tar.gz && sudo systemctl reload nginx"
else
    # Локальный путь
    cp "$ARCHIVE_FILE" "$MIRROR_PATH/frontend-build.tar.gz"
    cd "$MIRROR_PATH"
    rm -rf *
    tar -xzf frontend-build.tar.gz
    mv frontend/build/* .
    rm -rf frontend frontend-build.tar.gz
    sudo systemctl reload nginx
fi

echo "✅ Фронтенд успешно обновлен на втором сервере!"
rm -f "$ARCHIVE_FILE"
