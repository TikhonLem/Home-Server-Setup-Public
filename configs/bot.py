#!/usr/bin/env python3
import subprocess
import re
import logging
import time
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from urllib.parse import parse_qs
import asyncio

# === НАСТРОЙКИ ===
# ВАЖНО: Убедитесь, что эти данные соответствуют вашей домашней версии
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Замени на твой реальный токен бота
ADMIN_CHAT_ID = 981471707  # Замени на свой Chat ID

JAIL = "sshd"

# Пороги для уведомлений (в процентах)
THRESHOLDS = {
    'cpu': {'warning': 70, 'critical': 85, 'emergency': 95},
    'memory': {'warning': 70, 'critical': 85, 'emergency': 95},
    'disk': {'warning': 80, 'critical': 90, 'emergency': 95},
    'temperature': {'warning': 60, 'critical': 75, 'emergency': 85}
}

# Файл для хранения времени последних уведомлений
NOTIFY_LOG_FILE = '/tmp/server_monitor_notify_log.json'

# Таймер блокировки уведомлений (в секундах) - 30 минут
NOTIFY_COOLDOWN = 1800

# Порт для webhook (для Alertmanager)
WEBHOOK_PORT = 8080

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальная переменная для хранения времени последних уведомлений
notify_log = {}

# Загружаем лог уведомлений при запуске
def load_notify_log():
    global notify_log
    try:
        if os.path.exists(NOTIFY_LOG_FILE):
            with open(NOTIFY_LOG_FILE, 'r') as f:
                notify_log = json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки лога уведомлений: {e}")

# Сохраняем лог уведомлений
def save_notify_log():
    try:
        with open(NOTIFY_LOG_FILE, 'w') as f:
            json.dump(notify_log, f)
    except Exception as e:
        logger.error(f"Ошибка сохранения лога уведомлений: {e}")

# Проверяем, можно ли отправлять уведомление
def can_notify(alert_type):
    current_time = time.time()
    if alert_type in notify_log:
        last_time = notify_log[alert_type]
        if current_time - last_time < NOTIFY_COOLDOWN:
            return False
    return True

# Обновляем время последнего уведомления
def update_notify_time(alert_type):
    notify_log[alert_type] = time.time()
    save_notify_log()

# Получаем уровень тревоги
def get_alert_level(value, thresholds):
    if value >= thresholds['emergency']:
        return 'emergency'
    elif value >= thresholds['critical']:
        return 'critical'
    elif value >= thresholds['warning']:
        return 'warning'
    return 'normal'

# Форматируем уровень тревоги
def format_alert_level(level):
    levels = {
        'warning': '🟡',
        'critical': '🔴',
        'emergency': '💥',
        'normal': '🟢'
    }
    return levels.get(level, '🟢')

# Создаём текстовый прогресс-бар
def create_progress_bar(percentage, width=10):
    """Создаёт текстовый прогресс-бар"""
    filled = int(width * percentage // 100)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}] {percentage:.1f}%"

# Отправляем уведомление (асинхронная версия)
async def send_alert_async(context, alert_type, level, message):
    if can_notify(alert_type):
        alert_text = f"{format_alert_level(level)} {message}"
        try:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=alert_text, parse_mode='Markdown')
            update_notify_time(alert_type)
            logger.info(f"Отправлено уведомление: {alert_type} - {level}")
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
    else:
        logger.info(f"Уведомление {alert_type} заблокировано (cooldown)")

# Отправляем уведомление (синхронная версия для webhook)
def send_alert_sync(bot_app, alert_type, level, message):
    if can_notify(alert_type):
        alert_text = f"{format_alert_level(level)} {message}"
        try:
            # Получаем event loop или создаем новый
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Выполняем асинхронную отправку в синхронном контексте
            loop.run_until_complete(bot_app.bot.send_message(chat_id=ADMIN_CHAT_ID, text=alert_text, parse_mode='Markdown'))
            update_notify_time(alert_type)
            logger.info(f"Отправлено уведомление: {alert_type} - {level}")
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
    else:
        logger.info(f"Уведомление {alert_type} заблокировано (cooldown)")

