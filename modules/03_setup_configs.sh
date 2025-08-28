#!/bin/bash

source ./utils/logger.sh

# Создание SSH-notify скрипта
log "[*] Creating SSH notify script..."
cp ./configs/ssh-notify.sh /etc/profile.d/ssh-notify.sh
chmod +x /etc/profile.d/ssh-notify.sh

# Создание Fail2Ban action для Telegram
log "[*] Creating Fail2Ban Telegram action..."
mkdir -p /etc/fail2ban/action.d
cp ./configs/fail2ban/action.d/telegram.conf /etc/fail2ban/action.d/telegram.conf

# Создание скрипта уведомлений Fail2Ban
log "[*] Creating Fail2Ban Telegram alert script..."
cp ./configs/scripts/fail2ban-telegram-alert.sh /usr/local/bin/fail2ban-telegram-alert.sh
chmod +x /usr/local/bin/fail2ban-telegram-alert.sh

# Настройка Fail2Ban jail.local
log "[*] Configuring Fail2Ban jail.local..."
cp ./configs/fail2ban/jail.local /etc/fail2ban/jail.local
