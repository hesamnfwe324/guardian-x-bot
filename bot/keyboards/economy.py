from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Callable


def economy_menu_kb(_: Callable) -> InlineKeyboardMarkup:
    """Beautiful i18n economy menu with glass-styled buttons."""
    builder = InlineKeyboardBuilder()
    builder.button(text=_('btn_wallet'),       callback_data="eco:wallet")
    builder.button(text=_('btn_bank'),          callback_data="eco:bank")
    builder.button(text=_('btn_daily_reward'),  callback_data="eco:daily")
    builder.button(text=_('btn_weekly_reward'), callback_data="eco:weekly")
    builder.button(text=_('btn_monthly_reward'),callback_data="eco:monthly")
    builder.button(text=_('btn_referral'),      callback_data="eco:referral")
    builder.button(text=_('btn_transactions'),  callback_data="eco:transactions")
    builder.button(text=_('btn_back'),          callback_data="menu:main")
    builder.adjust(2, 3, 2, 1)
    return builder.as_markup()


def wallet_kb(_: Callable) -> InlineKeyboardMarkup:
    """Beautiful i18n wallet menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text=_('btn_deposit'),  callback_data="eco:deposit")
    builder.button(text=_('btn_withdraw'), callback_data="eco:withdraw")
    builder.button(text=_('btn_transfer'), callback_data="eco:transfer")
    builder.button(text=_('btn_back'),     callback_data="menu:economy")
    builder.adjust(3, 1)
    return builder.as_markup()


def rewards_menu_kb(_: Callable) -> InlineKeyboardMarkup:
    """Beautiful i18n rewards menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text=_('btn_achievements'), callback_data="rewards:achievements")
    builder.button(text=_('btn_missions'),     callback_data="rewards:missions")
    builder.button(text=_('btn_shop'),         callback_data="rewards:shop")
    builder.button(text=_('btn_back'),         callback_data="menu:main")
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def shop_categories_kb(_: Callable) -> InlineKeyboardMarkup:
    """Beautiful i18n shop categories."""
    builder = InlineKeyboardBuilder()
    builder.button(text=_('btn_shop_badges'),   callback_data="shop:badges")
    builder.button(text=_('btn_shop_titles'),   callback_data="shop:titles")
    builder.button(text=_('btn_shop_frames'),   callback_data="shop:frames")
    builder.button(text=_('btn_shop_lootboxes'),callback_data="shop:lootboxes")
    builder.button(text=_('btn_shop_cosmetics'),callback_data="shop:cosmetics")
    builder.button(text=_('btn_back'),          callback_data="menu:rewards")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def missions_kb(_: Callable) -> InlineKeyboardMarkup:
    """Beautiful i18n missions menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text=_('btn_missions_daily'),  callback_data="missions:daily")
    builder.button(text=_('btn_missions_weekly'), callback_data="missions:weekly")
    builder.button(text=_('btn_missions_monthly'),callback_data="missions:monthly")
    builder.button(text=_('btn_back'),            callback_data="menu:rewards")
    builder.adjust(3, 1)
    return builder.as_markup()
