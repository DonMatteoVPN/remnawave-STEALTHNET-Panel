#!/usr/bin/env python3
"""
Скрипт для автоматической рассылки уведомлений в Telegram боты
Проверяет пользователей с истекающими подписками и триалами
"""

import os
import sys
import json
from datetime import datetime, timezone, timedelta
import requests

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения ДО импорта app
from dotenv import load_dotenv
load_dotenv()

def get_user_subscription_info(remnawave_uuid):
    """Получить информацию о подписке пользователя из RemnaWave API"""
    try:
        api_url = os.getenv("API_URL")
        admin_token = os.getenv("ADMIN_TOKEN")
        
        if not api_url or not admin_token:
            return None
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{api_url}/api/users/{remnawave_uuid}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            user_data = data.get('response', {})
            return user_data
        return None
    except Exception as e:
        print(f"Error getting user info for {remnawave_uuid}: {e}")
        return None

def parse_iso_datetime(iso_string):
    """Парсинг ISO datetime строки"""
    if not iso_string:
        return None
    try:
        # Убираем микросекунды если есть
        if '.' in iso_string:
            iso_string = iso_string.split('.')[0] + 'Z'
        return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    except:
        return None

def send_telegram_message(bot_token, chat_id, text, photo_file=None, button_text=None, button_url=None, button_action=None):
    """Отправить сообщение в Telegram с опциональной inline кнопкой"""
    try:
        # Формируем inline keyboard если есть кнопка
        reply_markup = None
        if button_text and (button_url or button_action):
            if button_action == 'tariffs':
                # Callback кнопка для открытия тарифов
                reply_markup = {
                    "inline_keyboard": [[{
                        "text": button_text,
                        "callback_data": "tariffs"
                    }]]
                }
            elif button_action == 'webapp' and button_url:
                # Web App кнопка
                reply_markup = {
                    "inline_keyboard": [[{
                        "text": button_text,
                        "web_app": {"url": button_url}
                    }]]
                }
            elif button_action == 'url' and button_url:
                # Обычная URL кнопка
                reply_markup = {
                    "inline_keyboard": [[{
                        "text": button_text,
                        "url": button_url
                    }]]
                }
            elif button_action == 'trial':
                # Callback кнопка для триала
                reply_markup = {
                    "inline_keyboard": [[{
                        "text": button_text,
                        "callback_data": "activate_trial"
                    }]]
                }
        
        if photo_file:
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            caption = text[:1024] if len(text) > 1024 else text
            files = {'photo': photo_file}
            data = {
                "chat_id": chat_id,
                "caption": caption,
                "parse_mode": "HTML"
            }
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup)
            response = requests.post(url, files=files, data=data, timeout=30)
        else:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return True, result.get('result', {}).get('message_id')
        else:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get('description', f'HTTP {response.status_code}')
            return False, error_msg
    except Exception as e:
        return False, str(e)

