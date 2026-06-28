from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.main_menu import language_selection_kb, main_menu_kb, group_main_menu_kb
from bot.config import settings
from bot.middlewares.i18n import get_text
import structlog

logger = structlog.get_logger()
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, _: callable, db_session: AsyncSession = None, db_user=None, **kwargs):
    if message.chat.type != 'private':
        title = message.chat.title or 'Group'
        group_text = _('group_panel_title').replace('{title}', title)
        await message.answer(
            group_text,
            parse_mode='HTML',
            reply_markup=group_main_menu_kb(_),
        )
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
        await message.answer(text, parse_mode='HTML', reply_markup=main_menu_kb(_))


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

    await callback.message.edit_text(welcome_text, parse_mode='HTML', reply_markup=main_menu_kb(new_))
    await callback.answer(new_('language_set'))


@router.message(Command('language', 'lang'))
async def cmd_language(message: Message, _: callable, **kwargs):
    await message.answer(_('select_language'), reply_markup=language_selection_kb())


# ─── Main menu navigation ─────────────────────────────────

@router.callback_query(F.data == "menu:main")
async def main_menu_back(callback: CallbackQuery, _: callable, **kwargs):
    name = callback.from_user.first_name or 'User'
    text = _('welcome_bot').replace('{name}', name)
    try:
        await callback.message.edit_text(text, parse_mode='HTML', reply_markup=main_menu_kb(_))
    except Exception:
        await callback.message.answer(text, parse_mode='HTML', reply_markup=main_menu_kb(_))
    await callback.answer()


@router.callback_query(F.data == "group:main")
async def group_main_refresh(callback: CallbackQuery, _: callable, **kwargs):
    try:
        await callback.message.edit_reply_markup(reply_markup=group_main_menu_kb(_))
    except Exception:
        pass
    await callback.answer('✅ Refreshed')


@router.callback_query(F.data == "menu:economy")
async def menu_economy(callback: CallbackQuery, _: callable, **kwargs):
    text = _('economy_menu')
    from bot.keyboards.economy import economy_menu_kb
    from bot.keyboards.main_menu import back_button_kb
    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=economy_menu_kb(_))
    await callback.answer()


@router.callback_query(F.data == "menu:games")
async def menu_games(callback: CallbackQuery, _: callable, **kwargs):
    text = _('games_menu')
    from bot.keyboards.games import games_menu_kb
    from bot.keyboards.main_menu import back_button_kb
    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=games_menu_kb(_))
    await callback.answer()


@router.callback_query(F.data == "menu:reputation")
async def menu_reputation(callback: CallbackQuery, _: callable, db_session: AsyncSession = None, db_user=None, **kwargs):
    text = '✨ ┌─────────────────────────┐\n  🌟 <b>سیستم اعتبار شیشه‌ای</b>\n✨ ┣━━━━━━━━━━━━━━━━━━━━━━━━━┫\n'
    if db_session and db_user:
        from sqlalchemy import select
        from bot.database.models import Reputation
        rep = await db_session.scalar(select(Reputation).where(Reputation.user_id == db_user.id))
        pos = rep.positive if rep else 0
        neg = rep.negative if rep else 0
        text += f'  👍 مثبت: <b>{pos}</b>\n  👎 منفی: <b>{neg}</b>\n  📊 خالص: <b>{pos - neg}</b>\n✨ └─────────────────────────┘'
    else:
        text += '  ' + _('no_data') + '\n✨ └─────────────────────────┘'
    from bot.keyboards.main_menu import back_button_kb
    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=back_button_kb(_, 'menu:main'))
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def menu_help(callback: CallbackQuery, _: callable, **kwargs):
    from bot.handlers.help import HELP_TEXT
    from bot.keyboards.main_menu import back_button_kb
    await callback.message.edit_text(HELP_TEXT, parse_mode='HTML', reply_markup=back_button_kb(_, 'menu:main'))
    await callback.answer()


@router.callback_query(F.data == "menu:language")
async def menu_language(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(_('select_language'), reply_markup=language_selection_kb())
    await callback.answer()


@router.callback_query(F.data == "menu:channel")
async def menu_channel(callback: CallbackQuery, _: callable, **kwargs):
    await callback.answer('🔗 کانال ربات به زودی معرفی می‌شود!', show_alert=True)
