import asyncio
import logging
import warnings
from pathlib import Path

from colorama import Fore, Style, init as colorama_init

import urllib3
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import TelegramObject
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware

from bot.banner_cc import BANNER, CREDIT
from bot.config import Settings, load_settings
from bot.instance_lock import acquire as acquire_instance_lock
from bot.handlers import register_handlers
from bot.middlewares.admin import AdminMiddleware
from bot.middlewares.marzban_inject import MarzbanInjectMiddleware
from services.marzban_client import MarzbanClient

urllib3.disable_warnings()
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

colorama_init(autoreset=True)

logger = logging.getLogger(__name__)


class SettingsMiddleware(BaseMiddleware):
    def __init__(self, settings: Settings):
        self.settings = settings

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["settings"] = self.settings
        return await handler(event, data)


async def run_bot() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    print(Fore.CYAN + Style.BRIGHT + BANNER + Style.RESET_ALL)
    print(Fore.MAGENTA + Style.BRIGHT + CREDIT + Style.RESET_ALL)
    print()
    settings = load_settings()
    mb = MarzbanClient(settings.marzban_base_url, settings.marzban_username, settings.marzban_password)
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(SettingsMiddleware(settings))
    dp.update.middleware(AdminMiddleware(settings.telegram_admin_ids))
    dp.update.middleware(MarzbanInjectMiddleware(mb))
    register_handlers(dp)
    logger.info("polling started")
    await dp.start_polling(bot)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    acquire_instance_lock(project_root)
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
