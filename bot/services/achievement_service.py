from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from bot.database.models import Achievement, UserAchievement
from bot.services.economy_service import add_coins
from bot.services.user_service import add_xp
import structlog

logger = structlog.get_logger()

ACHIEVEMENTS = [
    {"code": "first_message", "category": "activity", "icon": "💬", "points": 5, "reward_coins": 50, "reward_xp": 10, "req_type": "messages", "req_value": 1},
    {"code": "chat_100", "category": "activity", "icon": "💬", "points": 10, "reward_coins": 100, "reward_xp": 25, "req_type": "messages", "req_value": 100},
    {"code": "chat_1000", "category": "activity", "icon": "📣", "points": 25, "reward_coins": 500, "reward_xp": 100, "req_type": "messages", "req_value": 1000},
    {"code": "chat_10000", "category": "activity", "icon": "📢", "points": 75, "reward_coins": 2000, "reward_xp": 500, "req_type": "messages", "req_value": 10000},
    {"code": "first_win", "category": "games", "icon": "🏆", "points": 10, "reward_coins": 100, "reward_xp": 20, "req_type": "game_wins", "req_value": 1},
    {"code": "wins_10", "category": "games", "icon": "🥇", "points": 20, "reward_coins": 300, "reward_xp": 50, "req_type": "game_wins", "req_value": 10},
    {"code": "wins_50", "category": "games", "icon": "🏅", "points": 50, "reward_coins": 1000, "reward_xp": 200, "req_type": "game_wins", "req_value": 50},
    {"code": "wins_100", "category": "games", "icon": "🎖️", "points": 100, "reward_coins": 3000, "reward_xp": 500, "req_type": "game_wins", "req_value": 100},
    {"code": "wins_500", "category": "games", "icon": "👑", "points": 200, "reward_coins": 10000, "reward_xp": 1000, "req_type": "game_wins", "req_value": 500},
    {"code": "dice_master", "category": "games", "icon": "🎲", "points": 30, "reward_coins": 500, "reward_xp": 100, "req_type": "dice_wins", "req_value": 20},
    {"code": "wheel_lucky", "category": "games", "icon": "🎡", "points": 20, "reward_coins": 300, "reward_xp": 50, "req_type": "wheel_wins", "req_value": 10},
    {"code": "rps_champion", "category": "games", "icon": "✊", "points": 20, "reward_coins": 300, "reward_xp": 50, "req_type": "rps_wins", "req_value": 10},
    {"code": "first_duel", "category": "games", "icon": "⚔️", "points": 10, "reward_coins": 150, "reward_xp": 30, "req_type": "duels", "req_value": 1},
    {"code": "duel_champion", "category": "games", "icon": "🗡️", "points": 50, "reward_coins": 1500, "reward_xp": 300, "req_type": "duel_wins", "req_value": 25},
    {"code": "rich_100", "category": "economy", "icon": "💰", "points": 5, "reward_coins": 0, "reward_xp": 10, "req_type": "coins", "req_value": 100},
    {"code": "rich_1000", "category": "economy", "icon": "💵", "points": 15, "reward_coins": 0, "reward_xp": 25, "req_type": "coins", "req_value": 1000},
    {"code": "rich_10000", "category": "economy", "icon": "💎", "points": 50, "reward_coins": 0, "reward_xp": 100, "req_type": "coins", "req_value": 10000},
    {"code": "rich_100000", "category": "economy", "icon": "👑", "points": 150, "reward_coins": 0, "reward_xp": 500, "req_type": "coins", "req_value": 100000},
    {"code": "daily_streak_7", "category": "activity", "icon": "🔥", "points": 20, "reward_coins": 500, "reward_xp": 100, "req_type": "streak", "req_value": 7},
    {"code": "daily_streak_30", "category": "activity", "icon": "⚡", "points": 75, "reward_coins": 2000, "reward_xp": 500, "req_type": "streak", "req_value": 30},
    {"code": "daily_streak_100", "category": "activity", "icon": "🌟", "points": 200, "reward_coins": 5000, "reward_xp": 1000, "req_type": "streak", "req_value": 100},
    {"code": "level_5", "category": "activity", "icon": "⭐", "points": 10, "reward_coins": 200, "reward_xp": 0, "req_type": "level", "req_value": 5},
    {"code": "level_10", "category": "activity", "icon": "🌟", "points": 25, "reward_coins": 500, "reward_xp": 0, "req_type": "level", "req_value": 10},
    {"code": "level_25", "category": "activity", "icon": "💫", "points": 75, "reward_coins": 1500, "reward_xp": 0, "req_type": "level", "req_value": 25},
    {"code": "level_50", "category": "activity", "icon": "✨", "points": 150, "reward_coins": 3000, "reward_xp": 0, "req_type": "level", "req_value": 50},
    {"code": "level_100", "category": "activity", "icon": "🏆", "points": 500, "reward_coins": 10000, "reward_xp": 0, "req_type": "level", "req_value": 100},
    {"code": "first_referral", "category": "community", "icon": "👥", "points": 15, "reward_coins": 300, "reward_xp": 50, "req_type": "referrals", "req_value": 1},
    {"code": "referral_10", "category": "community", "icon": "🤝", "points": 50, "reward_coins": 1000, "reward_xp": 200, "req_type": "referrals", "req_value": 10},
    {"code": "referral_50", "category": "community", "icon": "🌐", "points": 150, "reward_coins": 5000, "reward_xp": 500, "req_type": "referrals", "req_value": 50},
    {"code": "first_rep", "category": "community", "icon": "👍", "points": 5, "reward_coins": 50, "reward_xp": 10, "req_type": "rep_given", "req_value": 1},
    {"code": "rep_king", "category": "community", "icon": "🌟", "points": 100, "reward_coins": 2000, "reward_xp": 500, "req_type": "positive_rep", "req_value": 50},
    {"code": "tournament_participant", "category": "events", "icon": "🏆", "points": 10, "reward_coins": 200, "reward_xp": 50, "req_type": "tournaments", "req_value": 1},
    {"code": "tournament_winner", "category": "events", "icon": "🥇", "points": 100, "reward_coins": 5000, "reward_xp": 500, "req_type": "tournament_wins", "req_value": 1},
    {"code": "mission_10", "category": "activity", "icon": "📋", "points": 20, "reward_coins": 400, "reward_xp": 100, "req_type": "missions", "req_value": 10},
    {"code": "mission_50", "category": "activity", "icon": "📊", "points": 75, "reward_coins": 1500, "reward_xp": 300, "req_type": "missions", "req_value": 50},
    {"code": "mission_100", "category": "activity", "icon": "📈", "points": 200, "reward_coins": 5000, "reward_xp": 1000, "req_type": "missions", "req_value": 100},
    {"code": "early_bird", "category": "events", "icon": "🐦", "points": 25, "reward_coins": 500, "reward_xp": 100, "req_type": "special", "req_value": 1},
    {"code": "night_owl", "category": "events", "icon": "🦉", "points": 25, "reward_coins": 500, "reward_xp": 100, "req_type": "special", "req_value": 1},
    {"code": "collector", "category": "economy", "icon": "🗃️", "points": 30, "reward_coins": 600, "reward_xp": 150, "req_type": "shop_items", "req_value": 5},
    {"code": "big_spender", "category": "economy", "icon": "💸", "points": 40, "reward_coins": 0, "reward_xp": 200, "req_type": "total_spent", "req_value": 10000},
    {"code": "jackpot", "category": "games", "icon": "🎰", "points": 100, "reward_coins": 2000, "reward_xp": 500, "req_type": "big_win", "req_value": 1000},
    {"code": "perfectionist", "category": "activity", "icon": "💯", "points": 50, "reward_coins": 1000, "reward_xp": 300, "req_type": "missions_daily_7", "req_value": 7},
    {"code": "social_butterfly", "category": "community", "icon": "🦋", "points": 30, "reward_coins": 600, "reward_xp": 150, "req_type": "groups", "req_value": 3},
    {"code": "veteran", "category": "activity", "icon": "🎖️", "points": 100, "reward_coins": 2000, "reward_xp": 1000, "req_type": "days_active", "req_value": 365},
    {"code": "coin_hoarder", "category": "economy", "icon": "🐉", "points": 200, "reward_coins": 0, "reward_xp": 1000, "req_type": "coins", "req_value": 1000000},
    {"code": "quiz_scholar", "category": "games", "icon": "🧠", "points": 50, "reward_coins": 1000, "reward_xp": 250, "req_type": "quiz_wins", "req_value": 25},
    {"code": "mines_expert", "category": "games", "icon": "💣", "points": 40, "reward_coins": 800, "reward_xp": 200, "req_type": "mines_wins", "req_value": 15},
    {"code": "card_shark", "category": "games", "icon": "🃏", "points": 40, "reward_coins": 800, "reward_xp": 200, "req_type": "card_wins", "req_value": 20},
    {"code": "chess_player", "category": "games", "icon": "♟️", "points": 35, "reward_coins": 700, "reward_xp": 175, "req_type": "chess_wins", "req_value": 10},
    {"code": "game_addict", "category": "games", "icon": "🎮", "points": 75, "reward_coins": 1500, "reward_xp": 400, "req_type": "total_games", "req_value": 500},
    {"code": "high_roller", "category": "economy", "icon": "🎲", "points": 60, "reward_coins": 0, "reward_xp": 300, "req_type": "total_bet", "req_value": 50000},
    {"code": "lucky_one", "category": "games", "icon": "🍀", "points": 100, "reward_coins": 3000, "reward_xp": 500, "req_type": "special_win", "req_value": 1},
    {"code": "comeback_king", "category": "games", "icon": "👑", "points": 50, "reward_coins": 1000, "reward_xp": 300, "req_type": "win_after_loss", "req_value": 5},
    {"code": "win_streak_5", "category": "games", "icon": "🔥", "points": 30, "reward_coins": 500, "reward_xp": 150, "req_type": "win_streak", "req_value": 5},
    {"code": "win_streak_10", "category": "games", "icon": "⚡", "points": 75, "reward_coins": 1500, "reward_xp": 400, "req_type": "win_streak", "req_value": 10},
    {"code": "win_streak_20", "category": "games", "icon": "🌩️", "points": 150, "reward_coins": 4000, "reward_xp": 800, "req_type": "win_streak", "req_value": 20},
    {"code": "duel_streak_5", "category": "games", "icon": "⚔️", "points": 50, "reward_coins": 1000, "reward_xp": 250, "req_type": "duel_streak", "req_value": 5},
    {"code": "treasure_hunter", "category": "games", "icon": "🗺️", "points": 35, "reward_coins": 700, "reward_xp": 175, "req_type": "treasure_wins", "req_value": 10},
    {"code": "roulette_survivor", "category": "games", "icon": "🎰", "points": 25, "reward_coins": 500, "reward_xp": 125, "req_type": "roulette_played", "req_value": 10},
    {"code": "generous_donor", "category": "community", "icon": "🤲", "points": 40, "reward_coins": 0, "reward_xp": 200, "req_type": "transfers_sent", "req_value": 10},
    {"code": "good_karma", "category": "community", "icon": "☮️", "points": 30, "reward_coins": 600, "reward_xp": 150, "req_type": "positive_rep_given", "req_value": 10},
    {"code": "power_user", "category": "activity", "icon": "⚡", "points": 100, "reward_coins": 2000, "reward_xp": 1000, "req_type": "features_used", "req_value": 50},
]


