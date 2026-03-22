#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SERVICE_NAME="marzban-telegram.service"
UNIT_PATH="/etc/systemd/system/$SERVICE_NAME"

if [[ "$(uname -s 2>/dev/null)" != "Linux" ]]; then
  echo "systemd доступен только на Linux, пропуск."
  exit 0
fi

if ! command -v systemctl &>/dev/null; then
  echo "Команда systemctl не найдена, пропуск установки сервиса."
  exit 0
fi

VENV_PATH="${VENV:-$ROOT/.venv}"
PY="$VENV_PATH/bin/python"

if [[ ! -x "$PY" ]]; then
  echo "Нет интерпретатора venv: $PY"
  echo "Сначала: bash setup.sh"
  exit 1
fi

if [[ ! -f "$ROOT/.env" ]]; then
  echo "Нет $ROOT/.env"
  echo "Сначала: bash setup.sh"
  exit 1
fi

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
  SUDO=""
else
  if ! command -v sudo &>/dev/null; then
    echo "Нужны права root (sudo) для записи в /etc/systemd/system/"
    exit 1
  fi
  SUDO="sudo"
fi

SERVICE_USER="${SERVICE_USER:-${SUDO_USER:-$(logname 2>/dev/null || whoami)}}"
if [[ -z "$SERVICE_USER" ]] || [[ "$SERVICE_USER" == "root" ]]; then
  SERVICE_USER="$(whoami)"
fi

cat <<UNIT | $SUDO tee "$UNIT_PATH" > /dev/null
[Unit]
Description=Marzban Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$ROOT
Environment=PYTHONUNBUFFERED=1
ExecStart=$PY $ROOT/main.py
Restart=always
RestartSec=5
TimeoutStopSec=30
Nice=5
PrivateTmp=yes
NoNewPrivileges=yes

[Install]
WantedBy=multi-user.target
UNIT

$SUDO systemctl daemon-reload
$SUDO systemctl enable "$SERVICE_NAME"
$SUDO systemctl restart "$SERVICE_NAME"

echo ""
echo "Сервис установлен и запущен: $SERVICE_NAME"
echo "Статус: sudo systemctl status $SERVICE_NAME"
echo "Логи:   sudo journalctl -u $SERVICE_NAME -f"
