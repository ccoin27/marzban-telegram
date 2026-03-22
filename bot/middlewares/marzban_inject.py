from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from services.marzban_client import MarzbanClient


class MarzbanInjectMiddleware(BaseMiddleware):
    def __init__(self, client: MarzbanClient):
        self.client = client

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["mb"] = self.client
        return await handler(event, data)
