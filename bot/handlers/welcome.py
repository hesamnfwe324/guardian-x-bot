from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated, ChatPermissions
from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from bot.database.models import (
    Group, GroupMember, GroupSettings, WelcomeSettings,
    SecuritySettings, CaptchaChallenge, GroupStats, User
)
from bot.services.security_service import (
    check_message_violations, is_raid_detected, create_captcha_challenge
)
from bot.services.moderation_service import mute_user, ban_user, kick_user, warn_user, log_action
from bot.services.user_service import add_xp
from bot.middlewares.i18n import get_text
from bot.utils.helpers import safe_username, mention_user
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timezone
import structlog

logger = structlog.get_logger()
router = Router()


@router.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_new_member(event: ChatMemberUpdated, db_session: AsyncSession, **kwargs):
    user = event.new_chat_member.user
    chat = event.chat
    if user.is_bot:
        return

    group = await db_session.get(Group, chat.id)
    if not group:
        return

    lang = group.language or "en"
    _ = lambda key, **kw: get_text(lang, key, **kw)

    security = await db_session.scalar(select(SecuritySettings).where(SecuritySettings.group_id == chat.id))

    if security and security.anti_raid:
        redis = kwargs.get("redis_client") or getattr(event.bot, "_redis_client", None)
        if redis:
            from bot.services.security_service import is_raid_detected
            raid = await is_raid_detected(
                redis,
                chat.id,
                threshold=security.anti_raid_threshold or 10,
                window=security.anti_raid_window or 60,
            )
            if raid:
                logger.warning("Raid detected, rejecting join", chat_id=chat.id, user_id=user.id)
                try:
                    await event.bot.ban_chat_member(chat.id, user.id)
                    await event.bot.unban_chat_member(chat.id, user.id)
                except Exception:
                    pass
                return

    if security and security.captcha_enabled:
        await _handle_captcha(event, db_session, security, user, chat, _)
        return

    ws = await db_session.scalar(select(WelcomeSettings).where(WelcomeSettings.group_id == chat.id))
    if ws and ws.enabled and ws.message:
        welcome_text = ws.message
        replacements = {
            "{name}": user.first_name or "User",
            "{username}": f"@{user.username}" if user.username else user.first_name,
            "{id}": str(user.id),
            "{group}": chat.title or "Group",
        }
        for key, val in replacements.items():
            welcome_text = welcome_text.replace(key, val)

        try:
            await event.bot.send_message(chat.id, welcome_text, parse_mode="HTML")
        except Exception as e:
            logger.warning("Welcome message failed", error=str(e))

    gs = await db_session.scalar(select(GroupStats).where(GroupStats.group_id == chat.id))
    if gs:
        gs.total_joins = (gs.total_joins or 0) + 1

    gs_settings = await db_session.scalar(select(GroupSettings).where(GroupSettings.group_id == chat.id))
    if gs_settings and gs_settings.log_join and gs_settings.log_channel_id:
        try:
            name = mention_user(user.id, safe_username(user))
            await event.bot.send_message(
                gs_settings.log_channel_id,
                f"📥 {name} joined {chat.title}",
                parse_mode="HTML",
            )
        except Exception:
            pass


async def _handle_captcha(event, db_session, security, user, chat, _):
    challenge = await create_captcha_challenge(
        db_session, chat.id, user.id, security.captcha_type or "button", security.captcha_timeout or 60
    )
    try:
        await mute_user(event.bot, db_session, chat.id, user.id, event.bot.id, 300, "Pending captcha verification")
    except Exception:
        pass

    if security.captcha_type == "math":
        from bot.services.security_service import generate_math_question
        import random
        question, math_answer = generate_math_question()
        challenge.answer = math_answer
        text = _("captcha_question").format(question=question)
        builder = InlineKeyboardBuilder()
        correct_val = int(math_answer)
        options = [correct_val]
        while len(options) < 4:
            offset = random.randint(-5, 5)
            candidate = correct_val + offset
            if candidate != correct_val and candidate not in options and candidate > 0:
                options.append(candidate)
        random.shuffle(options)
        for opt in options:
            builder.button(text=str(opt), callback_data=f"captcha_verify:{chat.id}:{user.id}:{opt}")
        builder.adjust(2)
        try:
            msg = await event.bot.send_message(chat.id, text, parse_mode="HTML", reply_markup=builder.as_markup())
            challenge.message_id = msg.message_id
        except Exception as e:
            logger.error("Captcha message failed", error=str(e))
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text=_("btn_verify"), callback_data=f"captcha_verify:{chat.id}:{user.id}:button")
        try:
            name = mention_user(user.id, safe_username(user))
            text = f"{name}, {_('verification_required')}"
            msg = await event.bot.send_message(chat.id, text, parse_mode="HTML", reply_markup=builder.as_markup())
            challenge.message_id = msg.message_id
        except Exception as e:
            logger.error("Captcha message failed", error=str(e))


