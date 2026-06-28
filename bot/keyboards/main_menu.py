from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
  from aiogram.utils.keyboard import InlineKeyboardBuilder
  from typing import Callable


  def language_selection_kb() -> InlineKeyboardMarkup:
      builder = InlineKeyboardBuilder()
      languages = [
          ("🇬🇧 English", "lang:en"),
          ("🇮🇷 فارسی", "lang:fa"),
          ("🇸🇦 العربية", "lang:ar"),
          ("🇹🇷 Türkçe", "lang:tr"),
          ("🇷🇺 Русский", "lang:ru"),
          ("🇪🇸 Español", "lang:es"),
          ("🇫🇷 Français", "lang:fr"),
          ("🇩🇪 Deutsch", "lang:de"),
      ]
      for text, callback in languages:
          builder.button(text=text, callback_data=callback)
      builder.adjust(2)
      return builder.as_markup()


  def main_menu_kb(_: Callable) -> InlineKeyboardMarkup:
      """Private chat main menu — premium layout."""
      builder = InlineKeyboardBuilder()
      builder.button(text=_("btn_security"),    callback_data="menu:security")
      builder.button(text=_("btn_moderation"),  callback_data="menu:moderation")
      builder.button(text=_("btn_economy"),     callback_data="menu:economy")
      builder.button(text=_("btn_rewards"),     callback_data="menu:rewards")
      builder.button(text=_("btn_levels"),      callback_data="menu:levels")
      builder.button(text=_("btn_reputation"),  callback_data="menu:reputation")
      builder.button(text=_("btn_games"),       callback_data="menu:games")
      builder.button(text=_("btn_duels"),       callback_data="menu:duels")
      builder.button(text=_("btn_tournaments"), callback_data="menu:tournaments")
      builder.button(text=_("btn_statistics"),  callback_data="menu:statistics")
      builder.button(text=_("btn_channel"),     callback_data="menu:channel")
      builder.button(text=_("btn_settings"),    callback_data="menu:settings")
      builder.button(text=_("btn_language"),    callback_data="menu:language")
      builder.button(text=_("btn_help"),        callback_data="menu:help")
      builder.button(text=_("btn_support"),     url="https://t.me/VPS24H")
      builder.adjust(2, 2, 2, 3, 2, 3, 1)
      return builder.as_markup()


  def group_main_menu_kb(_: Callable) -> InlineKeyboardMarkup:
      """Group inline admin panel — shows all management categories."""
      builder = InlineKeyboardBuilder()
      builder.button(text=_("btn_security"),    callback_data="menu:security")
      builder.button(text=_("btn_moderation"),  callback_data="menu:moderation")
      builder.button(text=_("btn_statistics"),  callback_data="menu:statistics")
      builder.button(text=_("btn_economy"),     callback_data="menu:economy")
      builder.button(text=_("btn_games"),       callback_data="menu:games")
      builder.button(text=_("btn_levels"),      callback_data="menu:levels")
      builder.button(text=_("btn_channel"),     callback_data="menu:channel")
      builder.button(text=_("btn_settings"),    callback_data="menu:settings")
      builder.button(text=_("btn_language"),    callback_data="menu:language")
      builder.button(text=_("btn_help"),        callback_data="menu:help")
      builder.adjust(2, 2, 2, 2, 2)
      return builder.as_markup()


  def nav_kb(_: Callable, back_to: str = "menu:main", refresh_data: str = None) -> InlineKeyboardMarkup:
      """Standard navigation bar: Back · Home · Refresh."""
      builder = InlineKeyboardBuilder()
      builder.button(text=_("btn_back"), callback_data=back_to)
      # Determine home based on context (group vs private)
      builder.button(text=_("btn_home"), callback_data="menu:main")
      if refresh_data:
          builder.button(text=_("btn_refresh"), callback_data=refresh_data)
      builder.adjust(3 if refresh_data else 2)
      return builder.as_markup()


  def back_button_kb(_: Callable, back_to: str = "menu:main") -> InlineKeyboardMarkup:
      """Simple back + home."""
      builder = InlineKeyboardBuilder()
      builder.button(text=_("btn_back"), callback_data=back_to)
      builder.button(text=_("btn_home"), callback_data="menu:main")
      builder.adjust(2)
      return builder.as_markup()


  def confirm_cancel_kb(_: Callable, confirm_data: str, cancel_data: str) -> InlineKeyboardMarkup:
      builder = InlineKeyboardBuilder()
      builder.button(text=_("btn_confirm"), callback_data=confirm_data)
      builder.button(text=_("btn_cancel"),  callback_data=cancel_data)
      builder.adjust(2)
      return builder.as_markup()


  def toggle_button(label: str, enabled: bool, callback: str, _: Callable) -> InlineKeyboardButton:
      icon = "🟢" if enabled else "🔴"
      status = _("btn_enabled") if enabled else _("btn_disabled")
      return InlineKeyboardButton(
          text=f"{icon} {label}: {status}",
          callback_data=callback
      )


  def action_selector_kb(_: Callable, prefix: str, back_to: str = "menu:security") -> InlineKeyboardMarkup:
      builder = InlineKeyboardBuilder()
      actions = [
          (_("btn_action_delete"), f"{prefix}:delete"),
          (_("btn_action_warn"),   f"{prefix}:warn"),
          (_("btn_action_mute"),   f"{prefix}:mute"),
          (_("btn_action_kick"),   f"{prefix}:kick"),
          (_("btn_action_ban"),    f"{prefix}:ban"),
      ]
      for text, cb in actions:
          builder.button(text=text, callback_data=cb)
      builder.button(text=_("btn_back"), callback_data=back_to)
      builder.button(text=_("btn_home"), callback_data="menu:main")
      builder.adjust(2, 2, 1, 2)
      return builder.as_markup()
  