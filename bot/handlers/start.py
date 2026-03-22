from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards.inline import main_menu_kb
from services.marzban_client import MarzbanClient, MarzbanError

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, mb: MarzbanClient, state: FSMContext) -> None:
    await state.clear()
    try:
        adm = await mb.current_admin()
        sudo = bool(adm.get("is_sudo"))
    except MarzbanError:
        sudo = False
    await message.answer(
        "Marzban — панель управления.",
        reply_markup=main_menu_kb(sudo),
    )