# Обработчик алертов от Alertmanager
class AlertHandler(BaseHTTPRequestHandler):
    def __init__(self, bot_app, *args, **kwargs):
        self.bot_app = bot_app
        super().__init__(*args, **kwargs)
    
    def do_POST(self):
        try:
            # Получаем длину тела запроса
            content_length = int(self.headers['Content-Length'])
            # Читаем тело запроса
            post_data = self.rfile.read(content_length)
            
            # Парсим JSON
            alert_data = json.loads(post_data)
            logger.info(f"Получен алерт: {alert_data}")
            
            # Обрабатываем алерт
            self.process_alert(alert_data)
            
            # Отправляем ответ
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Error')
    
    def process_alert(self, alert_data):
        try:
            # Получаем информацию из алерта
            alerts = alert_data.get('alerts', [])
            for alert in alerts:
                # Определяем статус алерта
                status = alert.get('status', 'unknown')
                labels = alert.get('labels', {})
                annotations = alert.get('annotations', {})
                
                # Получаем данные алерта
                alertname = labels.get('alertname', 'Unknown Alert')
                severity = labels.get('severity', 'unknown')
                summary = annotations.get('summary', 'No summary')
                description = annotations.get('description', 'No description')
                
                # Формируем сообщение
                if status == 'firing':
                    emoji = "🚨"
                    status_text = "Сработал алерт"
                elif status == 'resolved':
                    emoji = "✅"
                    status_text = "Алерт разрешился"
                else:
                    emoji = "⚠️"
                    status_text = f"Статус алерта: {status}"
                
                message = f"{emoji} *{status_text}*\n\n📝 *Название:* {alertname}\n⚠️ *Уровень:* {severity}\n📋 *Сводка:* {summary}\n📄 *Описание:* {description}"
                
                # Отправляем сообщение в Telegram (синхронно)
                send_alert_sync(self.bot_app, f"alert_{alertname}", severity, message)
                logger.info(f"Отправлен алерт в Telegram: {alertname}")
        except Exception as e:
            logger.error(f"Ошибка обработки алерта: {e}")

# Фабрика для создания обработчиков с передачей bot_app
def make_handler(bot_app):
    def handler(*args, **kwargs):
        return AlertHandler(bot_app, *args, **kwargs)
    return handler

# Проверка состояния сервера
async def check_server_status(context):
    try:
        # Проверка CPU
        cpu_result = subprocess.run(['uptime'], capture_output=True, text=True, check=True)
        cpu_line = cpu_result.stdout.strip()
        cpu_match = re.search(r'load average: ([\d.]+), ([\d.]+), ([\d.]+)', cpu_line)
        if cpu_match:
            load_1min, load_5min, load_15min = map(float, cpu_match.groups())
            # Получаем количество ядер CPU
            cpu_cores_result = subprocess.run(['nproc'], capture_output=True, text=True, check=True)
            cpu_cores = int(cpu_cores_result.stdout.strip())
            # Рассчитываем процент загрузки (1 минута)
            cpu_percent = (load_1min / cpu_cores) * 100
            level = get_alert_level(cpu_percent, THRESHOLDS['cpu'])
            if level != 'normal':
                message = f"🧠 *Загрузка CPU*: `{cpu_percent:.1f}%`\n1 мин: `{load_1min}`, 5 мин: `{load_5min}`, 15 мин: `{load_15min}`, Ядер: `{cpu_cores}`"
                await send_alert_async(context, 'cpu', level, message)

        # Проверка памяти
        mem_result = subprocess.run(['free'], capture_output=True, text=True, check=True)
        mem_lines = mem_result.stdout.strip().split('\n')
        if len(mem_lines) >= 2:
            mem_info = mem_lines[1].split()
            if len(mem_info) >= 7:
                mem_total = int(mem_info[1])
                mem_used = int(mem_info[2])
                mem_percent = (mem_used / mem_total) * 100
                level = get_alert_level(mem_percent, THRESHOLDS['memory'])
                if level != 'normal':
                    message = f"💾 *Память*: `{mem_percent:.1f}%` использовано\nИспользовано: `{mem_used//1024//1024}MB` из `{mem_total//1024//1024}MB`"
                    await send_alert_async(context, 'memory', level, message)

        # Проверка диска
        disk_result = subprocess.run(['df', '/'], capture_output=True, text=True, check=True)
        disk_lines = disk_result.stdout.strip().split('\n')
        if len(disk_lines) >= 2:
            disk_info = disk_lines[1].split()
            if len(disk_info) >= 5:
                disk_percent_str = disk_info[4].replace('%', '')
                disk_percent = int(disk_percent_str)
                level = get_alert_level(disk_percent, THRESHOLDS['disk'])
                if level != 'normal':
                    message = f"💿 *Диск*: `{disk_percent}%` занято\nФайловая система: `{disk_info[0]}`\nТочка монтирования: `{disk_info[5]}`"
                    await send_alert_async(context, 'disk', level, message)

        # Проверка температуры
        try:
            temp_result = subprocess.run(['cat', '/sys/class/thermal/thermal_zone0/temp'], 
                                       capture_output=True, text=True, check=True)
            temp_raw = int(temp_result.stdout.strip())
            temp_celsius = temp_raw / 1000
            level = get_alert_level(temp_celsius, THRESHOLDS['temperature'])
            if level != 'normal':
                message = f"🌡 *Температура*: `{temp_celsius:.1f}°C`"
                await send_alert_async(context, 'temperature', level, message)
        except:
            pass  # Температура не доступна

    except Exception as e:
        logger.error(f"Ошибка проверки состояния сервера: {e}")

