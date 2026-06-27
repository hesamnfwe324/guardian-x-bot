from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.database.models import Wallet, Transaction, Referral
from bot.services.user_service import get_or_create_wallet
from bot.config import settings
import structlog

logger = structlog.get_logger()


async def get_balance(session: AsyncSession, user_id: int) -> Tuple[int, int]:
    wallet = await get_or_create_wallet(session, user_id)
    return wallet.balance, wallet.bank_balance


async def add_coins(
    session: AsyncSession,
    user_id: int,
    amount: int,
    tx_type: str = "reward",
    description: str = "",
    reference_id: Optional[str] = None,
) -> int:
    wallet = await get_or_create_wallet(session, user_id)
    wallet.balance = (wallet.balance or 0) + amount
    wallet.total_earned = (wallet.total_earned or 0) + max(0, amount)
    tx = Transaction(
        wallet_id=wallet.id,
        amount=amount,
        type=tx_type,
        description=description,
        reference_id=reference_id,
    )
    session.add(tx)
    return wallet.balance


async def deduct_coins(
    session: AsyncSession,
    user_id: int,
    amount: int,
    tx_type: str = "spend",
    description: str = "",
) -> Tuple[bool, int]:
    wallet = await get_or_create_wallet(session, user_id)
    if wallet.balance < amount:
        return False, wallet.balance
    wallet.balance -= amount
    wallet.total_spent = (wallet.total_spent or 0) + amount
    tx = Transaction(
        wallet_id=wallet.id,
        amount=-amount,
        type=tx_type,
        description=description,
    )
    session.add(tx)
    return True, wallet.balance


async def deposit_to_bank(session: AsyncSession, user_id: int, amount: int) -> Tuple[bool, int, int]:
    wallet = await get_or_create_wallet(session, user_id)
    if wallet.balance < amount:
        return False, wallet.balance, wallet.bank_balance
    wallet.balance -= amount
    wallet.bank_balance = (wallet.bank_balance or 0) + amount
    return True, wallet.balance, wallet.bank_balance


async def withdraw_from_bank(session: AsyncSession, user_id: int, amount: int) -> Tuple[bool, int, int]:
    wallet = await get_or_create_wallet(session, user_id)
    if wallet.bank_balance < amount:
        return False, wallet.balance, wallet.bank_balance
    wallet.bank_balance -= amount
    wallet.balance = (wallet.balance or 0) + amount
    return True, wallet.balance, wallet.bank_balance


async def transfer_coins(
    session: AsyncSession,
    from_user_id: int,
    to_user_id: int,
    amount: int,
) -> Tuple[bool, str]:
    success, remaining = await deduct_coins(session, from_user_id, amount, "transfer_out", f"Transfer to {to_user_id}")
    if not success:
        return False, "insufficient_funds"
    await add_coins(session, to_user_id, amount, "transfer_in", f"Transfer from {from_user_id}")
    return True, "success"


async def claim_daily_reward(session: AsyncSession, user_id: int) -> Tuple[bool, int, Optional[datetime]]:
    wallet = await get_or_create_wallet(session, user_id)
    now = datetime.now(timezone.utc)
    if wallet.last_daily:
        last = wallet.last_daily.replace(tzinfo=timezone.utc) if wallet.last_daily.tzinfo is None else wallet.last_daily
        next_claim = last + timedelta(hours=24)
        if now < next_claim:
            return False, 0, next_claim
    amount = settings.DAILY_REWARD
    wallet.balance = (wallet.balance or 0) + amount
    wallet.total_earned = (wallet.total_earned or 0) + amount
    wallet.last_daily = now
    tx = Transaction(wallet_id=wallet.id, amount=amount, type="daily_reward", description="Daily reward")
    session.add(tx)
    return True, amount, None


async def claim_weekly_reward(session: AsyncSession, user_id: int) -> Tuple[bool, int, Optional[datetime]]:
    wallet = await get_or_create_wallet(session, user_id)
    now = datetime.now(timezone.utc)
    if wallet.last_weekly:
        last = wallet.last_weekly.replace(tzinfo=timezone.utc) if wallet.last_weekly.tzinfo is None else wallet.last_weekly
        next_claim = last + timedelta(days=7)
        if now < next_claim:
            return False, 0, next_claim
    amount = settings.WEEKLY_REWARD
    wallet.balance = (wallet.balance or 0) + amount
    wallet.total_earned = (wallet.total_earned or 0) + amount
    wallet.last_weekly = now
    tx = Transaction(wallet_id=wallet.id, amount=amount, type="weekly_reward", description="Weekly reward")
    session.add(tx)
    return True, amount, None


async def claim_monthly_reward(session: AsyncSession, user_id: int) -> Tuple[bool, int, Optional[datetime]]:
    wallet = await get_or_create_wallet(session, user_id)
    now = datetime.now(timezone.utc)
    if wallet.last_monthly:
        last = wallet.last_monthly.replace(tzinfo=timezone.utc) if wallet.last_monthly.tzinfo is None else wallet.last_monthly
        next_claim = last + timedelta(days=30)
        if now < next_claim:
            return False, 0, next_claim
    amount = settings.MONTHLY_REWARD
    wallet.balance = (wallet.balance or 0) + amount
    wallet.total_earned = (wallet.total_earned or 0) + amount
    wallet.last_monthly = now
    tx = Transaction(wallet_id=wallet.id, amount=amount, type="monthly_reward", description="Monthly reward")
    session.add(tx)
    return True, amount, None


async def get_transactions(session: AsyncSession, user_id: int, limit: int = 10) -> list:
    wallet = await get_or_create_wallet(session, user_id)
    result = await session.execute(
        select(Transaction)
        .where(Transaction.wallet_id == wallet.id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def process_referral(
    session: AsyncSession,
    referrer_id: int,
    new_user_id: int,
) -> bool:
    """
    Record a referral and credit the referrer if not already rewarded.
    Returns True if the referral reward was granted, False otherwise.
    """
    existing = await session.scalar(
        select(Referral).where(Referral.referred_id == new_user_id)
    )
    if existing:
        return False

    referral = Referral(
        referrer_id=referrer_id,
        referred_id=new_user_id,
        reward_given=False,
    )
    session.add(referral)
    await session.flush()

    referrer_wallet = await get_or_create_wallet(session, referrer_id)
    referrer_wallet.balance = (referrer_wallet.balance or 0) + settings.REFERRAL_REWARD

    tx = Transaction(
        wallet_id=referrer_wallet.id,
        amount=settings.REFERRAL_REWARD,
        type="referral_reward",
        description=f"Referral reward for inviting user {new_user_id}",
    )
    session.add(tx)

    referral.reward_given = True

    logger.info(
        "Referral reward granted",
        referrer_id=referrer_id,
        new_user_id=new_user_id,
        reward=settings.REFERRAL_REWARD,
    )
    return True
