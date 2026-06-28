from aiogram.types import InlineKeyboardMarkup
  from aiogram.utils.keyboard import InlineKeyboardBuilder
  from typing import Callable


  def economy_menu_kb(_: Callable) -> InlineKeyboardMarkup:
      builder = InlineKeyboardBuilder()
      builder.button(text=_('btn_wallet'),       callback_data="eco:wallet")
      builder.button(text=_('btn_bank'),         callback_data="eco:bank")
      builder.button(text=_('btn_daily'),        callback_data="eco:daily")
      builder.button(text=_('btn_weekly'),       callback_data="eco:weekly")
      builder.button(text=_('btn_monthly'),      callback_data="eco:monthly")
      builder.button(text=_('btn_referral'),     callback_data="eco:referral")
      builder.button(text=_('btn_transactions'), callback_data="eco:transactions")
      builder.button(text=_('btn_back'),         callback_data="menu:main")
      builder.adjust(2, 3, 2, 1)
      return builder.as_markup()


  def wallet_kb(_: Callable) -> InlineKeyboardMarkup:
      builder = InlineKeyboardBuilder()
      builder.button(text=_('btn_deposit'),  callback_data="eco:deposit")
      builder.button(text=_('btn_withdraw'), callback_data="eco:withdraw")
      builder.button(text=_('btn_transfer'), callback_data="eco:transfer")
      builder.button(text=_('btn_back'),     callback_data="menu:economy")
      builder.adjust(3, 1)
      return builder.as_markup()


  def rewards_menu_kb(_: Callable) -> InlineKeyboardMarkup:
      builder = InlineKeyboardBuilder()
      builder.button(text=_('btn_my_achievements'), callback_data="rewards:achievements")
      builder.button(text=_('btn_daily_missions'),  callback_data="rewards:missions")
      builder.button(text=_('btn_shop'),            callback_data="rewards:shop")
      builder.button(text=_('btn_back'),            callback_data="menu:main")
      builder.adjust(2, 1, 1)
      return builder.as_markup()


  def shop_categories_kb(_: Callable) -> InlineKeyboardMarkup:
      builder = InlineKeyboardBuilder()
      builder.button(text=_('btn_badges'),     callback_data="shop:badges")
      builder.button(text=_('btn_titles'),     callback_data="shop:titles")
      builder.button(text=_('btn_frames'),     callback_data="shop:frames")
      builder.button(text=_('btn_loot_boxes'), callback_data="shop:lootboxes")
      builder.button(text=_('btn_cosmetics'),  callback_data="shop:cosmetics")
      builder.button(text=_('btn_back'),       callback_data="menu:rewards")
      builder.adjust(2, 2, 1, 1)
      return builder.as_markup()


  def missions_kb(_: Callable) -> InlineKeyboardMarkup:
      builder = InlineKeyboardBuilder()
      builder.button(text=_('btn_daily_missions'),   callback_data="missions:daily")
      builder.button(text=_('btn_weekly_missions'),  callback_data="missions:weekly")
      builder.button(text=_('btn_monthly_missions'), callback_data="missions:monthly")
      builder.button(text=_('btn_back'),             callback_data="menu:rewards")
      builder.adjust(3, 1)
      return builder.as_markup()
  