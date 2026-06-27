from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.database.models import Duel, User
from bot.keyboards.main_menu import back_button_kb
from bot.services.game_service import create_duel, accept_duel
from bot.services.user_service import get_or_create_duel_stats
from bot.utils.helpers import format_number, safe_username, mention_user
import structlog

logger = structlog.get_logger()
router = Router()


class DuelStates(StatesGroup):
    waiting_wager = State()
    waiting_opponent = State()


def duel_kb(duel_id: int, _: callable) -> object:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_accept_duel"), callback_data=f"duel_accept:{duel_id}")
    builder.button(text=_("btn_decline_duel"), callback_data=f"duel_decline:{duel_id}")
    builder.adjust(2)
    return builder.as_markup()


@router.callback_query(F.data == "menu:duels")
async def duels_menu(callback: CallbackQuery, _: callable, **kwargs):
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_new_duel"), callback_data="duel:new")
    builder.button(text=_("btn_duel_history"), callback_data="duel:history")
    builder.button(text=_("btn_duel_stats"), callback_data="duel:stats")
    builder.button(text=_("btn_duel_rankings"), callback_data="duel:rankings")
    builder.button(text=_("btn_back"), callback_data="menu:main")
    builder.adjust(2, 2, 1)
    await callback.message.edit_text(_("duel_menu"), reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "duel:new")
async def new_duel(callback: CallbackQuery, _: callable, state: FSMContext, **kwargs):
    if callback.message.chat.type == "private":
        await callback.answer("Duels can only be started in groups!", show_alert=True)
        return
    await callback.message.answer("⚔️ Enter the wager amount (0 for free duel):")
    await state.set_state(DuelStates.waiting_wager)
    await callback.answer()


@router.message(DuelStates.waiting_wager)
async def process_duel_wager(message: Message, _: callable, state: FSMContext, **kwargs):
    try:
        wager = int(message.text.strip())
        if wager < 0:
            raise ValueError
    except ValueError:
        await message.reply(_("invalid_amount"))
        return
    await state.update_data(wager=wager)
    await message.reply("👤 Now enter your opponent's @username or reply to their message:")
    await state.set_state(DuelStates.waiting_opponent)


@router.message(DuelStates.waiting_opponent)
async def process_duel_opponent(message: Message, _: callable, db_session: AsyncSession, db_user, state: FSMContext, **kwargs):
    data = await state.get_data()
    wager = data.get("wager", 0)

    opponent = None
    if message.reply_to_message:
        tg_user = message.reply_to_message.from_user
        opponent = await db_session.get(User, tg_user.id)
    elif message.text.startswith("@"):
        uname = message.text[1:]
        opponent = await db_session.scalar(select(User).where(User.username == uname))

    if not opponent:
        await message.reply(_("error_user_not_found"))
        await state.clear()
        return

    if opponent.id == db_user.id:
        await message.reply("❌ You can't duel yourself!")
        await state.clear()
        return

    duel = await create_duel(
        db_session,
        message.chat.id,
        db_user.id,
        opponent.id,
        wager,
        "dice",
        message.message_id,
    )

    if not duel:
        await message.reply(_("insufficient_funds").format(balance="?"))
        await state.clear()
        return

    challenger_name = mention_user(db_user.id, safe_username(db_user))
    opponent_name = mention_user(opponent.id, safe_username(opponent))
    text = _("duel_challenge").format(
        challenger=challenger_name,
        opponent=opponent_name,
        wager=format_number(wager),
        game="Dice",
    )
    await message.reply(text, reply_markup=duel_kb(duel.id, _), parse_mode="HTML")
    await state.clear()


