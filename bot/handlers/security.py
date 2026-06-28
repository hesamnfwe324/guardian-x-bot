from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.security import security_menu_kb, locks_menu_kb, captcha_menu_kb
import structlog

logger = structlog.get_logger()
router = Router()


async def _is_admin(message_or_callback, db_session, _) -> bool:
    obj = message_or_callback
    chat = obj.chat if hasattr(obj, 'chat') else obj.message.chat
    user = obj.from_user
    if chat.type == 'private':
        await (obj.answer if hasattr(obj, 'answer') else obj.message.answer)(_('error_admin_only'))
        return False
    try:
        member = await obj.bot.get_chat_member(chat.id, user.id)
        if member.status not in ('administrator', 'creator'):
            await (obj.answer if hasattr(obj, 'answer') else obj.message.answer)(_('error_admin_only'))
            return False
    except Exception:
        return False
    return True


# ─── /security ────────────────────────────────────────────
@router.message(Command('security'))
async def cmd_security(message: Message, _: callable, db_session: AsyncSession = None, **kwargs):
    if message.chat.type == 'private':
        await message.answer(_('error_admin_only'))
        return
    try:
        member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status not in ('administrator', 'creator'):
            await message.answer(_('error_admin_only'))
            return
    except Exception:
        return
    await message.answer(_('security_menu_title'), reply_markup=security_menu_kb(_), parse_mode='HTML')


@router.callback_query(F.data.startswith('sec:'))
async def security_section(callback: CallbackQuery, _: callable, db_session: AsyncSession = None, **kwargs):
    action = callback.data.split('sec:')[1]
    if action == 'locks':
        await callback.message.edit_text(_('locks_menu'), reply_markup=locks_menu_kb(_), parse_mode='HTML')
    elif action == 'captcha':
        await callback.message.edit_text(_('captcha_menu'), reply_markup=captcha_menu_kb(_), parse_mode='HTML')
    elif action == 'antiflood':
        await callback.message.edit_text(_('feature_coming'), parse_mode='HTML')
    elif action == 'antispam':
        await callback.message.edit_text(_('feature_coming'), parse_mode='HTML')
    else:
        await callback.message.edit_text(_('security_menu_title'), reply_markup=security_menu_kb(_), parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data.startswith('lock:'))
async def toggle_lock(callback: CallbackQuery, _: callable, db_session: AsyncSession = None, **kwargs):
    lock_type = callback.data.split('lock:')[1]
    from bot.database.models import Group
    group = await db_session.get(Group, callback.message.chat.id) if db_session else None
    if group:
        current = getattr(group, f'lock_{lock_type}', False)
        setattr(group, f'lock_{lock_type}', not current)
        await db_session.flush()
        status = _('enabled') if not current else _('disabled')
        await callback.answer(f'{lock_type}: {status}', show_alert=True)
    else:
        await callback.answer(_('no_data'), show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=locks_menu_kb(_))


@router.callback_query(F.data.startswith('captcha:'))
async def toggle_captcha(callback: CallbackQuery, _: callable, db_session: AsyncSession = None, **kwargs):
    setting = callback.data.split('captcha:')[1]
    from bot.database.models import Group
    group = await db_session.get(Group, callback.message.chat.id) if db_session else None
    if group:
        current = getattr(group, f'captcha_{setting}', False)
        setattr(group, f'captcha_{setting}', not current)
        await db_session.flush()
        status = _('enabled') if not current else _('disabled')
        await callback.answer(f'{setting}: {status}', show_alert=True)
    else:
        await callback.answer(_('no_data'), show_alert=True)


# ─── /lock /unlock ────────────────────────────────────────
@router.message(Command('lock', 'unlock'))
async def cmd_lock(message: Message, _: callable, db_session: AsyncSession = None, **kwargs):
    if message.chat.type == 'private':
        await message.answer(_('error_admin_only'))
        return
    try:
        member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status not in ('administrator', 'creator'):
            await message.answer(_('error_admin_only'))
            return
    except Exception:
        return
    cmd = message.text.split()[0].lstrip('/').split('@')[0]
    args = message.text.split()[1:]
    lock_type = args[0] if args else None
    is_locking = cmd == 'lock'
    if not lock_type:
        await message.answer('/lock <type>\n/unlock <type>\n\nانواع: text, media, sticker, link')
        return
    await message.reply(f"{'🔒' if is_locking else '🔓'} {lock_type} {'قفل شد' if is_locking else 'باز شد'}")
