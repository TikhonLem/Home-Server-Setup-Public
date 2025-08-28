#!/bin/bash

# === Fail2Ban Telegram Bot Auto Setup Script (Public Version) ===
# Main orchestrator script

# Source logger
source ./utils/logger.sh

# Проверка на root
if [ "$EUID" -ne 0 ]; then
    log "❌ Please run this script with sudo"
    exit 1
fi

log "🚀 Starting installation..."

# Run modules in order
./modules/01_install_packages.sh
./modules/02_setup_python.sh
./modules/03_setup_configs.sh
./modules/04_setup_services.sh
./modules/05_setup_firewall.sh

log "✅ Installation complete! Please reboot the server for full functionality."
log "⚠️  Remember to replace placeholders in config files with your personal data!"