async def seed_achievements(session: AsyncSession) -> None:
    for ach_data in ACHIEVEMENTS:
        existing = await session.scalar(
            select(Achievement).where(Achievement.code == ach_data["code"])
        )
        if not existing:
            ach = Achievement(
                code=ach_data["code"],
                category=ach_data["category"],
                name_key=f"ach_{ach_data['code']}_name",
                description_key=f"ach_{ach_data['code']}_desc",
                icon=ach_data["icon"],
                points=ach_data["points"],
                reward_coins=ach_data["reward_coins"],
                reward_xp=ach_data["reward_xp"],
                requirement_type=ach_data["req_type"],
                requirement_value=ach_data["req_value"],
            )
            session.add(ach)
    await session.commit()
    logger.info("Achievements seeded", count=len(ACHIEVEMENTS))


async def check_and_award_achievements(
    session: AsyncSession,
    user_id: int,
    metric_type: str,
    metric_value: int,
) -> list[Achievement]:
    result = await session.execute(
        select(Achievement).where(
            and_(
                Achievement.requirement_type == metric_type,
                Achievement.requirement_value <= metric_value,
            )
        )
    )
    all_matching = result.scalars().all()
    earned = []
    for ach in all_matching:
        existing = await session.scalar(
            select(UserAchievement).where(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_id == ach.id,
                )
            )
        )
        if not existing:
            ua = UserAchievement(user_id=user_id, achievement_id=ach.id, progress=metric_value)
            session.add(ua)
            if ach.reward_coins > 0:
                await add_coins(session, user_id, ach.reward_coins, "achievement", f"Achievement: {ach.code}")
            if ach.reward_xp > 0:
                await add_xp(session, user_id, ach.reward_xp)
            earned.append(ach)
    return earned


async def get_user_achievements(session: AsyncSession, user_id: int) -> list:
    result = await session.execute(
        select(UserAchievement, Achievement)
        .join(Achievement, Achievement.id == UserAchievement.achievement_id)
        .where(UserAchievement.user_id == user_id)
        .order_by(UserAchievement.earned_at.desc())
    )
    return result.all()
