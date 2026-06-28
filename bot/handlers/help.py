from aiogram import Router, F
  from aiogram.types import CallbackQuery, Message
  from aiogram.filters import Command
  from aiogram.utils.keyboard import InlineKeyboardBuilder
  from bot.keyboards.main_menu import nav_kb
  import structlog

  logger = structlog.get_logger()
  router = Router()


  def help_kb(_):
      builder = InlineKeyboardBuilder()
      builder.button(text=_("btn_help_security"),   callback_data="help:security")
      builder.button(text=_("btn_help_moderation"), callback_data="help:moderation")
      builder.button(text=_("btn_help_economy"),    callback_data="help:economy")
      builder.button(text=_("btn_help_games"),      callback_data="help:games")
      builder.button(text=_("btn_help_commands"),   callback_data="help:commands")
      builder.button(text=_("btn_help_duels"),      callback_data="help:duels")
      builder.button(text=_("btn_back"),            callback_data="menu:main")
      builder.button(text=_("btn_home"),            callback_data="menu:main")
      builder.button(text=_("btn_support"),         url="https://t.me/VPS24H")
      builder.adjust(2, 2, 2, 2, 1)
      return builder.as_markup()


  @router.callback_query(F.data == "menu:help")
  async def help_menu(callback: CallbackQuery, _: callable, **kwargs):
      await callback.message.edit_text(_("help_menu"), reply_markup=help_kb(_), parse_mode="HTML")
      await callback.answer()


  @router.callback_query(F.data == "help:security")
  async def help_security(callback: CallbackQuery, _: callable, **kwargs):
      await callback.message.edit_text(_("help_security_text"), reply_markup=nav_kb(_, "menu:help"), parse_mode="HTML")
      await callback.answer()


  @router.callback_query(F.data == "help:moderation")
  async def help_moderation(callback: CallbackQuery, _: callable, **kwargs):
      await callback.message.edit_text(_("help_moderation_text"), reply_markup=nav_kb(_, "menu:help"), parse_mode="HTML")
      await callback.answer()


  @router.callback_query(F.data == "help:economy")
  async def help_economy(callback: CallbackQuery, _: callable, **kwargs):
      await callback.message.edit_text(_("help_economy_text"), reply_markup=nav_kb(_, "menu:help"), parse_mode="HTML")
      await callback.answer()


  @router.callback_query(F.data == "help:games")
  async def help_games(callback: CallbackQuery, _: callable, **kwargs):
      await callback.message.edit_text(_("help_games_text"), reply_markup=nav_kb(_, "menu:help"), parse_mode="HTML")
      await callback.answer()


  @router.callback_query(F.data == "help:commands")
  async def help_commands(callback: CallbackQuery, _: callable, **kwargs):
      await callback.message.edit_text(_("help_commands_text"), reply_markup=nav_kb(_, "menu:help"), parse_mode="HTML")
      await callback.answer()


  @router.callback_query(F.data == "help:duels")
  async def help_duels(callback: CallbackQuery, _: callable, **kwargs):
      await callback.message.edit_text(_("help_duels_text"), reply_markup=nav_kb(_, "menu:help"), parse_mode="HTML")
      await callback.answer()


  @router.callback_query(F.data == "help:gameslist")
  async def help_gameslist(callback: CallbackQuery, _: callable, **kwargs):
      await callback.message.edit_text(_("help_gameslist_text"), reply_markup=nav_kb(_, "menu:help"), parse_mode="HTML")
      await callback.answer()


  @router.callback_query(F.data == "help:achievements")
  async def help_achievements(callback: CallbackQuery, _: callable, **kwargs):
      await callback.message.edit_text(_("help_achievements_text"), reply_markup=nav_kb(_, "menu:help"), parse_mode="HTML")
      await callback.answer()
  