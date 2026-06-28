from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Callable


def economy_menu_kb(_: Callable) -> InlineKeyboardMarkup:
    """Glass-styled economy menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text='👛 ◈ کیف پول',       callback_data="eco:wallet")
    builder.button(text='🏦 ◈ بانک',           callback_data="eco:bank")
    builder.button(text='🎁 ◈ روزانه',         callback_data="eco:daily")
    builder.button(text='🎁 ◈ هفتگی',          callback_data="eco:weekly")
    builder.button(text='🎁 ◈ ماهانه',         callback_data="eco:monthly")
    builder.button(text='👥 ◈ معرفی',          callback_data="eco:referral")
    builder.button(text='📋 ◈ تراکنش‌ها',       callback_data="eco:transactions")
    builder.button(text='🔙 ◈ بازگشت',         callback_data="menu:main")
    builder.adjust(2, 3, 2, 1)
    return builder.as_markup()


def wallet_kb(_: Callable) -> InlineKeyboardMarkup:
    """Glass-styled wallet menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text='📥 ◈ واریز',   callback_data="eco:deposit")
    builder.button(text='📤 ◈ برداشت', callback_data="eco:withdraw")
    builder.button(text='🔀 ◈ انتقال', callback_data="eco:transfer")
    builder.button(text='🔙 ◈ بازگشت', callback_data="menu:economy")
    builder.adjust(3, 1)
    return builder.as_markup()


def rewards_menu_kb(_: Callable) -> InlineKeyboardMarkup:
    """Glass-styled rewards menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text='🏅 ◈ دستاوردها',   callback_data="rewards:achievements")
    builder.button(text='📋 ◈ مأموریت‌ها',  callback_data="rewards:missions")
    builder.button(text='🛒 ◈ فروشگاه',     callback_data="rewards:shop")
    builder.button(text='🔙 ◈ بازگشت',     callback_data="menu:main")
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def shop_categories_kb(_: Callable) -> InlineKeyboardMarkup:
    """Glass-styled shop categories."""
    builder = InlineKeyboardBuilder()
    builder.button(text='🏷️ ◈ نشان‌ها',     callback_data="shop:badges")
    builder.button(text='👑 ◈ عناوین',        callback_data="shop:titles")
    builder.button(text='🖼️ ◈ قاب‌ها',        callback_data="shop:frames")
    builder.button(text='📦 ◈ جعبه شانس',   callback_data="shop:lootboxes")
    builder.button(text='🎨 ◈ آرایشی',       callback_data="shop:cosmetics")
    builder.button(text='🔙 ◈ بازگشت',       callback_data="menu:rewards")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def missions_kb(_: Callable) -> InlineKeyboardMarkup:
    """Glass-styled missions menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text='📋 ◈ مأموریت روزانه',   callback_data="missions:daily")
    builder.button(text='📋 ◈ مأموریت هفتگی',    callback_data="missions:weekly")
    builder.button(text='📋 ◈ مأموریت ماهانه',   callback_data="missions:monthly")
    builder.button(text='🔙 ◈ بازگشت',            callback_data="menu:rewards")
    builder.adjust(3, 1)
    return builder.as_markup()
