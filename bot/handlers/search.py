import html

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import Settings
from bot.keyboards.inline import back_menu_kb, users_list_kb
from bot.state_store import user_search
from bot.states import SearchState
from bot.user_cache import clear as clear_user_cache, get_all_users
from bot.utils.format import fmt_bytes
from services.marzban_client import MarzbanClient, MarzbanError

router = Router()


@router.callback_query(F.data == "m:find")
async def cb_find(cq: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SearchState.query)
    await cq.message.edit_text(
        "Введите строку поиска (username или заметка):",
        reply_markup=back_menu_kb(),
    )
    await cq.answer()


@router.message(SearchState.query, F.text)
async def msg_search(message: Message, state: FSMContext, mb: MarzbanClient, settings: Settings) -> None:
    q = (message.text or "").strip()
    await state.clear()
    uid = message.from_user.id
    clear_user_cache(uid)
    user_search[uid] = q
    wait = await message.answer("Загрузка по поиску…")
    try:
        all_items = await get_all_users(mb, uid, q)
    except MarzbanError as e:
        await wait.edit_text(f"Ошибка: {e}")
        return
    total = len(all_items)
    used_sum = sum(int(u.get("used_traffic") or 0) for u in all_items)
    ps = settings.users_page_size
    slice_items = all_items[0:ps]
    names = [u.get("username", "?") for u in slice_items]
    text = (
        f"Поиск «{html.escape(q)}»: <b>{total}</b>, трафик: <b>{fmt_bytes(used_sum)}</b>\n"
        f"Страница 1 из {max(1, (total + ps - 1) // ps)}:"
    )
    await wait.edit_text(text, reply_markup=users_list_kb(names, 0, total, ps, "q"))
