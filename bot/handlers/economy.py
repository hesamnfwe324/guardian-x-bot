from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.economy import economy_menu_kb, wallet_kb, rewards_menu_kb, shop_categories_kb, missions_kb
from bot.keyboards.main_menu import back_button_kb
from bot.services.economy_service import (
    get_balance, claim_daily_reward, claim_weekly_reward, claim_monthly_reward,
    deposit_to_bank, withdraw_from_bank, transfer_coins, get_transactions
)
from bot.services.user_service import get_or_create_wallet, add_xp, get_top_users_by_coins, get_top_users_by_level
from bot.utils.helpers import format_number, get_time_until, safe_username
import structlog

logger = structlog.get_logger()
router = Router()


class EconomyStates(StatesGroup):
    waiting_deposit = State()
    waiting_withdraw = State()
    waiting_transfer_user = State()
    waiting_transfer_amount = State()


@router.callback_query(F.data == "menu:economy")
async def economy_menu(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    balance, bank = await get_balance(db_session, db_user.id)
    text = (
        _("economy_menu") + "\n\n"
        + _("balance").format(amount=format_number(balance)) + "\n"
        + _("bank").format(amount=format_number(bank))
    )
    await callback.message.edit_text(text, reply_markup=economy_menu_kb(_), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "eco:wallet")
async def wallet_view(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    balance, bank = await get_balance(db_session, db_user.id)
    wallet = await get_or_create_wallet(db_session, db_user.id)
    text = (
        _("wallet_title") + "\n\n"
        + _("balance").format(amount=format_number(balance)) + "\n"
        + _("bank").format(amount=format_number(bank)) + "\n"
        + _("total_earned").format(amount=format_number(wallet.total_earned or 0))
    )
    await callback.message.edit_text(text, reply_markup=wallet_kb(_), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "eco:daily")
async def claim_daily(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    success, amount, next_claim = await claim_daily_reward(db_session, db_user.id)
    if success:
        await callback.answer(_("daily_reward").format(amount=amount), show_alert=True)
    else:
        time_str = get_time_until(next_claim) if next_claim else "soon"
        await callback.answer(_("reward_cooldown").format(type="daily", time=time_str), show_alert=True)


@router.callback_query(F.data == "eco:weekly")
async def claim_weekly(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    success, amount, next_claim = await claim_weekly_reward(db_session, db_user.id)
    if success:
        await callback.answer(_("weekly_reward").format(amount=amount), show_alert=True)
    else:
        time_str = get_time_until(next_claim) if next_claim else "soon"
        await callback.answer(_("reward_cooldown").format(type="weekly", time=time_str), show_alert=True)


@router.callback_query(F.data == "eco:monthly")
async def claim_monthly(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    success, amount, next_claim = await claim_monthly_reward(db_session, db_user.id)
    if success:
        await callback.answer(_("monthly_reward").format(amount=amount), show_alert=True)
    else:
        time_str = get_time_until(next_claim) if next_claim else "soon"
        await callback.answer(_("reward_cooldown").format(type="monthly", time=time_str), show_alert=True)


@router.callback_query(F.data == "eco:deposit")
async def start_deposit(callback: CallbackQuery, _: callable, state: FSMContext, **kwargs):
    await state.set_state(EconomyStates.waiting_deposit)
    await callback.message.answer(_("enter_amount"))
    await callback.answer()


@router.message(EconomyStates.waiting_deposit)
async def process_deposit(message: Message, _: callable, db_session: AsyncSession, db_user, state: FSMContext, **kwargs):
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.reply(_("invalid_amount"))
        return
    success, bal, bank = await deposit_to_bank(db_session, db_user.id, amount)
    if success:
        await message.reply(_("deposit_success").format(amount=format_number(amount)))
    else:
        wallet = await get_or_create_wallet(db_session, db_user.id)
        await message.reply(_("insufficient_funds").format(balance=format_number(wallet.balance or 0)))
    await state.clear()


@router.callback_query(F.data == "eco:withdraw")
async def start_withdraw(callback: CallbackQuery, _: callable, state: FSMContext, **kwargs):
    await state.set_state(EconomyStates.waiting_withdraw)
    await callback.message.answer(_("enter_amount"))
    await callback.answer()


@router.message(EconomyStates.waiting_withdraw)
async def process_withdraw(message: Message, _: callable, db_session: AsyncSession, db_user, state: FSMContext, **kwargs):
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.reply(_("invalid_amount"))
        return
    success, bal, bank = await withdraw_from_bank(db_session, db_user.id, amount)
    if success:
        await message.reply(_("withdraw_success").format(amount=format_number(amount)))
    else:
        wallet = await get_or_create_wallet(db_session, db_user.id)
        await message.reply(_("insufficient_funds").format(balance=format_number(wallet.bank_balance or 0)))
    await state.clear()


@router.callback_query(F.data == "eco:transactions")
async def view_transactions(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    txs = await get_transactions(db_session, db_user.id, limit=10)
    if not txs:
        await callback.answer(_("no_data"), show_alert=True)
        return
    text = "📋 <b>Recent Transactions</b>\n\n"
    for tx in txs:
        sign = "+" if tx.amount > 0 else ""
        text += f"{sign}{format_number(tx.amount)} — {tx.type} — {tx.created_at.strftime('%m/%d %H:%M')}\n"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "eco:wallet"))
    await callback.answer()


@router.callback_query(F.data == "eco:referral")
async def referral_info(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    from bot.config import settings
    bot_info = await callback.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{db_user.id}"
    text = (
        "👥 <b>Referral Program</b>\n\n"
        f"Invite friends and earn <b>{settings.REFERRAL_REWARD} coins</b> per referral!\n\n"
        f"Your referral link:\n<code>{ref_link}</code>"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:economy"))
    await callback.answer()


@router.callback_query(F.data == "menu:rewards")
async def rewards_menu(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(
        "🎁 <b>Rewards Center</b>",
        reply_markup=rewards_menu_kb(_),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "rewards:shop")
async def shop_menu(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(
        _("shop_menu"),
        reply_markup=shop_categories_kb(_),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "rewards:missions")
async def missions_menu(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(
        _("missions_menu"),
        reply_markup=missions_kb(_),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "rewards:achievements")
async def achievements_menu(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    from bot.services.achievement_service import get_user_achievements
    user_achs = await get_user_achievements(db_session, db_user.id)
    text = _("achievements_menu") + "\n\n"
    text += _("achievements_count").format(earned=len(user_achs), total=100) + "\n\n"
    if user_achs:
        for ua, ach in user_achs[:10]:
            text += f"{ach.icon} <b>{ach.code}</b> — {ach.points} pts\n"
    else:
        text += _("no_data")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:rewards"))
    await callback.answer()


@router.message(Command("balance", "wallet"))
async def cmd_balance(message: Message, _: callable, db_session: AsyncSession, db_user, **kwargs):
    balance, bank = await get_balance(db_session, db_user.id)
    text = (
        _("wallet_title") + "\n\n"
        + _("balance").format(amount=format_number(balance)) + "\n"
        + _("bank").format(amount=format_number(bank))
    )
    await message.reply(text, parse_mode="HTML")


@router.callback_query(F.data == "eco:bank")
async def bank_view(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_user, **kwargs):
    balance, bank = await get_balance(db_session, db_user.id)
    text = (
        "🏦 <b>Bank</b>\n\n"
        + _("bank").format(amount=format_number(bank)) + "\n"
        + _("balance").format(amount=format_number(balance)) + "\n\n"
        "Use <b>Deposit</b> to move coins to the bank (safe from theft).\n"
        "Use <b>Withdraw</b> to move coins back to your wallet."
    )
    from bot.keyboards.economy import wallet_kb
    await callback.message.edit_text(text, reply_markup=wallet_kb(_), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "eco:transfer")
async def start_transfer(callback: CallbackQuery, _: callable, state: FSMContext, **kwargs):
    await state.set_state(EconomyStates.waiting_transfer_user)
    await callback.message.answer(
        "↗️ <b>Transfer Coins</b>\n\nEnter the username or user ID to transfer to:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(EconomyStates.waiting_transfer_user)
async def process_transfer_user(message: Message, _: callable, db_session: AsyncSession, state: FSMContext, **kwargs):
    from sqlalchemy import select as _select
    from bot.database.models import User
    text = message.text.strip().lstrip("@")
    try:
        uid = int(text)
        target = await db_session.get(User, uid)
    except ValueError:
        target = await db_session.scalar(_select(User).where(User.username == text))
    if not target:
        await message.reply("❌ User not found. Try again with a valid @username or user ID.")
        return
    await state.update_data(transfer_target_id=target.id, transfer_target_name=target.first_name)
    await state.set_state(EconomyStates.waiting_transfer_amount)
    await message.reply(f"✅ Transferring to <b>{target.first_name}</b>. Now enter the amount:", parse_mode="HTML")


@router.message(EconomyStates.waiting_transfer_amount)
async def process_transfer_amount(message: Message, _: callable, db_session: AsyncSession, db_user, state: FSMContext, **kwargs):
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.reply(_("invalid_amount"))
        return
    data = await state.get_data()
    target_id = data.get("transfer_target_id")
    target_name = data.get("transfer_target_name", "User")
    success, sender_bal, _ = await transfer_coins(db_session, db_user.id, target_id, amount)
    if success:
        await message.reply(
            f"✅ Transferred <b>{format_number(amount)}</b> coins to <b>{target_name}</b>!\n"
            f"Your new balance: <b>{format_number(sender_bal)}</b>",
            parse_mode="HTML",
        )
    else:
        wallet = await get_or_create_wallet(db_session, db_user.id)
        await message.reply(_("insufficient_funds").format(balance=format_number(wallet.balance or 0)))
    await state.clear()


@router.callback_query(F.data.startswith("shop:"))
async def shop_category(callback: CallbackQuery, _: callable, **kwargs):
    category = callback.data.split(":")[1]
    icons = {"badges": "🏷️", "titles": "👑", "frames": "🖼️", "lootboxes": "📦", "cosmetics": "✨"}
    icon = icons.get(category, "🛒")
    from bot.keyboards.economy import shop_categories_kb
    await callback.message.edit_text(
        f"{icon} <b>{category.capitalize()} Shop</b>\n\n"
        "🚧 This shop section is coming soon!\n"
        "Check back later for exciting items.",
        reply_markup=shop_categories_kb(_),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("missions:"))
async def missions_category(callback: CallbackQuery, _: callable, **kwargs):
    category = callback.data.split(":")[1]
    icons = {"daily": "☀️", "weekly": "📅", "monthly": "🗓️"}
    icon = icons.get(category, "📋")
    from bot.keyboards.economy import missions_kb
    await callback.message.edit_text(
        f"{icon} <b>{category.capitalize()} Missions</b>\n\n"
        "🚧 Missions are coming soon!\n"
        "Complete daily tasks to earn bonus coins and XP.",
        reply_markup=missions_kb(_),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("daily"))
async def cmd_daily(message: Message, _: callable, db_session: AsyncSession, db_user, **kwargs):
    success, amount, next_claim = await claim_daily_reward(db_session, db_user.id)
    if success:
        await message.reply(_("daily_reward").format(amount=amount))
    else:
        time_str = get_time_until(next_claim) if next_claim else "soon"
        await message.reply(_("reward_cooldown").format(type="daily", time=time_str))
