from aiogram import Router, F
  from aiogram.types import Message, CallbackQuery
  from aiogram.filters import CommandStart, Command
  from sqlalchemy.ext.asyncio import AsyncSession
  from bot.keyboards.main_menu import language_selection_kb
  from bot.config import settings
  from bot.middlewares.i18n import get_text
  import structlog

  logger = structlog.get_logger()
  router = Router()

  COMMANDS_FA = """
  👋 سلام {name}!

  📋 دستورات موجود:

  💰 اقتصاد:
    /wallet — کیف پول
    /daily — جایزه روزانه
    /weekly — جایزه هفتگی
    /monthly — جایزه ماهانه
    /transfer — انتقال سکه
    /referral — لینک دعوت

  🎮 بازی‌ها:
    /dice — تاس
    /rps — سنگ کاغذ قیچی
    /quiz — مسابقه
    /wheel — چرخ شانس
    /roulette — رولت
    /duel — دوئل

  🛡️ مدیریت (در گروه):
    /security — تنظیمات امنیتی
    /settings — تنظیمات گروه
    /stats — آمار گروه
    /language — زبان

  ❓ راهنما:
    /help — لیست کامل دستورات
  """

  COMMANDS_EN = """
  👋 Hello {name}!

  📋 Available commands:

  💰 Economy:
    /wallet — wallet and balance
    /daily — daily reward
    /weekly — weekly reward
    /monthly — monthly reward
    /transfer — transfer coins
    /referral — referral link

  🎮 Games:
    /dice — dice roll
    /rps — rock paper scissors
    /quiz — quiz game
    /wheel — wheel of fortune
    /roulette — roulette
    /duel — duel

  🛡️ Management (in group):
    /security — security settings
    /settings — group settings
    /stats — group statistics
    /language — language

  ❓ Help:
    /help — full command list
  """


  @router.message(CommandStart())
  async def cmd_start(message: Message, _: callable, db_session: AsyncSession = None, db_user=None, **kwargs):
      if message.chat.type != 'private':
          title = message.chat.title or 'Group'
          group_text = _('group_panel_title').replace('{title}', title)
          await message.answer(group_text, parse_mode='HTML')
          return

      if db_session and db_user:
          args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ''
          if args.startswith('ref_'):
              try:
                  referrer_id = int(args[4:])
                  if referrer_id != message.from_user.id:
                      from bot.services.economy_service import process_referral
                      await process_referral(db_session, referrer_id=referrer_id, new_user_id=db_user.id)
              except Exception:
                  pass

      if not db_user or not db_user.language:
          await message.answer(_('select_language'), reply_markup=language_selection_kb())
          return

      name = message.from_user.first_name or 'User'
      lang = db_user.language if db_user else 'en'
      if lang == 'fa':
          text = COMMANDS_FA.format(name=name)
      else:
          text = COMMANDS_EN.format(name=name)
      await message.answer(text)


  @router.callback_query(F.data.startswith('lang:'))
  async def set_language(callback: CallbackQuery, db_session: AsyncSession = None, db_user=None, _: callable = None, **kwargs):
      selected_lang = callback.data.split(':')[1]
      if selected_lang not in settings.SUPPORTED_LANGUAGES:
          await callback.answer('Invalid language', show_alert=True)
          return

      if db_session and db_user:
          db_user.language = selected_lang
          await db_session.flush()

      new_ = lambda key, **kw: get_text(selected_lang, key, **kw)
      name = callback.from_user.first_name or 'User'

      if selected_lang == 'fa':
          text = COMMANDS_FA.format(name=name)
      else:
          text = COMMANDS_EN.format(name=name)

      await callback.message.edit_text(text)
      await callback.answer(new_('language_set'))


  @router.message(Command('language', 'lang'))
  async def cmd_language(message: Message, _: callable, **kwargs):
      await message.answer(_('select_language'), reply_markup=language_selection_kb())


  @router.callback_query(F.data.startswith('menu:'))
  async def menu_fallback(callback: CallbackQuery, **kwargs):
      await callback.answer()


  @router.callback_query(F.data == "group:main")
  async def group_main_refresh(callback: CallbackQuery, **kwargs):
      await callback.answer()
  