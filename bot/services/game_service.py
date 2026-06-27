import random
import json
from datetime import datetime, timezone
from typing import Optional, Tuple, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from bot.database.models import GameMatch, GameStats, DuelStats, Duel
from bot.services.economy_service import add_coins, deduct_coins
from bot.services.user_service import add_xp, get_or_create_game_stats, get_or_create_duel_stats
import structlog

logger = structlog.get_logger()

XP_PER_WIN = 25
XP_PER_GAME = 5

WHEEL_SEGMENTS = [
    (2, "2x", 0.25),
    (0, "LOSE", 0.30),
    (1.5, "1.5x", 0.20),
    (3, "3x", 0.15),
    (0.5, "0.5x", 0.05),
    (5, "5x", 0.03),
    (10, "10x", 0.01),
    (0.75, "0.75x", 0.01),
]


async def play_classic_dice(
    session: AsyncSession,
    user_id: int,
    wager: int = 0,
    opponent_id: Optional[int] = None,
) -> dict:
    player_roll = random.randint(1, 6)
    opponent_roll = random.randint(1, 6) if opponent_id else random.randint(1, 6)

    if player_roll > opponent_roll:
        result = "win"
    elif player_roll < opponent_roll:
        result = "lose"
    else:
        result = "draw"

    winnings = 0
    if wager > 0:
        success, _ = await deduct_coins(session, user_id, wager, "game_bet", "Dice bet")
        if not success:
            return {"error": "insufficient_funds"}

        if result == "win":
            win_amount = int(wager * 1.9)
            await add_coins(session, user_id, win_amount, "game_win", "Dice win")
            winnings = win_amount - wager
        elif result == "draw":
            await add_coins(session, user_id, wager, "game_draw", "Dice draw refund")

    stats = await get_or_create_game_stats(session, user_id)
    stats.total_games = (stats.total_games or 0) + 1
    stats.total_coins_bet = (stats.total_coins_bet or 0) + wager
    if result == "win":
        stats.total_wins = (stats.total_wins or 0) + 1
        stats.dice_wins = (stats.dice_wins or 0) + 1
        stats.total_coins_won = (stats.total_coins_won or 0) + max(0, winnings)
        await add_xp(session, user_id, XP_PER_WIN)
    elif result == "lose":
        stats.total_losses = (stats.total_losses or 0) + 1
    await add_xp(session, user_id, XP_PER_GAME)

    return {
        "result": result,
        "player_roll": player_roll,
        "opponent_roll": opponent_roll,
        "winnings": winnings,
    }


async def spin_wheel(
    session: AsyncSession,
    user_id: int,
    wager: int = 0,
) -> dict:
    if wager > 0:
        success, _ = await deduct_coins(session, user_id, wager, "game_bet", "Wheel spin bet")
        if not success:
            return {"error": "insufficient_funds"}

    rand = random.random()
    cumulative = 0.0
    chosen_multiplier = 0
    chosen_label = "LOSE"
    for multiplier, label, probability in WHEEL_SEGMENTS:
        cumulative += probability
        if rand <= cumulative:
            chosen_multiplier = multiplier
            chosen_label = label
            break

    winnings = 0
    if wager > 0 and chosen_multiplier > 0:
        win_amount = int(wager * chosen_multiplier)
        await add_coins(session, user_id, win_amount, "game_win", "Wheel win")
        winnings = win_amount - wager

    stats = await get_or_create_game_stats(session, user_id)
    stats.total_games = (stats.total_games or 0) + 1
    stats.wheel_wins = (stats.wheel_wins or 0) + (1 if chosen_multiplier > 1 else 0)
    await add_xp(session, user_id, XP_PER_GAME)

    return {"multiplier": chosen_multiplier, "label": chosen_label, "winnings": winnings}


async def play_rps(
    session: AsyncSession,
    user_id: int,
    player_choice: str,
    wager: int = 0,
) -> dict:
    choices = ["rock", "paper", "scissors"]
    bot_choice = random.choice(choices)

    wins = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
    if player_choice == bot_choice:
        result = "draw"
    elif wins.get(player_choice) == bot_choice:
        result = "win"
    else:
        result = "lose"

    winnings = 0
    if wager > 0:
        success, _ = await deduct_coins(session, user_id, wager, "game_bet", "RPS bet")
        if not success:
            return {"error": "insufficient_funds"}
        if result == "win":
            win_amount = int(wager * 1.9)
            await add_coins(session, user_id, win_amount, "game_win", "RPS win")
            winnings = win_amount - wager
        elif result == "draw":
            await add_coins(session, user_id, wager, "game_draw", "RPS draw refund")

    stats = await get_or_create_game_stats(session, user_id)
    stats.total_games = (stats.total_games or 0) + 1
    stats.rps_wins = (stats.rps_wins or 0) + (1 if result == "win" else 0)
    if result == "win":
        stats.total_wins = (stats.total_wins or 0) + 1
        await add_xp(session, user_id, XP_PER_WIN)
    elif result == "lose":
        stats.total_losses = (stats.total_losses or 0) + 1
    await add_xp(session, user_id, XP_PER_GAME)

    return {
        "result": result,
        "player_choice": player_choice,
        "bot_choice": bot_choice,
        "winnings": winnings,
    }


