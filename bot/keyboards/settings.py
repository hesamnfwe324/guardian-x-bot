from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Callable


def settings_menu_kb(_: Callable) -> InlineKeyboardMarkup:
    """Glass-styled settings menu with crystal buttons."""
    builder = InlineKeyboardBuilder()
    builder.button(text="👋 ◈ خوش‌آمد",          callback_data="settings:welcome")
    builder.button(text="👋 ◈ خداحافظی",         callback_data="settings:goodbye")
    builder.button(text="📋 ◈ کانال لاگ",        callback_data="settings:logs")
    builder.button(text="⚙️ ◈ تنظیمات عمومی",   callback_data="settings:general")
    builder.button(text="🐌 ◈ حالت آرام",       callback_data="settings:slowmode")
    builder.button(text="🗑️ ◈ حذف خودکار",      callback_data="settings:autodel")
    builder.button(text="🔙 ◈ بازگشت",            callback_data="menu:main")
    builder.button(text="🏠 ◈ خانه",              callback_data="menu:main")
    builder.adjust(2, 2, 2, 2)
    return builder.as_markup()
