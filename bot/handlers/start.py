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


@router.message(CommandStart())
async def cmd_start(message: Message, _: callable, db_session: AsyncSession = None, db_user=None, **kwargs):
    if message.chat.type != 'private':
        await message.answer('✅ ربات فعال است. دستور /help را بزنید.')
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
    else:
        name = message.from_user.first_name or 'User'
        text = _('welcome_bot').replace('{name}', name)
        await message.answer(text, parse_mode='HTML')


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
    welcome_text = new_('welcome_bot').replace('{name}', name)

    await callback.message.edit_text(welcome_text, parse_mode='HTML')
    await callback.answer(new_('language_set'))


@router.message(Command('language', 'lang'))
async def cmd_language(message: Message, _: callable, **kwargs):
    await message.answer(_('select_language'), reply_markup=language_selection_kb())
