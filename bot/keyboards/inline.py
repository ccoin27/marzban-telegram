from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb(is_sudo: bool) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="Система", callback_data="m:sys"),
            InlineKeyboardButton(text="Инбаунды", callback_data="m:inb"),
        ],
        [
            InlineKeyboardButton(text="Пользователи", callback_data="m:us:0"),
            InlineKeyboardButton(text="Поиск", callback_data="m:find"),
        ],
        [
            InlineKeyboardButton(text="Создать пользователя", callback_data="m:new"),
        ],
    ]
    if is_sudo:
        rows.append(
            [
                InlineKeyboardButton(text="Ноды", callback_data="m:nd"),
                InlineKeyboardButton(text="Админы", callback_data="m:adm"),
            ]
        )
        rows.append([InlineKeyboardButton(text="Перезапуск Xray", callback_data="m:rx")])
    rows.append([InlineKeyboardButton(text="Обновить меню", callback_data="m:me")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="В меню", callback_data="m:me")]]
    )


def users_list_kb(
    usernames: list[str],
    page: int,
    total: int,
    page_size: int,
    list_prefix: str = "m",
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for u in usernames:
        label = u if len(u) <= 28 else u[:25] + "..."
        row.append(InlineKeyboardButton(text=label, callback_data=f"u:o:{u}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    max_page = max(0, (total - 1) // page_size) if total else 0
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="<-", callback_data=f"{list_prefix}:us:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{max_page+1}", callback_data="m:noop"))
    if page < max_page:
        nav.append(InlineKeyboardButton(text="->", callback_data=f"{list_prefix}:us:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="В меню", callback_data="m:me")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def user_actions_kb(username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Ссылка + QR", callback_data=f"u:s:{username}"),
                InlineKeyboardButton(text="Конфиг-ссылки", callback_data=f"u:l:{username}"),
            ],
            [
                InlineKeyboardButton(text="Сброс трафика", callback_data=f"u:r:{username}"),
                InlineKeyboardButton(text="Отозвать sub", callback_data=f"u:v:{username}"),
            ],
            [
                InlineKeyboardButton(text="Вкл/Выкл", callback_data=f"u:t:{username}"),
                InlineKeyboardButton(text="Удалить", callback_data=f"u:d:{username}"),
            ],
            [
                InlineKeyboardButton(text="К списку", callback_data="m:us:0"),
                InlineKeyboardButton(text="В меню", callback_data="m:me"),
            ],
        ]
    )


def confirm_delete_kb(username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да, удалить", callback_data=f"u:dd:{username}"),
                InlineKeyboardButton(text="Отмена", callback_data=f"u:o:{username}"),
            ]
        ]
    )


def create_expire_kb(username: str) -> InlineKeyboardMarkup:
    u = username
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="7 дн.", callback_data=f"n:e:{u}:7"),
                InlineKeyboardButton(text="30 дн.", callback_data=f"n:e:{u}:30"),
                InlineKeyboardButton(text="90 дн.", callback_data=f"n:e:{u}:90"),
            ],
            [
                InlineKeyboardButton(text="365 дн.", callback_data=f"n:e:{u}:365"),
                InlineKeyboardButton(text="Без срока", callback_data=f"n:e:{u}:0"),
            ],
            [InlineKeyboardButton(text="Отмена", callback_data="m:me")],
        ]
    )


def create_traffic_kb(username: str, expire_days: int) -> InlineKeyboardMarkup:
    u = username
    d = expire_days
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="5 ГБ", callback_data=f"n:t:{u}:{d}:5368709120"),
                InlineKeyboardButton(text="50 ГБ", callback_data=f"n:t:{u}:{d}:53687091200"),
            ],
            [
                InlineKeyboardButton(text="200 ГБ", callback_data=f"n:t:{u}:{d}:214748364800"),
                InlineKeyboardButton(text="1 ТБ", callback_data=f"n:t:{u}:{d}:1099511627776"),
            ],
            [InlineKeyboardButton(text="Безлимит", callback_data=f"n:t:{u}:{d}:0")],
            [InlineKeyboardButton(text="Отмена", callback_data="m:me")],
        ]
    )


def restart_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да, перезапустить", callback_data="m:rxy"),
                InlineKeyboardButton(text="Отмена", callback_data="m:me"),
            ]
        ]
    )
