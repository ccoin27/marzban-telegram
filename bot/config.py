import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env")


@dataclass
class Settings:
    bot_token: str
    telegram_admin_ids: set[int]
    marzban_base_url: str
    marzban_username: str
    marzban_password: str
    users_page_size: int = 8


def _parse_admin_ids(raw: str) -> set[int]:
    out: set[int] = set()
    for part in raw.replace(";", ",").replace(" ", ",").split(","):
        part = part.strip()
        if not part:
            continue
        out.add(int(part))
    return out


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    admins = os.getenv("TELEGRAM_ADMIN_IDS", "").strip()
    base = os.getenv("MARZBAN_BASE_URL", "http://127.0.0.1:8000").strip().rstrip("/")
    user = os.getenv("MARZBAN_USERNAME", "").strip()
    pwd = os.getenv("MARZBAN_PASSWORD", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is empty")
    if not admins:
        raise RuntimeError("TELEGRAM_ADMIN_IDS is empty")
    if not base:
        raise RuntimeError("MARZBAN_BASE_URL is empty")
    if not user or not pwd:
        raise RuntimeError("MARZBAN_USERNAME or MARZBAN_PASSWORD is empty")
    return Settings(
        bot_token=token,
        telegram_admin_ids=_parse_admin_ids(admins),
        marzban_base_url=base,
        marzban_username=user,
        marzban_password=pwd,
    )
