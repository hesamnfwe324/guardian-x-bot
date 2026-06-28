from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.keyboards.main_menu import nav_kb
from bot.utils.helpers import format_number, safe_username
import structlog

logger = structlog.get_logger()
router = Router()


def tournaments_kb(_):
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_active_tournaments"),  callback_data="trn:active")
    builder.button(text=_("btn_my_tournaments"),      callback_data="trn:mine")
    builder.button(text=_("btn_tournament_history"),  callback_data="trn:history")
    builder.button(text=_("btn_tournament_rankings"), callback_data="trn:rankings")
    builder.button(text=_("btn_back"),  callback_data="menu:main")
    builder.button(text=_("btn_home"),  callback_data="menu:main")
    builder.adjust(2, 2, 2)
    return builder.as_markup()


async def render_tournaments_menu(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(_("tournaments_menu"), reply_markup=tournaments_kb(_), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu:tournaments")
async def tournaments_menu(callback: CallbackQuery, _: callable, **kwargs):
    await render_tournaments_menu(callback, _)


@router.callback_query(F.data == "trn:active")
async def active_tournaments(callback: CallbackQuery, _: callable, db_session: AsyncSession = None, **kwargs):
    text = _("no_active_tournaments")
    if db_session:
        try:
            from bot.database.models import Tournament
            stmt = select(Tournament).where(Tournament.status.in_(["open","running"])).order_by(Tournament.starts_at).limit(5)
            rows = (await db_session.execute(stmt)).scalars().all()
            if rows:
                text = _("active_tournaments_title") + "\n\n"
                for t in rows:
                    icon = "🟢" if t.status == "open" else "🔵"
                    text += f"{icon} <b>{t.name}</b>\n  {_('tournament_prize')}: {format_number(t.prize_pool)} {_('coin_unit')}\n  {t.participant_count}/{t.max_participants} {_('participants_unit')}\n\n"
        except Exception:
            pass
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=nav_kb(_, "menu:tournaments", "trn:active"))
    await callback.answer()


@router.callback_query(F.data == "trn:mine")
async def my_tournaments(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(_("no_tournament_history"), parse_mode="HTML", reply_markup=nav_kb(_, "menu:tournaments"))
    await callback.answer()


@router.callback_query(F.data == "trn:history")
async def tournament_history(callback: CallbackQuery, _: callable, db_session: AsyncSession = None, **kwargs):
    text = _("no_tournament_history")
    if db_session:
        try:
            from bot.database.models import Tournament
            stmt = select(Tournament).where(Tournament.status == "finished").order_by(desc(Tournament.ends_at)).limit(5)
            rows = (await db_session.execute(stmt)).scalars().all()
            if rows:
                text = _("tournament_history_title") + "\n\n"
                for t in rows:
                    text += f"🏆 <b>{t.name}</b>\n  {_('tournament_winner')}: {t.winner_name or _('no_data')}\n  {_('tournament_prize')}: {format_number(t.prize_pool)} {_('coin_unit')}\n\n"
        except Exception:
            pass
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=nav_kb(_, "menu:tournaments", "trn:history"))
    await callback.answer()


@router.callback_query(F.data == "trn:rankings")
async def tournament_rankings(callback: CallbackQuery, _: callable, db_session: AsyncSession = None, **kwargs):
    text = _("no_data")
    if db_session:
        try:
            from bot.database.models import DuelStats, User
            stmt = select(User, DuelStats).join(DuelStats, DuelStats.user_id == User.id).order_by(desc(DuelStats.wins)).limit(10)
            rows = (await db_session.execute(stmt)).all()
            medals = ["🥇","🥈","🥉"]
            text = _("tournament_rankings_title") + "\n\n"
            for i, (user, ds) in enumerate(rows, 1):
                medal = medals[i-1] if i <= 3 else f"{i}."
                text += f"{medal} {safe_username(user)} — {ds.wins} {_('wins_unit')}\n"
            if not rows:
                text = _("no_data")
        except Exception:
            pass
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=nav_kb(_, "menu:tournaments", "trn:rankings"))
    await callback.answer()
