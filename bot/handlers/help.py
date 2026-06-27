from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.keyboards.main_menu import back_button_kb
import structlog

logger = structlog.get_logger()
router = Router()


def help_kb(_) -> object:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_help_security"), callback_data="help:security")
    builder.button(text=_("btn_help_moderation"), callback_data="help:moderation")
    builder.button(text=_("btn_help_economy"), callback_data="help:economy")
    builder.button(text=_("btn_help_games"), callback_data="help:games")
    builder.button(text="🎮 Games List", callback_data="help:gameslist")
    builder.button(text="⚔️ Duels & Tournaments", callback_data="help:duels")
    builder.button(text="🏆 Achievements", callback_data="help:achievements")
    builder.button(text="📋 All Commands", callback_data="help:commands")
    builder.button(text=_("btn_back"), callback_data="menu:main")
    builder.adjust(2, 2, 2, 1, 1)
    return builder.as_markup()


@router.callback_query(F.data == "menu:help")
async def help_menu(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(_("help_menu"), reply_markup=help_kb(_), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "help:security")
async def help_security(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(
        _("help_security_text"),
        reply_markup=back_button_kb(_, "menu:help"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "help:moderation")
async def help_moderation(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(
        _("help_moderation_text"),
        reply_markup=back_button_kb(_, "menu:help"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "help:economy")
async def help_economy(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(
        _("help_economy_text"),
        reply_markup=back_button_kb(_, "menu:help"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "help:games")
async def help_games(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(
        _("help_games_text"),
        reply_markup=back_button_kb(_, "menu:help"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "help:gameslist")
async def help_gameslist(callback: CallbackQuery, _: callable, **kwargs):
    text = (
        "🎮 <b>Available Games</b>\n\n"
        "1️⃣ 🎲 <b>Smart Dice</b> — 10 modes: Classic, Prediction, Lucky Multiplier, Best of 3/5, Tournament, Group Battle, Daily Challenge, Streak, VIP Arena\n\n"
        "2️⃣ 🧠 <b>Quiz Battle AI</b> — Answer trivia questions to win coins and XP\n\n"
        "3️⃣ 🗺️ <b>Treasure Hunt</b> — Find hidden treasures before others\n\n"
        "4️⃣ 🎡 <b>Lucky Wheel</b> — Spin the wheel for multiplier rewards\n\n"
        "5️⃣ 🃏 <b>Card Battle</b> — Classic card game with betting\n\n"
        "6️⃣ 🔢 <b>Number War</b> — Higher number wins the round\n\n"
        "7️⃣ ✊ <b>Rock Paper Scissors Arena</b> — Classic RPS with wagers\n\n"
        "8️⃣ 💣 <b>Mines Challenge</b> — Reveal tiles, avoid mines\n\n"
        "9️⃣ ♟️ <b>Chess Mini</b> — Quick chess battles\n\n"
        "🔟 🎰 <b>Safe Russian Roulette</b> — Thrill without real risk\n\n"
        "All games support: PvP • Coin Betting • Rankings • Statistics • Achievements"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:help"))
    await callback.answer()


@router.callback_query(F.data == "help:duels")
async def help_duels(callback: CallbackQuery, _: callable, **kwargs):
    text = (
        "⚔️ <b>Duels & Tournaments</b>\n\n"
        "<b>Duels:</b>\n"
        "• Challenge any user with /duel @user [wager]\n"
        "• Loser's wager goes to the winner\n"
        "• Track your duel history and stats\n"
        "• Win streak bonuses available\n\n"
        "<b>Tournaments:</b>\n"
        "• Automatic & Scheduled tournaments\n"
        "• Entry fee creates the prize pool\n"
        "• Bracket system for fair competition\n"
        "• Top 3 receive rewards and rankings boost"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:help"))
    await callback.answer()


@router.callback_query(F.data == "help:achievements")
async def help_achievements(callback: CallbackQuery, _: callable, **kwargs):
    text = (
        "🏅 <b>Achievement System</b>\n\n"
        "100+ achievements across 5 categories:\n\n"
        "🎮 <b>Games</b> — Win games, hit streaks, master specific games\n"
        "💰 <b>Economy</b> — Accumulate coins, spend wisely, bank milestones\n"
        "📊 <b>Activity</b> — Send messages, claim daily rewards, reach levels\n"
        "🤝 <b>Community</b> — Invite friends, give reputation, participate\n"
        "🎪 <b>Events</b> — Join tournaments, complete seasonal challenges\n\n"
        "Each achievement grants: Coins + XP + Achievement Points"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:help"))
    await callback.answer()


@router.callback_query(F.data == "help:commands")
async def help_commands(callback: CallbackQuery, _: callable, **kwargs):
    text = (
        "📋 <b>All Commands</b>\n\n"
        "<b>Moderation (Admin only):</b>\n"
        "/ban @user [reason] — Ban user\n"
        "/unban @user — Unban user\n"
        "/kick @user — Kick user\n"
        "/mute @user [time] — Mute user\n"
        "/unmute @user — Unmute user\n"
        "/warn @user [reason] — Warn user\n"
        "/unwarn @user — Remove warning\n"
        "/warns @user — View warnings\n"
        "/note @user <text> — Add note\n"
        "/history @user — View history\n\n"
        "<b>Economy:</b>\n"
        "/balance or /wallet — Check balance\n"
        "/daily — Claim daily reward\n\n"
        "<b>Games:</b>\n"
        "/duel @user [wager] — Challenge to duel\n\n"
        "<b>General:</b>\n"
        "/start — Start the bot\n"
        "/menu — Open main menu\n"
        "/help — Show this help\n"
        "/lock — Manage content locks\n"
        "/setwelcome — Set welcome message"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:help"))
    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message, _: callable, **kwargs):
    await message.answer(_("help_menu"), reply_markup=help_kb(_), parse_mode="HTML")
