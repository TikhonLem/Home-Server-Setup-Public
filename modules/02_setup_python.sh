#!/bin/bash

source ./utils/logger.sh

# Создание директории для бота
log "[*] Creating bot directory..."
mkdir -p /opt/fail2ban-telegram-bot
chown $SUDO_USER:$SUDO_USER /opt/fail2ban-telegram-bot

# Создание виртуального окружения и установка зависимостей
log "[*] Creating Python virtual environment and installing dependencies..."
sudo -u $SUDO_USER bash << 'EOF'
cd /opt/fail2ban-telegram-bot
python3 -m venv venv
source venv/bin/activate
pip install "python-telegram-bot[job-queue]" httpx
EOF

# Копирование бота
log "[*] Copying bot.py..."
cp ./configs/bot.py /opt/fail2ban-telegram-bot/bot.py
chmod +x /opt/fail2ban-telegram-bot/bot.py
chown $SUDO_USER:$SUDO_USER /opt/fail2ban-telegram-bot/bot.py
