#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if command -v systemctl &>/dev/null; then
  if systemctl is-active --quiet marzban-telegram.service 2>/dev/null; then
    echo "Уже работает systemd: marzban-telegram.service"
    echo "Не запускайте бота второй раз. Статус: sudo systemctl status marzban-telegram.service"
    echo "Чтобы запускать вручную: sudo systemctl stop marzban-telegram.service"
    exit 1
  fi
fi

VENV_PATH="${VENV:-$ROOT/.venv}"
PY="$VENV_PATH/bin/python"

if [[ ! -x "$PY" ]]; then
  echo "Виртуальное окружение не найдено: $VENV_PATH"
  echo "Сначала выполните: bash setup.sh"
  exit 1
fi

if [[ ! -f "$ROOT/.env" ]]; then
  echo "Нет файла .env в $ROOT"
  echo "Сначала выполните: bash setup.sh"
  exit 1
fi

exec "$PY" "$ROOT/main.py" "$@"
