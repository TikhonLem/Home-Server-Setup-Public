

```markdown
# 🏠 Home Server Setup (Публичная версия)

Автоматизированная настройка домашнего сервера на базе Ubuntu Server с полным стеком:
- Fail2Ban с уведомлениями в Telegram
- Telegram-бот для управления и мониторинга
- SSH-уведомления о входе/выходе
- Cockpit для веб-управления
- Поддержка виртуализации (KVM/Libvirt)

Этот репозиторий содержит **публичную версию** скрипта установки. Все личные данные (токены, ID, IP) заменены плейсхолдерами и должны быть настроены пользователем перед запуском.

## 📦 Что делает скрипт `setup-server.sh`

### Установка пакетов:
- `fail2ban` — защита от брутфорса
- `cockpit` — веб-интерфейс управления
- `cockpit-machines` — управление виртуальными машинами
- `python3`, `pip`, `venv` — для бота
- `libvirt` — библиотеки для виртуализации
- `ufw` — фаервол
- `curl`, `net-tools` — сетевые утилиты

### Настройка безопасности:
- SSH-уведомления в Telegram при входе/выходе
- Fail2Ban с кастомными правилами и уведомлениями в Telegram
- Автоматические уведомления о блокировках IP
- Защита от подбора паролей

### Telegram-бот:
- Команды для управления сервером
- Мониторинг ресурсов (CPU, RAM, диск, температура)
- Управление Fail2Ban через Telegram (ban/unban/check)
- Автоматические уведомления о состоянии сервера

### Сервисы:
- Systemd-сервис для бота
- Автозапуск всех компонентов
- Логирование установки
```
## 🚀 Установка

### 1. Клонирование репозитория

```bash
# Установите git, если его нет
sudo apt update && sudo apt install -y git

# Склонируйте репозиторий
git clone https://github.com/<ваш_логин>/home-server-setup.git
cd home-server-setup
```

### 2. Настройка личных данных

Перед запуском **обязательно** отредактируйте скрипт `setup-server.sh` и замените все плейсхолдеры на свои данные:

