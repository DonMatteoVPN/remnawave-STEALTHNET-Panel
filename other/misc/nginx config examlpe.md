# Nginx Configuration Example для StealthNET Admin Panel

Этот конфиг основан на рабочей конфигурации и включает поддержку:
- Admin Panel (React SPA)
- Telegram Mini Apps (`/miniapp/` и `/miniapp-v2/`)
- API endpoints (`/api/`)
- Страницы успешной оплаты
- SSL/TLS с современными настройками безопасности
- Gzip компрессия
- CORS для мини-приложений

## 📋 Переменные для замены

Перед использованием замените следующие значения:

- `your-domain.com` → ваш домен (например, `panel.example.com`)
- `127.0.0.1:5000` или `172.17.0.1:5000` → адрес и порт вашего Flask приложения
  - `127.0.0.1:5000` - если Flask запущен на том же сервере
  - `172.17.0.1:5000` - если Flask запущен в Docker контейнере (Docker bridge network)
  - `flask-app:5000` - если используете docker-compose с именем сервиса
- `/opt/admin/frontend/build` → путь к вашему React build
- `/etc/nginx/ssl/your-domain.com/` → путь к вашим SSL сертификатам

## 🔧 Конфигурация

```nginx
# ============================================================================
# HTTP SERVER - Редирект на HTTPS и Let's Encrypt валидация
# ============================================================================
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com;  # ❗️ ЗАМЕНИТЕ НА ВАШ ДОМЕН
    
    # Webroot для Let's Encrypt валидации (для получения SSL сертификата)
    location /.well-known/acme-challenge/ {
        root /var/www/html;
        try_files $uri =404;
    }
    
    # Редирект на HTTPS для всего остального
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# ============================================================================
# HTTPS SERVER - Основная конфигурация
# ============================================================================
server {
    server_name your-domain.com;  # ❗️ ЗАМЕНИТЕ НА ВАШ ДОМЕН

    listen 443 ssl http2;
    listen [::]:443 ssl http2;

    # ========================================================================
    # SSL CONFIGURATION (Mozilla Intermediate Guidelines)
    # ========================================================================
    ssl_protocols          TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:DHE-RSA-CHACHA20-POLY1305;

    ssl_session_timeout 1d;
    ssl_session_cache shared:MozSSL:10m;
    ssl_session_tickets    off;
    
    # Пути к SSL сертификатам
    # ❗️ ЗАМЕНИТЕ НА ПУТИ К ВАШИМ СЕРТИФИКАТАМ
    ssl_certificate /etc/nginx/ssl/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/your-domain.com/privkey.pem;
    ssl_trusted_certificate /etc/nginx/ssl/your-domain.com/fullchain.pem;

    ssl_stapling           on;
    ssl_stapling_verify    on;
    resolver               1.1.1.1 1.0.0.1 8.8.8.8 8.8.4.4 208.67.222.222 208.67.220.220 valid=60s;
    resolver_timeout       2s;

    # Увеличиваем лимит размера тела запроса для загрузки файлов
    # (например, фото для рассылки в админ-панели)
    client_max_body_size 20M;

    # ========================================================================
    # BACKEND API - Проксирование запросов к Flask приложению
    # ========================================================================
    
    # Любой запрос, начинающийся с /api/...
    location /api/ {
        # ❗️ ЗАМЕНИТЕ НА АДРЕС ВАШЕГО FLASK ПРИЛОЖЕНИЯ
        # Варианты:
        # - http://127.0.0.1:5000 - если Flask на том же сервере
        # - http://172.17.0.1:5000 - если Flask в Docker контейнере
        # - http://flask-app:5000 - если используете docker-compose
        proxy_pass http://127.0.0.1:5000;
        
        # Стандартные заголовки для проксирования
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Лимит размера тела запроса для API
        client_max_body_size 20M;
    }

    # ========================================================================
    # TELEGRAM MINI APP v1 (/miniapp/)
    # ========================================================================
    
    # Статические файлы мини-приложения (HTML, JS, CSS, изображения)
    # Отдаем напрямую из файловой системы для лучшей производительности
    location ~ ^/miniapp/.*\.(html|js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|json)$ {
        # ❗️ ЗАМЕНИТЕ НА ПУТЬ К ВАШЕМУ BUILD
        root /opt/admin/frontend/build;
        try_files $uri =404;
        
        # Кэширование статических файлов (1 год)
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Все остальные запросы к /miniapp/* проксируем к бэкенду
    # (например, API запросы из мини-приложения)
    location /miniapp/ {
        # ❗️ ЗАМЕНИТЕ НА АДРЕС ВАШЕГО FLASK ПРИЛОЖЕНИЯ
        proxy_pass http://127.0.0.1:5000;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 20M;
        
        # CORS заголовки для мини-приложения (Telegram WebApp)
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization, X-Telegram-Init-Data" always;
        
        # Обработка OPTIONS запросов (preflight для CORS)
        if ($request_method = OPTIONS) {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type, Authorization, X-Telegram-Init-Data";
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type "text/plain; charset=utf-8";
            add_header Content-Length 0;
            return 204;
        }
    }

    # ========================================================================
    # TELEGRAM MINI APP v2 (/miniapp-v2/)
    # ========================================================================
    
    # Статические файлы мини-приложения v2
    location ~ ^/miniapp-v2/.*\.(html|js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|json)$ {
        # ❗️ ЗАМЕНИТЕ НА ПУТЬ К ВАШЕМУ BUILD
        root /opt/admin/frontend/build;
        try_files $uri =404;
        
        # Кэширование статических файлов (1 год)
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Все остальные запросы к /miniapp-v2/* проксируем к бэкенду
    location /miniapp-v2/ {
        # ❗️ ЗАМЕНИТЕ НА АДРЕС ВАШЕГО FLASK ПРИЛОЖЕНИЯ
        proxy_pass http://127.0.0.1:5000;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 20M;
        
        # CORS заголовки для мини-приложения
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization, X-Telegram-Init-Data" always;
        
        # Обработка OPTIONS запросов
        if ($request_method = OPTIONS) {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type, Authorization, X-Telegram-Init-Data";
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type "text/plain; charset=utf-8";
            add_header Content-Length 0;
            return 204;
        }
    }

    # ========================================================================
    # PAYMENT SUCCESS PAGES - Страницы успешной оплаты
    # ========================================================================
    
    # Страница успешной оплаты для старого мини-аппа
    location = /miniapp/payment-success.html {
        # ❗️ ЗАМЕНИТЕ НА ПУТЬ К ВАШЕМУ BUILD
        root /opt/admin/frontend/build;
        try_files /miniapp/payment-success.html =404;
        
        # Отключаем кэширование для этой страницы (важно для динамического контента)
        add_header Cache-Control "no-cache, no-store, must-revalidate" always;
        add_header Pragma "no-cache" always;
        add_header Expires "0" always;
    }
    
    # Страница успешной оплаты для нового мини-аппа
    location = /miniapp-v2/payment-success.html {
        # ❗️ ЗАМЕНИТЕ НА ПУТЬ К ВАШЕМУ BUILD
        root /opt/admin/frontend/build;
        try_files /miniapp-v2/payment-success.html =404;
        
        # Отключаем кэширование для этой страницы
        add_header Cache-Control "no-cache, no-store, must-revalidate" always;
        add_header Pragma "no-cache" always;
        add_header Expires "0" always;
    }
    
    # Общая страница успешной оплаты (для обратной совместимости)
    location = /payment-success.html {
        # ❗️ ЗАМЕНИТЕ НА ПУТЬ К ВАШЕМУ BUILD
        root /opt/admin/frontend/build;
        # Пробуем сначала новый мини-апп, потом старый
        try_files /miniapp-v2/payment-success.html /miniapp/payment-success.html =404;
        
        # Отключаем кэширование для этой страницы
        add_header Cache-Control "no-cache, no-store, must-revalidate" always;
        add_header Pragma "no-cache" always;
        add_header Expires "0" always;
    }

    # ========================================================================
    # FRONTEND - React SPA (Admin Panel)
    # ========================================================================
    
    # SPA routing - все пути отдаем index.html (React Router)
    location / {
        # ❗️ ЗАМЕНИТЕ НА ПУТЬ К ВАШЕМУ BUILD
        root /opt/admin/frontend/build;
        
        # Сначала пытаемся найти файл, затем директорию, затем index.html
        # Это позволяет React Router обрабатывать маршруты на клиенте
        try_files $uri $uri/ /index.html;
    }

    # Статические файлы (JS, CSS, изображения, шрифты)
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        # ❗️ ЗАМЕНИТЕ НА ПУТЬ К ВАШЕМУ BUILD
        root /opt/admin/frontend/build;
        
        # Кэширование статических файлов (1 год)
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # ========================================================================
    # GZIP COMPRESSION - Сжатие ответов для ускорения загрузки
    # ========================================================================
    
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_buffers 16 8k;
    gzip_http_version 1.1;
    gzip_min_length 256;
    gzip_types
        application/atom+xml
        application/geo+json
        application/javascript
        application/x-javascript
        application/json
        application/ld+json
        application/manifest+json
        application/rdf+xml
        application/rss+xml
        application/xhtml+xml
        application/xml
        font/eot
        font/otf
        font/ttf
        image/svg+xml
        text/css
        text/javascript
        text/plain
        text/xml;
}

# ============================================================================
# ПРИМЕЧАНИЯ И ДОПОЛНИТЕЛЬНАЯ НАСТРОЙКА
# ============================================================================
# 
# 1. Для Docker окружения:
#    - Если Flask запущен в Docker контейнере, используйте:
#      * http://172.17.0.1:5000 (Docker bridge network)
#      * http://flask-app:5000 (если используете docker-compose с именем сервиса)
#      * http://host.docker.internal:5000 (для Docker Desktop на Mac/Windows)
#
# 2. Для production окружения:
#    - Используйте Gunicorn или uWSGI для запуска Flask приложения
#    - Настройте systemd service для автоматического запуска
#    - Настройте логирование и мониторинг
#    - Рассмотрите возможность использования нескольких worker процессов
#
# 3. SSL сертификаты:
#    - Для получения Let's Encrypt сертификата используйте Certbot:
#      certbot --nginx -d your-domain.com
#    - Или настройте вручную, указав пути к сертификатам в конфиге
#
# 4. Безопасность:
#    - Рекомендуется добавить rate limiting для API endpoints
#    - Настройте firewall для ограничения доступа
#    - Регулярно обновляйте SSL сертификаты
#
# 5. Производительность:
#    - Gzip компрессия уже включена
#    - Статические файлы кэшируются на 1 год
#    - Рассмотрите возможность использования CDN для статических файлов
#
# ============================================================================
```
