import argparse
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path

import httpx

try:
    from colorama import Fore, Style, init as colorama_init

    colorama_init(autoreset=True)
except ImportError:
    class Fore:
        CYAN = MAGENTA = GREEN = YELLOW = RED = BLUE = ""

    class Style:
        BRIGHT = RESET_ALL = ""

    def colorama_init(*a, **k):
        pass


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
MARZBAN_ENV = Path("/opt/marzban/.env")

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bot.banner_cc import BANNER, CREDIT


def banner() -> None:
    print(Fore.CYAN + Style.BRIGHT + BANNER + Style.RESET_ALL)
    print(Fore.MAGENTA + Style.BRIGHT + CREDIT + Style.RESET_ALL)
    print(Fore.YELLOW + "  Marzban Telegram Bot — setup" + Style.RESET_ALL)
    print()


def cprint(msg: str, color: str = Fore.GREEN) -> None:
    print(color + msg + Style.RESET_ALL)


def parse_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        out[k] = v
    return out


def marzban_present() -> bool:
    if shutil.which("marzban"):
        return True
    if sys.platform != "win32" and Path("/opt/marzban").is_dir():
        return True
    return False


def install_marzban_linux() -> bool:
    cprint("Marzban не найден. Запуск установки (нужны права root)...", Fore.YELLOW)
    cmd = 'bash -c "$(curl -sL https://github.com/Gozargah/Marzban-scripts/raw/master/marzban.sh)" @ install'
    try:
        if hasattr(os, "geteuid") and os.geteuid() != 0:
            subprocess.run(["sudo", "bash", "-c", cmd], check=True)
        else:
            subprocess.run(["bash", "-c", cmd], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        cprint(f"Ошибка установки: {e}", Fore.RED)
        cprint("Установите вручную: https://github.com/Gozargah/Marzban", Fore.YELLOW)
        return False
    cprint("Ожидание запуска панели...", Fore.CYAN)
    for _ in range(90):
        try:
            r = httpx.get("http://127.0.0.1:8000/", timeout=2.0, verify=False)
            if r.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(2)
    cprint("Панель не ответила на 127.0.0.1:8000 — проверьте сервис вручную.", Fore.YELLOW)
    return True


def create_sudo_admin_linux(username: str, password: str) -> bool:
    env = os.environ.copy()
    env["MARZBAN_ADMIN_PASSWORD"] = password
    try:
        subprocess.run(
            ["marzban", "cli", "admin", "create", "-u", username, "--sudo"],
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        cprint(f"Не удалось создать админа CLI: {e}", Fore.RED)
        return False


def probe_api(base: str, user: str, pwd: str) -> bool:
    base = base.rstrip("/")
    try:
        r = httpx.post(
            f"{base}/api/admin/token",
            data={"username": user, "password": pwd},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30.0,
            verify=False,
        )
        if r.status_code != 200:
            return False
        tok = r.json().get("access_token")
        if not tok:
            return False
        h = httpx.Headers({"Authorization": f"Bearer {tok}"})
        s = httpx.get(f"{base}/api/system", headers=h, timeout=30.0, verify=False)
        return s.status_code == 200
    except Exception:
        return False


def read_input(prompt: str, default: str = "") -> str:
    d = f" [{default}]" if default else ""
    raw = input(Fore.GREEN + prompt + d + ": " + Style.RESET_ALL).strip()
    return raw or default


def read_secret(prompt: str, default: str = "") -> str:
    if default:
        r = read_input(prompt, default)
        return r
    try:
        import getpass

        v = getpass.getpass(Fore.GREEN + prompt + ": " + Style.RESET_ALL)
    except Exception:
        v = input(Fore.GREEN + prompt + ": " + Style.RESET_ALL)
    return v.strip()


def normalize_admin_ids(raw: str) -> str:
    parts = re.split(r"[,;\s]+", raw.strip())
    ids = [p.strip() for p in parts if p.strip().isdigit()]
    return ",".join(ids)


def write_env(data: dict[str, str]) -> None:
    lines = [f"{k}={v}" for k, v in data.items()]
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cprint(f"Сохранено: {ENV_PATH}", Fore.GREEN)


def url_from_marzban_env(d: dict[str, str]) -> str:
    port = d.get("UVICORN_PORT", "8000")
    host = d.get("UVICORN_HOST", "127.0.0.1")
    if host in ("0.0.0.0", "::"):
        host = "127.0.0.1"
    return f"http://{host}:{port}".rstrip("/")


def parse_cli() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Marzban Telegram bot — настройка .env")
    p.add_argument(
        "-t",
        "--bot-token",
        default=os.getenv("BOT_TOKEN", ""),
        help="Токен бота от @BotFather (можно также через переменную BOT_TOKEN)",
    )
    p.add_argument(
        "-a",
        "--admin-ids",
        default=os.getenv("TELEGRAM_ADMIN_IDS", ""),
        help="Telegram user id админов через запятую",
    )
    return p.parse_args()


def main() -> None:
    args = parse_cli()
    banner()
    bot_token = (args.bot_token or "").strip()
    if not bot_token:
        bot_token = read_input("Telegram BOT_TOKEN", os.getenv("BOT_TOKEN", ""))
    if not bot_token:
        cprint("BOT_TOKEN обязателен (укажите -t или переменную BOT_TOKEN)", Fore.RED)
        sys.exit(1)
    admin_ids = (args.admin_ids or "").strip()
    if not admin_ids:
        admin_ids = read_input(
            "TELEGRAM_ADMIN_IDS (через запятую, например: 123456789, 987654321)",
            os.getenv("TELEGRAM_ADMIN_IDS", ""),
        )
    admin_ids_norm = normalize_admin_ids(admin_ids)
    if not admin_ids_norm:
        cprint("Нужен хотя бы один числовой Telegram user id", Fore.RED)
        sys.exit(1)

    base_url = (os.getenv("MARZBAN_BASE_URL") or "").strip() or "http://127.0.0.1:8000"
    mb_user = (os.getenv("MARZBAN_USERNAME") or "").strip()
    mb_pass = (os.getenv("MARZBAN_PASSWORD") or "").strip()

    fresh_linux_install = False
    if sys.platform != "win32" and not marzban_present():
        if not install_marzban_linux():
            sys.exit(1)
        fresh_linux_install = True
        d = parse_env_file(MARZBAN_ENV)
        base_url = url_from_marzban_env(d)
        if d.get("SUDO_USERNAME") and d.get("SUDO_PASSWORD"):
            mb_user = d["SUDO_USERNAME"]
            mb_pass = d["SUDO_PASSWORD"]
            cprint("Найдены SUDO_USERNAME / SUDO_PASSWORD в /opt/marzban/.env", Fore.CYAN)
        else:
            mb_user = f"tg_{secrets.token_hex(3)}"
            mb_pass = secrets.token_urlsafe(16)
            cprint(f"Создаётся sudo-админ CLI: {mb_user}", Fore.CYAN)
            if not create_sudo_admin_linux(mb_user, mb_pass):
                mb_user = read_input("MARZBAN_USERNAME", "")
                mb_pass = read_secret("MARZBAN_PASSWORD")

    if not fresh_linux_install:
        ok = False
        if mb_user and mb_pass and probe_api(base_url, mb_user, mb_pass):
            cprint("API: успешная авторизация по переменным окружения.", Fore.GREEN)
            ok = True
        if not ok and MARZBAN_ENV.is_file():
            d = parse_env_file(MARZBAN_ENV)
            u = d.get("SUDO_USERNAME", "")
            p = d.get("SUDO_PASSWORD", "")
            try_url = url_from_marzban_env(d)
            if u and p and probe_api(try_url, u, p):
                base_url, mb_user, mb_pass = try_url, u, p
                cprint(f"API: данные из {MARZBAN_ENV}", Fore.CYAN)
                ok = True
        if not ok and (not mb_user or not mb_pass or not probe_api(base_url, mb_user, mb_pass)):
            cprint("Введите параметры панели Marzban (или проверьте, что она запущена).", Fore.YELLOW)
            base_url = read_input("MARZBAN_BASE_URL", base_url)
            mb_user = read_input("MARZBAN_USERNAME", mb_user)
            mb_pass = read_secret("MARZBAN_PASSWORD", mb_pass)

    attempts = 0
    while not probe_api(base_url, mb_user, mb_pass):
        attempts += 1
        cprint(f"Проверка API не прошла (попытка {attempts}).", Fore.RED)
        base_url = read_input("MARZBAN_BASE_URL", base_url)
        mb_user = read_input("MARZBAN_USERNAME", mb_user)
        mb_pass = read_secret("MARZBAN_PASSWORD")
        if attempts > 8:
            cprint("Слишком много ошибок.", Fore.RED)
            sys.exit(1)

    write_env(
        {
            "BOT_TOKEN": bot_token,
            "TELEGRAM_ADMIN_IDS": admin_ids_norm,
            "MARZBAN_BASE_URL": base_url.rstrip("/"),
            "MARZBAN_USERNAME": mb_user,
            "MARZBAN_PASSWORD": mb_pass,
        }
    )
    cprint("", Fore.RESET)
    cprint("Готово. Запуск: python main.py", Fore.CYAN + Style.BRIGHT)


if __name__ == "__main__":
    main()
