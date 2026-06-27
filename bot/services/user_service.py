from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from bot.database.models import User, Wallet, Economy, Reputation, DuelStats, GameStats
import structlog

logger = structlog.get_logger()


async def get_or_create_wallet(session: AsyncSession, user_id: int) -> Wallet:
    wallet = await session.scalar(select(Wallet).where(Wallet.user_id == user_id))
    if not wallet:
        wallet = Wallet(user_id=user_id, balance=0, bank_balance=0)
        session.add(wallet)
        await session.flush()
    return wallet


async def get_or_create_economy(session: AsyncSession, user_id: int) -> Economy:
    eco = await session.scalar(select(Economy).where(Economy.user_id == user_id))
    if not eco:
        eco = Economy(user_id=user_id, xp=0, level=1)
        session.add(eco)
        await session.flush()
    return eco


async def get_or_create_reputation(session: AsyncSession, user_id: int) -> Reputation:
    rep = await session.scalar(select(Reputation).where(Reputation.user_id == user_id))
    if not rep:
        rep = Reputation(user_id=user_id, positive=0, negative=0)
        session.add(rep)
        await session.flush()
    return rep


async def get_or_create_duel_stats(session: AsyncSession, user_id: int) -> DuelStats:
    stats = await session.scalar(select(DuelStats).where(DuelStats.user_id == user_id))
    if not stats:
        stats = DuelStats(user_id=user_id)
        session.add(stats)
        await session.flush()
    return stats


async def get_or_create_game_stats(session: AsyncSession, user_id: int) -> GameStats:
    stats = await session.scalar(select(GameStats).where(GameStats.user_id == user_id))
    if not stats:
        stats = GameStats(user_id=user_id)
        session.add(stats)
        await session.flush()
    return stats


async def set_user_language(session: AsyncSession, user_id: int, lang: str) -> None:
    await session.execute(
        update(User).where(User.id == user_id).values(language=lang)
    )


async def add_xp(session: AsyncSession, user_id: int, amount: int) -> tuple[int, int, bool]:
    from bot.utils.helpers import calculate_level
    eco = await get_or_create_economy(session, user_id)
    old_level = eco.level
    eco.total_xp = (eco.total_xp or 0) + amount
    eco.xp = (eco.xp or 0) + amount
    new_level, current_xp, needed_xp = calculate_level(eco.total_xp)
    leveled_up = new_level > old_level
    eco.level = new_level
    eco.xp = current_xp
    return new_level, current_xp, leveled_up


async def get_top_users_by_level(session: AsyncSession, limit: int = 10) -> list:
    result = await session.execute(
        select(User, Economy)
        .join(Economy, Economy.user_id == User.id)
        .order_by(Economy.total_xp.desc())
        .limit(limit)
    )
    return result.all()


async def get_top_users_by_coins(session: AsyncSession, limit: int = 10) -> list:
    result = await session.execute(
        select(User, Wallet)
        .join(Wallet, Wallet.user_id == User.id)
        .order_by((Wallet.balance + Wallet.bank_balance).desc())
        .limit(limit)
    )
    return result.all()


async def get_top_reputation(session: AsyncSession, limit: int = 10) -> list:
    result = await session.execute(
        select(User, Reputation)
        .join(Reputation, Reputation.user_id == User.id)
        .order_by(Reputation.positive.desc())
        .limit(limit)
    )
    return result.all()
