from aiogram import Router, F
  from aiogram.types import Message, CallbackQuery
  from aiogram.filters import CommandStart, Command
  from sqlalchemy.ext.asyncio import AsyncSession
  from bot.config import settings
  import structlog

  logger = structlog.get_logger()
  router = Router()

  COMMANDS_FA = (
      "👋 سلام {name}!\n\n"
      "📋 دستورات موجود:\n\n"
      "💰 اقتصاد:\n"
      "  /wallet — کیف پول\n"
      "  /daily — جایزه روزانه\n"
      "  /weekly — جایزه هفتگی\n"
      "  /monthly — جایزه ماهانه\n"
      "  /transfer — انتقال سکه\n"
      "  /referral — لینک دعوت\n\n"
      "🎮 بازی‌ها:\n"
      "  /dice — تاس\n"
      "  /rps — سنگ کاغذ قیچی\n"
      "  /quiz — مسابقه\n"
      "  /wheel — چرخ شانس\n"
      "  /roulette — رولت\n"
      "  /duel — دوئل\n\n"
      "🛡️ مدیریت (در گروه):\n"
      "  /security — تنظیمات امنیتی\n"
      "  /settings — تنظیمات گروه\n"
      "  /stats — آمار گروه\n"
      "  /language — تغییر زبان\n\n"
      "❓ راهنما:\n"
      "  /help — لیست کامل دستورات"
  )

  COMMANDS_EN = (
      "👋 Hello {name}!\n\n"
      "📋 Available commands:\n\n"
      "💰 Economy:\n"
      "  /wallet — wallet and balance\n"
      "  /daily — daily reward\n"
      "  /weekly — weekly reward\n"
      "  /monthly — monthly reward\n"
      "  /transfer — transfer coins\n"
      "  /referral — referral link\n\n"
      "🎮 Games:\n"
      "  /dice — dice roll\n"
      "  /rps — rock paper scissors\n"
      "  /quiz — quiz game\n"
      "  /wheel — wheel of fortune\n"
      "  /roulette — roulette\n"
      "  /duel — duel\n\n"
      "🛡️ Management (in group):\n"
      "  /security — security settings\n"
      "  /settings — group settings\n"
      "  /stats — group statistics\n"
      "  /language — change language\n\n"
      "❓ Help:\n"
      "  /help — full command list"
  )


  def _get_commands(lang: str, name: str) -> str:
      if lang == "fa":
          return COMMANDS_FA.format(name=name)
      return COMMANDS_EN.format(name=name)


  def _detect_lang(telegram_lang: str | None) -> str:
      if not telegram_lang:
          return "fa"
      code = telegram_lang.split("-")[0].lower()
      if code in settings.SUPPORTED_LANGUAGES:
          return code
      return "fa"


  @router.message(CommandStart())
  async def cmd_start(message: Message, _: callable, db_session: AsyncSession = None, db_user=None, **kwargs):
      if message.chat.type != "private":
          await message.answer("✅ ربات فعال است. دستور /help را بزنید.")
          return

      args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
      if args.startswith("ref_") and db_session and db_user:
          try:
              referrer_id = int(args[4:])
              if referrer_id != message.from_user.id:
                  from bot.services.economy_service import process_referral
                  await process_referral(db_session, referrer_id=referrer_id, new_user_id=db_user.id)
          except Exception:
              pass

      if db_user and db_user.language:
          lang = db_user.language
      else:
          lang = _detect_lang(message.from_user.language_code)
          if db_session and db_user:
              db_user.language = lang
              try:
                  await db_session.flush()
              except Exception:
                  pass

      name = message.from_user.first_name or "User"
      await message.answer(_get_commands(lang, name))


  @router.message(Command("language", "lang"))
  async def cmd_language(message: Message, _: callable, **kwargs):
      text = (
          "🌐 زبان خود را انتخاب کنید / Select your language:\n\n"
          "/setlang_fa — 🇮🇷 فارسی\n"
          "/setlang_en — 🇬🇧 English\n"
          "/setlang_ar — 🇸🇦 عربی\n"
          "/setlang_tr — 🇹🇷 Türkçe\n"
          "/setlang_ru — 🇷🇺 Русский\n"
      )
      await message.answer(text)


  @router.message(F.text.startswith("/setlang_"))
  async def set_language_cmd(message: Message, _: callable, db_session: AsyncSession = None, db_user=None, **kwargs):
      lang = message.text.replace("/setlang_", "").strip()
      if lang not in settings.SUPPORTED_LANGUAGES:
          await message.answer("❌ زبان نامعتبر است.")
          return
      if db_session and db_user:
          db_user.language = lang
          try:
              await db_session.flush()
          except Exception:
              pass
      name = message.from_user.first_name or "User"
      await message.answer(_get_commands(lang, name))


  @router.callback_query(F.data.startswith("lang:"))
  async def lang_callback_fallback(callback: CallbackQuery, db_session: AsyncSession = None, db_user=None, **kwargs):
      lang = callback.data.split(":")[1]
      if lang in settings.SUPPORTED_LANGUAGES and db_session and db_user:
          db_user.language = lang
          try:
              await db_session.flush()
          except Exception:
              pass
      name = callback.from_user.first_name or "User"
      effective = lang if lang in settings.SUPPORTED_LANGUAGES else "fa"
      await callback.message.edit_text(_get_commands(effective, name))
      await callback.answer()


  @router.callback_query(F.data.startswith("menu:"))
  async def menu_fallback(callback: CallbackQuery, **kwargs):
      await callback.answer()


  @router.callback_query(F.data == "group:main")
  async def group_main_refresh(callback: CallbackQuery, **kwargs):
      await callback.answer()
  