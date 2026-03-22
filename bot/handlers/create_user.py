import re
import time

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import Settings
from bot.keyboards.inline import back_menu_kb, create_expire_kb, create_traffic_kb, user_actions_kb
from bot.states import CreateUserState
from bot.utils.format import fmt_user_card
from services.marzban_client import MarzbanClient, MarzbanError

router = Router()

_UNAME = re.compile(r"^(?=\w{3,32}\b)[a-zA-Z0-9-_@.]+(?:_[a-zA-Z0-9-_@.]+)*$")


def _parse_nt(data: str) -> tuple[str, int, int]:
    if not data.startswith("n:t:"):
        raise ValueError
    rest = data[4:]
    li = rest.rfind(":")
    if li <= 0:
        raise ValueError
    traffic = int(rest[li + 1 :])
    rest = rest[:li]
    li2 = rest.rfind(":")
    if li2 <= 0:
        raise ValueError
    days = int(rest[li2 + 1 :])
    username = rest[:li2]
    return username, days, traffic


@router.callback_query(F.data == "m:new")
async def cb_new_start(cq: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CreateUserState.name)
    await cq.message.edit_text(
        "Введите username нового пользователя (3–32 символа, латиница, цифры, _ - @ .):",
        reply_markup=back_menu_kb(),
    )
    await cq.answer()


@router.message(CreateUserState.name, F.text)
async def msg_new_name(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not _UNAME.match(raw):
        await message.answer("Некорректный username. Повторите.")
        return
    await state.clear()
    await message.answer(
        f"Срок для <code>{raw}</code>:",
        reply_markup=create_expire_kb(raw),
    )


@router.callback_query(F.data.startswith("n:e:"))
async def cb_new_expire(cq: CallbackQuery, mb: MarzbanClient) -> None:
    p = cq.data.split(":")
    if len(p) < 4:
        await cq.answer("Ошибка данных", show_alert=True)
        return
    days = int(p[-1])
    username = ":".join(p[2:-1])
    await cq.message.edit_text(
        f"Трафик для <code>{username}</code> (срок {days} дн.):",
        reply_markup=create_traffic_kb(username, days),
    )
    await cq.answer()


@router.callback_query(F.data.startswith("n:t:"))
async def cb_new_traffic(cq: CallbackQuery, mb: MarzbanClient, settings: Settings) -> None:
    try:
        username, days, traffic = _parse_nt(cq.data)
    except (ValueError, IndexError):
        await cq.answer("Ошибка данных", show_alert=True)
        return
    try:
        inv = await mb.inbounds()
        proto = next(iter(inv.keys()))
    except (StopIteration, MarzbanError) as e:
        await cq.answer(f"Нет инбаундов или ошибка API: {e}", show_alert=True)
        return
    exp = 0
    if days > 0:
        exp = int(time.time()) + days * 86400
    payload: dict = {
        "username": username,
        "proxies": {str(proto): {}},
        "expire": exp,
        "data_limit": traffic,
        "status": "active",
    }
    try:
        u = await mb.create_user(payload)
    except MarzbanError as e:
        await cq.answer(f"Ошибка: {e}", show_alert=True)
        return
    await cq.message.edit_text(
        fmt_user_card(u, settings.marzban_base_url),
        reply_markup=user_actions_kb(username),
    )
    await cq.answer("Создано")
