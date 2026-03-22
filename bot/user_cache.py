from __future__ import annotations

from typing import Optional

from services.marzban_client import MarzbanClient

_cache: dict[int, tuple[list[dict], Optional[str]]] = {}


def clear(uid: int) -> None:
    _cache.pop(uid, None)


async def get_all_users(mb: MarzbanClient, uid: int, search: Optional[str]) -> list[dict]:
    entry = _cache.get(uid)
    if entry is not None:
        items, q = entry
        if q == search:
            return items
    items = await mb.fetch_all_users(search=search)
    _cache[uid] = (items, search)
    return items
