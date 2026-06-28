from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from bot.database.models import GroupMember, User, Economy, Wallet, DuelStats, Reputation, ActionLog, Group
from bot.services.user_service import get_top_users_by_level, get_top_users_by_coins, get_top_reputation
from bot.utils.helpers import format_number, safe_username, progress_bar
import structlog
from datetime import datetime, timezone, timedelta

logger = structlog.get_logger()
router = Router()


@router.callback_query(F.data == "menu:statistics")
async def stats_menu(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(_("stats_menu"), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats:menu")
async def stats_menu_back(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(_("stats_menu"), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats:leaderboards")
async def leaderboards_menu(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(_("leaderboards_title"), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "lb:richest")
async def lb_richest(callback: CallbackQuery, _: callable, db_session: AsyncSession, **kwargs):
    top = await get_top_users_by_coins(db_session, limit=10)
    medals = ["U0001f947","U0001f948","U0001f949"]
    lines_out = []
    for i, (user, wallet) in enumerate(top, 1):
        total = (wallet.balance or 0) + (wallet.bank_balance or 0)
        medal = medals[i-1] if i <= 3 else f"{i}."
        lines_out.append(f"{medal} {safe_username(user)} — {format_number(total)} {_(\"coin_unit\")}")
    text = _("lb_richest_title") + "\n\n" + ("\n".join(lines_out) if lines_out else _("no_data"))
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "lb:levels")
async def lb_levels(callback: CallbackQuery, _: callable, db_session: AsyncSession, **kwargs):
    top = await get_top_users_by_level(db_session, limit=10)
    medals = ["U0001f947","U0001f948","U0001f949"]
    lines_out = []
    for i, (user, eco) in enumerate(top, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        lines_out.append(f"{medal} {safe_username(user)} — {_(\"level_label\")} {eco.level} ({format_number(eco.total_xp or 0)} XP)")
    text = _("lb_levels_title") + "\n\n" + ("\n".join(lines_out) if lines_out else _("no_data"))
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "lb:rep")
async def lb_rep(callback: CallbackQuery, _: callable, db_session: AsyncSession, **kwargs):
    top = await get_top_reputation(db_session, limit=10)
    medals = ["U0001f947","U0001f948","U0001f949"]
    lines_out = []
    for i, (user, rep) in enumerate(top, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        score = (rep.positive or 0) - (rep.negative or 0)
        lines_out.append(f"{medal} {safe_username(user)} — +{rep.positive or 0}/-{rep.negative or 0} (net: {score})")
    text = _("lb_rep_title") + "\n\n" + ("\n".join(lines_out) if lines_out else _("no_data"))
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "lb:wins")
async def lb_wins(callback: CallbackQuery, _: callable, db_session: AsyncSession, **kwargs):
    stmt = select(User, DuelStats).join(DuelStats, DuelStats.user_id == User.id).order_by(desc(DuelStats.wins)).limit(10)
    rows = (await db_session.execute(stmt)).all()
    medals = ["U0001f947","U0001f948","U0001f949"]
    lines_out = []
    for i, (user, ds) in enumerate(rows, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        wr = int(ds.wins / max(ds.wins + ds.losses, 1) * 100)
        lines_out.append(f"{medal} {safe_username(user)} — {ds.wins}W/{ds.losses}L ({wr}% WR)")
    text = _("lb_wins_title") + "\n\n" + ("\n".join(lines_out) if lines_out else _("no_data"))
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "lb:players")
async def lb_players(callback: CallbackQuery, _: callable, db_session: AsyncSession, **kwargs):
    stmt = select(User, Economy).join(Economy, Economy.user_id == User.id).order_by(desc(Economy.xp)).limit(10)
    rows = (await db_session.execute(stmt)).all()
    medals = ["U0001f947","U0001f948","U0001f949"]
    lines_out = []
    for i, (user, eco) in enumerate(rows, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        lines_out.append(f"{medal} {safe_username(user)} — {format_number(eco.xp or 0)} XP")
    text = _("lb_players_title") + "\n\n" + ("\n".join(lines_out) if lines_out else _("no_data"))
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats:mine")
async def my_stats(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    if not db_user:
        await callback.answer(_("error_generic"), show_alert=True)
        return
    wallet = await db_session.scalar(select(Wallet).where(Wallet.user_id == db_user.id))
    eco = await db_session.scalar(select(Economy).where(Economy.user_id == db_user.id))
    rep = await db_session.scalar(select(Reputation).where(Reputation.user_id == db_user.id))
    ds = await db_session.scalar(select(DuelStats).where(DuelStats.user_id == db_user.id))
    balance = (wallet.balance if wallet else 0) or 0
    bank = (wallet.bank_balance if wallet else 0) or 0
    level = (eco.level if eco else 1) or 1
    xp = (eco.xp if eco else 0) or 0
    total_xp = (eco.total_xp if eco else 0) or 0
    pos_rep = (rep.positive if rep else 0) or 0
    neg_rep = (rep.negative if rep else 0) or 0
    wins = (ds.wins if ds else 0) or 0
    losses = (ds.losses if ds else 0) or 0
    xp_needed = level * 100
    bar = progress_bar(xp, xp_needed) if xp_needed else ""
    wr = int(wins / max(wins + losses, 1) * 100)
    name = db_user.first_name or safe_username(db_user)
    text = _("my_stats_text").format(
        name=name, level=level, xp=format_number(xp), xp_needed=format_number(xp_needed),
        bar=bar, total_xp=format_number(total_xp), balance=format_number(balance),
        bank=format_number(bank), pos_rep=pos_rep, neg_rep=neg_rep, wins=wins, losses=losses, winrate=wr,
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats:active")
async def active_members(callback: CallbackQuery, _: callable, db_session: AsyncSession, **kwargs):
    chat = callback.message.chat
    if chat.type not in ("group", "supergroup"):
        await callback.answer(_("error_group_only"), show_alert=True)
        return
    stmt = select(GroupMember, User).join(User, User.id == GroupMember.user_id).where(
        GroupMember.group_id == chat.id).order_by(desc(GroupMember.message_count)).limit(10)
    rows = (await db_session.execute(stmt)).all()
    medals = ["U0001f947","U0001f948","U0001f949"]
    lines_out = []
    for i, (gm, user) in enumerate(rows, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        lines_out.append(f"{medal} {safe_username(user)} — {format_number(gm.message_count)} {_(\"msg_unit\")}")
    text = _("active_members_title") + "\n\n" + ("\n".join(lines_out) if lines_out else _("no_data"))
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats:daily")
async def daily_stats(callback: CallbackQuery, _: callable, db_session: AsyncSession, **kwargs):
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)
    total_users = await db_session.scalar(select(func.count(User.id)))
    new_users = await db_session.scalar(select(func.count(User.id)).where(User.created_at >= day_ago))
    total_actions = await db_session.scalar(select(func.count(ActionLog.id)).where(ActionLog.created_at >= day_ago))
    text = _("daily_stats_text").format(
        total_users=format_number(total_users or 0),
        new_users=format_number(new_users or 0),
        actions=format_number(total_actions or 0),
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats:growth")
async def group_growth(callback: CallbackQuery, _: callable, db_session: AsyncSession, **kwargs):
    chat = callback.message.chat
    if chat.type in ("group", "supergroup"):
        total_members = await db_session.scalar(select(func.count(GroupMember.id)).where(GroupMember.group_id == chat.id))
        try:
            chat_obj = await callback.bot.get_chat(chat.id)
            member_count = chat_obj.member_count or total_members
        except Exception:
            member_count = total_members
        text = _("group_growth_text").format(title=chat.title or "Group", members=format_number(member_count or 0), db_members=format_number(total_members or 0))
    else:
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        total_groups = await db_session.scalar(select(func.count(Group.id)))
        new_groups = await db_session.scalar(select(func.count(Group.id)).where(Group.created_at >= week_ago))
        total_members = await db_session.scalar(select(func.count(GroupMember.id)))
        text = _("global_growth_text").format(total_groups=format_number(total_groups or 0), new_groups=format_number(new_groups or 0), total_members=format_number(total_members or 0))
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()
