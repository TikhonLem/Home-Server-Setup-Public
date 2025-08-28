#!/bin/bash

USER=$(whoami)
IP=$(echo $SSH_CLIENT | awk '{print $1}')
HOST=$(hostname)

# Не для root и не при пустом IP
[ "$USER" = "root" ] && exit 0
[ -z "$IP" ] && exit 0

# !!! ВАЖНО: Замените плейсхолдеры на ваши личные данные !!!
TOKEN="YOUR_BOT_TOKEN_HERE"
CHAT_ID=YOUR_CHAT_ID_HERE

# При входе
if [ -z "$SSH_ORIGINAL_COMMAND" ]; then
    MESSAGE="🔐 *Вход по SSH*  
*Пользователь:* \`$USER\`  
*IP:* \`$IP\`  
*Сервер:* $HOST  
*Время:* $(date '+%d.%m.%Y %H:%M:%S')"
    
    /usr/bin/curl -s -X POST \
      -H 'Content-Type: application/json' \
      -d "{\"chat_id\": \"$CHAT_ID\", \"text\": \"$MESSAGE\", \"parse_mode\": \"Markdown\"}" \
      "https://api.telegram.org/bot$TOKEN/sendMessage" \
      > /dev/null 2>&1
fi

# При выходе
trap '
    MESSAGE="🚪 *Выход из SSH*  
*Пользователь:* \`$USER\`  
*IP:* \`$IP\`  
*Сервер:* $HOST  
*Время:* $(date '"'"'+%d.%m.%Y %H:%M:%S'"'"')"
    
    /usr/bin/curl -s -X POST \
      -H "Content-Type: application/json" \
      -d "{\"chat_id\": \"$CHAT_ID\", \"text\": \"$MESSAGE\", \"parse_mode\": \"Markdown\"}" \
      "https://api.telegram.org/bot$TOKEN/sendMessage" \
      > /dev/null 2>&1
' EXIT
