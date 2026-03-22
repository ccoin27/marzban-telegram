import datetime as dt
from typing import Any


def fmt_bytes(n: int | float) -> str:
    x = float(n)
    for unit in ("Б", "КБ", "МБ", "ГБ", "ТБ", "ПБ"):
        if x < 1024.0 or unit == "ПБ":
            if unit == "Б":
                return f"{int(x)} {unit}"
            return f"{x:.2f} {unit}"
        x /= 1024.0
    return f"{int(n)} Б"


def subscription_full_url(sub: str, marzban_base_url: str) -> str:
    s = (sub or "").strip()
    if not s:
        return ""
    if s.startswith(("http://", "https://")):
        return s
    base = (marzban_base_url or "").strip().rstrip("/")
    if not base:
        return s
    if s.startswith("/"):
        return base + s
    return f"{base}/{s}"


def fmt_expire(ts: Any) -> str:
    if ts is None or ts == 0:
        return "без срока"
    try:
        t = int(ts)
    except (TypeError, ValueError):
        return str(ts)
    return dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M UTC")


def fmt_user_card(d: dict[str, Any], marzban_base_url: str) -> str:
    lines = [
        f"Пользователь: <code>{d.get('username','')}</code>",
        f"Статус: <b>{d.get('status','')}</b>",
        f"Истекает: {fmt_expire(d.get('expire'))}",
        f"Лимит: {fmt_bytes(d.get('data_limit') or 0) if d.get('data_limit') else 'безлимит'}",
        f"Использовано: {fmt_bytes(d.get('used_traffic') or 0)}",
    ]
    sub = d.get("subscription_url") or ""
    if sub:
        sub = subscription_full_url(sub, marzban_base_url)
        lines.append("")
        lines.append(f"Ссылка: <code>{sub}</code>")
    return "\n".join(lines)
