
# Jitsi Meet

Видео-конференции на домашнем сервере.

## Доступ

- Внутри сети: `https://192.168.1.26:8443`
- Снаружи: `https://YOUR_EXTERNAL_IP:8443`

## Установка

```bash
./modules/jitsi/install.sh
```

## Настройка

1. Отредактируй `.env`:
   ```bash
   nano ~/docker-compose/jitsi/docker-jitsi-meet/.env
   ```

2. Запусти:
   ```bash
   sudo systemctl start jitsi.service
   ```

## Команды

```bash
# Статус
sudo systemctl status jitsi.service

# Логи
docker compose logs -f

# Обновление
cd ~/docker-compose/jitsi/docker-jitsi-meet
git pull
docker compose down
docker compose up -d
```

## Примечания

- Используется самоподписанный SSL.
- Для HTTPS требуется принять сертификат в браузере.
```

---

### **5. Обнови `main.sh`**

Добавь в `main.sh`:

```bash
# Установка Jitsi Meet
if [ "$INSTALL_JITSI" = true ]; then
  source ./modules/jitsi/install.sh
fi
```

И в `.env`:

```env
INSTALL_JITSI=true
```
