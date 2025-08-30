#!/bin/bash

source ./utils/logger.sh

log "[*] Setting up aliases for enhanced CLI experience..."

# Создаем файл алиасов для пользователя
ALIASES_FILE="/home/$SUDO_USER/.bash_aliases"

# Добавляем алиасы
cat << 'EOF' > "$ALIASES_FILE"
# Modern CLI tools aliases
alias cat='bat'
alias ls='eza --icons'
alias ll='eza -l --icons'
alias la='eza -la --icons'
alias l='eza -la --icons'
alias tree='eza --tree'
alias top='btop'

# Git aliases (if git is installed)
if command -v git &> /dev/null; then
    alias g='git'
    alias gs='git status'
    alias ga='git add'
    alias gc='git commit'
    alias gp='git push'
    alias gl='git log --oneline'
fi

# Kubernetes aliases (if kubectl is installed)
if command -v kubectl &> /dev/null; then
    alias k='kubectl'
    alias kga='kubectl get all'
    alias kgp='kubectl get pods'
    alias kgn='kubectl get nodes'
fi

# Docker aliases (if docker is installed)
if command -v docker &> /dev/null; then
    alias d='docker'
    alias dps='docker ps'
    alias di='docker images'
    alias drm='docker rm'
    alias drmi='docker rmi'
fi

# Common shortcuts
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias ~='cd ~'
alias -- -='cd -'

# Safety aliases
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# System information
alias df='df -h'
alias du='du -h'
alias free='free -h'

# Network
alias ping='ping -c 5'
alias ports='netstat -tulanp'

# Search
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'
EOF

# Устанавливаем права доступа
chown $SUDO_USER:$SUDO_USER "$ALIASES_FILE"

# Добавляем загрузку алиасов в .bashrc если её там нет
if ! grep -q ".bash_aliases" "/home/$SUDO_USER/.bashrc"; then
    echo "" >> "/home/$SUDO_USER/.bashrc"
    echo "# Load aliases" >> "/home/$SUDO_USER/.bashrc"
    echo 'if [ -f ~/.bash_aliases ]; then' >> "/home/$SUDO_USER/.bashrc"
    echo '    . ~/.bash_aliases' >> "/home/$SUDO_USER/.bashrc"
    echo 'fi' >> "/home/$SUDO_USER/.bashrc"
    chown $SUDO_USER:$SUDO_USER "/home/$SUDO_USER/.bashrc"
fi

# Также создаем системные алиасы для root
ROOT_ALIASES_FILE="/root/.bash_aliases"
cp "$ALIASES_FILE" "$ROOT_ALIASES_FILE"

log "[*] Aliases setup complete. Reload your shell or run 'source ~/.bashrc' to use them."
