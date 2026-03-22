#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="marzban-telegram.service"
UNIT_PATH="/etc/systemd/system/$SERVICE_NAME"

if [[ "$(uname -s 2>/dev/null)" != "Linux" ]] || ! command -v systemctl &>/dev/null; then
  exit 0
fi

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
  SUDO=""
else
  SUDO="sudo"
fi

if [[ ! -f "$UNIT_PATH" ]]; then
  echo "Unit не найден: $UNIT_PATH"
  exit 0
fi

$SUDO systemctl stop "$SERVICE_NAME" 2>/dev/null || true
$SUDO systemctl disable "$SERVICE_NAME" 2>/dev/null || true
$SUDO rm -f "$UNIT_PATH"
$SUDO systemctl daemon-reload
echo "Сервис $SERVICE_NAME удалён."
