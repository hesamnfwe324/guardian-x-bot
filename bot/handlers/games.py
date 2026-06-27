import random
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.games import games_menu_kb, dice_menu_kb, rps_choice_kb
from bot.keyboards.main_menu import back_button_kb
from bot.services.game_service import play_classic_dice, spin_wheel, play_rps
from bot.services.user_service import get_or_create_game_stats
from bot.utils.helpers import format_number
import structlog

logger = structlog.get_logger()
router = Router()


class GameStates(StatesGroup):
    waiting_dice_bet = State()
    waiting_wheel_bet = State()
    waiting_rps_bet = State()
    waiting_numwar_bet = State()
    waiting_cards_bet = State()
    waiting_roulette_bet = State()
    waiting_treasure_bet = State()


def _no_db_kb(_):
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_back"), callback_data="menu:games")
    return builder.as_markup()


# ─── منوی بازی‌ها ─────────────────────────────────────
@router.callback_query(F.data == "menu:games")
async def games_menu(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(_("games_menu"), reply_markup=games_menu_kb(_), parse_mode="HTML")
    await callback.answer()


# ─── تاس هوشمند ──────────────────────────────────────
@router.callback_query(F.data == "game:dice")
async def dice_menu(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(_("dice_menu"), reply_markup=dice_menu_kb(_), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("dice:"))
async def play_dice(callback: CallbackQuery, _: callable, db_session=None, db_user=None, state: FSMContext = None, **kwargs):
    mode = callback.data.split("dice:", 1)[1]

    if db_user is None or db_session is None:
        await callback.answer("❌ لطفاً دوباره /start بزنید.", show_alert=True)
        return

    if mode == "classic":
        await callback.message.answer(
            _("game_bet_prompt").format(min=0, max=1000),
            parse_mode="HTML"
        )
        if state:
            await state.set_state(GameStates.waiting_dice_bet)
            await state.update_data(mode="classic")
        await callback.answer()
        return

    wager = 50 if mode == "daily" else 0
    result = await play_classic_dice(db_session, db_user.id, wager=wager)
    if "error" in result:
        await callback.answer(_("insufficient_funds").format(balance="?"), show_alert=True)
        return

    dice_emoji = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    p = dice_emoji[result["player_roll"] - 1]
    b = dice_emoji[result["opponent_roll"] - 1]

    if mode == "daily":
        title = "📅 <b>چالش تاس روزانه</b>"
    elif mode == "lucky_mult":
        title = "⚡ <b>ضریب شانس</b>"
    else:
        title = "🎲 <b>تاس</b>"

    text = f"{title}\n━━━━━━━━━━━━\n\nشما: {p} <b>{result['player_roll']}</b>  vs  ربات: {b} <b>{result['opponent_roll']}</b>\n\n"
    if result["result"] == "win":
        text += _("game_won").format(amount=format_number(result["winnings"]))
    elif result["result"] == "lose":
        text += _("game_lost").format(amount=format_number(wager))
    else:
        text += _("game_draw")

    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:games"))
    await callback.answer()


@router.message(GameStates.waiting_dice_bet)
async def process_dice_bet(message: Message, _: callable, db_session=None, db_user=None, state: FSMContext = None, **kwargs):
    try:
        wager = int(message.text.strip())
        if wager < 0:
            raise ValueError
    except ValueError:
        await message.reply(_("invalid_amount"))
        return

    if db_user is None or db_session is None:
        await message.reply("❌ لطفاً دوباره /start بزنید.")
        if state:
            await state.clear()
        return

    result = await play_classic_dice(db_session, db_user.id, wager=wager)
    if "error" in result:
        await message.reply(_("insufficient_funds").format(balance="?"))
        if state:
            await state.clear()
        return

    dice_emoji = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    p = dice_emoji[result["player_roll"] - 1]
    b = dice_emoji[result["opponent_roll"] - 1]
    text = f"🎲 <b>نتیجه تاس</b>\n━━━━━━━━━━━━\n\nشما: {p} <b>{result['player_roll']}</b>  vs  ربات: {b} <b>{result['opponent_roll']}</b>\n\n"
    if result["result"] == "win":
        text += _("game_won").format(amount=format_number(result["winnings"]))
    elif result["result"] == "lose":
        text += _("game_lost").format(amount=format_number(wager))
    else:
        text += _("game_draw")

    await message.reply(text, parse_mode="HTML")
    if state:
        await state.clear()


# ─── چرخ شانس ────────────────────────────────────────
@router.callback_query(F.data == "game:wheel")
async def wheel_game(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await callback.answer("❌ لطفاً دوباره /start بزنید.", show_alert=True)
        return

    segments = [
        ("💀 باخت", 0),
        ("🟡 0.5×", 0),
        ("🟢 1.5×", 0),
        ("🔵 2×", 0),
        ("🟣 3×", 0),
        ("🌟 5×", 0),
        ("💎 10×", 0),
    ]
    probs = [0.30, 0.05, 0.20, 0.25, 0.15, 0.03, 0.02]
    rand = random.random()
    cumulative = 0.0
    chosen_label, chosen_mult = "💀 باخت", 0
    for i, prob in enumerate(probs):
        cumulative += prob
        if rand <= cumulative:
            chosen_label, chosen_mult = segments[i]
            break

    wager = 100
    result = await spin_wheel(db_session, db_user.id, wager=0)

    spin_animation = "🎡 " + " → ".join([s[0] for s in random.sample(segments, 4)]) + f" → <b>{chosen_label}</b>"

    if chosen_mult == 0:
        outcome = _("game_lost").format(amount=0)
    else:
        winnings = int(0)
        outcome = f"🎉 ضریب <b>{chosen_label}</b>!"

    text = (
        f"🎡 <b>چرخ شانس</b>\n━━━━━━━━━━━━\n\n"
        f"{spin_animation}\n\n"
        f"نتیجه: {chosen_label}\n\n"
        f"{outcome}"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:games"))
    await callback.answer()


# ─── سنگ کاغذ قیچی ────────────────────────────────────
@router.callback_query(F.data == "game:rps")
async def rps_game(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    builder = InlineKeyboardBuilder()
    builder.button(text="🪨 سنگ", callback_data="rps:0:rock")
    builder.button(text="📄 کاغذ", callback_data="rps:0:paper")
    builder.button(text="✂️ قیچی", callback_data="rps:0:scissors")
    builder.button(text=_("btn_back"), callback_data="menu:games")
    builder.adjust(3, 1)
    await callback.message.answer(
        "✊ <b>سنگ کاغذ قیچی</b>\n━━━━━━━━━━━━\n\nانتخاب خود را بزنید!",
        parse_mode="HTML",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rps:"))
async def process_rps(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    parts = callback.data.split(":")
    player_choice = parts[2] if len(parts) > 2 else "rock"

    if db_user is None or db_session is None:
        await callback.answer("❌ لطفاً دوباره /start بزنید.", show_alert=True)
        return

    result = await play_rps(db_session, db_user.id, player_choice, wager=0)
    emojis = {"rock": "🪨 سنگ", "paper": "📄 کاغذ", "scissors": "✂️ قیچی"}
    p_e = emojis.get(result["player_choice"], "❓")
    b_e = emojis.get(result["bot_choice"], "❓")

    if result["result"] == "win":
        outcome = f"🎉 <b>بردید!</b>"
    elif result["result"] == "lose":
        outcome = f"😔 <b>باختید!</b>"
    else:
        outcome = f"🤝 <b>مساوی!</b>"

    text = (
        f"✊ <b>سنگ کاغذ قیچی</b>\n━━━━━━━━━━━━\n\n"
        f"شما: {p_e}\n"
        f"ربات: {b_e}\n\n"
        f"{outcome}"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:games"))
    await callback.answer()


# ─── کوئیز هوش ────────────────────────────────────────
QUIZ_QUESTIONS = [
    ("پایتخت ایران کدام شهر است؟", ["تهران", "مشهد", "اصفهان", "شیراز"], 0),
    ("۷ × ۸ چند است؟", ["۵۴", "۵۶", "۶۴", "۴۸"], 1),
    ("کره زمین به دور خورشید در چند روز می‌گردد؟", ["۳۶۵", "۳۶۰", "۳۵۵", "۳۷۰"], 0),
    ("بزرگ‌ترین اقیانوس جهان کدام است؟", ["اطلس", "هند", "آرام", "منجمد شمالی"], 2),
    ("کدام عنصر سازنده اصلی آب است؟", ["اکسیژن", "هیدروژن", "نیتروژن", "کربن"], 1),
    ("چند ساعت در یک روز وجود دارد؟", ["۱۲", "۲۰", "۲۴", "۴۸"], 2),
    ("سریع‌ترین حیوان جهان کدام است؟", ["شیر", "یوزپلنگ", "عقاب", "اسب"], 1),
    ("اختراع تلفن به چه کسی نسبت داده می‌شود؟", ["ادیسون", "گراهام بل", "نیوتن", "مارکونی"], 1),
    ("۱۰۰ × ۱۰۰ چند است؟", ["۱۰۰۰", "۱۰۰۰۰", "۱۰۰۰۰۰", "۱۰۰"], 1),
    ("در شطرنج وزیر چگونه حرکت می‌کند؟", ["مثل رخ", "مثل اسب", "در همه جهات", "مورب"], 2),
]


@router.callback_query(F.data == "game:quiz")
async def quiz_game(callback: CallbackQuery, _: callable, **kwargs):
    q_text, options, correct = random.choice(QUIZ_QUESTIONS)
    builder = InlineKeyboardBuilder()
    for i, opt in enumerate(options):
        builder.button(text=opt, callback_data=f"quiz_ans:{correct}:{i}")
    builder.button(text=_("btn_back"), callback_data="menu:games")
    builder.adjust(2, 2, 1)
    await callback.message.answer(
        f"🧠 <b>کوئیز هوش</b>\n━━━━━━━━━━━━\n\n❓ {q_text}",
        parse_mode="HTML",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("quiz_ans:"))
async def quiz_answer(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    parts = callback.data.split(":")
    correct = int(parts[1])
    chosen = int(parts[2])
    is_correct = correct == chosen
    if is_correct:
        await callback.answer("✅ آفرین! جواب درسته! +20 XP", show_alert=True)
        if db_session and db_user:
            from bot.services.user_service import add_xp
            await add_xp(db_session, db_user.id, 20)
    else:
        await callback.answer("❌ اشتباه! جواب درست بود گزینه دیگری!", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=back_button_kb(_, "menu:games"))


# ─── نبرد اعداد ────────────────────────────────────────
@router.callback_query(F.data == "game:numwar")
async def numwar_game(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await callback.answer("❌ لطفاً دوباره /start بزنید.", show_alert=True)
        return

    player_num = random.randint(1, 100)
    bot_num = random.randint(1, 100)

    if player_num > bot_num:
        result_text = _("game_won").format(amount=50)
        icon = "🏆"
        if db_session and db_user:
            from bot.services.economy_service import add_coins
            await add_coins(db_session, db_user.id, 50, "game_win", "Number War win")
    elif player_num < bot_num:
        result_text = _("game_lost").format(amount=0)
        icon = "💀"
    else:
        result_text = _("game_draw")
        icon = "🤝"

    # نمایش پیشرفت‌وار
    p_bar = "█" * (player_num // 10) + "░" * (10 - player_num // 10)
    b_bar = "█" * (bot_num // 10) + "░" * (10 - bot_num // 10)

    text = (
        f"🔢 <b>نبرد اعداد</b>\n━━━━━━━━━━━━\n\n"
        f"شما:  <b>{player_num}</b> [{p_bar}]\n"
        f"ربات: <b>{bot_num}</b> [{b_bar}]\n\n"
        f"{icon} {result_text}"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:games"))
    await callback.answer()


# ─── نبرد کارت ────────────────────────────────────────
CARD_RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
CARD_SUITS = ["♠️", "♥️", "♦️", "♣️"]


def random_card():
    return random.choice(CARD_RANKS), random.choice(CARD_SUITS)


@router.callback_query(F.data == "game:cards")
async def cards_game(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await callback.answer("❌ لطفاً دوباره /start بزنید.", show_alert=True)
        return

    p_rank, p_suit = random_card()
    b_rank, b_suit = random_card()
    p_val = CARD_RANKS.index(p_rank)
    b_val = CARD_RANKS.index(b_rank)

    if p_val > b_val:
        result_text = _("game_won").format(amount=75)
        icon = "🏆"
        if db_session and db_user:
            from bot.services.economy_service import add_coins
            await add_coins(db_session, db_user.id, 75, "game_win", "Card Battle win")
    elif p_val < b_val:
        result_text = _("game_lost").format(amount=0)
        icon = "💀"
    else:
        result_text = _("game_draw")
        icon = "🤝"

    text = (
        f"🃏 <b>نبرد کارت</b>\n━━━━━━━━━━━━\n\n"
        f"کارت شما:  {p_suit} <b>{p_rank}</b>\n"
        f"کارت ربات: {b_suit} <b>{b_rank}</b>\n\n"
        f"{icon} {result_text}"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:games"))
    await callback.answer()


# ─── شکار گنج ────────────────────────────────────────
TREASURE_MAPS = [
    "🗺️ نقشه به ❌۳، ⬇️۲ اشاره می‌کند...",
    "🗺️ نقشه می‌گوید گنج زیر ⭐ است...",
    "🗺️ نقشه رمزآلود را باز کردید!",
]

TREASURE_ITEMS = [
    ("💰 کیسه طلا", 200),
    ("💎 جواهر نفیس", 500),
    ("🏺 گلدان باستانی", 150),
    ("⚔️ شمشیر افسانه‌ای", 300),
    ("📜 طومار رازآلود", 100),
    ("🔮 کریستال جادویی", 250),
    ("💀 تله! چیزی نیافتید", 0),
    ("💀 تله! چیزی نیافتید", 0),
]


@router.callback_query(F.data == "game:treasure")
async def treasure_game(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await callback.answer("❌ لطفاً دوباره /start بزنید.", show_alert=True)
        return

    map_text = random.choice(TREASURE_MAPS)
    item_name, reward = random.choice(TREASURE_ITEMS)

    if reward > 0:
        result_text = f"🎉 <b>یافتید:</b> {item_name}!\n\n✨ <b>+{reward} سکه</b> دریافت کردید!"
        if db_session and db_user:
            from bot.services.economy_service import add_coins
            await add_coins(db_session, db_user.id, reward, "game_win", "Treasure Hunt win")
    else:
        result_text = f"💀 <b>تله!</b> {item_name}\n\nدفعه بعد شانس بیشتری داری!"

    text = (
        f"🗺️ <b>شکار گنج</b>\n━━━━━━━━━━━━\n\n"
        f"{map_text}\n\n"
        f"🔍 کاوش می‌کنید...\n\n"
        f"{result_text}"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:games"))
    await callback.answer()


# ─── مین‌یاب ──────────────────────────────────────────
@router.callback_query(F.data == "game:mines")
async def mines_game(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await callback.answer("❌ لطفاً دوباره /start بزنید.", show_alert=True)
        return

    # یک صفحه ۴×۴ با ۴ مین
    total = 16
    mines = set(random.sample(range(total), 4))
    board = []
    for i in range(total):
        board.append("💣" if i in mines else "💎")

    # نشان دادن یک کلیک تصادفی
    safe_cells = [i for i in range(total) if i not in mines]
    clicked = random.choice(safe_cells)
    revealed = board[clicked]

    # ساخت صفحه نمایش با 4 تا آشکار
    reveal_count = random.randint(2, 5)
    reveal_cells = random.sample(safe_cells, min(reveal_count, len(safe_cells)))

    display_board = ["⬜"] * total
    for i in reveal_cells:
        display_board[i] = "💎"

    rows = []
    for r in range(4):
        row = " ".join(display_board[r*4:(r+1)*4])
        rows.append(row)

    # پاداش بر اساس تعداد خانه‌های کشف شده
    reward = reveal_count * 30
    if db_session and db_user:
        from bot.services.economy_service import add_coins
        await add_coins(db_session, db_user.id, reward, "game_win", "Mines win")

    text = (
        f"💣 <b>مین‌یاب</b>\n━━━━━━━━━━━━\n\n"
        f"{chr(10).join(rows)}\n\n"
        f"✅ <b>{reveal_count}</b> خانه امن کشف کردید!\n"
        f"🎉 <b>+{reward} سکه</b> دریافت کردید!\n\n"
        f"💡 صفحه رو با دقت بررسی کن!"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:games"))
    await callback.answer()


# ─── رولت ──────────────────────────────────────────────
ROULETTE_NUMBERS = list(range(0, 37))
ROULETTE_RED = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}


@router.callback_query(F.data == "game:roulette")
async def roulette_game(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await callback.answer("❌ لطفاً دوباره /start بزنید.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="🔴 قرمز (2×)", callback_data="roulette:red")
    builder.button(text="⚫ مشکی (2×)", callback_data="roulette:black")
    builder.button(text="🟢 صفر", callback_data="roulette:zero")
    builder.button(text="🔢 فرد (2×)", callback_data="roulette:odd")
    builder.button(text="🔢 زوج (2×)", callback_data="roulette:even")
    builder.button(text=_("btn_back"), callback_data="menu:games")
    builder.adjust(2, 3, 1)
    await callback.message.answer(
        "🎰 <b>رولت</b>\n━━━━━━━━━━━━\n\nروی کدام گزینه شرط می‌بندید؟\n\n💰 شرط: ۵۰ سکه | برد: ۲× جایزه",
        parse_mode="HTML",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("roulette:"))
async def process_roulette(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await callback.answer("❌ لطفاً دوباره /start بزنید.", show_alert=True)
        return

    bet = callback.data.split(":")[1]
    number = random.choice(ROULETTE_NUMBERS)
    is_red = number in ROULETTE_RED
    color_icon = "🔴" if is_red else ("🟢" if number == 0 else "⚫")
    color_text = "قرمز" if is_red else ("سبز" if number == 0 else "مشکی")

    won = False
    wager = 50
    if bet == "red" and is_red:
        won = True
    elif bet == "black" and not is_red and number != 0:
        won = True
    elif bet == "zero" and number == 0:
        won = True
        wager = 50  # بُرد بزرگ‌تر
    elif bet == "odd" and number % 2 == 1:
        won = True
    elif bet == "even" and number % 2 == 0 and number != 0:
        won = True

    if won:
        reward = wager * 2
        result_text = f"🎉 <b>بردید!</b>\n\n✨ <b>+{reward} سکه</b> دریافت کردید!"
        if db_session and db_user:
            from bot.services.economy_service import add_coins
            await add_coins(db_session, db_user.id, reward, "game_win", "Roulette win")
    else:
        result_text = f"😔 <b>باختید!</b>\n\nدفعه بعد شانس بیشتری بیار!"

    text = (
        f"🎰 <b>رولت</b>\n━━━━━━━━━━━━\n\n"
        f"🎡 گردونه می‌چرخد...\n\n"
        f"نتیجه: {color_icon} <b>{number}</b> ({color_text})\n\n"
        f"{result_text}"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:games"))
    await callback.answer()


# ─── شطرنج سریع ─────────────────────────────────────
@router.callback_query(F.data == "game:chess")
async def chess_game(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    # نسخه ساده شده شطرنج
    pieces = ["♟ پیاده", "♞ اسب", "♝ فیل", "♜ رخ", "♛ وزیر"]
    p_piece = random.choice(pieces)
    b_piece = random.choice(pieces)

    p_power = pieces.index(p_piece)
    b_power = pieces.index(b_piece)

    if p_power > b_power:
        result_text = _("game_won").format(amount=100)
        icon = "♔ <b>شاه‌مات!</b>"
        if db_session and db_user:
            from bot.services.economy_service import add_coins
            await add_coins(db_session, db_user.id, 100, "game_win", "Chess win")
    elif p_power < b_power:
        result_text = _("game_lost").format(amount=0)
        icon = "♚ <b>شکست!</b>"
    else:
        result_text = _("game_draw")
        icon = "🤝 <b>پات!</b>"

    board = (
        "♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜\n"
        "♟ ♟ ♟ ♟ ♟ ♟ ♟ ♟\n"
        "· · · · · · · ·\n"
        "· · · · · · · ·\n"
        "· · · · · · · ·\n"
        "· · · · · · · ·\n"
        "♙ ♙ ♙ ♙ ♙ ♙ ♙ ♙\n"
        "♖ ♘ ♗ ♕ ♔ ♗ ♘ ♖"
    )

    text = (
        f"♟️ <b>شطرنج سریع</b>\n━━━━━━━━━━━━\n\n"
        f"<code>{board}</code>\n\n"
        f"مهره شما: {p_piece}\n"
        f"مهره ربات: {b_piece}\n\n"
        f"{icon}\n{result_text}"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:games"))
    await callback.answer()


# ─── آمار بازی‌ها ──────────────────────────────────────
@router.callback_query(F.data == "gstats:all")
async def game_stats_view(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await callback.answer("❌ لطفاً دوباره /start بزنید.", show_alert=True)
        return

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
