
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
```

Скрипт выполнит все шаги по установке и настройке.

## 4. Проверка работы

После завершения установки:

1.  Перезагрузите сервер (опционально, но рекомендуется).
2.  Проверьте статус сервиса бота:
    ```bash
    sudo systemctl status fail2ban-tgbot
    ```
3.  Откройте Telegram и отправьте боту команду `/start`.
4.  Проверьте работу Cockpit по адресу `https://<ip-вашего-сервера>:9090`.
5.  Попробуйте выполнить SSH-вход/выход с другого терминала и проверьте уведомления в Telegram.


---

### 5. **`configs/sshd_config`** (новый шаблон)

Создай файл `configs/sshd_config`:

```bash
# Это шаблон конфигурации SSH для установки
# Все параметры должны быть заменены на реальные значения

Port 2222
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
AuthorizedKeysFile .ssh/authorized_keys
MaxAuthTries 3
MaxSessions 2
ClientAliveInterval 300
ClientAliveCountMax 2
X11Forwarding no
UsePAM yes
PrintMotd no
AcceptEnv LANG LC_*
Subsystem sftp /usr/lib/openssh/sftp-server
AllowUsers YOUR_USER_HERE
```
