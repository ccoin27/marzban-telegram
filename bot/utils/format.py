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


def fmt_expire(ts: Any) -> str:
    if ts is None or ts == 0:
        return "без срока"
    try:
        t = int(ts)
    except (TypeError, ValueError):
        return str(ts)
    return dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M UTC")


def fmt_user_card(d: dict[str, Any]) -> str:
    lines = [
        f"Пользователь: <code>{d.get('username','')}</code>",
        f"Статус: <b>{d.get('status','')}</b>",
        f"Истекает: {fmt_expire(d.get('expire'))}",
        f"Лимит: {fmt_bytes(d.get('data_limit') or 0) if d.get('data_limit') else 'безлимит'}",
        f"Использовано: {fmt_bytes(d.get('used_traffic') or 0)}",
    ]
    sub = d.get("subscription_url") or ""
    if sub:
        lines.append("")
        lines.append(f"Ссылка: <code>{sub}</code>")
    return "\n".join(lines)
