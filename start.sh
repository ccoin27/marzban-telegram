#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

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
