from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update


class AdminMiddleware(BaseMiddleware):
    def __init__(self, admin_ids: set[int]):
        self.admin_ids = admin_ids

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        uid: int | None = None
        if isinstance(event, Update):
            if event.message and event.message.from_user:
                uid = event.message.from_user.id
            elif event.callback_query and event.callback_query.from_user:
                uid = event.callback_query.from_user.id
            elif event.inline_query and event.inline_query.from_user:
                uid = event.inline_query.from_user.id
        if uid is None:
            return await handler(event, data)
        if uid not in self.admin_ids:
            if isinstance(event, Update) and event.callback_query:
                await event.callback_query.answer("Нет доступа", show_alert=True)
            elif isinstance(event, Update) and event.message:
                await event.message.answer("Нет доступа.")
            return None
        return await handler(event, data)
