from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Callable


def games_menu_kb(_: Callable) -> InlineKeyboardMarkup:
    """Glass-styled games menu with crystal buttons."""
    builder = InlineKeyboardBuilder()
    games = [
        ("🎲 ◈ تاس",           "game:dice"),
        ("🧠 ◈ کوئیز",         "game:quiz"),
        ("💎 ◈ شکار گنج",      "game:treasure"),
        ("🎡 ◈ چرخ شانس",      "game:wheel"),
        ("🃏 ◈ نبرد کارت",      "game:cards"),
        ("🔢 ◈ نبرد اعداد",     "game:numwar"),
        ("✊ ◈ سنگ کاغذ قیچی",  "game:rps"),
        ("💣 ◈ مین‌یاب",        "game:mines"),
        ("♟️ ◈ شطرنج",          "game:chess"),
        ("🎰 ◈ رولت",           "game:roulette"),
    ]
    for text, cb in games:
        builder.button(text=text, callback_data=cb)
    builder.button(text="🔙 ◈ بازگشت", callback_data="menu:main")
    builder.adjust(2)
    return builder.as_markup()


def dice_menu_kb(_: Callable) -> InlineKeyboardMarkup:
    """Glass-styled dice menu."""
    builder = InlineKeyboardBuilder()
    modes = [
        ("🎲 ◈ کلاسیک",        "dice:classic"),
        ("🎯 ◈ پیش‌بینی",      "dice:prediction"),
        ("💫 ◈ ضریب شانس",     "dice:lucky_mult"),
        ("🏆 ◈ بهترین از ۳",    "dice:best3"),
        ("🏆 ◈ بهترین از ۵",    "dice:best5"),
        ("⚔️ ◈ تورنمنت تاس",    "dice:tournament"),
        ("👥 ◈ نبرد گروهی",     "dice:group_battle"),
        ("📅 ◈ چالش روزانه",    "dice:daily"),
        ("🔥 ◈ رشته تاس",       "dice:streak"),
        ("👑 ◈ VIP",            "dice:vip"),
    ]
    for text, cb in modes:
        builder.button(text=text, callback_data=cb)
    builder.button(text="🔙 ◈ بازگشت", callback_data="menu:games")
    builder.adjust(2)
    return builder.as_markup()


def game_action_kb(_: Callable, game_type: str, match_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 ◈ آمار بازی",  callback_data=f"gstats:{game_type}")
    builder.button(text="🏅 ◈ رتبه‌بندی",    callback_data=f"grank:{game_type}")
    builder.button(text="🔙 ◈ بازگشت",      callback_data="menu:games")
    builder.adjust(2, 1)
    return builder.as_markup()


def join_game_kb(_: Callable, match_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ ◈ شرکت",   callback_data=f"game_join:{match_id}")
    builder.button(text="❌ ◈ انصراف", callback_data=f"game_cancel:{match_id}")
    builder.adjust(2)
    return builder.as_markup()


def rps_choice_kb(_: Callable, match_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✊ ◈ سنگ",    callback_data=f"rps:{match_id}:rock")
    builder.button(text="✋ ◈ کاغذ",   callback_data=f"rps:{match_id}:paper")
    builder.button(text="✌️ ◈ قیچی",  callback_data=f"rps:{match_id}:scissors")
    builder.adjust(3)
    return builder.as_markup()


def wheel_spin_kb(_: Callable, match_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎡 ◈ چرخاندن", callback_data=f"wheel_spin:{match_id}")
    builder.adjust(1)
    return builder.as_markup()


def mines_board_kb(board: list, match_id: int, rows: int = 5, cols: int = 5) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for r in range(rows):
        for c in range(cols):
            cell = board[r][c] if board else None
            if cell is None:
                text = "⬜"
            elif cell:
                text = "💣"
            else:
                text = "💎"
            builder.button(text=text, callback_data=f"mines:{match_id}:{r}:{c}")
    builder.adjust(cols)
    return builder.as_markup()