@router.callback_query(F.data.startswith("captcha_verify:"))
async def captcha_verify(callback, db_session: AsyncSession, **kwargs):
    parts = callback.data.split(":")
    if len(parts) < 4:
        return
    group_id = int(parts[1])
    user_id = int(parts[2])
    answer = parts[3]

    if callback.from_user.id != user_id:
        await callback.answer("This captcha is not for you!", show_alert=True)
        return

    from bot.services.security_service import verify_captcha
    success = await verify_captcha(db_session, group_id, user_id, answer)

    group = await db_session.get(Group, group_id)
    lang = group.language if group else "en"
    _ = lambda key, **kw: get_text(lang, key, **kw)

    if success:
        try:
            from bot.services.moderation_service import FULL_PERMISSIONS
            await callback.bot.restrict_chat_member(
                chat_id=group_id,
                user_id=user_id,
                permissions=FULL_PERMISSIONS,
            )
        except Exception:
            pass
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.answer(_("verification_success"), show_alert=True)
    else:
        try:
            await callback.bot.ban_chat_member(chat_id=group_id, user_id=user_id)
            await callback.bot.unban_chat_member(chat_id=group_id, user_id=user_id)
        except Exception:
            pass
        await callback.answer(_("verification_failed"), show_alert=True)


@router.chat_member(ChatMemberUpdatedFilter(LEAVE_TRANSITION))
async def on_member_left(event: ChatMemberUpdated, db_session: AsyncSession, **kwargs):
    user = event.old_chat_member.user
    chat = event.chat
    if user.is_bot:
        return

    gs = await db_session.scalar(select(GroupStats).where(GroupStats.group_id == chat.id))
    if gs:
        gs.total_leaves = (gs.total_leaves or 0) + 1

    group = await db_session.get(Group, chat.id)
    if not group:
        return
    gs_settings = await db_session.scalar(select(GroupSettings).where(GroupSettings.group_id == chat.id))
    if gs_settings and gs_settings.log_leave and gs_settings.log_channel_id:
        try:
            name = safe_username(user)
            await event.bot.send_message(
                gs_settings.log_channel_id,
                f"📤 {name} left {chat.title}",
            )
        except Exception:
            pass


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def group_message_handler(message: Message, db_session: AsyncSession, db_user=None, db_group=None, group_security=None, _=None, **kwargs):
    if not db_user or not db_group or not group_security:
        return
    if message.from_user.is_bot:
        return

    violations = await check_message_violations(message, group_security)
    if violations:
        action = group_security.spam_action or "delete"
        if action == "delete":
            try:
                await message.delete()
            except Exception:
                pass
        elif action == "warn":
            gs = await db_session.scalar(select(GroupSettings).where(GroupSettings.group_id == db_group.id))
            max_warns = gs.max_warns if gs else 3
            count, reached = await warn_user(db_session, db_group.id, db_user.id, message.bot.id, violations[0], max_warns)
            try:
                await message.delete()
            except Exception:
                pass
        elif action in ("mute", "ban", "kick"):
            try:
                await message.delete()
            except Exception:
                pass
            if action == "mute":
                await mute_user(message.bot, db_session, db_group.id, db_user.id, message.bot.id, 3600, violations[0])
            elif action == "ban":
                await ban_user(message.bot, db_session, db_group.id, db_user.id, message.bot.id, violations[0])
            elif action == "kick":
                await kick_user(message.bot, db_session, db_group.id, db_user.id, message.bot.id, violations[0])
        return

    flood_detected = kwargs.get("flood_detected", False)
    if flood_detected:
        action = group_security.flood_action or "mute"
        try:
            await message.delete()
        except Exception:
            pass
        if action == "mute":
            await mute_user(message.bot, db_session, db_group.id, db_user.id, message.bot.id, 300, "Flood")
        elif action == "ban":
            await ban_user(message.bot, db_session, db_group.id, db_user.id, message.bot.id, "Flood")
        return

    from sqlalchemy import and_
    member = await db_session.scalar(
        select(GroupMember).where(
            and_(GroupMember.group_id == db_group.id, GroupMember.user_id == db_user.id)
        )
    )
    if member:
        member.message_count = (member.message_count or 0) + 1
        from datetime import datetime, timezone
        member.last_activity = datetime.now(timezone.utc)

    gs_settings = await db_session.scalar(select(GroupSettings).where(GroupSettings.group_id == db_group.id))
    if gs_settings and gs_settings.xp_enabled:
        from bot.config import settings
        _, _, leveled_up = await add_xp(db_session, db_user.id, settings.ACTIVITY_XP_PER_MSG)
        if leveled_up:
            from bot.services.user_service import get_or_create_economy
            eco = await get_or_create_economy(db_session, db_user.id)
            try:
                name = mention_user(db_user.id, safe_username(db_user))
                await message.answer(
                    _("level_up").format(name=name, level=eco.level),
                    parse_mode="HTML",
                )
            except Exception:
                pass

    gs_stats = await db_session.scalar(select(GroupStats).where(GroupStats.group_id == db_group.id))
    if not gs_stats:
        gs_stats = GroupStats(group_id=db_group.id, total_messages=1)
        db_session.add(gs_stats)
    else:
        gs_stats.total_messages = (gs_stats.total_messages or 0) + 1
