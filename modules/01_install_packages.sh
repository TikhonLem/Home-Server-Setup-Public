#!/bin/bash

source ./utils/logger.sh

log "[*] Updating system..."
apt update >> "$LOG_FILE" 2>&1 && apt upgrade -y >> "$LOG_FILE" 2>&1

log "[*] Installing required packages..."
apt install -y \
  fail2ban cockpit cockpit-machines \
  python3 python3-pip python3-venv \
  libvirt-daemon-system libvirt-clients virtinst \
  ufw net-tools curl \
  btop bat atuin eza >> "$LOG_FILE" 2>&1
