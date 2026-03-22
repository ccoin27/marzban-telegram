#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON:-python3}"
if ! command -v "$PYTHON_BIN" &>/dev/null; then
  echo "Не найден $PYTHON_BIN. Установите Python 3.10+."
  exit 1
fi

VENV_PATH="${VENV:-$ROOT/.venv}"
if [[ ! -d "$VENV_PATH" ]]; then
  echo "Создание venv: $VENV_PATH"
  "$PYTHON_BIN" -m venv "$VENV_PATH"
fi

PY="$VENV_PATH/bin/python"
PIP="$VENV_PATH/bin/pip"

"$PIP" install -U pip wheel setuptools
"$PIP" install -r "$ROOT/requirements.txt"

echo ""
echo "Запуск настройки (токен можно передать: $0 -t TOKEN -a ID1,ID2) ..."
exec "$PY" "$ROOT/scripts/setup.py" "$@"
