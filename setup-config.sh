#!/bin/bash

# === Интерактивный скрипт настройки конфигов ===
# setup-config.sh

CONFIG_DIR="./configs"
BACKUP_SUFFIX=".bak"

echo "=== Интерактивная настройка конфигурационных файлов ==="

# Проверка существования директории configs
if [ ! -d "$CONFIG_DIR" ]; then
    echo "❌ Ошибка: Директория $CONFIG_DIR не найдена."
    exit 1
fi

# Функция для резервного копирования файла
backup_file() {
    local file=$1
    if [ -f "$file" ] && [ ! -f "${file}${BACKUP_SUFFIX}" ]; then
        cp "$file" "${file}${BACKUP_SUFFIX}"
        echo "  Создана резервная копия: ${file}${BACKUP_SUFFIX}"
    fi
}

# Сбор данных от пользователя
echo ""
echo "Пожалуйста, введите следующие данные:"
echo "----------------------------------------"

read -p "Введите токен вашего Telegram бота: " BOT_TOKEN
while [ -z "$BOT_TOKEN" ]; do
    echo "❌ Токен не может быть пустым."
    read -p "Введите токен вашего Telegram бота: " BOT_TOKEN
done

read -p "Введите ваш Telegram Chat ID: " ADMIN_CHAT_ID
while ! [[ "$ADMIN_CHAT_ID" =~ ^-?[0-9]+$ ]]; do
    echo "❌ Chat ID должен быть числом."
    read -p "Введите ваш Telegram Chat ID: " ADMIN_CHAT_ID
done

read -p "Введите ваш IP адрес для исключения из Fail2Ban (например, 192.168.1.100): " USER_IP
while ! [[ "$USER_IP" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; do
    echo "❌ Неверный формат IP адреса."
    read -p "Введите ваш IP адрес для исключения из Fail2Ban: " USER_IP
done

read -p "Введите email для Fail2Ban (опционально): " FAIL2BAN_EMAIL
FAIL2BAN_EMAIL=${FAIL2BAN_EMAIL:-"your-email@example.com"}

echo ""
echo "Собранные данные:"
echo "  Токен бота: $BOT_TOKEN"
echo "  Chat ID: $ADMIN_CHAT_ID"
echo "  Ваш IP: $USER_IP"
echo "  Email для Fail2Ban: $FAIL2BAN_EMAIL"
echo ""

read -p "Продолжить настройку с этими данными? (y/N): " confirm
confirm=${confirm:-"n"}
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Настройка отменена пользователем."
    exit 0
fi

echo ""
echo "Начинается настройка конфигурационных файлов..."
echo "----------------------------------------"

# 1. Настройка bot.py
BOT_PY_FILE="$CONFIG_DIR/bot.py"
if [ -f "$BOT_PY_FILE" ]; then
    echo "Настройка $BOT_PY_FILE..."
    backup_file "$BOT_PY_FILE"
    sed -i "s/YOUR_BOT_TOKEN_HERE/$BOT_TOKEN/g" "$BOT_PY_FILE"
    sed -i "s/YOUR_CHAT_ID_HERE/$ADMIN_CHAT_ID/g" "$BOT_PY_FILE"
    echo "  ✅ $BOT_PY_FILE обновлён"
else
    echo "❌ Файл $BOT_PY_FILE не найден"
fi

# 2. Настройка ssh-notify.sh
SSH_NOTIFY_FILE="$CONFIG_DIR/ssh-notify.sh"
if [ -f "$SSH_NOTIFY_FILE" ]; then
    echo "Настройка $SSH_NOTIFY_FILE..."
    backup_file "$SSH_NOTIFY_FILE"
    sed -i "s/YOUR_BOT_TOKEN_HERE/$BOT_TOKEN/g" "$SSH_NOTIFY_FILE"
    sed -i "s/YOUR_CHAT_ID_HERE/$ADMIN_CHAT_ID/g" "$SSH_NOTIFY_FILE"
    echo "  ✅ $SSH_NOTIFY_FILE обновлён"
else
    echo "❌ Файл $SSH_NOTIFY_FILE не найден"
fi

# 3. Настройка fail2ban-telegram-alert.sh
ALERT_SCRIPT="$CONFIG_DIR/scripts/fail2ban-telegram-alert.sh"
if [ -f "$ALERT_SCRIPT" ]; then
    echo "Настройка $ALERT_SCRIPT..."
    backup_file "$ALERT_SCRIPT"
    sed -i "s/YOUR_BOT_TOKEN_HERE/$BOT_TOKEN/g" "$ALERT_SCRIPT"
    sed -i "s/YOUR_CHAT_ID_HERE/$ADMIN_CHAT_ID/g" "$ALERT_SCRIPT"
    echo "  ✅ $ALERT_SCRIPT обновлён"
else
    echo "❌ Файл $ALERT_SCRIPT не найден"
fi

# 4. Настройка jail.local
JAIL_LOCAL="$CONFIG_DIR/fail2ban/jail.local"
if [ -f "$JAIL_LOCAL" ]; then
    echo "Настройка $JAIL_LOCAL..."
    backup_file "$JAIL_LOCAL"
    sed -i "s/YOUR_IP_HERE/$USER_IP/g" "$JAIL_LOCAL"
    sed -i "s/your-email@example.com/$FAIL2BAN_EMAIL/g" "$JAIL_LOCAL"
    echo "  ✅ $JAIL_LOCAL обновлён"
else
    echo "❌ Файл $JAIL_LOCAL не найден"
fi

# 5. Настройка systemd сервиса (замена плейсхолдера на $SUDO_USER)
SERVICE_FILE="$CONFIG_DIR/systemd/fail2ban-tgbot.service"
if [ -f "$SERVICE_FILE" ]; then
    echo "Проверка $SERVICE_FILE..."
    if grep -q "YOUR_USER_HERE" "$SERVICE_FILE"; then
        echo "  ℹ️  Плейсхолдер 'YOUR_USER_HERE' будет заменён автоматически при установке на \$SUDO_USER"
    else
        echo "  ✅ $SERVICE_FILE готов к использованию"
    fi
else
    echo "❌ Файл $SERVICE_FILE не найден"
fi

echo ""
echo "✅ Настройка конфигурационных файлов завершена!"
echo ""
echo "Теперь вы можете запустить установку:"
echo "  chmod +x main.sh"
echo "  sudo ./main.sh"
echo ""
