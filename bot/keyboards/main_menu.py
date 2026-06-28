from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Callable
from bot.utils.glass_panel import glass_status, glass_lock_status


def language_selection_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🇬🇧 English", callback_data="lang:en")
    builder.button(text="🇮🇷 فارسی",  callback_data="lang:fa")
    builder.adjust(2)
    return builder.as_markup()


def main_menu_kb(_: Callable) -> InlineKeyboardMarkup:
    """Glass-styled main menu with crystal-themed button labels."""
    builder = InlineKeyboardBuilder()
    # Row 1: Core features
    builder.button(text="🛡️ ◈ مرکز امنیت",     callback_data="menu:security")
    builder.button(text="⚖️ ◈ مدیریت",         callback_data="menu:moderation")
    # Row 2: Fun & Economy
    builder.button(text="🎮 ◈ سرگرمی",          callback_data="menu:games")
    builder.button(text="💰 ◈ اقتصاد",          callback_data="menu:economy")
    # Row 3: Competition
    builder.button(text="🏆 ◈ تورنمنت",         callback_data="menu:tournaments")
    builder.button(text="⚔️ ◈ دوئل",            callback_data="menu:duels")
    # Row 4: Info
    builder.button(text="📊 ◈ آمار",            callback_data="menu:statistics")
    builder.button(text="🌟 ◈ شهرت",            callback_data="menu:reputation")
    # Row 5: Config
    builder.button(text="⚙️ ◈ مرکز کنترل",      callback_data="menu:settings")
    builder.button(text="❓ ◈ راهنما",          callback_data="menu:help")
    # Row 6: Misc
    builder.button(text="🌐 ◈ زبان",            callback_data="menu:language")
    builder.button(text="📢 ◈ کانال",           callback_data="menu:channel")
    builder.adjust(2, 2, 2, 2, 2, 2)
    return builder.as_markup()


def group_main_menu_kb(_: Callable) -> InlineKeyboardMarkup:
    """Glass-styled group admin panel with crystal buttons."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🛡️ ◈ امنیت",      callback_data="menu:security")
    builder.button(text="⚖️ ◈ مدیریت",     callback_data="menu:moderation")
    builder.button(text="⚙️ ◈ تنظیمات",     callback_data="menu:settings")
    builder.button(text="📊 ◈ آمار",         callback_data="menu:statistics")
    builder.button(text="🎮 ◈ سرگرمی",      callback_data="menu:games")
    builder.button(text="💰 ◈ اقتصاد",      callback_data="menu:economy")
    builder.button(text="❓ ◈ راهنما",       callback_data="menu:help")
    builder.button(text="📢 ◈ کانال",       callback_data="menu:channel")
    builder.button(text="🔄 ◈ بروزرسانی",    callback_data="group:main")
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup()


def back_button_kb(_: Callable, back_cb: str = "menu:main") -> InlineKeyboardMarkup:
    """Glass-styled back/home navigation."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 ◈ بازگشت", callback_data=back_cb)
    builder.button(text="🏠 ◈ خانه",   callback_data="menu:main")
    builder.adjust(2)
    return builder.as_markup()


def nav_kb(_: Callable, back_cb: str = "menu:main", refresh_cb: str = None) -> InlineKeyboardMarkup:
    """Glass-styled navigation bar with Back, Home, and optional Refresh."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 ◈ بازگشت",    callback_data=back_cb)
    builder.button(text="🏠 ◈ خانه",      callback_data="menu:main")
    if refresh_cb:
        builder.button(text="🔄 ◈ بروزرسانی", callback_data=refresh_cb)
        builder.adjust(2, 1)
    else:
        builder.adjust(2)
    return builder.as_markup()


def confirm_cancel_kb(_: Callable, confirm_cb: str, cancel_cb: str = 'menu:main') -> InlineKeyboardMarkup:
    """Glass-styled confirm/cancel buttons."""
    builder = InlineKeyboardBuilder()
    builder.button(text='✅ ◈ تأیید',   callback_data=confirm_cb)
    builder.button(text='❌ ◈ انصراف', callback_data=cancel_cb)
    builder.adjust(2)
    return builder.as_markup()