# Проверка доступа
def restricted(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.id != ADMIN_CHAT_ID:
            await update.message.reply_text("❌ Доступ запрещён.")
            return
        return await func(update, context)
    return wrapper

# /start
@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я Home Server Bot.\n\n"
        "Доступные команды:\n"
        "  /help — справка\n"
        "  /status — общее состояние сервера *(с кнопками)*\n"
        "  /check — статус SSH\n"
        "  /who — активные сессии\n"
        "  /ban <ip> — заблокировать IP\n"
        "  /unban <ip> — разблокировать IP\n"
        "  /banned — список заблокированных IP\n"
        "  /jailstatus — статус всех тюрем\n"
        "  /cpu — загрузка CPU\n"
        "  /temp — температура системы\n"
        "  /disk — использование диска\n"
        "  /mem — использование памяти\n"
        "  /top — топ процессов\n"
        "  /monitor — вкл/выкл мониторинг\n"
    )

# /help — справка
@restricted
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем статус мониторинга
    monitor_status = "✅ ВКЛЮЧЕН" if context.bot_data.get('monitor_job') else "❌ ВЫКЛЮЧЕН"
    
    help_text = f"""
🔧 **Fail2Ban — Справка и команды**

📌 Основные команды в терминале:

  Показывает, сколько IP заблокировано:
`sudo fail2ban-client status sshd`

  Вручную заблокировать IP:
`sudo fail2ban-client set sshd banip 1.2.3.4`

  Вручную разблокировать IP:
`sudo fail2ban-client set sshd unbanip 1.2.3.4`

  Перезапустить службу:
`sudo systemctl restart fail2ban`


📁 Конфигурация:
  `/etc/fail2ban/jail.local` — основной конфиг
  `/etc/fail2ban/action.d/telegram.conf` — действие для Telegram
  `/usr/local/bin/fail2ban-telegram-alert.sh` — скрипт уведомлений
  `/var/log/fail2ban.log` — логи

🤖 **Команды Telegram-бота:**

`/status` — общее состояние сервера *(с кнопками)*
`/check` — текущий статус защиты SSH  
`/who` — показать активные SSH-сессии  
`/ban <ip>` — заблокировать IP  
`/unban <ip>` — разблокировать IP  
`/banned` — список заблокированных IP  
`/jailstatus` — статус всех тюрем  
`/cpu` — загрузка CPU  
`/temp` — температура системы  
`/disk` — использование диска  
`/mem` — использование памяти  
`/top` — топ процессов  
`/monitor` — вкл/выкл мониторинг *(текущий статус: {monitor_status})*  
`/help` — эта справка

💡 Совет: все настройки — через терминал.  
Уведомления о входе и блокировках приходят автоматически.
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

# /status — общее состояние сервера с кнопками
@restricted
async def server_status_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет главное меню статуса сервера с кнопками."""
    # Получаем данные для прогресс-баров
    try:
        # CPU
        cpu_result = subprocess.run(['uptime'], capture_output=True, text=True, check=True)
        cpu_line = cpu_result.stdout.strip()
        cpu_match = re.search(r'load average: ([\d.]+), ([\d.]+), ([\d.]+)', cpu_line)
        if cpu_match:
            load_1min = float(cpu_match.group(1))
            cpu_cores_result = subprocess.run(['nproc'], capture_output=True, text=True, check=True)
            cpu_cores = int(cpu_cores_result.stdout.strip())
            cpu_percent = (load_1min / cpu_cores) * 100
        else:
            cpu_percent = 0

        # Memory
        mem_result = subprocess.run(['free'], capture_output=True, text=True, check=True)
        mem_lines = mem_result.stdout.strip().split('\n')
        if len(mem_lines) >= 2:
            mem_info = mem_lines[1].split()
            if len(mem_info) >= 7:
                mem_total = int(mem_info[1])
                mem_used = int(mem_info[2])
                mem_percent = (mem_used / mem_total) * 100
            else:
                mem_percent = 0
        else:
            mem_percent = 0

        # Disk
        disk_result = subprocess.run(['df', '/'], capture_output=True, text=True, check=True)
        disk_lines = disk_result.stdout.strip().split('\n')
        if len(disk_lines) >= 2:
            disk_info = disk_lines[1].split()
            if len(disk_info) >= 5:
                disk_percent_str = disk_info[4].replace('%', '')
                disk_percent = int(disk_percent_str)
            else:
                disk_percent = 0
        else:
            disk_percent = 0

        # Temperature
        try:
            temp_result = subprocess.run(['cat', '/sys/class/thermal/thermal_zone0/temp'], 
                                       capture_output=True, text=True, check=True)
            temp_raw = int(temp_result.stdout.strip())
            temp_celsius = temp_raw / 1000
        except:
            temp_celsius = 0

        # Статус мониторинга
        monitor_status = "✅ ВКЛ" if context.bot_data.get('monitor_job') else "❌ ВЫКЛ"

        # Формируем текст с прогресс-барами и временем для обхода ошибки
        status_text = (
            f"📊 *Состояние сервера*\n\n"
            f"🧠 CPU: {create_progress_bar(cpu_percent)}\n"
            f"💾 Память: {create_progress_bar(mem_percent)}\n"
            f"💿 Диск: {create_progress_bar(disk_percent)}\n"
            f"🌡 Температура: `{temp_celsius:.1f}°C`\n"
            f"🔍 Мониторинг: `{monitor_status}`\n"
            f"🕐 Время: `{time.strftime('%H:%M:%S')}`"
        )

        # Кнопки
        keyboard = [
            [InlineKeyboardButton("🧠 Подробнее о CPU", callback_data='detail_cpu')],
            [InlineKeyboardButton("💾 Подробнее о памяти", callback_data='detail_mem')],
            [InlineKeyboardButton("💿 Подробнее о диске", callback_data='detail_disk')],
            [InlineKeyboardButton("🔄 Обновить", callback_data='refresh_status')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.message:
            await update.message.reply_text(status_text, parse_mode='Markdown', reply_markup=reply_markup)
        elif update.callback_query:
            # При обновлении добавляем уникальный элемент, чтобы избежать ошибки
            await update.callback_query.edit_message_text(text=status_text, parse_mode='Markdown', reply_markup=reply_markup)
            await update.callback_query.answer()

    except Exception as e:
        error_msg = f"❌ Ошибка получения статуса: `{e}`"
        if update.message:
            await update.message.reply_text(error_msg, parse_mode='Markdown')
        elif update.callback_query:
            await update.callback_query.edit_message_text(text=error_msg, parse_mode='Markdown')
            await update.callback_query.answer()

# Обработчик callback-запросов от кнопок
@restricted
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на кнопки."""
    query = update.callback_query
    await query.answer() # Подтверждаем получение callback'а

    data = query.data

    if data == 'refresh_status':
        # Обновляем основное меню статуса
        await server_status_menu(update, context)
        
    elif data == 'detail_cpu':
        # Подробности о CPU
        try:
            # Uptime
            uptime_result = subprocess.run(['uptime', '-p'], capture_output=True, text=True, check=True)
            uptime = uptime_result.stdout.strip()
            
            # CPU Load
            cpu_result = subprocess.run(['uptime'], capture_output=True, text=True, check=True)
            cpu_line = cpu_result.stdout.strip()
            cpu_match = re.search(r'load average: ([\d.]+), ([\d.]+), ([\d.]+)', cpu_line)
            if cpu_match:
                cpu_load = f"{cpu_match.group(1)}, {cpu_match.group(2)}, {cpu_match.group(3)}"
            else:
                cpu_load = "Не удалось получить"
            
            # CPU Cores
            cpu_cores_result = subprocess.run(['nproc'], capture_output=True, text=True, check=True)
            cpu_cores = cpu_cores_result.stdout.strip()
            
            detail_text = (
                f"🧠 *Загрузка CPU*\n"
                f"⏱ Аптайм: `{uptime.replace('up ', '')}`\n"
                f"📈 Load Average: `{cpu_load}`\n"
                f"🔢 Ядер: `{cpu_cores}`"
            )
            
            # Кнопка "Назад"
            back_button = [[InlineKeyboardButton("⬅️ Назад", callback_data='back_to_status')]]
            reply_markup = InlineKeyboardMarkup(back_button)
            
            await query.edit_message_text(text=detail_text, parse_mode='Markdown', reply_markup=reply_markup)
        except Exception as e:
            await query.edit_message_text(text=f"❌ Ошибка получения данных CPU: `{e}`", parse_mode='Markdown')
            
    elif data == 'detail_mem':
        # Подробности о памяти
        try:
            result = subprocess.run(['free', '-h'], capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')
            
            if len(lines) >= 3:
                mem_line = lines[1].split()
                swap_line = lines[2].split()
                
                mem_info = f"""🧠 *Использование памяти*

*RAM:*
├─ Всего: `{mem_line[1]}`
├─ Использовано: `{mem_line[2]}`
├─ Свободно: `{mem_line[3]}`
└─ Доступно: `{mem_line[6] if len(mem_line) > 6 else 'N/A'}`

*Swap:*
├─ Всего: `{swap_line[1]}`
├─ Использовано: `{swap_line[2]}`
└─ Свободно: `{swap_line[3]}`"""
                
                # Кнопка "Назад"
                back_button = [[InlineKeyboardButton("⬅️ Назад", callback_data='back_to_status')]]
                reply_markup = InlineKeyboardMarkup(back_button)
                
                await query.edit_message_text(text=mem_info, parse_mode='Markdown', reply_markup=reply_markup)
            else:
                await query.edit_message_text(text="❌ Не удалось получить информацию о памяти.", parse_mode='Markdown')
        except Exception as e:
            await query.edit_message_text(text=f"❌ Ошибка получения информации о памяти: `{e}`", parse_mode='Markdown')
            
    elif data == 'detail_disk':
        # Подробности о диске
        try:
            result = subprocess.run(['df', '-h'], capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')
            
            # Фильтруем только локальные файловые системы
            filtered_lines = [line for line in lines if line.startswith(('/dev/', 'tmpfs'))]
            
            if filtered_lines:
                disk_info = "💿 *Использование диска*\n```\n"
                disk_info += f"{'ФС':<15} {'Размер':<8} {'Исп.':<8} {'Дост.':<8} {'Исп.%':<6} {'Точка монт.'}\n"
                disk_info += "-" * 65 + "\n"
                
                for line in filtered_lines:
                    parts = line.split()
                    if len(parts) >= 6:
                        fs = parts[0][:14]  # Ограничиваем длину
                        size = parts[1]
                        used = parts[2]
                        avail = parts[3]
                        perc = parts[4]
                        mount = parts[5][:15] # Ограничиваем длину точки монтирования
                        disk_info += f"{fs:<15} {size:<8} {used:<8} {avail:<8} {perc:<6} {mount}\n"
                
                disk_info += "```"
                
                # Кнопка "Назад"
                back_button = [[InlineKeyboardButton("⬅️ Назад", callback_data='back_to_status')]]
                reply_markup = InlineKeyboardMarkup(back_button)
                
                await query.edit_message_text(text=disk_info, parse_mode='Markdown', reply_markup=reply_markup)
            else:
                await query.edit_message_text(text="✅ Нет информации о дисках.", parse_mode='Markdown')
        except Exception as e:
            await query.edit_message_text(text=f"❌ Ошибка получения информации о дисках: `{e}`", parse_mode='Markdown')
            
    elif data == 'back_to_status':
        # Возвращаемся к основному меню статуса
        await server_status_menu(update, context)

# /check — статус fail2ban
@restricted
async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = subprocess.run(
            ['sudo', 'fail2ban-client', 'status', JAIL],
            capture_output=True,
            text=True,
            check=True
        )
        await update.message.reply_text(f"```\n{result.stdout}\n```", parse_mode='Markdown')
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"❌ Ошибка: `{e.stderr}`")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: `{e}`")

# /who — активные SSH-сессии
@restricted
async def who(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = subprocess.run(['who'], capture_output=True, text=True, check=True)
        sessions = result.stdout.strip()
        if sessions:
            await update.message.reply_text(f"👥 *Активные сессии:*\n```\n{sessions}\n```", parse_mode='Markdown')
        else:
            await update.message.reply_text("✅ Нет активных сессий.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: `{e}`")

# /ban <ip> — заблокировать IP
@restricted
async def ban_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Укажите IP адрес: `/ban 1.2.3.4`", parse_mode='Markdown')
        return
    
    ip = context.args[0]
    if not is_valid_ip(ip):
        await update.message.reply_text("❌ Неверный формат IP адреса.")
        return

    try:
        result = subprocess.run(
            ['sudo', 'fail2ban-client', 'set', JAIL, 'banip', ip],
            capture_output=True,
            text=True,
            check=True
        )
        await update.message.reply_text(f"✅ IP `{ip}` успешно заблокирован.", parse_mode='Markdown')
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"❌ Ошибка блокировки: `{e.stderr}`")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: `{e}`")

# /unban <ip> — разблокировать IP
@restricted
async def unban_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Укажите IP адрес: `/unban 1.2.3.4`", parse_mode='Markdown')
        return
    
    ip = context.args[0]
    if not is_valid_ip(ip):
        await update.message.reply_text("❌ Неверный формат IP адреса.")
        return

    try:
        result = subprocess.run(
            ['sudo', 'fail2ban-client', 'set', JAIL, 'unbanip', ip],
            capture_output=True,
            text=True,
            check=True
        )
        await update.message.reply_text(f"✅ IP `{ip}` успешно разблокирован.", parse_mode='Markdown')
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"❌ Ошибка разблокировки: `{e.stderr}`")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: `{e}`")

# /banned — список заблокированных IP
@restricted
async def banned_ips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = subprocess.run(
            ['sudo', 'fail2ban-client', 'get', JAIL, 'banned'],
            capture_output=True,
            text=True,
            check=True
        )
        banned = result.stdout.strip()
        if banned:
            await update.message.reply_text(f"🚫 *Заблокированные IP:*\n```\n{banned}\n```", parse_mode='Markdown')
        else:
            await update.message.reply_text("✅ Нет заблокированных IP.")
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"❌ Ошибка получения списка: `{e.stderr}`")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: `{e}`")

# /jailstatus — статус всех тюрем
@restricted
async def jail_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = subprocess.run(
            ['sudo', 'fail2ban-client', 'status'],
            capture_output=True,
            text=True,
            check=True
        )
        await update.message.reply_text(f"```\n{result.stdout}\n```", parse_mode='Markdown')
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"❌ Ошибка: `{e.stderr}`")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: `{e}`")

# /cpu — загрузка CPU (улучшенный формат)
@restricted
async def cpu_load(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # CPU Load
        cpu_result = subprocess.run(['uptime'], capture_output=True, text=True, check=True)
        cpu_line = cpu_result.stdout.strip()
        cpu_match = re.search(r'load average: ([\d.]+), ([\d.]+), ([\d.]+)', cpu_line)
        if cpu_match:
            load_1min, load_5min, load_15min = map(float, cpu_match.groups())
        else:
            load_1min, load_5min, load_15min = "N/A", "N/A", "N/A"
        
        # CPU Cores
        cpu_cores_result = subprocess.run(['nproc'], capture_output=True, text=True, check=True)
        cpu_cores = cpu_cores_result.stdout.strip()
        
        cpu_text = (
            f"🧠 *Загрузка CPU*\n"
            f"📈 Load Average: `{load_1min}, {load_5min}, {load_15min}`\n"
            f"🔢 Ядер: `{cpu_cores}`"
        )
        await update.message.reply_text(cpu_text, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения загрузки CPU: `{e}`")

# /temp — температура
@restricted
async def temperature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        temp = "Не доступно"
        temp_source = "system"
        
        try:
            # Основной способ
            temp_result = subprocess.run(['cat', '/sys/class/thermal/thermal_zone0/temp'], 
                                       capture_output=True, text=True, check=True)
            temp_raw = int(temp_result.stdout.strip())
            temp = f"{temp_raw/1000:.1f}°C"
        except:
            try:
                # Альтернативный способ через sensors
                temp_result = subprocess.run(['sensors'], capture_output=True, text=True, check=True)
                temp_lines = temp_result.stdout.strip().split('\n')
                temp_info = ""
                for line in temp_lines:
                    if 'Core' in line or 'Tctl' in line or 'Package id' in line or 'temp' in line.lower():
                        temp_info += line + "\n"
                if temp_info:
                    temp = f"```\n{temp_info}\n```"
                    temp_source = "sensors"
                else:
                    raise Exception("No temperature data found")
            except:
                temp = "Не удалось получить температуру"
        
        if temp_source == "system":
            temp_text = f"🌡 *Температура системы:*\n\n`{temp}`"
        else:
            temp_text = f"🌡 *Температура системы (sensors):*\n\n{temp}"
            
        await update.message.reply_text(temp_text, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения температуры: `{e}`")

# /disk — использование диска
@restricted
async def disk_usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = subprocess.run(['df', '-h'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        # Фильтруем только локальные файловые системы (исключаем tmpfs и т.п.)
        filtered_lines = [line for line in lines if line.startswith(('/dev/', 'tmpfs'))]
        
        if filtered_lines:
            disk_info = "💿 *Использование диска:*\n```\n"
            disk_info += f"{'ФС':<15} {'Размер':<8} {'Исп.':<8} {'Дост.':<8} {'Исп.%':<6} {'Точка монт.'}\n"
            disk_info += "-" * 65 + "\n"
            
            for line in filtered_lines:
                parts = line.split()
                if len(parts) >= 6:
                    fs = parts[0][:14]  # Ограничиваем длину
                    size = parts[1]
                    used = parts[2]
                    avail = parts[3]
                    perc = parts[4]
                    mount = parts[5][:15] # Ограничиваем длину точки монтирования
                    disk_info += f"{fs:<15} {size:<8} {used:<8} {avail:<8} {perc:<6} {mount}\n"
            
            disk_info += "```"
            await update.message.reply_text(disk_info, parse_mode='Markdown')
        else:
            await update.message.reply_text("✅ Нет информации о дисках.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения информации о дисках: `{e}`")

# /mem — использование памяти
@restricted
async def memory_usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = subprocess.run(['free', '-h'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        if len(lines) >= 3:
            mem_line = lines[1].split()
            swap_line = lines[2].split()
            
            mem_info = f"""
🧠 *Использование памяти:*

*RAM:*
├─ Всего: `{mem_line[1]}`
├─ Использовано: `{mem_line[2]}`
├─ Свободно: `{mem_line[3]}`
└─ Доступно: `{mem_line[6] if len(mem_line) > 6 else 'N/A'}`

*Swap:*
├─ Всего: `{swap_line[1]}`
├─ Использовано: `{swap_line[2]}`
└─ Свободно: `{swap_line[3]}`"""
            await update.message.reply_text(mem_info, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Не удалось получить информацию о памяти.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения информации о памяти: `{e}`")

# /top — топ 20 процессов
@restricted
async def top_processes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = subprocess.run(['top', '-b', '-n', '1'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        # Находим строку с заголовками процессов
        header_index = -1
        for i, line in enumerate(lines):
            if 'PID' in line and 'USER' in line and 'CPU' in line:
                header_index = i
                break
        
        if header_index != -1:
            # Берем заголовок и следующие 20 строк
            process_lines = lines[header_index:header_index+21]
            top_info = "🔥 *Топ 20 процессов:*\n```\n"
            top_info += "\n".join(process_lines)
            top_info += "\n```"
            await update.message.reply_text(top_info, parse_mode='Markdown')
        else:
            # Если не нашли заголовок, просто покажем первые 25 строк
            top_info = "🔥 *Топ процессов:*\n```\n"
            top_info += "\n".join(lines[:25])
            top_info += "\n```"
            await update.message.reply_text(top_info, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения топа процессов: `{e}`")

# /monitor — управление мониторингом
@restricted
async def monitor_control(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, есть ли job_queue
    if not hasattr(context, 'job_queue') or not context.job_queue:
        await update.message.reply_text("❌ Ошибка: Job queue недоступен.", parse_mode='Markdown')
        return
    
    if not context.bot_data.get('monitor_job'):
        # Запускаем мониторинг
        try:
            monitor_job = context.job_queue.run_repeating(
                check_server_status, 
                interval=60,  # Проверка каждую минуту
                first=10
            )
            context.bot_data['monitor_job'] = monitor_job
            await update.message.reply_text("✅ Мониторинг сервера *включен*\nПроверка состояния каждую минуту.", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка запуска мониторинга: `{e}`")
    else:
        # Останавливаем мониторинг
        monitor_job = context.bot_data['monitor_job']
        if monitor_job:
            monitor_job.schedule_removal()
        context.bot_data['monitor_job'] = None
        await update.message.reply_text("❌ Мониторинг сервера *выключен*", parse_mode='Markdown')

# Валидация IP
def is_valid_ip(ip):
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(pattern, ip):
        parts = ip.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    return False

# Запуск
if __name__ == '__main__':
    # Загружаем лог уведомлений
    load_notify_log()
    
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    print("✅ Job queue инициализирован успешно")

    # Хэндлеры
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", server_status_menu)) # Обновлённый хендлер
    app.add_handler(CommandHandler("check", check_status))
    app.add_handler(CommandHandler("who", who))
    app.add_handler(CommandHandler("ban", ban_ip))
    app.add_handler(CommandHandler("unban", unban_ip))
    app.add_handler(CommandHandler("banned", banned_ips))
    app.add_handler(CommandHandler("jailstatus", jail_status))
    app.add_handler(CommandHandler("cpu", cpu_load))
    app.add_handler(CommandHandler("temp", temperature))
    app.add_handler(CommandHandler("disk", disk_usage))
    app.add_handler(CommandHandler("mem", memory_usage))
    app.add_handler(CommandHandler("top", top_processes))
    app.add_handler(CommandHandler("monitor", monitor_control))
    
    # Добавляем хендлер для кнопок
    app.add_handler(CallbackQueryHandler(button_handler))

    # Запуск webhook-сервера в отдельном потоке
    handler = make_handler(app)
    server = HTTPServer(('', WEBHOOK_PORT), handler)
    webhook_thread = threading.Thread(target=server.serve_forever, daemon=True)
    webhook_thread.start()
    logger.info(f"Webhook сервер запущен на порту {WEBHOOK_PORT}")
    
    logger.info("Home Server Bot запущен и готов к работе")
    print("✅ Home Server Bot запущен. Ожидание команд...")
    app.run_polling()
