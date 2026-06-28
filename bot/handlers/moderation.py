from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from bot.database.models import User, GroupMember, GroupSettings
from bot.keyboards.moderation import moderation_menu_kb, mute_duration_kb, warn_actions_kb
from bot.keyboards.main_menu import back_button_kb
from bot.services.moderation_service import (
    ban_user, unban_user, kick_user, mute_user, unmute_user,
    warn_user, unwarn_user, get_user_warnings, get_user_history, add_note, get_notes
)
from bot.utils.helpers import format_duration, mention_user, safe_username
import structlog

logger = structlog.get_logger()
router = Router()


async def get_target_user(message: Message, session: AsyncSession) -> tuple:
    target = None
    reason = ""
    if message.reply_to_message:
        tg_user = message.reply_to_message.from_user
        target = await session.get(User, tg_user.id)
        if not target:
            target = User(id=tg_user.id, first_name=tg_user.first_name or "User", username=tg_user.username)
        args = message.text.split(None, 1)[1] if len(message.text.split()) > 1 else ""
        reason = args
    elif len(message.text.split()) > 1:
        parts = message.text.split(None, 2)
        identifier = parts[1]
        reason = parts[2] if len(parts) > 2 else ""
        if identifier.startswith("@"):
            target = await session.scalar(select(User).where(User.username == identifier[1:]))
        else:
            try:
                uid = int(identifier)
                target = await session.get(User, uid)
            except ValueError:
                pass
    return target, reason


