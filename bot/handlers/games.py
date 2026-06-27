import random
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.games import games_menu_kb, dice_menu_kb, rps_choice_kb, wheel_spin_kb, join_game_kb
from bot.keyboards.main_menu import back_button_kb
from bot.services.game_service import play_classic_dice, spin_wheel, play_rps, create_duel, accept_duel
from bot.services.user_service import get_or_create_game_stats
from bot.utils.helpers import format_number, safe_username
import structlog

logger = structlog.get_logger()
router = Router()


class GameStates(StatesGroup):
    waiting_dice_bet = State()
    waiting_wheel_bet = State()
    waiting_rps_bet = State()


@router.callback_query(F.data == "menu:games")
async def games_menu(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(_("games_menu"), reply_markup=games_menu_kb(_), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "game:dice")
async def dice_menu(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(_("dice_menu"), reply_markup=dice_menu_kb(_), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("dice:"))
async def play_dice(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, state: FSMContext, **kwargs):
    mode = callback.data.split("dice:", 1)[1]
    if mode == "classic":
        await callback.message.answer(_("game_bet_prompt").format(min=0, max=1000))
        await state.set_state(GameStates.waiting_dice_bet)
        await state.update_data(mode="classic")
        await callback.answer()
    elif mode == "lucky_mult":
        result = await play_classic_dice(db_session, db_user.id, wager=0)
        text = f"🎲 You rolled: <b>{result['player_roll']}</b> vs <b>{result['opponent_roll']}</b>\n"
        text += _("game_won").format(amount=0) if result["result"] == "win" else _("game_lost").format(amount=0) if result["result"] == "lose" else _("game_draw")
        await callback.message.answer(text, parse_mode="HTML")
        await callback.answer()
    elif mode == "daily":
        result = await play_classic_dice(db_session, db_user.id, wager=50)
        if "error" in result:
            await callback.answer(_("insufficient_funds"), show_alert=True)
            return
        text = f"📅 <b>Daily Dice Challenge</b>\n🎲 You: <b>{result['player_roll']}</b> vs Bot: <b>{result['opponent_roll']}</b>\n"
        text += _("game_won").format(amount=result["winnings"]) if result["result"] == "win" else _("game_lost").format(amount=50)
        await callback.message.answer(text, parse_mode="HTML")
        await callback.answer()
    else:
        await callback.answer(f"Mode '{mode}' coming soon!", show_alert=True)


@router.message(GameStates.waiting_dice_bet)
async def process_dice_bet(message: Message, _: callable, db_session: AsyncSession, db_user, state: FSMContext, **kwargs):
    try:
        wager = int(message.text.strip())
        if wager < 0:
            raise ValueError
    except ValueError:
        await message.reply(_("invalid_amount"))
        return

    result = await play_classic_dice(db_session, db_user.id, wager=wager)
    if "error" in result:
        await message.reply(_("insufficient_funds").format(balance="?"))
        await state.clear()
        return

    text = f"🎲 You rolled: <b>{result['player_roll']}</b> vs Bot: <b>{result['opponent_roll']}</b>\n\n"
    if result["result"] == "win":
        text += _("game_won").format(amount=format_number(result["winnings"]))
    elif result["result"] == "lose":
        text += _("game_lost").format(amount=format_number(wager))
    else:
        text += _("game_draw")

    await message.reply(text, parse_mode="HTML")
    await state.clear()


@router.callback_query(F.data == "game:wheel")
async def wheel_game(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    from bot.database.models import GameMatch
    from datetime import datetime, timezone
    import json

    match = GameMatch(
        group_id=callback.message.chat.id,
        game_type="wheel",
        player1_id=db_user.id,
        wager=0,
        status="active",
        message_id=callback.message.message_id,
        data={"bet": 0},
    )
    db_session.add(match)
    await db_session.flush()

    await callback.message.answer(
        "🎡 <b>Lucky Wheel</b>\nBet 0 for free spin, or type a number:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "game:rps")
async def rps_game(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    await callback.message.answer(
        "✊ <b>Rock Paper Scissors</b>\nChoose your move!",
        parse_mode="HTML",
        reply_markup=rps_choice_kb(_, 0),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rps:"))
async def process_rps(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    parts = callback.data.split(":")
    player_choice = parts[2] if len(parts) > 2 else "rock"
    result = await play_rps(db_session, db_user.id, player_choice, wager=0)

    emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
    text = (
        f"✊ <b>RPS Result</b>\n"
        f"You: {emojis.get(result['player_choice'], '?')} vs Bot: {emojis.get(result['bot_choice'], '?')}\n\n"
    )
    if result["result"] == "win":
        text += "🎉 You win!"
    elif result["result"] == "lose":
        text += "😔 You lose!"
    else:
        text += "🤝 Draw!"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:games"))
    await callback.answer()


@router.callback_query(F.data == "game:quiz")
async def quiz_game(callback: CallbackQuery, _: callable, **kwargs):
    questions = [
        ("What is the capital of France?", ["Paris", "London", "Berlin", "Madrid"], 0),
        ("What is 2 + 2?", ["3", "4", "5", "6"], 1),
        ("Which planet is closest to the Sun?", ["Venus", "Earth", "Mercury", "Mars"], 2),
        ("What color is the sky?", ["Green", "Blue", "Red", "Yellow"], 1),
        ("How many sides does a triangle have?", ["2", "3", "4", "5"], 1),
    ]
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    q_text, options, correct = random.choice(questions)
    builder = InlineKeyboardBuilder()
    for i, opt in enumerate(options):
        builder.button(text=opt, callback_data=f"quiz_ans:{correct}:{i}")
    builder.button(text=_("btn_back"), callback_data="menu:games")
    builder.adjust(2, 2, 1)
    await callback.message.answer(
        f"🧠 <b>Quiz Battle</b>\n\n{q_text}",
        parse_mode="HTML",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("quiz_ans:"))
async def quiz_answer(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    parts = callback.data.split(":")
    correct = int(parts[1])
    chosen = int(parts[2])
    is_correct = correct == chosen
    if is_correct:
        await callback.answer("✅ Correct! +20 XP", show_alert=True)
        await add_xp_wrap(db_session, db_user.id, 20)
    else:
        await callback.answer("❌ Wrong answer!", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=back_button_kb(_, "menu:games"))


async def add_xp_wrap(session, user_id, amount):
    from bot.services.user_service import add_xp
    await add_xp(session, user_id, amount)


@router.callback_query(F.data.in_({"game:treasure", "game:cards", "game:numwar", "game:mines", "game:chess", "game:roulette"}))
async def game_coming_soon(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    game_map = {
        "game:treasure": "🗺️ Treasure Hunt",
        "game:cards": "🃏 Card Battle",
        "game:numwar": "🔢 Number War",
        "game:mines": "💣 Mines Challenge",
        "game:chess": "♟️ Chess Mini",
        "game:roulette": "🎰 Safe Russian Roulette",
    }
    game_name = game_map.get(callback.data, "Game")
    result = await play_classic_dice(db_session, db_user.id, wager=0)
    text = (
        f"{game_name}\n\n"
        f"🎲 Quick Play — Roll: <b>{result['player_roll']}</b>\n"
        + (_("game_won").format(amount=0) if result["result"] == "win" else _("game_lost").format(amount=0))
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:games"))
    await callback.answer()


@router.callback_query(F.data == "gstats:all")
async def game_stats_view(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    stats = await get_or_create_game_stats(db_session, db_user.id)
    total = stats.total_games or 0
    wins = stats.total_wins or 0
    rate = int(wins / total * 100) if total > 0 else 0
    text = (
        _("game_stats_title") + "\n\n"
        + _("games_played").format(count=total) + "\n"
        + _("games_won").format(count=wins) + "\n"
        + _("games_lost").format(count=stats.total_losses or 0) + "\n"
        + _("win_rate").format(rate=rate) + "\n"
        + _("coins_bet").format(amount=format_number(stats.total_coins_bet or 0)) + "\n"
        + _("coins_won_total").format(amount=format_number(stats.total_coins_won or 0))
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:games"))
    await callback.answer()
