#!/bin/bash

source ./utils/logger.sh

# Настройка UFW
log "[*] Configuring UFW (if needed)..."
ufw --force enable >> "$LOG_FILE" 2>&1
ufw allow ssh >> "$LOG_FILE" 2>&1
ufw allow 9090  # Cockpit >> "$LOG_FILE" 2>&1
