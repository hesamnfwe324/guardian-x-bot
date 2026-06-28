from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Callable


def moderation_menu_kb(_: Callable, is_group: bool = False) -> InlineKeyboardMarkup:
    """Glass-styled moderation menu with crystal buttons."""
    builder = InlineKeyboardBuilder()
    buttons = [
        ("🔨 ◈ بن",         "mod:ban"),
        ("✅ ◈ رفع بن",     "mod:unban"),
        ("👢 ◈ اخراج",      "mod:kick"),
        ("🔇 ◈ سکوت",       "mod:mute"),
        ("🔊 ◈ رفع سکوت",   "mod:unmute"),
        ("⚠️ ◈ اخطار",      "mod:warn"),
        ("✅ ◈ رفع اخطار",  "mod:unwarn"),
        ("⏱️ ◈ بن موقت",    "mod:tban"),
        ("⏱️ ◈ سکوت موقت", "mod:tmute"),
        ("📝 ◈ یادداشت",    "mod:notes"),
        ("📂 ◈ تاریخچه",    "mod:history"),
        ("🎭 ◈ نقش‌ها",     "mod:roles"),
        ("⚡ ◈ استرایک",    "mod:strike"),
    ]
    for text, cb in buttons:
        builder.button(text=text, callback_data=cb)
    builder.button(text="🔙 ◈ بازگشت", callback_data="menu:main")
    builder.button(text="🏠 ◈ خانه",   callback_data="menu:main")
    builder.adjust(2, 2, 3, 2, 2, 2)
    return builder.as_markup()


def mute_duration_kb(_: Callable, user_id: int) -> InlineKeyboardMarkup:
    """Glass-styled mute duration selection."""
    builder = InlineKeyboardBuilder()
    durations = [
        ("5m ◈",   f"mute_dur:{user_id}:300"),
        ("30m ◈",  f"mute_dur:{user_id}:1800"),
        ("1h ◈",   f"mute_dur:{user_id}:3600"),
        ("6h ◈",   f"mute_dur:{user_id}:21600"),
        ("12h ◈",  f"mute_dur:{user_id}:43200"),
        ("24h ◈",  f"mute_dur:{user_id}:86400"),
        ("3d ◈",   f"mute_dur:{user_id}:259200"),
        ("7d ◈",   f"mute_dur:{user_id}:604800"),
        ("♾️ ◈ همیشه", f"mute_dur:{user_id}:0"),
    ]
    for text, cb in durations:
        builder.button(text=text, callback_data=cb)
    builder.button(text="❌ ◈ انصراف", callback_data="mod:menu")
    builder.button(text="🏠 ◈ خانه",   callback_data="menu:main")
    builder.adjust(3, 3, 3, 2)
    return builder.as_markup()


def warn_actions_kb(_: Callable, user_id: int, warn_count: int, max_warns: int) -> InlineKeyboardMarkup:
    """Glass-styled warn actions."""
    builder = InlineKeyboardBuilder()
    builder.button(text=f"⚠️ ◈ اخطار ({warn_count}/{max_warns})", callback_data=f"warn_confirm:{user_id}")
    builder.button(text="❌ ◈ انصراف", callback_data="mod:menu")
    builder.button(text="🏠 ◈ خانه",   callback_data="menu:main")
    builder.adjust(1, 2)
    return builder.as_markup()


def ban_duration_kb(_: Callable, user_id: int) -> InlineKeyboardMarkup:
    """Glass-styled ban duration selection."""
    builder = InlineKeyboardBuilder()
    durations = [
        ("1h ◈",   f"tban_dur:{user_id}:3600"),
        ("6h ◈",   f"tban_dur:{user_id}:21600"),
        ("12h ◈",  f"tban_dur:{user_id}:43200"),
        ("1d ◈",   f"tban_dur:{user_id}:86400"),
        ("3d ◈",   f"tban_dur:{user_id}:259200"),
        ("7d ◈",   f"tban_dur:{user_id}:604800"),
        ("30d ◈",  f"tban_dur:{user_id}:2592000"),
        ("♾️ ◈ بن دائم", f"tban_dur:{user_id}:0"),
    ]
    for text, cb in durations:
        builder.button(text=text, callback_data=cb)
    builder.button(text="❌ ◈ انصراف", callback_data="mod:menu")
    builder.button(text="🏠 ◈ خانه",   callback_data="menu:main")
    builder.adjust(4, 4, 2)
    return builder.as_markup()


def notes_kb(_: Callable, user_id: int, group_id: int) -> InlineKeyboardMarkup:
    """Glass-styled notes menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ ◈ افزودن یادداشت",  callback_data=f"note:add:{user_id}:{group_id}")
    builder.button(text="📄 ◈ مشاهده یادداشت", callback_data=f"note:view:{user_id}:{group_id}")
    builder.button(text="🗑️ ◈ حذف یادداشت",     callback_data=f"note:clear:{user_id}:{group_id}")
    builder.button(text="🔙 ◈ بازگشت", callback_data="mod:menu")
    builder.button(text="🏠 ◈ خانه",   callback_data="menu:main")
    builder.adjust(2, 1, 2)
    return builder.as_markup()
