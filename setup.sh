#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON:-python3}"
if ! command -v "$PYTHON_BIN" &>/dev/null; then
  echo "Не найден $PYTHON_BIN. Установите Python 3.10+."
  exit 1
fi

is_linux() {
  [[ "$(uname -s 2>/dev/null)" == "Linux" ]]
}

has_apt() {
  command -v apt-get &>/dev/null || command -v apt &>/dev/null
}

apt_install_venv() {
  echo "Установка python3-venv и python3-pip (нужны права root)..."
  if command -v apt-get &>/dev/null; then
    if command -v sudo &>/dev/null; then
      sudo apt-get update -y
      sudo apt-get install -y python3-venv python3-pip
    else
      apt-get update -y
      apt-get install -y python3-venv python3-pip
    fi
  else
    if command -v sudo &>/dev/null; then
      sudo apt update -y
      sudo apt install -y python3-venv python3-pip
    else
      apt update -y
      apt install -y python3-venv python3-pip
    fi
  fi
}

venv_smoke_test() {
  local td="$1"
  if ! "$PYTHON_BIN" -m venv "$td/v" 2>/dev/null; then
    rm -rf "$td"
    return 1
  fi
  if [[ ! -x "$td/v/bin/python" ]]; then
    rm -rf "$td"
    return 1
  fi
  rm -rf "$td"
  return 0
}

ensure_venv_capability() {
  local tmp
  tmp="$(mktemp -d)"
  if venv_smoke_test "$tmp"; then
    return 0
  fi
  if is_linux && has_apt; then
    if apt_install_venv; then
      tmp="$(mktemp -d)"
      if venv_smoke_test "$tmp"; then
        return 0
      fi
    fi
  fi
  echo ""
  echo "Не удалось создать venv. На Debian/Ubuntu выполните от root:"
  echo "  apt update && apt install -y python3-venv python3-pip"
  echo "Затем: rm -rf $ROOT/.venv && bash $ROOT/setup.sh"
  exit 1
}

VENV_PATH="${VENV:-$ROOT/.venv}"

if [[ "${RECREATE_VENV:-0}" == "1" ]] || [[ "${FORCE_VENV:-0}" == "1" ]]; then
  echo "Пересоздание venv (RECREATE_VENV/FORCE_VENV)..."
  rm -rf "$VENV_PATH"
fi

if [[ -d "$VENV_PATH" ]]; then
  if [[ ! -x "$VENV_PATH/bin/python" ]]; then
    echo "Обнаружено повреждённое venv, удаление $VENV_PATH ..."
    rm -rf "$VENV_PATH"
  fi
fi

ensure_venv_capability

if [[ ! -d "$VENV_PATH" ]]; then
  echo "Создание виртуального окружения: $VENV_PATH"
  if ! "$PYTHON_BIN" -m venv "$VENV_PATH"; then
    echo "Ошибка: python -m venv не сработал. Попробуйте RECREATE_VENV=1 bash setup.sh"
    exit 1
  fi
fi

PY="$VENV_PATH/bin/python"

if [[ ! -x "$PY" ]]; then
  echo "Нет интерпретатора в venv, пересоздаю $VENV_PATH"
  rm -rf "$VENV_PATH"
  ensure_venv_capability
  "$PYTHON_BIN" -m venv "$VENV_PATH"
  PY="$VENV_PATH/bin/python"
fi

echo "Обновление pip и установка зависимостей из requirements.txt ..."
"$PY" -m pip install -U pip wheel setuptools
"$PY" -m pip install -r "$ROOT/requirements.txt"

echo ""
echo "Запуск настройки (пример: $0 -t TOKEN -a ID1,ID2) ..."
"$PY" "$ROOT/scripts/setup.py" "$@" || exit $?

DO_SYSTEMD="${INSTALL_SYSTEMD-}"
if [[ -z "$DO_SYSTEMD" ]]; then
  if [[ "$(uname -s 2>/dev/null)" == "Linux" ]] && command -v systemctl &>/dev/null; then
    DO_SYSTEMD=1
  else
    DO_SYSTEMD=0
  fi
fi

if [[ "$DO_SYSTEMD" == "1" ]]; then
  echo ""
  bash "$ROOT/scripts/install_service.sh" || {
    echo ""
    echo "Сервис systemd не установлен (нужен sudo). Позже: bash scripts/install_service.sh"
  }
elif [[ "$DO_SYSTEMD" != "0" ]]; then
  echo ""
  echo "INSTALL_SYSTEMD ожидает 0 или 1, сейчас: $DO_SYSTEMD — пропуск unit."
fi
