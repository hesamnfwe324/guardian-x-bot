from aiogram import Router, F
  from aiogram.types import Message, CallbackQuery
  from aiogram.filters import CommandStart, Command
  from aiogram.utils.keyboard import InlineKeyboardBuilder
  from sqlalchemy.ext.asyncio import AsyncSession
  from bot.keyboards.main_menu import language_selection_kb, main_menu_kb
  from bot.config import settings
  from bot.middlewares.i18n import get_text
  import structlog

  logger = structlog.get_logger()
  router = Router()


  @router.message(CommandStart())
  async def cmd_start(message: Message, _: callable, db_session: AsyncSession = None, db_user=None, lang: str = "en"):
      if message.chat.type != "private":
          try:
              bot_info = await message.bot.get_me()
              bot_username = bot_info.username
          except Exception:
              bot_username = "GuardianXBot"
          builder = InlineKeyboardBuilder()
          builder.button(
              text="🤖 باز کردن پنل ربات" if lang == "fa" else "🤖 Open Bot Panel",
              url=f"https://t.me/{bot_username}?start=from_group"
          )
          group_text = (
              "👋 برای مشاهده پنل کامل ربات، روی دکمه زیر کلیک کنید:"
              if lang == "fa"
              else "👋 Click the button below to open the bot panel in private chat:"
          )
          await message.answer(group_text, reply_markup=builder.as_markup())
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

      await message.answer(
          _("select_language"),
          reply_markup=language_selection_kb(),
      )


  @router.callback_query(F.data.startswith("lang:"))
  async def set_language(callback: CallbackQuery, db_session: AsyncSession = None, db_user=None, _: callable = None, lang: str = "en"):
      selected_lang = callback.data.split(":")[1]
      if selected_lang not in settings.SUPPORTED_LANGUAGES:
          if callable(_):
              await callback.answer(_("error_generic") if _ else "Invalid language", show_alert=True)
          return

      if db_session and db_user:
          db_user.language = selected_lang
          await db_session.flush()

      new_ = lambda key, **kw: get_text(selected_lang, key, **kw)
      name = callback.from_user.first_name or "کاربر"
      welcome_text = new_("welcome_bot").replace("{name}", name) if "{name}" in new_("welcome_bot") else new_("welcome_bot")

      try:
          await callback.message.edit_text(
              welcome_text,
              reply_markup=main_menu_kb(new_),
              parse_mode="HTML",
          )
      except Exception:
          await callback.message.answer(
              welcome_text,
              reply_markup=main_menu_kb(new_),
              parse_mode="HTML",
          )
      await callback.answer(new_("language_set"))


  @router.callback_query(F.data == "menu:main")
  async def main_menu(callback: CallbackQuery, _: callable, **kwargs):
      await callback.message.edit_text(
          _("main_menu"),
          reply_markup=main_menu_kb(_),
          parse_mode="HTML",
      )
      await callback.answer()


  @router.callback_query(F.data == "menu:language")
  async def change_language(callback: CallbackQuery, _: callable, **kwargs):
      await callback.message.edit_text(
          _("select_language"),
          reply_markup=language_selection_kb(),
      )
      await callback.answer()


  @router.callback_query(F.data == "menu:channel")
  async def channel_info(callback: CallbackQuery, _: callable, **kwargs):
      from bot.keyboards.main_menu import back_button_kb
      text = (
          "📢 <b>کانال رسمی گاردیان X</b>\n\n"
          "آخرین اخبار، بروزرسانی‌ها و اطلاعیه‌ها را دنبال کنید!\n\n"
          "🔔 همین الان عضو شوید: @VPS24H"
      ) if kwargs.get("lang") == "fa" else (
          "📢 <b>Official Channel</b>\n\n"
          "Follow us for the latest news and updates!\n\n"
          "🔔 Join now: @VPS24H"
      )
      await callback.message.edit_text(text, reply_markup=back_button_kb(_), parse_mode="HTML")
      await callback.answer()


  @router.callback_query(F.data == "menu:tournaments")
  async def tournaments_menu(callback: CallbackQuery, _: callable, **kwargs):
      from bot.keyboards.main_menu import back_button_kb
      text = (
          "🏆 <b>تورنمنت‌ها</b>\n\n"
          "🚧 <b>به زودی!</b>\n\n"
          "با گروه‌های دیگر رقابت کنید!\n"
          "• 🎮 تورنمنت بازی‌ها\n"
          "• ⚔️ قهرمانی مبارزه\n"
          "• 🏅 جوایز و پاداش‌ها"
      ) if kwargs.get("lang") == "fa" else (
          "🏆 <b>Tournaments</b>\n\n"
          "🚧 <b>Coming Soon!</b>\n\n"
          "Compete with other groups!\n"
          "• 🎮 Game tournaments\n"
          "• ⚔️ Duel championships\n"
          "• 🏅 Prize pools & rewards"
      )
      await callback.message.edit_text(text, reply_markup=back_button_kb(_), parse_mode="HTML")
      await callback.answer()


  @router.message(Command("menu"))
  async def cmd_menu(message: Message, _: callable, **kwargs):
      if message.chat.type != "private":
          return
      await message.answer(
          _("main_menu"),
          reply_markup=main_menu_kb(_),
          parse_mode="HTML",
      )
  