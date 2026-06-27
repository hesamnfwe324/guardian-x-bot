from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.database.models import GroupMember, User, Economy, Wallet, DuelStats, Reputation
from bot.services.user_service import get_top_users_by_level, get_top_users_by_coins, get_top_reputation
from bot.keyboards.main_menu import back_button_kb
from bot.utils.helpers import format_number, safe_username, progress_bar, calculate_level
import structlog

logger = structlog.get_logger()
router = Router()


def stats_menu_kb(_) -> object:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_leaderboards"), callback_data="stats:leaderboards")
    builder.button(text=_("btn_active_members"), callback_data="stats:active")
    builder.button(text=_("btn_group_growth"), callback_data="stats:growth")
    builder.button(text=_("btn_daily_stats"), callback_data="stats:daily")
    builder.button(text=_("btn_back"), callback_data="menu:main")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def leaderboard_kb(_) -> object:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_richest"), callback_data="lb:richest")
    builder.button(text=_("btn_top_levels"), callback_data="lb:levels")
    builder.button(text=_("btn_best_players"), callback_data="lb:players")
    builder.button(text=_("btn_most_wins"), callback_data="lb:wins")
    builder.button(text=_("btn_top_rep"), callback_data="lb:rep")
    builder.button(text=_("btn_back"), callback_data="stats:menu")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


@router.callback_query(F.data == "menu:statistics")
async def stats_menu(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(_("stats_menu"), reply_markup=stats_menu_kb(_), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats:menu")
async def stats_menu_back(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(_("stats_menu"), reply_markup=stats_menu_kb(_), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats:leaderboards")
async def leaderboards_menu(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text("🏆 <b>Leaderboards</b>", reply_markup=leaderboard_kb(_), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "lb:richest")
async def lb_richest(callback: CallbackQuery, _: callable, db_session: AsyncSession, **kwargs):
    top = await get_top_users_by_coins(db_session, limit=10)
    text = "💰 <b>Richest Users</b>\n\n"
    for i, (user, wallet) in enumerate(top, 1):
        total = (wallet.balance or 0) + (wallet.bank_balance or 0)
        text += f"{i}. {safe_username(user)} — {format_number(total)} coins\n"
    if not top:
        text += _("no_data")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "stats:leaderboards"))
    await callback.answer()


@router.callback_query(F.data == "lb:levels")
async def lb_levels(callback: CallbackQuery, _: callable, db_session: AsyncSession, **kwargs):
    top = await get_top_users_by_level(db_session, limit=10)
    text = "⭐ <b>Highest Levels</b>\n\n"
    for i, (user, eco) in enumerate(top, 1):
        text += f"{i}. {safe_username(user)} — Level {eco.level} ({format_number(eco.total_xp or 0)} XP)\n"
    if not top:
        text += _("no_data")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "stats:leaderboards"))
    await callback.answer()


@router.callback_query(F.data == "lb:rep")
async def lb_rep(callback: CallbackQuery, _: callable, db_session: AsyncSession, **kwargs):
    top = await get_top_reputation(db_session, limit=10)
    text = "🌟 <b>Top Reputation</b>\n\n"
    for i, (user, rep) in enumerate(top, 1):
        text += f"{i}. {safe_username(user)} — +{rep.positive or 0} / -{rep.negative or 0}\n"
    if not top:
        text += _("no_data")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "stats:leaderboards"))
    await callback.answer()


@router.callback_query(F.data == "lb:wins")
async def lb_wins(callback: CallbackQuery, _: callable, db_session: AsyncSession, **kwargs):
    result = await db_session.execute(
        select(User, DuelStats)
        .join(DuelStats, DuelStats.user_id == User.id)
        .order_by(desc(DuelStats.wins))
        .limit(10)
    )
    top = result.all()
    text = "🏆 <b>Most Wins</b>\n\n"
    for i, (user, stats) in enumerate(top, 1):
        text += f"{i}. {safe_username(user)} — {stats.wins or 0} wins\n"
    if not top:
        text += _("no_data")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "stats:leaderboards"))
    await callback.answer()


@router.callback_query(F.data == "lb:players")
async def lb_players(callback: CallbackQuery, _: callable, db_session: AsyncSession, **kwargs):
    from bot.database.models import GameStats
    result = await db_session.execute(
        select(User, GameStats)
        .join(GameStats, GameStats.user_id == User.id)
        .order_by(desc(GameStats.total_wins))
        .limit(10)
    )
    top = result.all()
    text = "🎮 <b>Best Players</b>\n\n"
    for i, (user, stats) in enumerate(top, 1):
        text += f"{i}. {safe_username(user)} — {stats.total_wins or 0} game wins\n"
    if not top:
        text += _("no_data")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "stats:leaderboards"))
    await callback.answer()


@router.callback_query(F.data == "stats:active")
async def active_members(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if not db_group:
        await callback.answer(_("error_group_only"), show_alert=True)
        return
    result = await db_session.execute(
        select(User, GroupMember)
        .join(GroupMember, GroupMember.user_id == User.id)
        .where(GroupMember.group_id == db_group.id)
        .order_by(desc(GroupMember.message_count))
        .limit(10)
    )
    top = result.all()
    text = f"👥 <b>Most Active in {db_group.title}</b>\n\n"
    for i, (user, member) in enumerate(top, 1):
        text += f"{i}. {safe_username(user)} — {format_number(member.message_count or 0)} messages\n"
    if not top:
        text += _("no_data")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "stats:menu"))
    await callback.answer()


@router.callback_query(F.data.in_({"stats:growth", "stats:daily", "stats:weekly", "stats:monthly"}))
async def generic_stats(callback: CallbackQuery, _: callable, db_session: AsyncSession, **kwargs):
    result = await db_session.execute(select(func.count()).select_from(User))
    total_users = result.scalar() or 0
    from bot.database.models import Group
    result2 = await db_session.execute(select(func.count()).select_from(Group))
    total_groups = result2.scalar() or 0
    text = (
        "📊 <b>Global Statistics</b>\n\n"
        + _("total_users").format(count=format_number(total_users)) + "\n"
        + _("total_groups").format(count=format_number(total_groups))
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "stats:menu"))
    await callback.answer()


@router.callback_query(F.data == "menu:levels")
async def levels_menu(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    from bot.services.user_service import get_or_create_economy
    eco = await get_or_create_economy(db_session, db_user.id)
    level, current_xp, needed_xp = calculate_level(eco.total_xp or 0)
    bar = progress_bar(current_xp, needed_xp)
    text = (
        _("level_menu") + "\n\n"
        + _("your_level").format(level=level) + "\n"
        + _("your_xp").format(xp=format_number(current_xp), next_xp=format_number(needed_xp)) + "\n"
        + _("level_progress").format(bar=bar)
    )
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_leaderboard"), callback_data="lb:levels")
    builder.button(text=_("btn_back"), callback_data="menu:main")
    builder.adjust(2)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "menu:reputation")
async def reputation_menu(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    from bot.services.user_service import get_or_create_reputation
    rep = await get_or_create_reputation(db_session, db_user.id)
    text = (
        _("reputation_menu") + "\n\n"
        + _("your_rep").format(pos=rep.positive or 0, neg=rep.negative or 0)
    )
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_rep_rankings"), callback_data="lb:rep")
    builder.button(text=_("btn_back"), callback_data="menu:main")
    builder.adjust(2)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()
