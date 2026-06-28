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

COMMANDS_FA = (
    "\U0001f44b سلام {name}!\n\n"
    "U0001f4cb دستورات موجود:\n\n"
    "U0001f4b0 اقتصاد:\n"
    "  /wallet — کیف پول\n"
    "  /daily — جایزه روزانه\n"
    "  /weekly — جایزه هفتگی\n"
    "  /monthly — جایزه ماهانه\n"
    "  /transfer — انتقال سکه\n"
    "  /referral — لینک دعوت\n\n"
    "U0001f3ae بازی‌ها:\n"
    "  /dice — تاس\n"
    "  /rps — سنگ کاغذ قیچی\n"
    "  /quiz — مسابقه\n"
    "  /wheel — چرخ شانس\n"
    "  /roulette — رولت\n"
    "  /duel — دوئل\n\n"
    "U0001f6e1️ مدیریت (در گروه):\n"
    "  /security — تنظیمات امنیتی\n"
    "  /settings — تنظیمات گروه\n"
    "  /stats — آمار گروه\n"
    "  /language — زبان\n\n"
    "❓ راهنما:\n"
    "  /help — لیست کامل دستورات"
)

COMMANDS_EN = (
    "\U0001f44b Hello {name}!\n\n"
    "U0001f4cb Available commands:\n\n"
    "U0001f4b0 Economy:\n"
    "  /wallet \u2014 wallet and balance\n"
    "  /daily \u2014 daily reward\n"
    "  /weekly \u2014 weekly reward\n"
    "  /monthly \u2014 monthly reward\n"
    "  /transfer \u2014 transfer coins\n"
    "  /referral \u2014 referral link\n\n"
    "U0001f3ae Games:\n"
    "  /dice \u2014 dice roll\n"
    "  /rps \u2014 rock paper scissors\n"
    "  /quiz \u2014 quiz game\n"
    "  /wheel \u2014 wheel of fortune\n"
    "  /roulette \u2014 roulette\n"
    "  /duel \u2014 duel\n\n"
    "U0001f6e1️ Management (in group):\n"
    "  /security \u2014 security settings\n"
    "  /settings \u2014 group settings\n"
    "  /stats \u2014 group statistics\n"
    "  /language \u2014 language\n\n"
    "\u2753 Help:\n"
    "  /help \u2014 full command list"
)


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


@router.callback_query(F.data == 'group:main')
async def group_main_refresh(callback: CallbackQuery, **kwargs):
    await callback.answer()
