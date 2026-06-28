from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Callable


def moderation_menu_kb(_: Callable, is_group: bool = False) -> InlineKeyboardMarkup:
    """Beautiful i18n moderation menu."""
    builder = InlineKeyboardBuilder()
    buttons = [
        (_('btn_ban'),       "mod:ban"),
        (_('btn_unban'),     "mod:unban"),
        (_('btn_kick'),      "mod:kick"),
        (_('btn_mute'),      "mod:mute"),
        (_('btn_unmute'),    "mod:unmute"),
        (_('btn_warn'),      "mod:warn"),
        (_('btn_unwarn'),    "mod:unwarn"),
        (_('btn_temp_ban'),  "mod:tban"),
        (_('btn_temp_mute'), "mod:tmute"),
        (_('btn_notes'),     "mod:notes"),
        (_('btn_history'),   "mod:history"),
        (_('btn_roles'),     "mod:roles"),
        (_('btn_strike'),    "mod:strike"),
    ]
    for text, cb in buttons:
        builder.button(text=text, callback_data=cb)
    builder.button(text=_('btn_back'), callback_data="menu:main")
    builder.button(text=_('btn_home'), callback_data="menu:main")
    builder.adjust(2, 2, 3, 2, 2, 2)
    return builder.as_markup()


def mute_duration_kb(_: Callable, user_id: int) -> InlineKeyboardMarkup:
    """Beautiful i18n mute duration selection."""
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
        (_('btn_mute_forever'), f"mute_dur:{user_id}:0"),
    ]
    for text, cb in durations:
        builder.button(text=text, callback_data=cb)
    builder.button(text=_('btn_cancel'), callback_data="mod:menu")
    builder.button(text=_('btn_home'),   callback_data="menu:main")
    builder.adjust(3, 3, 3, 2)
    return builder.as_markup()


def warn_actions_kb(_: Callable, user_id: int, warn_count: int, max_warns: int) -> InlineKeyboardMarkup:
    """Beautiful i18n warn actions."""
    builder = InlineKeyboardBuilder()
    builder.button(text=f"⚠️ ◈ {warn_count}/{max_warns}", callback_data=f"warn_confirm:{user_id}")
    builder.button(text=_('btn_cancel'), callback_data="mod:menu")
    builder.button(text=_('btn_home'),   callback_data="menu:main")
    builder.adjust(1, 2)
    return builder.as_markup()


def ban_duration_kb(_: Callable, user_id: int) -> InlineKeyboardMarkup:
    """Beautiful i18n ban duration selection."""
    builder = InlineKeyboardBuilder()
    durations = [
        ("1h ◈",   f"tban_dur:{user_id}:3600"),
        ("6h ◈",   f"tban_dur:{user_id}:21600"),
        ("12h ◈",  f"tban_dur:{user_id}:43200"),
        ("1d ◈",   f"tban_dur:{user_id}:86400"),
        ("3d ◈",   f"tban_dur:{user_id}:259200"),
        ("7d ◈",   f"tban_dur:{user_id}:604800"),
        ("30d ◈",  f"tban_dur:{user_id}:2592000"),
        (_('btn_ban_forever'), f"tban_dur:{user_id}:0"),
    ]
    for text, cb in durations:
        builder.button(text=text, callback_data=cb)
    builder.button(text=_('btn_cancel'), callback_data="mod:menu")
    builder.button(text=_('btn_home'),   callback_data="menu:main")
    builder.adjust(4, 4, 2)
    return builder.as_markup()


def notes_kb(_: Callable, user_id: int, group_id: int) -> InlineKeyboardMarkup:
    """Beautiful i18n notes menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text=_('btn_add_note'),  callback_data=f"note:add:{user_id}:{group_id}")
    builder.button(text=_('btn_view_notes'),callback_data=f"note:view:{user_id}:{group_id}")
    builder.button(text=_('btn_clear_notes'),callback_data=f"note:clear:{user_id}:{group_id}")
    builder.button(text=_('btn_back'), callback_data="mod:menu")
    builder.button(text=_('btn_home'), callback_data="menu:main")
    builder.adjust(2, 1, 2)
    return builder.as_markup()
