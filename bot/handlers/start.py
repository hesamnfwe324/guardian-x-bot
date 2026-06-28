from aiogram import Router, F
  from aiogram.types import Message, CallbackQuery
  from aiogram.filters import CommandStart, Command
  from aiogram.utils.keyboard import InlineKeyboardBuilder
  from sqlalchemy.ext.asyncio import AsyncSession
  from bot.keyboards.main_menu import language_selection_kb, main_menu_kb, group_main_menu_kb, nav_kb
  from bot.config import settings
  from bot.middlewares.i18n import get_text
  import structlog

  logger = structlog.get_logger()
  router = Router()


  @router.message(CommandStart())
  async def cmd_start(message: Message, _: callable, db_session: AsyncSession = None, db_user=None, lang: str = "en"):
      if message.chat.type != "private":
          try:
              member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
              is_admin = member.status in ("administrator", "creator")
          except Exception:
              is_admin = False

          from bot.database.models import Group
          group_lang = "en"
          if db_session:
              grp = await db_session.get(Group, message.chat.id)
              if grp:
                  group_lang = grp.language or "en"
          if db_user and db_user.language:
              group_lang = db_user.language

          group_ = lambda key, **kw: get_text(group_lang, key, **kw)
          group_title = message.chat.title or "Group"

          if not is_admin:
              await message.answer(group_("error_admin_only"))
              return

          text = group_("group_panel_title").format(title=group_title)
          await message.answer(text, reply_markup=group_main_menu_kb(group_), parse_mode="HTML")
          return

      if db_session and db_user:
          args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
          if args.startswith("ref_"):
              try:
                  referrer_id = int(args[4:])
                  if referrer_id != message.from_user.id:
                      from bot.services.economy_service import process_referral
                      await process_referral(db_session, referrer_id=referrer_id, new_user_id=db_user.id)
              except Exception:
                  pass

      await message.answer(_("select_language"), reply_markup=language_selection_kb())


  @router.callback_query(F.data.startswith("lang:"))
  async def set_language(callback: CallbackQuery, db_session: AsyncSession = None, db_user=None, _: callable = None, lang: str = "en"):
      selected_lang = callback.data.split(":")[1]
      if selected_lang not in settings.SUPPORTED_LANGUAGES:
          await callback.answer("Invalid language", show_alert=True)
          return

      if db_session and db_user:
          db_user.language = selected_lang
          await db_session.flush()

      new_ = lambda key, **kw: get_text(selected_lang, key, **kw)
      name = callback.from_user.first_name or "User"
      welcome_text = new_("welcome_bot").replace("{name}", name)

      try:
          await callback.message.edit_text(welcome_text, reply_markup=main_menu_kb(new_), parse_mode="HTML")
      except Exception:
          await callback.message.answer(welcome_text, reply_markup=main_menu_kb(new_), parse_mode="HTML")
      await callback.answer(new_("language_set"))


  @router.callback_query(F.data == "menu:main")
  async def main_menu(callback: CallbackQuery, _: callable, **kwargs):
      if callback.message.chat.type in ("group", "supergroup"):
          group_title = callback.message.chat.title or "Group"
          try:
              await callback.message.edit_text(
                  _("group_panel_title").format(title=group_title),
                  reply_markup=group_main_menu_kb(_),
                  parse_mode="HTML",
              )
          except Exception:
              pass
      else:
          try:
              await callback.message.edit_text(_("main_menu"), reply_markup=main_menu_kb(_), parse_mode="HTML")
          except Exception:
              pass
      await callback.answer()


  @router.callback_query(F.data == "group:main")
  async def group_main_menu_cb(callback: CallbackQuery, _: callable, **kwargs):
      group_title = callback.message.chat.title or "Group"
      try:
          await callback.message.edit_text(
              _("group_panel_title").format(title=group_title),
              reply_markup=group_main_menu_kb(_),
              parse_mode="HTML",
          )
      except Exception:
          pass
      await callback.answer()


  @router.callback_query(F.data == "menu:language")
  async def change_language(callback: CallbackQuery, _: callable, **kwargs):
      await callback.message.edit_text(_("select_language"), reply_markup=language_selection_kb())
      await callback.answer()


  @router.callback_query(F.data == "menu:channel")
  async def channel_info(callback: CallbackQuery, _: callable, **kwargs):
      text = _("channel_info_text")
      await callback.message.edit_text(text, reply_markup=nav_kb(_, "menu:main"), parse_mode="HTML")
      await callback.answer()


  @router.callback_query(F.data == "menu:tournaments")
  async def tournaments_menu(callback: CallbackQuery, _: callable, db_session: AsyncSession = None, db_user=None, **kwargs):
      from bot.handlers.tournaments import render_tournaments_menu
      await render_tournaments_menu(callback, _)


  @router.message(Command("menu"))
  async def cmd_menu(message: Message, _: callable, **kwargs):
      if message.chat.type != "private":
          return
      await message.answer(_("main_menu"), reply_markup=main_menu_kb(_), parse_mode="HTML")
  