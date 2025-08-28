#!/bin/bash

source ./utils/logger.sh

# Создание systemd-сервиса для бота
log "[*] Creating systemd service for bot..."
# Заменяем placeholder в файле сервиса
sed "s/YOUR_USER_HERE/$SUDO_USER/g" ./configs/systemd/fail2ban-tgbot.service > /etc/systemd/system/fail2ban-tgbot.service

# Перезагрузка systemd и включение сервисов
log "[*] Reloading systemd and enabling services..."
systemctl daemon-reload >> "$LOG_FILE" 2>&1
systemctl enable fail2ban cockpit.socket ssh fail2ban-tgbot >> "$LOG_FILE" 2>&1
systemctl restart fail2ban cockpit.socket ssh >> "$LOG_FILE" 2>&1
