# 🔧 Настройка systemd сервиса для StealthNET API

## 📋 Создание сервиса

### 1. Скопируйте файл сервиса

```bash
sudo cp /opt/STEALTHNET-Admin-Panel/stealthnet-api.service /etc/systemd/system/
```

### 2. Если используете виртуальное окружение

Отредактируйте файл сервиса и укажите правильный путь к Python:

```bash
sudo nano /etc/systemd/system/stealthnet-api.service
```

Измените строку:
```ini
ExecStart=/opt/STEALTHNET-Admin-Panel/venv/bin/python3 /opt/STEALTHNET-Admin-Panel/app.py
```

На ваш путь к Python (если venv в другом месте или используете системный Python):
```ini
ExecStart=/usr/bin/python3 /opt/STEALTHNET-Admin-Panel/app.py
```

### 3. Перезагрузите systemd

```bash
sudo systemctl daemon-reload
```

### 4. Запустите сервис

```bash
sudo systemctl start stealthnet-api
sudo systemctl enable stealthnet-api  # Автозапуск при загрузке
```

### 5. Проверьте статус

```bash
sudo systemctl status stealthnet-api
```

### 6. Просмотр логов

```bash
sudo journalctl -u stealthnet-api -f
```

---

## 🔄 Управление сервисом

```bash
# Запустить
sudo systemctl start stealthnet-api

# Остановить
sudo systemctl stop stealthnet-api

# Перезапустить
sudo systemctl restart stealthnet-api

# Статус
sudo systemctl status stealthnet-api

# Логи
sudo journalctl -u stealthnet-api -n 100
sudo journalctl -u stealthnet-api -f
```

---

## ⚙️ Настройка для вашего окружения

### Если используете venv

Убедитесь, что путь к venv правильный:
```bash
ls -la /opt/STEALTHNET-Admin-Panel/venv/bin/python3
```

### Если используете системный Python

Измените в сервисе:
```ini
ExecStart=/usr/bin/python3 /opt/STEALTHNET-Admin-Panel/app.py
```

### Если нужны переменные окружения

Добавьте в секцию `[Service]`:
```ini
Environment="FLASK_ENV=production"
EnvironmentFile=/opt/STEALTHNET-Admin-Panel/.env
```

---

## 🐳 Альтернатива: Docker

Если предпочитаете Docker, используйте `docker-compose.yml` - он уже настроен для запуска через `app.py` напрямую.
