from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Callable


def settings_menu_kb(_: Callable) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_welcome"),          callback_data="settings:welcome")
    builder.button(text=_("btn_goodbye"),          callback_data="settings:goodbye")
    builder.button(text=_("btn_log_channel"),      callback_data="settings:logs")
    builder.button(text=_("btn_general_settings"), callback_data="settings:general")
    builder.button(text=_("btn_slow_mode"),        callback_data="settings:slowmode")
    builder.button(text=_("btn_auto_delete"),      callback_data="settings:autodel")
    builder.button(text=_("btn_back"),             callback_data="menu:main")
    builder.button(text=_("btn_home"),             callback_data="menu:main")
    builder.adjust(2, 2, 2, 2)
    return builder.as_markup()