- `YOUR_BOT_TOKEN_HERE` — Токен вашего Telegram-бота (получить у [@BotFather](https://t.me/BotFather))
- `YOUR_CHAT_ID_HERE` — Ваш Telegram Chat ID (узнать можно через [@userinfobot](https://t.me/userinfobot) или [@myidbot](https://t.me/myidbot))
- `YOUR_IP_HERE` — Ваш IP-адрес, который нужно исключить из блокировок Fail2Ban

Также замените плейсхолдеры в создаваемых скриптах:
- `/etc/profile.d/ssh-notify.sh`
- `/usr/local/bin/fail2ban-telegram-alert.sh`
- `/etc/fail2ban/jail.local`

### 3. Запуск установки

```bash
chmod +x setup-server.sh
sudo ./setup-server.sh
```

### 4. Что происходит при установке:
- Установка всех необходимых пакетов
- Создание директории и виртуального окружения Python для бота
- Создание всех конфигурационных файлов
- Настройка и включение автозапуска systemd-сервисов
- Настройка UFW (открываются порты SSH и 9090 для Cockpit)

Лог установки сохраняется в `/var/log/setup-server.log`.

## 📋 Ручная настройка (альтернатива скрипту)

Если вы хотите повторить всё вручную или понять, что делает скрипт:

### 1. Установка пакетов

```bash
sudo apt update
sudo apt install fail2ban cockpit cockpit-machines python3 python3-pip python3-venv libvirt-daemon-system libvirt-clients virtinst ufw net-tools curl
```

### 2. Подготовка окружения для бота

```bash
# Создайте директорию (вместо $USER можно указать другого пользователя)
mkdir -p /opt/fail2ban-telegram-bot
sudo chown $USER:$USER /opt/fail2ban-telegram-bot

# Создайте виртуальное окружение и установите зависимости
cd /opt/fail2ban-telegram-bot
python3 -m venv venv
source venv/bin/activate
pip install "python-telegram-bot[job-queue]" httpx
```

### 3. Создание бота

Создайте файл `/opt/fail2ban-telegram-bot/bot.py` и добавьте в него код бота (см. `setup-server.sh`).

### 4. Настройка SSH-уведомлений

Создайте `/etc/profile.d/ssh-notify.sh` с соответствующим скриптом.

### 5. Настройка Fail2Ban

- Создайте `/etc/fail2ban/action.d/telegram.conf`
- Создайте `/usr/local/bin/fail2ban-telegram-alert.sh`
- Настройте `/etc/fail2ban/jail.local`

### 6. Systemd-сервис

Создайте `/etc/systemd/system/fail2ban-tgbot.service`.

### 7. Включение сервисов

```bash
sudo systemctl daemon-reload
sudo systemctl enable fail2ban cockpit.socket ssh fail2ban-tgbot
sudo systemctl restart fail2ban cockpit.socket ssh
```

## 🤖 Команды Telegram-бота

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие и список команд |
| `/help` | Полная справка |
| `/check` | Статус защиты SSH (Fail2Ban) |
| `/who` | Активные SSH-сессии |
| `/ban <ip>` | Вручную заблокировать IP через Fail2Ban |
| `/unban <ip>` | Вручную разблокировать IP через Fail2Ban |
| `/banned` | Список заблокированных IP |
| `/jailstatus` | Статус всех "тюрем" Fail2Ban |
| `/status` | Общее состояние сервера (аптайм, CPU, память, диск, температура) |
| `/cpu` | Загрузка CPU |
| `/temp` | Температура системы |
| `/disk` | Использование диска |
| `/mem` | Использование памяти |
| `/top` | Топ 20 процессов |
| `/monitor` | Вкл/выкл автоматический мониторинг ресурсов |

## 🔧 Управление через терминал

### Fail2Ban:

```bash
# Статус SSH
sudo fail2ban-client status sshd

# Заблокировать IP вручную
sudo fail2ban-client set sshd banip 1.2.3.4

# Разблокировать IP вручную
sudo fail2ban-client set sshd unbanip 1.2.3.4

# Перезапустить службу Fail2Ban
sudo systemctl restart fail2ban
```

### Cockpit:

Доступен по адресу: `https://<ip-адрес-сервера>:9090`

### SSH-уведомления:

Работают автоматически при входе/выходе через SSH, если настроен скрипт `/etc/profile.d/ssh-notify.sh`.

## 📁 Структура файлов (после установки)

```
/opt/fail2ban-telegram-bot/
├── bot.py              # Основной скрипт бота
├── venv/               # Python виртуальное окружение
/etc/profile.d/
├── ssh-notify.sh       # Уведомления SSH
/etc/fail2ban/
├── jail.local          # Конфигурация Fail2Ban
├── action.d/
│   └── telegram.conf   # Действие для Telegram
/usr/local/bin/
├── fail2ban-telegram-alert.sh  # Скрипт уведомлений Fail2Ban
/etc/systemd/system/
├── fail2ban-tgbot.service      # Systemd-сервис бота
```

## 🛡️ Безопасность

- Бот работает от имени пользователя, запустившего скрипт (`$SUDO_USER`).
- SSH-уведомления не передают пароли.
- Fail2Ban защищает от брутфорса.
- UFW включается по умолчанию.
- **Важно**: Не забудьте заменить все плейсхолдеры на свои данные перед запуском!

## 📊 Мониторинг

Бот автоматически отслеживает:
- Загрузку CPU (>70% — предупреждение)
- Использование памяти (>70% — предупреждение)
- Заполнение диска (>80% — предупреждение)
- Температуру (>60°C — предупреждение)

Уведомления отправляются с интервалом 30 минут для каждого типа события, чтобы избежать спама.

## 🆘 Решение проблем

### Бот не запускается:

```bash
# Проверить статус сервиса
sudo systemctl status fail2ban-tgbot

# Просмотреть логи сервиса
sudo journalctl -u fail2ban-tgbot -f

# Проверить лог установки
tail -f /var/log/setup-server.log
```

### SSH-уведомления не приходят:

Проверьте файл `/etc/profile.d/ssh-notify.sh` и права доступа:
```bash
ls -l /etc/profile.d/ssh-notify.sh
```

### Fail2Ban не блокирует:

```bash
# Проверить статус
sudo fail2ban-client status sshd

# Просмотреть логи Fail2Ban
tail -f /var/log/fail2ban.log
```

## 📝 Лицензия

MIT — используйте как хотите, но на свой страх и риск.

## 📞 Поддержка

Если что-то не работает — откройте Issue в репозитории.
```

Этот `README.md` предоставляет полное описание публичной версии проекта, включая установку, настройку и использование, без раскрытия ваших личных данных.
