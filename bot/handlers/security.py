from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.database.models import SecuritySettings, Group
from bot.keyboards.security import security_menu_kb, locks_menu_kb, captcha_menu_kb
from bot.keyboards.main_menu import back_button_kb
from bot.filters.admin import AdminFilter
import structlog

logger = structlog.get_logger()
router = Router()

TOGGLE_FIELDS = {
    "anti_spam": "anti_spam",
    "anti_flood": "anti_flood",
    "anti_raid": "anti_raid",
    "anti_bot": "anti_bot",
    "anti_fake": "anti_fake",
    "anti_ad": "anti_advertisement",
    "anti_link": "anti_link",
    "anti_mention": "anti_mention_spam",
    "anti_username": "anti_username_spam",
    "anti_forward": "anti_forward_spam",
    "anti_emoji": "anti_emoji_spam",
    "anti_hashtag": "anti_hashtag_spam",
    "anti_phone": "anti_phone",
    "anti_scam": "anti_scam",
    "anti_crypto": "anti_crypto_scam",
    "anti_nsfw": "anti_nsfw",
    "anti_invite": "anti_invite",
    "anti_promo": "anti_channel_promo",
    "anti_mass_join": "anti_mass_join",
}

LOCK_FIELDS = {
    "text": "lock_text",
    "links": "lock_links",
    "photos": "lock_photos",
    "videos": "lock_videos",
    "gifs": "lock_gifs",
    "audio": "lock_audio",
    "voice": "lock_voice",
    "docs": "lock_documents",
    "polls": "lock_polls",
    "games": "lock_games",
    "bots": "lock_bots",
    "forwards": "lock_forwards",
    "contacts": "lock_contacts",
    "locations": "lock_locations",
    "stickers": "lock_stickers",
    "inline": "lock_inline",
    "mentions": "lock_mentions",
    "hashtags": "lock_hashtags",
}


async def get_or_create_security(session: AsyncSession, group_id: int) -> SecuritySettings:
    sec = await session.scalar(select(SecuritySettings).where(SecuritySettings.group_id == group_id))
    if not sec:
        sec = SecuritySettings(group_id=group_id)
        session.add(sec)
        await session.flush()
    return sec


@router.callback_query(F.data == "menu:security")
async def security_menu(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if not db_group:
        await callback.answer(_("error_group_only"), show_alert=True)
        return
    security = await get_or_create_security(db_session, db_group.id)
    await callback.message.edit_text(
        _("security_menu"),
        reply_markup=security_menu_kb(_, security),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "sec:menu")
async def security_menu_back(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if not db_group:
        await callback.answer(_("error_group_only"), show_alert=True)
        return
    security = await get_or_create_security(db_session, db_group.id)
    await callback.message.edit_text(
        _("security_menu"),
        reply_markup=security_menu_kb(_, security),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sec:"))
async def security_toggle(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_group, db_user, **kwargs):
    if not db_group:
        await callback.answer(_("error_group_only"), show_alert=True)
        return

    action = callback.data.split("sec:", 1)[1]
    security = await get_or_create_security(db_session, db_group.id)

    if action in TOGGLE_FIELDS:
        field = TOGGLE_FIELDS[action]
        current = getattr(security, field, False)
        setattr(security, field, not current)
        status = "✅ Enabled" if not current else "❌ Disabled"
        await callback.answer(f"{field}: {status}")
        await callback.message.edit_reply_markup(reply_markup=security_menu_kb(_, security))

    elif action == "locks":
        await callback.message.edit_text(
            _("lock_menu"),
            reply_markup=locks_menu_kb(_, security),
            parse_mode="HTML",
        )
        await callback.answer()

    elif action == "captcha":
        await callback.message.edit_text(
            _("captcha_menu").format(status="✅" if security.captcha_enabled else "❌"),
            reply_markup=captcha_menu_kb(_, security),
            parse_mode="HTML",
        )
        await callback.answer()

    elif action == "emergency":
        security.emergency_mode = not security.emergency_mode
        status = "🚨 ACTIVATED" if security.emergency_mode else "✅ Deactivated"
        await callback.answer(status)
        await callback.message.edit_reply_markup(reply_markup=security_menu_kb(_, security))

    elif action == "advanced":
        text = "⚔️ <b>Advanced Protection</b>\n\nFeatures: Quarantine Mode, Trusted Users, Whitelist, Blacklist, Join Rate Limiter, Anti-Raid Lockdown"
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "sec:menu"))
        await callback.answer()


@router.callback_query(F.data.startswith("lock:"))
async def lock_toggle(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if not db_group:
        await callback.answer(_("error_group_only"), show_alert=True)
        return

    lock_type = callback.data.split("lock:", 1)[1]
    security = await get_or_create_security(db_session, db_group.id)

    if lock_type in LOCK_FIELDS:
        field = LOCK_FIELDS[lock_type]
        current = getattr(security, field, False)
        setattr(security, field, not current)
        status = "🔒 Locked" if not current else "🔓 Unlocked"
        await callback.answer(f"{lock_type}: {status}")
        await callback.message.edit_reply_markup(reply_markup=locks_menu_kb(_, security))


@router.callback_query(F.data.startswith("captcha:"))
async def captcha_settings(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if not db_group:
        await callback.answer(_("error_group_only"), show_alert=True)
        return

    parts = callback.data.split(":")
    security = await get_or_create_security(db_session, db_group.id)

    if parts[1] == "toggle":
        security.captcha_enabled = not security.captcha_enabled
        await callback.answer(_("btn_enabled") if security.captcha_enabled else _("btn_disabled"))
        await callback.message.edit_reply_markup(reply_markup=captcha_menu_kb(_, security))
    elif parts[1] == "type" and len(parts) > 2:
        security.captcha_type = parts[2]
        await callback.answer(_("captcha_set").format(type=parts[2]))
        await callback.message.edit_reply_markup(reply_markup=captcha_menu_kb(_, security))


@router.message(Command("lock", "unlock"))
async def cmd_lock(message: Message, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if not db_group or message.chat.type == "private":
        return
    security = await get_or_create_security(db_session, db_group.id)
    await message.answer(
        _("lock_menu"),
        reply_markup=locks_menu_kb(_, security),
        parse_mode="HTML",
    )