async def moderation_menu(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(
        _("moderation_menu"),
        reply_markup=moderation_menu_kb(_),
        parse_mode="HTML",
    )
    await callback.answer()


async def moderation_menu_back(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(
        _("moderation_menu"),
        reply_markup=moderation_menu_kb(_),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("ban"))
async def cmd_ban(message: Message, bot: Bot, _: callable, db_session: AsyncSession, db_group, db_user, **kwargs):
    if message.chat.type == "private":
        await message.reply(_("error_group_only"))
        return
    target, reason = await get_target_user(message, db_session)
    if not target:
        await message.reply(_("provide_user"))
        return
    success = await ban_user(bot, db_session, message.chat.id, target.id, message.from_user.id, reason)
    if success:
        name = mention_user(target.id, safe_username(target))
        await message.reply(_("user_banned").format(name=name, reason=reason or _("no_reason")), parse_mode="HTML")


@router.message(Command("unban"))
async def cmd_unban(message: Message, bot: Bot, _: callable, db_session: AsyncSession, **kwargs):
    if message.chat.type == "private":
        return
    target, _ = await get_target_user(message, db_session)
    if not target:
        await message.reply(_("provide_user"))
        return
    success = await unban_user(bot, db_session, message.chat.id, target.id, message.from_user.id)
    if success:
        await message.reply(_("user_unbanned").format(name=safe_username(target)))


@router.message(Command("kick"))
async def cmd_kick(message: Message, bot: Bot, _: callable, db_session: AsyncSession, **kwargs):
    if message.chat.type == "private":
        return
    target, reason = await get_target_user(message, db_session)
    if not target:
        await message.reply(_("provide_user"))
        return
    success = await kick_user(bot, db_session, message.chat.id, target.id, message.from_user.id, reason)
    if success:
        name = mention_user(target.id, safe_username(target))
        await message.reply(_("user_kicked").format(name=name, reason=reason or _("no_reason")), parse_mode="HTML")


@router.message(Command("mute"))
async def cmd_mute(message: Message, bot: Bot, _: callable, db_session: AsyncSession, **kwargs):
    if message.chat.type == "private":
        return
    target, args = await get_target_user(message, db_session)
    if not target:
        await message.reply(_("provide_user"))
        return

    from bot.utils.helpers import parse_duration
    duration = None
    reason = args
    if args:
        parts = args.split(None, 1)
        dur = parse_duration(parts[0])
        if dur:
            duration = dur
            reason = parts[1] if len(parts) > 1 else ""

    success = await mute_user(bot, db_session, message.chat.id, target.id, message.from_user.id, duration, reason)
    if success:
        name = mention_user(target.id, safe_username(target))
        dur_str = format_duration(duration) if duration else "Forever"
        await message.reply(
            _("user_muted").format(name=name, duration=dur_str, reason=reason or _("no_reason")),
            parse_mode="HTML",
        )


@router.message(Command("unmute"))
async def cmd_unmute(message: Message, bot: Bot, _: callable, db_session: AsyncSession, **kwargs):
    if message.chat.type == "private":
        return
    target, _ = await get_target_user(message, db_session)
    if not target:
        await message.reply(_("provide_user"))
        return
    success = await unmute_user(bot, db_session, message.chat.id, target.id, message.from_user.id)
    if success:
        await message.reply(_("user_unmuted").format(name=safe_username(target)))


@router.message(Command("warn"))
async def cmd_warn(message: Message, bot: Bot, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if message.chat.type == "private":
        return
    target, reason = await get_target_user(message, db_session)
    if not target:
        await message.reply(_("provide_user"))
        return

    gs = await db_session.scalar(select(GroupSettings).where(GroupSettings.group_id == message.chat.id))
    max_warns = gs.max_warns if gs else 3
    warn_action = gs.warn_action if gs else "mute"

    count, reached_max = await warn_user(db_session, message.chat.id, target.id, message.from_user.id, reason, max_warns)
    name = mention_user(target.id, safe_username(target))
    await message.reply(
        _("user_warned").format(name=name, count=count, max=max_warns, reason=reason or _("no_reason")),
        parse_mode="HTML",
    )

    if reached_max:
        await message.reply(
            _("max_warns_reached").format(name=safe_username(target), action=warn_action),
            parse_mode="HTML",
        )
        if warn_action == "ban":
            await ban_user(bot, db_session, message.chat.id, target.id, message.from_user.id, "Max warnings reached")
        elif warn_action == "kick":
            await kick_user(bot, db_session, message.chat.id, target.id, message.from_user.id, "Max warnings reached")
        elif warn_action == "mute":
            await mute_user(bot, db_session, message.chat.id, target.id, message.from_user.id, 3600, "Max warnings reached")


@router.message(Command("unwarn"))
async def cmd_unwarn(message: Message, _: callable, db_session: AsyncSession, **kwargs):
    if message.chat.type == "private":
        return
    target, _ = await get_target_user(message, db_session)
    if not target:
        await message.reply(_("provide_user"))
        return
    success = await unwarn_user(db_session, message.chat.id, target.id)
    if success:
        await message.reply(_("user_unwarned").format(name=safe_username(target)))


@router.message(Command("warns"))
async def cmd_warns(message: Message, _: callable, db_session: AsyncSession, **kwargs):
    if message.chat.type == "private":
        return
    target, _ = await get_target_user(message, db_session)
    if not target:
        if message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
        else:
            target_id = message.from_user.id
        target = await db_session.get(User, target_id)

    if not target:
        return
    warnings = await get_user_warnings(db_session, message.chat.id, target.id)
    text = f"⚠️ <b>Warnings for {safe_username(target)}</b>\n\n"
    if not warnings:
        text += "No warnings."
    else:
        for i, w in enumerate(warnings, 1):
            text += f"{i}. {w.reason or 'No reason'} — {w.created_at.strftime('%Y-%m-%d')}\n"
    await message.reply(text, parse_mode="HTML")


@router.message(Command("note"))
async def cmd_note(message: Message, _: callable, db_session: AsyncSession, **kwargs):
    if message.chat.type == "private":
        return
    if not message.reply_to_message:
        await message.reply("Reply to a user's message to add a note.")
        return
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.reply("Usage: /note <text>")
        return
    note_text = parts[1]
    await add_note(db_session, message.chat.id, message.reply_to_message.from_user.id, message.from_user.id, note_text)
    await message.reply(f"📝 Note added for {safe_username(message.reply_to_message.from_user)}")


@router.callback_query(F.data == "mod:unwarn")
async def cb_unwarn_info(callback: CallbackQuery, _: callable, **kwargs):
    await callback.answer("Reply to a user's message and use /unwarn to remove their last warning.", show_alert=True)


@router.callback_query(F.data == "mod:tban")
async def cb_tban_info(callback: CallbackQuery, _: callable, **kwargs):
    await callback.answer("Use /ban @user <duration> to temporarily ban.\nExample: /ban @user 7d spamming", show_alert=True)


@router.callback_query(F.data == "mod:tmute")
async def cb_tmute_info(callback: CallbackQuery, _: callable, **kwargs):
    await callback.answer("Use /mute @user <duration> to temporarily mute.\nExample: /mute @user 1h flooding", show_alert=True)


@router.callback_query(F.data == "mod:notes")
async def cb_notes_info(callback: CallbackQuery, _: callable, **kwargs):
    await callback.answer("Use /note <text> (reply to a user) to add a note.\nUse /history @user to view notes.", show_alert=True)


@router.callback_query(F.data == "mod:history")
async def cb_history_info(callback: CallbackQuery, _: callable, **kwargs):
    await callback.answer("Use /history @user or reply to a user and type /history to view their full moderation history.", show_alert=True)


@router.callback_query(F.data == "mod:roles")
async def cb_roles_info(callback: CallbackQuery, _: callable, **kwargs):
    await callback.answer("🚧 Custom roles are coming soon! For now, use Telegram's built-in admin system.", show_alert=True)


@router.callback_query(F.data == "mod:strike")
async def cb_strike_info(callback: CallbackQuery, _: callable, **kwargs):
    await callback.answer("🚧 Strike system is coming soon! It will automate progressive punishments.", show_alert=True)


@router.callback_query(F.data.in_({"mod:ban", "mod:unban", "mod:kick", "mod:mute", "mod:unmute", "mod:warn"}))
async def cb_mod_command_hint(callback: CallbackQuery, _: callable, **kwargs):
    hints = {
        "mod:ban":    "Use /ban @user [reason] or reply to a user and type /ban",
        "mod:unban":  "Use /unban @user or reply to a user and type /unban",
        "mod:kick":   "Use /kick @user [reason] or reply to a user and type /kick",
        "mod:mute":   "Use /mute @user [duration] [reason]\nExample: /mute @user 30m spamming",
        "mod:unmute": "Use /unmute @user or reply to a user and type /unmute",
        "mod:warn":   "Use /warn @user [reason] or reply to a user and type /warn",
    }
    await callback.answer(hints.get(callback.data, "Use the command in the group."), show_alert=True)


@router.message(Command("history"))
async def cmd_history(message: Message, _: callable, db_session: AsyncSession, **kwargs):
    if message.chat.type == "private":
        return
    target, _ = await get_target_user(message, db_session)
    if not target:
        await message.reply(_("provide_user"))
        return

    history = await get_user_history(db_session, message.chat.id, target.id)
    member = history["member"]
    logs = history["logs"]
    warnings = history["warnings"]

    text = _("user_history_title").format(name=safe_username(target)) + "\n\n"
    text += _("history_warnings").format(count=len(warnings)) + "\n"
    if member:
        text += _("history_messages").format(count=member.message_count or 0) + "\n"
        if member.joined_at:
            text += _("history_joined").format(date=member.joined_at.strftime("%Y-%m-%d")) + "\n"

    ban_count = sum(1 for l in logs if l.action == "ban")
    mute_count = sum(1 for l in logs if l.action == "mute")
    kick_count = sum(1 for l in logs if l.action == "kick")
    text += _("history_bans").format(count=ban_count) + "\n"
    text += _("history_mutes").format(count=mute_count) + "\n"
    text += _("history_kicks").format(count=kick_count) + "\n"

    await message.reply(text, parse_mode="HTML", reply_markup=back_button_kb(_, "mod:menu"))
