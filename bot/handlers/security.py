from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.database.models import Group, SecuritySettings
from bot.keyboards.security import security_menu_kb, locks_menu_kb, captcha_menu_kb
import structlog

logger = structlog.get_logger()
router = Router()


async def _get_or_create_security(db_session: AsyncSession, chat_id: int) -> SecuritySettings:
    security = await db_session.scalar(select(SecuritySettings).where(SecuritySettings.group_id == chat_id))
    if not security:
        security = SecuritySettings(group_id=chat_id)
        db_session.add(security)
        await db_session.flush()
    return security


async def _is_admin(message_or_callback, _) -> bool:
    obj = message_or_callback
    chat = obj.chat if hasattr(obj, 'chat') else obj.message.chat
    user = obj.from_user
    if chat.type == 'private':
        return False
    try:
        member = await obj.bot.get_chat_member(chat.id, user.id)
        if member.status not in ('administrator', 'creator'):
            return False
    except Exception:
        return False
    return True


#  /security 
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
    if db_session:
        security = await _get_or_create_security(db_session, message.chat.id)
        await message.answer(_('security_menu_title'), reply_markup=security_menu_kb(_, security), parse_mode='HTML')
    else:
        await message.answer(_('error_generic'))


@router.callback_query(F.data == "menu:security")
async def security_menu_cb(callback: CallbackQuery, _: callable, db_session: AsyncSession = None, **kwargs):
    if callback.message.chat.type == 'private':
        await callback.answer(_('error_admin_only'), show_alert=True)
        return
    try:
        member = await callback.bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
        if member.status not in ('administrator', 'creator'):
            await callback.answer(_('error_admin_only'), show_alert=True)
            return
    except Exception:
        await callback.answer()
        return
    if db_session:
        security = await _get_or_create_security(db_session, callback.message.chat.id)
        await callback.message.edit_text(_('security_menu_title'), reply_markup=security_menu_kb(_, security), parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data == "sec:menu")
async def security_section_back(callback: CallbackQuery, _: callable, db_session: AsyncSession = None, **kwargs):
    if db_session:
        security = await _get_or_create_security(db_session, callback.message.chat.id)
        await callback.message.edit_text(_('security_menu_title'), reply_markup=security_menu_kb(_, security), parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data.startswith('sec:'))
async def security_section(callback: CallbackQuery, _: callable, db_session: AsyncSession = None, **kwargs):
    action = callback.data.split('sec:', 1)[1]

    if not db_session:
        await callback.answer(_('error_generic'), show_alert=True)
        return

    security = await _get_or_create_security(db_session, callback.message.chat.id)

    # Toggle boolean security settings
    toggle_map = {
        'anti_spam': 'anti_spam',
        'anti_flood': 'anti_flood',
        'anti_raid': 'anti_raid',
        'anti_bot': 'anti_bot',
        'anti_fake': 'anti_fake',
        'anti_ad': 'anti_advertisement',
        'anti_link': 'anti_link',
        'anti_mention': 'anti_mention_spam',
        'anti_forward': 'anti_forward_spam',
        'anti_emoji': 'anti_emoji_spam',
        'anti_hashtag': 'anti_hashtag_spam',
        'anti_phone': 'anti_phone',
        'anti_scam': 'anti_scam',
        'anti_crypto': 'anti_crypto_scam',
        'anti_nsfw': 'anti_nsfw',
        'anti_invite': 'anti_invite',
        'anti_promo': 'anti_channel_promo',
        'anti_mass_join': 'anti_mass_join',
        'captcha': 'captcha_enabled',
        'emergency': 'emergency_mode',
    }

    if action in toggle_map:
        field = toggle_map[action]
        current = getattr(security, field, False)
        setattr(security, field, not current)
        status = _('enabled') if not current else _('disabled')
        await callback.answer(f"{action}: {status}", show_alert=False)
        await callback.message.edit_reply_markup(reply_markup=security_menu_kb(_, security))
    elif action == 'locks':
        await callback.message.edit_text(_('locks_menu'), reply_markup=locks_menu_kb(_, security), parse_mode='HTML')
    elif action in ('antiflood', 'antispam', 'advanced'):
        await callback.message.edit_text(_('feature_coming'), parse_mode='HTML')
    else:
        await callback.answer(_('feature_coming'), show_alert=True)

    await callback.answer()


@router.callback_query(F.data.startswith('lock:'))
async def toggle_lock(callback: CallbackQuery, _: callable, db_session: AsyncSession = None, **kwargs):
    if not db_session:
        await callback.answer(_('error_generic'), show_alert=True)
        return
    lock_type = callback.data.split('lock:', 1)[1]
    security = await _get_or_create_security(db_session, callback.message.chat.id)

    field_map = {
        'text': 'lock_text', 'links': 'lock_links', 'photos': 'lock_photos',
        'videos': 'lock_videos', 'gifs': 'lock_gifs', 'audio': 'lock_audio',
        'voice': 'lock_voice', 'docs': 'lock_documents', 'polls': 'lock_polls',
        'games': 'lock_games', 'bots': 'lock_bots', 'forwards': 'lock_forwards',
        'contacts': 'lock_contacts', 'locations': 'lock_locations',
        'stickers': 'lock_stickers', 'inline': 'lock_inline',
        'mentions': 'lock_mentions', 'hashtags': 'lock_hashtags',
    }
    field = field_map.get(lock_type)
    if field:
        current = getattr(security, field, False)
        setattr(security, field, not current)
        status = _('enabled') if not current else _('disabled')
        await callback.answer(f"{lock_type}: {status}", show_alert=False)
        await callback.message.edit_reply_markup(reply_markup=locks_menu_kb(_, security))
    else:
        await callback.answer(_('no_data'), show_alert=True)


@router.callback_query(F.data.startswith('captcha:'))
async def toggle_captcha(callback: CallbackQuery, _: callable, db_session: AsyncSession = None, **kwargs):
    if not db_session:
        await callback.answer(_('error_generic'), show_alert=True)
        return
    parts = callback.data.split(':', 2)
    action = parts[1] if len(parts) > 1 else ''
    security = await _get_or_create_security(db_session, callback.message.chat.id)

    if action == 'toggle':
        security.captcha_enabled = not security.captcha_enabled
        status = _('enabled') if security.captcha_enabled else _('disabled')
        await callback.answer(f"Captcha: {status}")
    elif action == 'type' and len(parts) > 2:
        captcha_type = parts[2]
        security.captcha_type = captcha_type
        await callback.answer(f"Captcha type: {captcha_type}")
    else:
        await callback.answer(_('feature_coming'), show_alert=True)

    await callback.message.edit_reply_markup(reply_markup=captcha_menu_kb(_, security))


#  /lock /unlock 
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
        await message.answer(_('lock_usage'), parse_mode='HTML')
        return
    if db_session:
        security = await _get_or_create_security(db_session, message.chat.id)
        field_map = {
            'text': 'lock_text', 'link': 'lock_links', 'links': 'lock_links',
            'photo': 'lock_photos', 'photos': 'lock_photos', 'video': 'lock_videos',
            'videos': 'lock_videos', 'sticker': 'lock_stickers', 'stickers': 'lock_stickers',
        }
        field = field_map.get(lock_type.lower())
        if field:
            setattr(security, field, is_locking)
    await message.reply(_('lock_locked').format(type=lock_type) if is_locking else _('lock_unlocked').format(type=lock_type))
