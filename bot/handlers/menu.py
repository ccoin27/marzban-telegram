import html

from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery

from bot.config import Settings
from bot.keyboards.inline import (
    back_menu_kb,
    confirm_delete_kb,
    main_menu_kb,
    restart_confirm_kb,
    user_actions_kb,
    users_list_kb,
)
from bot.state_store import user_search
from bot.user_cache import clear as clear_user_cache, get_all_users
from bot.utils.format import fmt_bytes, fmt_user_card, subscription_full_url
from bot.utils.qr_png import subscription_qr_png
from services.marzban_client import MarzbanClient, MarzbanError

router = Router()


async def _sudo(mb: MarzbanClient) -> bool:
    try:
        adm = await mb.current_admin()
        return bool(adm.get("is_sudo"))
    except MarzbanError:
        return False


@router.callback_query(F.data == "m:noop")
async def cb_noop(cq: CallbackQuery) -> None:
    await cq.answer()


@router.callback_query(F.data == "m:me")
async def cb_menu(cq: CallbackQuery, mb: MarzbanClient) -> None:
    user_search.pop(cq.from_user.id, None)
    clear_user_cache(cq.from_user.id)
    sudo = await _sudo(mb)
    await cq.message.edit_text(
        "Marzban — главное меню.",
        reply_markup=main_menu_kb(sudo),
    )
    await cq.answer()


@router.callback_query(F.data == "m:sys")
async def cb_sys(cq: CallbackQuery, mb: MarzbanClient) -> None:
    try:
        s = await mb.system_stats()
    except MarzbanError as e:
        await cq.answer(f"Ошибка: {e}", show_alert=True)
        return
    text = (
        f"Версия: <b>{html.escape(str(s.get('version','?')))}</b>\n"
        f"CPU: {s.get('cpu_usage','?')}%  Ядер: {s.get('cpu_cores','?')}\n"
        f"RAM: {fmt_bytes(s.get('mem_used',0))} / {fmt_bytes(s.get('mem_total',0))}\n"
        f"Пользователей: {s.get('total_user','?')}  Онлайн: {s.get('online_users','?')}\n"
        f"Активных: {s.get('users_active','?')}  Отключённых: {s.get('users_disabled','?')}\n"
        f"Истекших: {s.get('users_expired','?')}  Лимит: {s.get('users_limited','?')}\n"
        f"На паузе: {s.get('users_on_hold','?')}\n"
        f"Входящий трафик: {fmt_bytes(s.get('incoming_bandwidth',0) or 0)}\n"
        f"Исходящий трафик: {fmt_bytes(s.get('outgoing_bandwidth',0) or 0)}"
    )
    await cq.message.edit_text(text, reply_markup=back_menu_kb())
    await cq.answer()


@router.callback_query(F.data == "m:inb")
async def cb_inb(cq: CallbackQuery, mb: MarzbanClient) -> None:
    try:
        inv = await mb.inbounds()
    except MarzbanError as e:
        await cq.answer(f"Ошибка: {e}", show_alert=True)
        return
    lines: list[str] = []
    for proto, items in inv.items():
        lines.append(f"<b>{html.escape(str(proto))}</b>")
        for it in items or []:
            tag = it.get("tag", "?") if isinstance(it, dict) else getattr(it, "tag", "?")
            lines.append(f"  • {html.escape(str(tag))}")
    text = "\n".join(lines) if lines else "Нет инбаундов."
    await cq.message.edit_text(text[:4000], reply_markup=back_menu_kb())
    await cq.answer()


@router.callback_query(F.data.startswith("m:us:"))
async def cb_users(cq: CallbackQuery, mb: MarzbanClient, settings: Settings) -> None:
    page = int(cq.data.split(":")[2])
    uid = cq.from_user.id
    if page == 0:
        user_search.pop(uid, None)
        clear_user_cache(uid)
    await cq.message.edit_text("Загрузка пользователей…")
    try:
        all_items = await get_all_users(mb, uid, None)
    except MarzbanError as e:
        await cq.answer(f"Ошибка: {e}", show_alert=True)
        return
    total = len(all_items)
    used_sum = sum(int(u.get("used_traffic") or 0) for u in all_items)
    ps = settings.users_page_size
    start = page * ps
    slice_items = all_items[start : start + ps]
    names = [u.get("username", "?") for u in slice_items]
    text = (
        f"Пользователи: загружено <b>{total}</b>, суммарно использовано: <b>{fmt_bytes(used_sum)}</b>\n"
        f"Страница {page + 1} из {max(1, (total + ps - 1) // ps)}:"
    )
    await cq.message.edit_text(
        text,
        reply_markup=users_list_kb(names, page, total, ps, "m"),
    )
    await cq.answer()


