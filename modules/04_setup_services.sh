#!/bin/bash

source ./utils/logger.sh

# Создание systemd-сервиса для бота
log "[*] Creating systemd service for bot..."
sed "s/YOUR_USER_HERE/$SUDO_USER/g" ./configs/systemd/fail2ban-tgbot.service > /etc/systemd/system/fail2ban-tgbot.service

# Настройка SSH порта 2222
log "[*] Configuring SSH to use port 2222..."
sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config
sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Перезапуск SSH
log "[*] Restarting SSH service..."
systemctl restart ssh

# Настройка UFW
log "[*] Configuring UFW firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 2222/tcp
ufw allow from 192.168.1.0/24 to any port 9090
ufw allow from 192.168.1.0/24 to any port 9000
ufw --force enable

# Перезагрузка systemd и включение сервисов
log "[*] Reloading systemd and enabling services..."
systemctl daemon-reload >> "$LOG_FILE" 2>&1
systemctl enable fail2ban cockpit.socket ssh fail2ban-tgbot >> "$LOG_FILE" 2>&1
systemctl restart fail2ban cockpit.socket ssh >> "$LOG_FILE" 2>&1