async def create_duel(
    session: AsyncSession,
    group_id: int,
    challenger_id: int,
    opponent_id: Optional[int],
    wager: int,
    game_type: str,
    message_id: Optional[int] = None,
) -> Optional[Duel]:
    if wager > 0:
        success, _ = await deduct_coins(session, challenger_id, wager, "duel_bet", "Duel wager")
        if not success:
            return None

    duel = Duel(
        group_id=group_id,
        challenger_id=challenger_id,
        opponent_id=opponent_id,
        wager=wager,
        game_type=game_type,
        status="pending",
        message_id=message_id,
    )
    session.add(duel)
    await session.flush()
    return duel


async def accept_duel(
    session: AsyncSession,
    duel_id: int,
    opponent_id: int,
) -> Tuple[Optional[Duel], dict]:
    duel = await session.get(Duel, duel_id)
    if not duel or duel.status != "pending":
        return None, {}

    if duel.wager > 0:
        success, _ = await deduct_coins(session, opponent_id, duel.wager, "duel_bet", "Duel wager")
        if not success:
            return duel, {"error": "insufficient_funds"}

    duel.opponent_id = opponent_id
    duel.status = "active"
    result = await _play_duel(session, duel)
    return duel, result


async def _play_duel(session: AsyncSession, duel: Duel) -> dict:
    game = duel.game_type

    if game in ("dice", "classic_dice"):
        c_score = random.randint(1, 6)
        o_score = random.randint(1, 6)
    elif game == "rps":
        choices = [1, 2, 3]
        c_score = random.choice(choices)
        o_score = random.choice(choices)
    else:
        c_score = random.randint(1, 100)
        o_score = random.randint(1, 100)

    duel.challenger_score = c_score
    duel.opponent_score = o_score

    if c_score > o_score:
        winner_id = duel.challenger_id
        loser_id = duel.opponent_id
    elif o_score > c_score:
        winner_id = duel.opponent_id
        loser_id = duel.challenger_id
    else:
        duel.status = "completed"
        duel.winner_id = None
        duel.completed_at = datetime.now(timezone.utc)
        if duel.wager > 0:
            await add_coins(session, duel.challenger_id, duel.wager, "duel_draw", "Duel draw refund")
            await add_coins(session, duel.opponent_id, duel.wager, "duel_draw", "Duel draw refund")
        return {"result": "draw", "challenger_score": c_score, "opponent_score": o_score}

    duel.winner_id = winner_id
    duel.status = "completed"
    duel.completed_at = datetime.now(timezone.utc)

    if duel.wager > 0:
        prize = duel.wager * 2
        await add_coins(session, winner_id, prize, "duel_win", "Duel prize")

    c_stats = await get_or_create_duel_stats(session, duel.challenger_id)
    o_stats = await get_or_create_duel_stats(session, duel.opponent_id)

    if winner_id == duel.challenger_id:
        c_stats.wins = (c_stats.wins or 0) + 1
        c_stats.win_streak = (c_stats.win_streak or 0) + 1
        c_stats.best_streak = max(c_stats.best_streak or 0, c_stats.win_streak)
        c_stats.coins_won = (c_stats.coins_won or 0) + duel.wager
        o_stats.losses = (o_stats.losses or 0) + 1
        o_stats.win_streak = 0
        o_stats.coins_lost = (o_stats.coins_lost or 0) + duel.wager
    else:
        o_stats.wins = (o_stats.wins or 0) + 1
        o_stats.win_streak = (o_stats.win_streak or 0) + 1
        o_stats.best_streak = max(o_stats.best_streak or 0, o_stats.win_streak)
        o_stats.coins_won = (o_stats.coins_won or 0) + duel.wager
        c_stats.losses = (c_stats.losses or 0) + 1
        c_stats.win_streak = 0
        c_stats.coins_lost = (c_stats.coins_lost or 0) + duel.wager

    await add_xp(session, winner_id, XP_PER_WIN * 2)
    await add_xp(session, loser_id, XP_PER_GAME)

    return {
        "result": "win",
        "winner_id": winner_id,
        "loser_id": loser_id,
        "challenger_score": c_score,
        "opponent_score": o_score,
        "prize": duel.wager * 2 if duel.wager > 0 else 0,
    }


async def play_mines(
    session: AsyncSession,
    user_id: int,
    row: int,
    col: int,
    match_id: int,
    wager: int = 0,
) -> dict:
    match = await session.get(GameMatch, match_id)
    if not match or match.status != "active":
        return {"error": "match_not_found"}

    data = match.data or {}
    board = data.get("board", [])
    revealed = data.get("revealed", [])
    mines = data.get("mines", [])
    multiplier = data.get("multiplier", 1.0)

    cell_idx = row * 5 + col
    if cell_idx in revealed:
        return {"error": "already_revealed"}

    revealed.append(cell_idx)
    is_mine = cell_idx in mines

    if is_mine:
        match.status = "completed"
        data["revealed"] = revealed
        data["result"] = "mine"
        match.data = data
        return {"result": "mine", "row": row, "col": col}

    safe_count = len(revealed)
    multiplier = round(1 + (safe_count * 0.2), 2)
    data["revealed"] = revealed
    data["multiplier"] = multiplier
    match.data = data

    return {
        "result": "safe",
        "row": row,
        "col": col,
        "multiplier": multiplier,
        "safe_count": safe_count,
    }


def create_mines_board(rows: int = 5, cols: int = 5, mine_count: int = 5) -> dict:
    total = rows * cols
    mines = random.sample(range(total), mine_count)
    return {"board": [[None] * cols for _ in range(rows)], "mines": mines, "revealed": [], "multiplier": 1.0}