@router.callback_query(F.data.startswith("q:us:"))
async def cb_users_search(cq: CallbackQuery, mb: MarzbanClient, settings: Settings) -> None:
    page = int(cq.data.split(":")[2])
    uid = cq.from_user.id
    q = user_search.get(uid)
    if not q:
        await cq.answer("Поиск сброшен. Откройте список снова.", show_alert=True)
        return
    await cq.message.edit_text("Загрузка по поиску…")
    try:
        all_items = await get_all_users(mb, uid, q)
    except MarzbanError as e:
        await cq.answer(f"Ошибка: {e}", show_alert=True)
        return
    total = len(all_items)
    used_sum = sum(int(u.get("used_traffic") or 0) for u in all_items)
    ps = settings.users_page_size
    start = page * ps
    slice_items = all_items[start : start + ps]
    names = [u.get("username", "?") for u in slice_items]
    text = (
        f"Поиск «{html.escape(q)}»: <b>{total}</b>, трафик: <b>{fmt_bytes(used_sum)}</b>\n"
        f"Страница {page + 1} из {max(1, (total + ps - 1) // ps)}:"
    )
    await cq.message.edit_text(
        text,
        reply_markup=users_list_kb(names, page, total, ps, "q"),
    )
    await cq.answer()


@router.callback_query(F.data.startswith("u:o:"))
async def cb_user_open(cq: CallbackQuery, mb: MarzbanClient, settings: Settings) -> None:
    username = cq.data[4:]
    try:
        u = await mb.user(username)
    except MarzbanError as e:
        await cq.answer(f"Ошибка: {e}", show_alert=True)
        return
    await cq.message.edit_text(
        fmt_user_card(u, settings.marzban_base_url),
        reply_markup=user_actions_kb(username),
    )
    await cq.answer()


@router.callback_query(F.data.startswith("u:s:"))
async def cb_user_sub(cq: CallbackQuery, mb: MarzbanClient, settings: Settings) -> None:
    username = cq.data[4:]
    try:
        u = await mb.user(username)
    except MarzbanError as e:
        await cq.answer(f"Ошибка: {e}", show_alert=True)
        return
    sub = u.get("subscription_url") or ""
    if not sub:
        await cq.answer("Нет ссылки", show_alert=True)
        return
    sub = subscription_full_url(sub, settings.marzban_base_url)
    await cq.message.answer(
        f"Подписка <code>{html.escape(username)}</code>:\n<code>{html.escape(sub)}</code>"
    )
    await cq.message.answer_photo(
        BufferedInputFile(subscription_qr_png(sub), filename="subscription.png"),
        caption=f"QR подписки <code>{html.escape(username)}</code>",
    )
    await cq.answer()


@router.callback_query(F.data.startswith("u:l:"))
async def cb_user_links(cq: CallbackQuery, mb: MarzbanClient) -> None:
    username = cq.data[4:]
    try:
        u = await mb.user(username)
    except MarzbanError as e:
        await cq.answer(f"Ошибка: {e}", show_alert=True)
        return
    links = u.get("links") or []
    if not links:
        await cq.answer("Нет конфиг-ссылок", show_alert=True)
        return
    raw = "\n\n".join(str(x) for x in links)
    esc = html.escape(raw)
    chunk = 3500
    parts = [esc[i : i + chunk] for i in range(0, len(esc), chunk)]
    for i, p in enumerate(parts):
        prefix = (
            f"{html.escape(username)} — конфиг-ссылки"
            + (f" ({i + 1}/{len(parts)})" if len(parts) > 1 else "")
        )
        await cq.message.answer(f"{prefix}\n<pre>{p}</pre>")
    await cq.answer()


@router.callback_query(F.data.startswith("u:r:"))
async def cb_user_reset(cq: CallbackQuery, mb: MarzbanClient, settings: Settings) -> None:
    username = cq.data[4:]
    try:
        u = await mb.reset_user_usage(username)
    except MarzbanError as e:
        await cq.answer(f"Ошибка: {e}", show_alert=True)
        return
    await cq.message.edit_text(fmt_user_card(u, settings.marzban_base_url), reply_markup=user_actions_kb(username))
    await cq.answer("Сброшено")


