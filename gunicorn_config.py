"""Gunicorn конфигурация для инициализации базы данных в worker процессах"""

# Глобальная переменная для отслеживания, запущен ли планировщик
scheduler_started = False

def on_starting(server):
    """Вызывается при старте master процесса"""
    print("🚀 [gunicorn] Master процесс запущен")

def when_ready(server):
    """Вызывается когда master процесс готов к работе"""
    print("✅ [gunicorn] Master процесс готов")
    
    # Запускаем планировщик автоматической рассылки в master процессе
    import os
    try:
        auto_broadcast_enabled = os.getenv('AUTO_BROADCAST_ENABLED', 'true').lower() == 'true'
        if auto_broadcast_enabled:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
            
            auto_broadcast_hours = os.getenv('AUTO_BROADCAST_HOURS', '9,14,19')
            hours = [int(h.strip()) for h in auto_broadcast_hours.split(',')]
            
            def run_auto_broadcasts_job():
                """Задача для автоматической рассылки"""
                try:
                    from app import app
                    with app.app_context():
                        from send_auto_broadcasts import send_auto_broadcasts
                        print("📬 [scheduler] Запуск автоматической рассылки...")
                        send_auto_broadcasts()
                        print("✅ [scheduler] Автоматическая рассылка завершена")
                except Exception as e:
                    print(f"❌ [scheduler] Ошибка автоматической рассылки: {e}")
            
            scheduler = BackgroundScheduler(daemon=True)
            
            for hour in hours:
                scheduler.add_job(
                    func=run_auto_broadcasts_job,
                    trigger=CronTrigger(hour=hour, minute=0),
                    id=f'auto_broadcast_{hour}',
                    name=f'Auto Broadcast at {hour}:00',
                    replace_existing=True
                )
            
            scheduler.start()
            server.scheduler = scheduler  # Сохраняем ссылку для остановки
            print(f"📅 [gunicorn] Планировщик автоматической рассылки запущен: {auto_broadcast_hours}:00")
        else:
            print("📅 [gunicorn] Автоматическая рассылка отключена (AUTO_BROADCAST_ENABLED=false)")
    except ImportError:
        print("⚠️ [gunicorn] APScheduler не установлен")
    except Exception as e:
        print(f"⚠️ [gunicorn] Ошибка запуска планировщика: {e}")

def pre_fork(server, worker):
    """Вызывается перед форком worker процесса"""
    print(f"🔧 [gunicorn] Подготовка worker процесса {worker.age}")

def post_fork(server, worker):
    """Вызывается после форка worker процесса - здесь инициализируем БД"""
    import os
    print(f"🚀 [gunicorn] Worker процесс {worker.age} запущен, инициализация БД...")
    print(f"🔍 [gunicorn] Worker {worker.age}: Текущая директория: {os.getcwd()}")
    try:
        # Импортируем app и init_database в worker процессе
        from app import app, init_database
        print(f"🔍 [gunicorn] Worker {worker.age}: app импортирован")
        
        with app.app_context():
            print(f"🔍 [gunicorn] Worker {worker.age}: app_context создан, вызываю init_database()")
            init_database()
            print(f"✅ [gunicorn] Worker {worker.age}: База данных инициализирована")
            
            # Проверяем, что БД создалась
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            if db_path and os.path.exists(db_path):
                db_size = os.path.getsize(db_path)
                print(f"✅ [gunicorn] Worker {worker.age}: БД найдена: {db_path}, размер: {db_size} байт")
            else:
                print(f"⚠️ [gunicorn] Worker {worker.age}: БД НЕ найдена: {db_path}")
    except Exception as e:
        print(f"❌ [gunicorn] Worker {worker.age}: Ошибка инициализации БД: {e}")
        import traceback
        traceback.print_exc()

def worker_int(worker):
    """Вызывается при получении SIGINT/SIGQUIT worker процессом"""
    print(f"🛑 [gunicorn] Worker {worker.age} получил сигнал остановки")

def worker_abort(worker):
    """Вызывается при получении SIGABRT worker процессом"""
    print(f"⚠️ [gunicorn] Worker {worker.age} получил сигнал аварийной остановки")

def on_exit(server):
    """Вызывается при выходе из master процесса"""
    print("🛑 [gunicorn] Остановка master процесса")
    # Останавливаем планировщик
    if hasattr(server, 'scheduler'):
        try:
            server.scheduler.shutdown()
            print("✅ [gunicorn] Планировщик остановлен")
        except Exception as e:
            print(f"⚠️ [gunicorn] Ошибка остановки планировщика: {e}")
