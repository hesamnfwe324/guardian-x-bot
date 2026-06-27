from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, delete
from aiogram import Bot
from aiogram.types import ChatPermissions
from bot.database.models import (
    GroupMember, Warning, UserNote, ActionLog, GroupSettings
)
import structlog

logger = structlog.get_logger()

FULL_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_audios=True,
    can_send_documents=True,
    can_send_photos=True,
    can_send_videos=True,
    can_send_video_notes=True,
    can_send_voice_notes=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
    can_change_info=False,
    can_invite_users=True,
    can_pin_messages=False,
)

MUTED_PERMISSIONS = ChatPermissions(
    can_send_messages=False,
    can_send_audios=False,
    can_send_documents=False,
    can_send_photos=False,
    can_send_videos=False,
    can_send_video_notes=False,
    can_send_voice_notes=False,
    can_send_polls=False,
    can_send_other_messages=False,
)


async def log_action(
    session: AsyncSession,
    group_id: int,
    action: str,
    user_id: Optional[int] = None,
    admin_id: Optional[int] = None,
    details: Optional[dict] = None,
    message_id: Optional[int] = None,
) -> None:
    log = ActionLog(
        group_id=group_id,
        user_id=user_id,
        admin_id=admin_id,
        action=action,
        details=details,
        message_id=message_id,
    )
    session.add(log)


async def ban_user(
    bot: Bot,
    session: AsyncSession,
    group_id: int,
    user_id: int,
    admin_id: int,
    reason: str = "",
    until: Optional[datetime] = None,
) -> bool:
    try:
        await bot.ban_chat_member(
            chat_id=group_id,
            user_id=user_id,
            until_date=until,
        )
        member = await session.scalar(
            select(GroupMember).where(
                and_(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
            )
        )
        if member:
            member.is_banned = True
            member.ban_reason = reason
        await log_action(session, group_id, "ban", user_id, admin_id, {"reason": reason})
        return True
    except Exception as e:
        logger.error("Ban failed", error=str(e), user_id=user_id, group_id=group_id)
        return False


async def unban_user(
    bot: Bot,
    session: AsyncSession,
    group_id: int,
    user_id: int,
    admin_id: int,
) -> bool:
    try:
        await bot.unban_chat_member(chat_id=group_id, user_id=user_id, only_if_banned=True)
        member = await session.scalar(
            select(GroupMember).where(
                and_(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
            )
        )
        if member:
            member.is_banned = False
            member.ban_reason = None
        await log_action(session, group_id, "unban", user_id, admin_id)
        return True
    except Exception as e:
        logger.error("Unban failed", error=str(e))
        return False


async def kick_user(
    bot: Bot,
    session: AsyncSession,
    group_id: int,
    user_id: int,
    admin_id: int,
    reason: str = "",
) -> bool:
    try:
        await bot.ban_chat_member(chat_id=group_id, user_id=user_id)
        await bot.unban_chat_member(chat_id=group_id, user_id=user_id)
        await log_action(session, group_id, "kick", user_id, admin_id, {"reason": reason})
        return True
    except Exception as e:
        logger.error("Kick failed", error=str(e))
        return False


async def mute_user(
    bot: Bot,
    session: AsyncSession,
    group_id: int,
    user_id: int,
    admin_id: int,
    duration: Optional[int] = None,
    reason: str = "",
) -> bool:
    try:
        until = None
        until_dt = None
        if duration and duration > 0:
            until_dt = datetime.now(timezone.utc) + timedelta(seconds=duration)
            until = until_dt
        await bot.restrict_chat_member(
            chat_id=group_id,
            user_id=user_id,
            permissions=MUTED_PERMISSIONS,
            until_date=until,
        )
        member = await session.scalar(
            select(GroupMember).where(
                and_(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
            )
        )
        if member:
            member.is_muted = True
            member.mute_until = until_dt
        await log_action(session, group_id, "mute", user_id, admin_id, {"duration": duration, "reason": reason})
        return True
    except Exception as e:
        logger.error("Mute failed", error=str(e))
        return False


async def unmute_user(
    bot: Bot,
    session: AsyncSession,
    group_id: int,
    user_id: int,
    admin_id: int,
) -> bool:
    try:
        await bot.restrict_chat_member(
            chat_id=group_id,
            user_id=user_id,
            permissions=FULL_PERMISSIONS,
        )
        member = await session.scalar(
            select(GroupMember).where(
                and_(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
            )
        )
        if member:
            member.is_muted = False
            member.mute_until = None
        await log_action(session, group_id, "unmute", user_id, admin_id)
        return True
    except Exception as e:
        logger.error("Unmute failed", error=str(e))
        return False


async def warn_user(
    session: AsyncSession,
    group_id: int,
    user_id: int,
    admin_id: int,
    reason: str = "",
    max_warns: int = 3,
) -> tuple[int, bool]:
    warning = Warning(
        group_id=group_id,
        user_id=user_id,
        admin_id=admin_id,
        reason=reason,
    )
    session.add(warning)
    member = await session.scalar(
        select(GroupMember).where(
            and_(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        )
    )
    if member:
        member.warn_count = (member.warn_count or 0) + 1
        warn_count = member.warn_count
    else:
        warn_count_result = await session.scalar(
            select(func.count()).where(
                and_(Warning.group_id == group_id, Warning.user_id == user_id)
            )
        )
        warn_count = warn_count_result or 1
    await log_action(session, group_id, "warn", user_id, admin_id, {"reason": reason})
    return warn_count, warn_count >= max_warns


async def unwarn_user(
    session: AsyncSession,
    group_id: int,
    user_id: int,
) -> bool:
    latest = await session.scalar(
        select(Warning)
        .where(and_(Warning.group_id == group_id, Warning.user_id == user_id))
        .order_by(Warning.created_at.desc())
    )
    if not latest:
        return False
    await session.delete(latest)
    member = await session.scalar(
        select(GroupMember).where(
            and_(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        )
    )
    if member and member.warn_count > 0:
        member.warn_count -= 1
    return True


async def get_user_warnings(session: AsyncSession, group_id: int, user_id: int) -> list:
    result = await session.execute(
        select(Warning)
        .where(and_(Warning.group_id == group_id, Warning.user_id == user_id))
        .order_by(Warning.created_at.desc())
    )
    return result.scalars().all()


async def add_note(
    session: AsyncSession,
    group_id: int,
    user_id: int,
    admin_id: int,
    note: str,
) -> None:
    n = UserNote(group_id=group_id, user_id=user_id, admin_id=admin_id, note=note)
    session.add(n)


async def get_notes(session: AsyncSession, group_id: int, user_id: int) -> list:
    result = await session.execute(
        select(UserNote)
        .where(and_(UserNote.group_id == group_id, UserNote.user_id == user_id))
        .order_by(UserNote.created_at.desc())
    )
    return result.scalars().all()


async def get_user_history(session: AsyncSession, group_id: int, user_id: int) -> dict:
    from bot.database.models import GroupMember
    member = await session.scalar(
        select(GroupMember).where(
            and_(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        )
    )
    logs = await session.execute(
        select(ActionLog)
        .where(and_(ActionLog.group_id == group_id, ActionLog.user_id == user_id))
        .order_by(ActionLog.created_at.desc())
        .limit(20)
    )
    warnings = await get_user_warnings(session, group_id, user_id)
    return {
        "member": member,
        "logs": logs.scalars().all(),
        "warnings": warnings,
    }