@router.callback_query(F.data.startswith("u:v:"))
async def cb_user_revoke(cq: CallbackQuery, mb: MarzbanClient, settings: Settings) -> None:
    username = cq.data[4:]
    try:
        u = await mb.revoke_subscription(username)
    except MarzbanError as e:
        await cq.answer(f"Ошибка: {e}", show_alert=True)
        return
    await cq.message.edit_text(fmt_user_card(u, settings.marzban_base_url), reply_markup=user_actions_kb(username))
    await cq.answer("Подписка отозвана")


@router.callback_query(F.data.startswith("u:t:"))
async def cb_user_toggle(cq: CallbackQuery, mb: MarzbanClient, settings: Settings) -> None:
    username = cq.data[4:]
    try:
        cur = await mb.user(username)
        st = cur.get("status")
        new_st = "disabled" if st == "active" else "active"
        u = await mb.modify_user(username, {"status": new_st})
    except MarzbanError as e:
        await cq.answer(f"Ошибка: {e}", show_alert=True)
        return
    await cq.message.edit_text(fmt_user_card(u, settings.marzban_base_url), reply_markup=user_actions_kb(username))
    await cq.answer("Статус обновлён")


@router.callback_query(F.data.startswith("u:d:"))
async def cb_user_del_ask(cq: CallbackQuery) -> None:
    username = cq.data[4:]
    await cq.message.edit_text(
        f"Удалить <code>{html.escape(username)}</code>?",
        reply_markup=confirm_delete_kb(username),
    )
    await cq.answer()


@router.callback_query(F.data.startswith("u:dd:"))
async def cb_user_del_do(cq: CallbackQuery, mb: MarzbanClient) -> None:
    username = cq.data[5:]
    try:
        await mb.delete_user(username)
    except MarzbanError as e:
        await cq.answer(f"Ошибка: {e}", show_alert=True)
        return
    sudo = await _sudo(mb)
    await cq.message.edit_text("Пользователь удалён.", reply_markup=main_menu_kb(sudo))
    await cq.answer("Удалено")


@router.callback_query(F.data == "m:rx")
async def cb_restart_ask(cq: CallbackQuery, mb: MarzbanClient) -> None:
    if not await _sudo(mb):
        await cq.answer("Только sudo", show_alert=True)
        return
    await cq.message.edit_text(
        "Перезапустить ядро Xray?",
        reply_markup=restart_confirm_kb(),
    )
    await cq.answer()


@router.callback_query(F.data == "m:rxy")
async def cb_restart_do(cq: CallbackQuery, mb: MarzbanClient) -> None:
    if not await _sudo(mb):
        await cq.answer("Только sudo", show_alert=True)
        return
    try:
        await mb.restart_core()
    except MarzbanError as e:
        await cq.answer(f"Ошибка: {e}", show_alert=True)
        return
    sudo = await _sudo(mb)
    await cq.message.edit_text("Перезапуск запланирован.", reply_markup=main_menu_kb(sudo))
    await cq.answer("Готово")


@router.callback_query(F.data == "m:nd")
async def cb_nodes(cq: CallbackQuery, mb: MarzbanClient) -> None:
    if not await _sudo(mb):
        await cq.answer("Только sudo", show_alert=True)
        return
    try:
        nodes = await mb.nodes()
    except MarzbanError as e:
        await cq.answer(f"Ошибка: {e}", show_alert=True)
        return
    lines = []
    for n in nodes or []:
        if isinstance(n, dict):
            lines.append(
                f"• {html.escape(str(n.get('name','?')))} id={n.get('id')} "
                f"{html.escape(str(n.get('status','?')))} addr={html.escape(str(n.get('address','')))}"
            )
        else:
            lines.append(str(n))
    text = "\n".join(lines) if lines else "Нет нод."
    await cq.message.edit_text(text[:4000], reply_markup=back_menu_kb())
    await cq.answer()


@router.callback_query(F.data == "m:adm")
async def cb_admins(cq: CallbackQuery, mb: MarzbanClient) -> None:
    if not await _sudo(mb):
        await cq.answer("Только sudo", show_alert=True)
        return
    try:
        admins = await mb.admins()
    except MarzbanError as e:
        await cq.answer(f"Ошибка: {e}", show_alert=True)
        return
    lines = []
    for a in admins or []:
        if isinstance(a, dict):
            sudo = "sudo" if a.get("is_sudo") else "admin"
            lines.append(f"• <code>{html.escape(str(a.get('username','?')))}</code> ({sudo})")
    text = "\n".join(lines) if lines else "Нет данных."
    await cq.message.edit_text(text, reply_markup=back_menu_kb())
    await cq.answer()