@router.callback_query(F.data.startswith("duel_accept:"))
async def accept_duel_cb(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    duel_id = int(callback.data.split(":")[1])
    duel = await db_session.get(Duel, duel_id)
    if not duel:
        await callback.answer("Duel not found.", show_alert=True)
        return
    if duel.opponent_id and duel.opponent_id != db_user.id:
        await callback.answer("This duel is not for you.", show_alert=True)
        return
    if duel.challenger_id == db_user.id:
        await callback.answer("You can't accept your own duel!", show_alert=True)
        return

    duel_obj, result = await accept_duel(db_session, duel_id, db_user.id)
    if not duel_obj:
        await callback.answer("Duel is no longer available.", show_alert=True)
        return
    if "error" in result:
        await callback.answer(_("insufficient_funds"), show_alert=True)
        return

    if result.get("result") == "draw":
        text = f"🤝 It's a draw! Wager returned.\n🎲 {result['challenger_score']} vs {result['opponent_score']}"
    else:
        winner = await db_session.get(User, result["winner_id"])
        prize = result.get("prize", 0)
        text = _("duel_won").format(
            winner=safe_username(winner) if winner else "Unknown",
            amount=format_number(prize),
        )
        text += f"\n🎲 {result['challenger_score']} vs {result['opponent_score']}"

    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer(_("duel_accepted"))


@router.callback_query(F.data.startswith("duel_decline:"))
async def decline_duel_cb(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    duel_id = int(callback.data.split(":")[1])
    duel = await db_session.get(Duel, duel_id)
    if not duel:
        await callback.answer("Duel not found.", show_alert=True)
        return
    if duel.opponent_id and duel.opponent_id != db_user.id:
        await callback.answer("This duel is not for you.", show_alert=True)
        return

    from bot.services.economy_service import add_coins
    if duel.wager > 0:
        await add_coins(db_session, duel.challenger_id, duel.wager, "duel_refund", "Duel declined refund")
    duel.status = "declined"
    await callback.message.edit_text(_("duel_declined"))
    await callback.answer()


@router.callback_query(F.data == "duel:stats")
async def duel_stats_view(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    stats = await get_or_create_duel_stats(db_session, db_user.id)
    total = (stats.wins or 0) + (stats.losses or 0)
    rate = int((stats.wins or 0) / total * 100) if total > 0 else 0
    text = (
        "⚔️ <b>Duel Statistics</b>\n\n"
        f"🏆 Wins: <b>{stats.wins or 0}</b>\n"
        f"💔 Losses: <b>{stats.losses or 0}</b>\n"
        f"🤝 Draws: <b>{stats.draws or 0}</b>\n"
        f"📈 Win Rate: <b>{rate}%</b>\n"
        f"🔥 Win Streak: <b>{stats.win_streak or 0}</b>\n"
        f"⭐ Best Streak: <b>{stats.best_streak or 0}</b>\n"
        f"💰 Coins Won: <b>{format_number(stats.coins_won or 0)}</b>\n"
        f"💸 Coins Lost: <b>{format_number(stats.coins_lost or 0)}</b>"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:duels"))
    await callback.answer()


@router.message(Command("duel"))
async def cmd_duel(message: Message, _: callable, db_session: AsyncSession, db_user, state: FSMContext, **kwargs):
    if message.chat.type == "private":
        await message.reply("Use duels in a group chat!")
        return
    if not message.reply_to_message:
        await message.reply("Reply to a user to challenge them to a duel!\n/duel [wager]")
        return
    parts = message.text.split()
    wager = 0
    if len(parts) > 1:
        try:
            wager = int(parts[1])
        except ValueError:
            wager = 0

    opponent_tg = message.reply_to_message.from_user
    opponent = await db_session.get(User, opponent_tg.id)
    if not opponent:
        opponent = User(id=opponent_tg.id, first_name=opponent_tg.first_name or "User", username=opponent_tg.username)
        db_session.add(opponent)
        await db_session.flush()

    duel = await create_duel(db_session, message.chat.id, db_user.id, opponent.id, wager, "dice", message.message_id)
    if not duel:
        await message.reply(_("insufficient_funds").format(balance="?"))
        return

    challenger_name = mention_user(db_user.id, safe_username(db_user))
    opponent_name = mention_user(opponent.id, safe_username(opponent))
    text = _("duel_challenge").format(
        challenger=challenger_name,
        opponent=opponent_name,
        wager=format_number(wager),
        game="Dice",
    )
    await message.reply(text, reply_markup=duel_kb(duel.id, _), parse_mode="HTML")