def send_auto_broadcasts():
    """Отправить автоматические рассылки"""
    # Импортируем уже инициализированное приложение из app.py
    # app.py уже импортирует и инициализирует все модели
    from app import app, db, User, AutoBroadcastMessage
    
    with app.app_context():
        
        # Получаем настройки автоматических рассылок
        subscription_msg = AutoBroadcastMessage.query.filter_by(
            message_type='subscription_expiring_3days'
        ).first()
        
        trial_msg = AutoBroadcastMessage.query.filter_by(
            message_type='trial_expiring'
        ).first()
        
        no_subscription_msg = AutoBroadcastMessage.query.filter_by(
            message_type='no_subscription'
        ).first()
        
        trial_not_used_msg = AutoBroadcastMessage.query.filter_by(
            message_type='trial_not_used'
        ).first()
        
        trial_active_msg = AutoBroadcastMessage.query.filter_by(
            message_type='trial_active'
        ).first()
        
        # Получаем токены ботов
        old_bot_token = os.getenv("CLIENT_BOT_TOKEN")
        new_bot_token = os.getenv("CLIENT_BOT_V2_TOKEN") or os.getenv("CLIENT_BOT_TOKEN")
        
        if not old_bot_token and not new_bot_token:
            print("❌ Bot tokens not configured")
            return False
        
        # Текущая дата
        now = datetime.now(timezone.utc)
        three_days_later = now + timedelta(days=3)
        
        # Получаем всех пользователей с telegram_id и remnawave_uuid
        users = User.query.filter(
            User.telegram_id != None,
            User.telegram_id != '',
            User.remnawave_uuid != None,
            User.remnawave_uuid != ''
        ).all()
        
        subscription_sent = 0
        subscription_failed = 0
        trial_sent = 0
        trial_failed = 0
        no_subscription_sent = 0
        no_subscription_failed = 0
        trial_not_used_sent = 0
        trial_not_used_failed = 0
        trial_active_sent = 0
        trial_active_failed = 0
        
        print(f"Проверяем {len(users)} пользователей...")
        
        for user in users:
            try:
                # Получаем информацию о подписке
                user_info = get_user_subscription_info(user.remnawave_uuid)
                if not user_info:
                    # Пользователь без подписки
                    if no_subscription_msg and no_subscription_msg.enabled:
                        bot_token = None
                        if no_subscription_msg.bot_type == 'old' or no_subscription_msg.bot_type == 'both':
                            bot_token = old_bot_token
                        elif no_subscription_msg.bot_type == 'new':
                            bot_token = new_bot_token
                        
                        if bot_token:
                            success, result = send_telegram_message(
                                bot_token, user.telegram_id, no_subscription_msg.message_text,
                                button_text=no_subscription_msg.button_text,
                                button_url=no_subscription_msg.button_url,
                                button_action=no_subscription_msg.button_action
                            )
                            if success:
                                no_subscription_sent += 1
                                print(f"✅ Отправлено сообщение 'без подписки' пользователю {user.email} (ID: {user.telegram_id})")
                            else:
                                no_subscription_failed += 1
                                print(f"❌ Ошибка отправки 'без подписки' пользователю {user.email}: {result}")
                    continue
                
                expire_at_str = user_info.get('expireAt')
                active_squads = user_info.get('activeInternalSquads', [])
                has_active_subscription = len(active_squads) > 0 if active_squads else False
                
                # Проверяем, есть ли у пользователя активная подписка
                if not has_active_subscription:
                    # Пользователь без активной подписки
                    if no_subscription_msg and no_subscription_msg.enabled:
                        bot_token = None
                        if no_subscription_msg.bot_type == 'old' or no_subscription_msg.bot_type == 'both':
                            bot_token = old_bot_token
                        elif no_subscription_msg.bot_type == 'new':
                            bot_token = new_bot_token
                        
                        if bot_token:
                            success, result = send_telegram_message(
                                bot_token, user.telegram_id, no_subscription_msg.message_text,
                                button_text=no_subscription_msg.button_text,
                                button_url=no_subscription_msg.button_url,
                                button_action=no_subscription_msg.button_action
                            )
                            if success:
                                no_subscription_sent += 1
                                print(f"✅ Отправлено сообщение 'без подписки' пользователю {user.email} (ID: {user.telegram_id})")
                            else:
                                no_subscription_failed += 1
                                print(f"❌ Ошибка отправки 'без подписки' пользователю {user.email}: {result}")
                    continue
                
                if not expire_at_str:
                    continue
                
                expire_at = parse_iso_datetime(expire_at_str)
                if not expire_at:
                    continue
                
                # Проверяем, истекает ли подписка через 3 дня
                days_until_expiry = (expire_at - now).days
                
                # Проверяем, является ли это триалом (обычно 3 дня)
                created_at_str = user_info.get('createdAt')
                created_at = parse_iso_datetime(created_at_str) if created_at_str else None
                is_trial = False
                if created_at and expire_at:
                    total_days = (expire_at - created_at).days
                    # Если подписка длится 3 дня или меньше, считаем это триалом
                    if total_days <= 3:
                        is_trial = True
                
                # Проверяем подписку, истекающую через 3 дня
                # Отправляем за 3 дня до окончания
                is_subscription_expiring = (
                    days_until_expiry == 3 and 
                    expire_at > now and 
                    expire_at <= three_days_later and
                    not is_trial
                )
                
                # Проверяем триал, который заканчивается сегодня или завтра
                is_trial_expiring = (
                    is_trial and
                    days_until_expiry <= 1 and
                    expire_at > now and
                    expire_at <= (now + timedelta(days=1))
                )
                
                # Проверяем активный триал (осталось больше 1 дня)
                is_trial_active = (
                    is_trial and
                    days_until_expiry > 1 and
                    expire_at > now
                )
                
                # Отправляем уведомление о подписке
                if is_subscription_expiring and subscription_msg and subscription_msg.enabled:
                    message_text = subscription_msg.message_text
                    bot_type = subscription_msg.bot_type
                    
                    # Выбираем токен бота
                    bot_token = None
                    if bot_type == 'old' or bot_type == 'both':
                        bot_token = old_bot_token
                    elif bot_type == 'new':
                        bot_token = new_bot_token
                    
                    if bot_token:
                        success, result = send_telegram_message(
                            bot_token, user.telegram_id, message_text,
                            button_text=subscription_msg.button_text,
                            button_url=subscription_msg.button_url,
                            button_action=subscription_msg.button_action
                        )
                        if success:
                            subscription_sent += 1
                            print(f"✅ Отправлено уведомление о подписке пользователю {user.email} (ID: {user.telegram_id})")
                        else:
                            subscription_failed += 1
                            print(f"❌ Ошибка отправки подписки пользователю {user.email}: {result}")
                
                # Отправляем уведомление о триале
                if is_trial_expiring and trial_msg and trial_msg.enabled:
                    message_text = trial_msg.message_text
                    bot_type = trial_msg.bot_type
                    
                    # Выбираем токен бота
                    bot_token = None
                    if bot_type == 'old' or bot_type == 'both':
                        bot_token = old_bot_token
                    elif bot_type == 'new':
                        bot_token = new_bot_token
                    
                    if bot_token:
                        success, result = send_telegram_message(
                            bot_token, user.telegram_id, message_text,
                            button_text=trial_msg.button_text,
                            button_url=trial_msg.button_url,
                            button_action=trial_msg.button_action
                        )
                        if success:
                            trial_sent += 1
                            print(f"✅ Отправлено уведомление о триале пользователю {user.email} (ID: {user.telegram_id})")
                        else:
                            trial_failed += 1
                            print(f"❌ Ошибка отправки триала пользователю {user.email}: {result}")
                
                # Отправляем уведомление об активном триале
                if is_trial_active and trial_active_msg and trial_active_msg.enabled:
                    message_text = trial_active_msg.message_text
                    bot_type = trial_active_msg.bot_type
                    
                    # Выбираем токен бота
                    bot_token = None
                    if bot_type == 'old' or bot_type == 'both':
                        bot_token = old_bot_token
                    elif bot_type == 'new':
                        bot_token = new_bot_token
                    
                    if bot_token:
                        success, result = send_telegram_message(
                            bot_token, user.telegram_id, message_text,
                            button_text=trial_active_msg.button_text,
                            button_url=trial_active_msg.button_url,
                            button_action=trial_active_msg.button_action
                        )
                        if success:
                            trial_active_sent += 1
                            print(f"✅ Отправлено уведомление об активном триале пользователю {user.email} (ID: {user.telegram_id})")
                        else:
                            trial_active_failed += 1
                            print(f"❌ Ошибка отправки активного триала пользователю {user.email}: {result}")
            
            except Exception as e:
                print(f"❌ Ошибка обработки пользователя {user.email}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Проверяем пользователей без триала (если они зарегистрированы, но не использовали триал)
        if trial_not_used_msg and trial_not_used_msg.enabled:
            # Получаем пользователей, которые зарегистрированы, но не имеют активной подписки
            users_without_trial = User.query.filter(
                User.telegram_id != None,
                User.telegram_id != '',
                User.remnawave_uuid != None,
                User.remnawave_uuid != ''
            ).all()
            
            for user in users_without_trial:
                try:
                    user_info = get_user_subscription_info(user.remnawave_uuid)
                    if not user_info:
                        continue
                    
                    active_squads = user_info.get('activeInternalSquads', [])
                    has_active = len(active_squads) > 0 if active_squads else False
                    
                    # Если нет активной подписки, проверяем, использовал ли пользователь триал
                    if not has_active:
                        created_at_str = user_info.get('createdAt')
                        created_at = parse_iso_datetime(created_at_str) if created_at_str else None
                        
                        # Если пользователь зарегистрирован более 3 дней назад и не имеет подписки - вероятно, не использовал триал
                        if created_at:
                            days_since_registration = (now - created_at).days
                            if days_since_registration >= 3:
                                bot_token = None
                                if trial_not_used_msg.bot_type == 'old' or trial_not_used_msg.bot_type == 'both':
                                    bot_token = old_bot_token
                                elif trial_not_used_msg.bot_type == 'new':
                                    bot_token = new_bot_token
                                
                                if bot_token:
                                    success, result = send_telegram_message(
                                        bot_token, user.telegram_id, trial_not_used_msg.message_text,
                                        button_text=trial_not_used_msg.button_text,
                                        button_url=trial_not_used_msg.button_url,
                                        button_action=trial_not_used_msg.button_action
                                    )
                                    if success:
                                        trial_not_used_sent += 1
                                        print(f"✅ Отправлено сообщение 'триал не использован' пользователю {user.email} (ID: {user.telegram_id})")
                                    else:
                                        trial_not_used_failed += 1
                                        print(f"❌ Ошибка отправки 'триал не использован' пользователю {user.email}: {result}")
                except Exception as e:
                    print(f"❌ Ошибка обработки пользователя {user.email} для 'триал не использован': {e}")
                    continue
        
        print()
        print("=" * 80)
        print("✅ АВТОМАТИЧЕСКАЯ РАССЫЛКА ЗАВЕРШЕНА")
        print(f"   Подписка (истекает через 3 дня): отправлено {subscription_sent}, ошибок {subscription_failed}")
        print(f"   Триал (истекает): отправлено {trial_sent}, ошибок {trial_failed}")
        print(f"   Без подписки: отправлено {no_subscription_sent}, ошибок {no_subscription_failed}")
        print(f"   Триал не использован: отправлено {trial_not_used_sent}, ошибок {trial_not_used_failed}")
        print(f"   Триал активен: отправлено {trial_active_sent}, ошибок {trial_active_failed}")
        print("=" * 80)
        
        return True

if __name__ == '__main__':
    try:
        send_auto_broadcasts()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

