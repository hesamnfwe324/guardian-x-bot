from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Callable
from bot.utils.glass_panel import glass_status, glass_lock_status


# Language flag emoji map
LANG_FLAGS = {
    "en": "🇬🇧",
    "fa": "🇮🇷",
    "ar": "🇸🇦",
    "tr": "🇹🇷",
    "ru": "🇷🇺",
    "es": "🇪🇸",
    "fr": "🇫🇷",
    "de": "🇩🇪",
}


def language_selection_kb() -> InlineKeyboardMarkup:
    """Beautiful 8-language selection grid with flag emojis."""
    builder = InlineKeyboardBuilder()
    languages = [
        ("🇬🇧 English",    "lang:en"),
        ("🇮🇷 فارسی",      "lang:fa"),
        ("🇸🇦 العربية",    "lang:ar"),
        ("🇹🇷 Türkçe",     "lang:tr"),
        ("🇷🇺 Русский",    "lang:ru"),
        ("🇪🇸 Español",    "lang:es"),
        ("🇫🇷 Français",   "lang:fr"),
        ("🇩🇪 Deutsch",    "lang:de"),
    ]
    for text, cb in languages:
        builder.button(text=text, callback_data=cb)
    builder.adjust(2, 2, 2, 2)
    return builder.as_markup()


def main_menu_kb(_: Callable) -> InlineKeyboardMarkup:
    """Beautiful i18n main menu with emoji-rich buttons."""
    builder = InlineKeyboardBuilder()
    # Row 1: Core features
    builder.button(text=_('btn_security'),     callback_data="menu:security")
    builder.button(text=_('btn_moderation'),    callback_data="menu:moderation")
    # Row 2: Fun & Economy
    builder.button(text=_('btn_games'),         callback_data="menu:games")
    builder.button(text=_('btn_economy'),       callback_data="menu:economy")
    # Row 3: Competition
    builder.button(text=_('btn_tournaments'),   callback_data="menu:tournaments")
    builder.button(text=_('btn_duels'),         callback_data="menu:duels")
    # Row 4: Info
    builder.button(text=_('btn_statistics'),    callback_data="menu:statistics")
    builder.button(text=_('btn_reputation'),    callback_data="menu:reputation")
    # Row 5: Config
    builder.button(text=_('btn_settings'),      callback_data="menu:settings")
    builder.button(text=_('btn_help'),          callback_data="menu:help")
    # Row 6: Misc
    builder.button(text=_('btn_language'),      callback_data="menu:language")
    builder.button(text=_('btn_channel'),       callback_data="menu:channel")
    builder.adjust(2, 2, 2, 2, 2, 2)
    return builder.as_markup()


def group_main_menu_kb(_: Callable) -> InlineKeyboardMarkup:
    """Beautiful i18n group admin panel."""
    builder = InlineKeyboardBuilder()
    builder.button(text=_('btn_security'),     callback_data="menu:security")
    builder.button(text=_('btn_moderation'),    callback_data="menu:moderation")
    builder.button(text=_('btn_settings'),      callback_data="menu:settings")
    builder.button(text=_('btn_statistics'),    callback_data="menu:statistics")
    builder.button(text=_('btn_games'),         callback_data="menu:games")
    builder.button(text=_('btn_economy'),       callback_data="menu:economy")
    builder.button(text=_('btn_help'),          callback_data="menu:help")
    builder.button(text=_('btn_channel'),       callback_data="menu:channel")
    builder.button(text="🔄 " + _('btn_refresh'), callback_data="group:main")
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup()


def back_button_kb(_: Callable, back_cb: str = "menu:main") -> InlineKeyboardMarkup:
    """Beautiful i18n back/home navigation."""
    builder = InlineKeyboardBuilder()
    builder.button(text=_('btn_back'), callback_data=back_cb)
    builder.button(text=_('btn_home'), callback_data="menu:main")
    builder.adjust(2)
    return builder.as_markup()


def nav_kb(_: Callable, back_cb: str = "menu:main", refresh_cb: str = None) -> InlineKeyboardMarkup:
    """Beautiful i18n navigation bar with Back, Home, and optional Refresh."""
    builder = InlineKeyboardBuilder()
    builder.button(text=_('btn_back'),     callback_data=back_cb)
    builder.button(text=_('btn_home'),     callback_data="menu:main")
    if refresh_cb:
        builder.button(text=_('btn_refresh'), callback_data=refresh_cb)
        builder.adjust(2, 1)
    else:
        builder.adjust(2)
    return builder.as_markup()


def confirm_cancel_kb(_: Callable, confirm_cb: str, cancel_cb: str = 'menu:main') -> InlineKeyboardMarkup:
    """Beautiful i18n confirm/cancel buttons."""
    builder = InlineKeyboardBuilder()
    builder.button(text=_('btn_confirm'), callback_data=confirm_cb)
    builder.button(text=_('btn_cancel'),  callback_data=cancel_cb)
    builder.adjust(2)
    return builder.as_markup()
