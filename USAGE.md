# 📋 Как использовать публичную версию

## 1. Настройка Telegram-бота

1.  Создайте бота через [@BotFather](https://t.me/BotFather).
2.  Получите токен вида: `123456789:ABCdefGhIJKlmnOPQrstUVWxyz`.
3.  Узнайте свой Chat ID через [@userinfobot](https://t.me/userinfobot) или [@myidbot](https://t.me/myidbot).

## 2. Настройка конфигурационных файлов

Откройте и отредактируйте следующие файлы в папке `configs/`, заменив плейсхолдеры на ваши данные:

### `configs/bot.py`

- `YOUR_BOT_TOKEN_HERE` -> `123456789:ABCdefGhIJKlmnOPQrstUVWxyz`
- `YOUR_CHAT_ID_HERE` -> `123456789`

### `configs/ssh-notify.sh`

- `YOUR_BOT_TOKEN_HERE` -> `123456789:ABCdefGhIJKlmnOPQrstUVWxyz`
- `YOUR_CHAT_ID_HERE` -> `123456789`

### `configs/scripts/fail2ban-telegram-alert.sh`

- `YOUR_BOT_TOKEN_HERE` -> `123456789:ABCdefGhIJKlmnOPQrstUVWxyz`
- `YOUR_CHAT_ID_HERE` -> `123456789`

### `configs/fail2ban/jail.local`

- `YOUR_IP_HERE` -> `192.168.1.100` (ваш IP-адрес, который не должен блокироваться)

## 3. Запуск установки

Убедитесь, что вы находитесь в корневой директории проекта (`home-server-setup`).

```bash
chmod +x main.sh
sudo ./main.sh
