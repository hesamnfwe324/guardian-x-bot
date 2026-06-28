from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Callable


def language_selection_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🇬🇧 English", callback_data="lang:en")
    builder.button(text="🇮🇷 فارسی",  callback_data="lang:fa")
    builder.adjust(2)
    return builder.as_markup()


def main_menu_kb(_: Callable) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_security"),    callback_data="menu:security")
    builder.button(text=_("btn_moderation"),  callback_data="menu:moderation")
    builder.button(text=_("btn_games"),       callback_data="menu:games")
    builder.button(text=_("btn_economy"),     callback_data="menu:economy")
    builder.button(text=_("btn_tournaments"), callback_data="menu:tournaments")
    builder.button(text=_("btn_duels"),       callback_data="menu:duels")
    builder.button(text=_("btn_statistics"),  callback_data="menu:statistics")
    builder.button(text=_("btn_reputation"),  callback_data="menu:reputation")
    builder.button(text=_("btn_settings"),    callback_data="menu:settings")
    builder.button(text=_("btn_help"),        callback_data="menu:help")
    builder.button(text=_("btn_language"),    callback_data="menu:language")
    builder.button(text=_("btn_channel"),     callback_data="menu:channel")
    builder.adjust(2, 2, 2, 2, 2, 2)
    return builder.as_markup()


def group_main_menu_kb(_: Callable) -> InlineKeyboardMarkup:
    """Full inline group admin panel — replaces redirect to private chat."""
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_security"),   callback_data="menu:security")
    builder.button(text=_("btn_moderation"), callback_data="menu:moderation")
    builder.button(text=_("btn_settings"),   callback_data="menu:settings")
    builder.button(text=_("btn_statistics"), callback_data="menu:statistics")
    builder.button(text=_("btn_games"),      callback_data="menu:games")
    builder.button(text=_("btn_economy"),    callback_data="menu:economy")
    builder.button(text=_("btn_help"),       callback_data="menu:help")
    builder.button(text=_("btn_channel"),    callback_data="menu:channel")
    builder.button(text=_("btn_refresh"),    callback_data="group:main")
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup()


def back_button_kb(_: Callable, back_cb: str = "menu:main") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_back"), callback_data=back_cb)
    builder.button(text=_("btn_home"), callback_data="menu:main")
    builder.adjust(2)
    return builder.as_markup()


def nav_kb(_: Callable, back_cb: str = "menu:main", refresh_cb: str = None) -> InlineKeyboardMarkup:
    """Navigation bar with Back, Home, and optional Refresh buttons."""
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_back"), callback_data=back_cb)
    builder.button(text=_("btn_home"), callback_data="menu:main")
    if refresh_cb:
        builder.button(text=_("btn_refresh"), callback_data=refresh_cb)
        builder.adjust(2, 1)
    else:
        builder.adjust(2)
    return builder.as_markup()
