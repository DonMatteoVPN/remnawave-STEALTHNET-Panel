#!/usr/bin/env python3
"""
Скрипт для запуска приложения с автоматическими миграциями.
Проверяет наличие БД и выполняет все миграции перед запуском app.py
"""

import os
import sys
import subprocess
from pathlib import Path

def find_database():
    """Находит путь к базе данных в стандартных местах"""
    possible_paths = [
        Path("instance/stealthnet.db"),
        Path("stealthnet.db"),
        Path("/var/www/stealthnet-api/instance/stealthnet.db"),
        Path("/var/www/stealthnet-api/stealthnet.db"),
    ]
    
    # Пробуем прочитать путь из .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        import os
        db_uri = os.getenv('SQLALCHEMY_DATABASE_URI', '')
        if db_uri and db_uri.startswith('sqlite:///'):
            db_path = Path(db_uri.replace('sqlite:///', ''))
            if db_path.exists():
                return db_path
    except:
        pass
    
    # Ищем в стандартных путях
    for db_path in possible_paths:
        if db_path.exists():
            return db_path
    
    return None

def main():
    print("=" * 60)
    print("  Запуск StealthNET API с миграциями")
    print("=" * 60)
    print()
    
    # Ищем базу данных
    db_path = find_database()
    
    # Проверяем наличие базы данных
    if db_path:
        print(f"✅ База данных найдена: {db_path}")
        print("🔄 Выполнение миграций...")
        print()
        
        # Список миграций в правильном порядке
        migrations = [
            "migration/migrate_all.py",
            "migration/migrate_add_active_languages_currencies.py",
            "migration/migrate_add_bonus_days.py",
            "migration/migrate_add_bot_config.py",
            "migration/migrate_add_hwid_device_limit.py",
            "migration/migrate_add_quick_download.py",
            "migration/migrate_add_theme_colors.py",
        ]
        
        # Выполняем миграции
        for migration in migrations:
            migration_path = Path(migration)
            if migration_path.exists():
                print(f"📦 Выполнение {migration}...")
                try:
                    # Для migrate_all.py передаем путь к БД
                    if "migrate_all.py" in migration:
                        result = subprocess.run(
                            [sys.executable, str(migration_path), str(db_path)],
                            check=False,
                            text=True
                        )
                    else:
                        result = subprocess.run(
                            [sys.executable, str(migration_path)],
                            check=False,
                            text=True
                        )
                    
                    if result.returncode == 0:
                        print(f"   ✅ {migration} выполнен успешно")
                    else:
                        # Многие миграции могут завершиться с ошибкой, если уже выполнены
                        # Это нормально, просто выводим предупреждение
                        print(f"   ⚠️  {migration} завершился с кодом {result.returncode} (возможно уже выполнено)")
                except Exception as e:
                    print(f"   ⚠️  Ошибка при выполнении {migration}: {e}")
                print()
            else:
                print(f"   ⚠️  Файл миграции не найден: {migration}")
        
        print("✅ Миграции завершены")
        print()
    else:
        print("ℹ️  База данных не найдена в стандартных местах")
        print("ℹ️  База данных будет создана автоматически при первом запуске")
        print()
    
    # Запускаем приложение
    print("🚀 Запуск приложения...")
    print()
    
    # Заменяем текущий процесс на app.py
    os.execv(sys.executable, [sys.executable, "app.py"] + sys.argv[1:])

if __name__ == "__main__":
    main()

