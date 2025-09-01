#!/bin/bash

# Установка Jitsi Meet через Docker Compose

echo "🔧 Установка Jitsi Meet..."

# Создание директории
mkdir -p ~/docker-compose/jitsi
cd ~/docker-compose/jitsi

# Клонирование репозитория
if [ ! -d "docker-jitsi-meet" ]; then
  git clone https://github.com/jitsi/docker-jitsi-meet.git
fi

cd docker-jitsi-meet

# Копирование конфига
cp env.example .env

# Создание директорий конфигов
mkdir -p ~/.jitsi-meet-cfg/{web,prosody,jicofo,jvb}

# Генерация паролей
./gen-passwords.sh

# Настройка systemd-сервиса
sudo tee /etc/systemd/system/jitsi.service > /dev/null <<EOF
[Unit]
Description=Jitsi Meet Docker Compose
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/tikhon/docker-compose/jitsi/docker-jitsi-meet
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
EOF

# Включение сервиса
sudo systemctl daemon-reload
sudo systemctl enable jitsi.service

# Открытие портов
sudo ufw allow 8443/tcp
sudo ufw allow 10000/udp

echo "✅ Jitsi Meet установлен!"
echo "🔧 Настрой .env и запусти: sudo systemctl start jitsi.service"
