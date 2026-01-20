#!/bin/bash
# Wrapper скрипт для запуска автоматической рассылки через Docker

# Путь к проекту
PROJECT_DIR="/opt/remnawave-STEALTHNET-Panel"
LOG_FILE="${PROJECT_DIR}/logs/auto_broadcasts.log"

# Создаем директорию для логов, если её нет
mkdir -p "${PROJECT_DIR}/logs"

# Переходим в директорию проекта
cd "${PROJECT_DIR}" || exit 1

# Логируем начало выполнения
echo "" >> "${LOG_FILE}"
echo "========================================" >> "${LOG_FILE}"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting auto broadcasts..." >> "${LOG_FILE}"
echo "========================================" >> "${LOG_FILE}"

# Проверяем, запущен ли контейнер
if ! docker compose ps api 2>/dev/null | grep -q "Up"; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: API container is not running" >> "${LOG_FILE}"
    exit 1
fi

# Запускаем скрипт внутри контейнера
docker compose exec -T api python3 /app/send_auto_broadcasts.py >> "${LOG_FILE}" 2>&1
EXIT_CODE=$?

# Логируем результат
if [ $EXIT_CODE -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ✅ Auto broadcasts completed successfully" >> "${LOG_FILE}"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ❌ ERROR: Auto broadcasts failed with exit code $EXIT_CODE" >> "${LOG_FILE}"
fi

exit $EXIT_CODE

