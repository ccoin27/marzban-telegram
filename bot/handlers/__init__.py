from aiogram import Dispatcher

from bot.handlers import create_user, menu, search, start


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(create_user.router)
    dp.include_router(search.router)
