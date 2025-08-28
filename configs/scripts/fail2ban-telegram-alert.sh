#!/bin/bash

ACTION=$1
IP=$2
NAME=$3
FAILURES=$4

# !!! ВАЖНО: Замените плейсхолдеры на ваши личные данные !!!
TOKEN="YOUR_BOT_TOKEN_HERE"
CHAT_ID=YOUR_CHAT_ID_HERE

if [ "$ACTION" = "ban" ]; then
    MESSAGE="🚫 *Fail2Ban заблокировал IP*  
*IP:* \`$IP\`  
*Jail:* $NAME  
*Попытки:* $FAILURES  
*Время:* $(date '+%d.%m.%Y %H:%M:%S')"
elif [ "$ACTION" = "unban" ]; then
    MESSAGE="✅ *Fail2Ban разблокировал IP*  
*IP:* \`$IP\`  
*Jail:* $NAME  
*Время:* $(date '+%d.%m.%Y %H:%M:%S')"
else
    exit 0
fi

/usr/bin/curl -s -X POST \
  -H 'Content-Type: application/json' \
  -d "{\"chat_id\": \"$CHAT_ID\", \"text\": \"$MESSAGE\", \"parse_mode\": \"Markdown\"}" \
  "https://api.telegram.org/bot$TOKEN/sendMessage" \
  > /dev/null 2>&1
