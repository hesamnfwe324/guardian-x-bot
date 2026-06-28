import random
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.games import dice_menu_kb
from bot.services.game_service import play_classic_dice, spin_wheel, play_rps
from bot.services.user_service import get_or_create_game_stats
from bot.utils.helpers import format_number
import structlog

logger = structlog.get_logger()
router = Router()


class GameStates(StatesGroup):
    waiting_dice_bet = State()


# ─── /games ───────────────────────────────────────────────
@router.message(Command('games'))
async def cmd_games(message: Message, _: callable, **kwargs):
    text = (
        '🎮 <b>بازی‌های موجود:</b>\n\n'
        '/dice — 🎲 تاس هوشمند\n'
        '/rps — ✊ سنگ کاغذ قیچی\n'
        '/quiz — 🧠 کوئیز هوش\n'
        '/wheel — 🎡 چرخ شانس\n'
        '/numwar — 🔢 نبرد اعداد\n'
        '/cards — 🃏 نبرد کارت\n'
        '/treasure — 💎 شکار گنج\n'
        '/mines — 💣 مین‌یاب\n'
        '/roulette — 🎰 رولت'
    )
    await message.answer(text, parse_mode='HTML')


# ─── /dice ────────────────────────────────────────────────
@router.message(Command('dice'))
async def cmd_dice(message: Message, _: callable, **kwargs):
    await message.answer(_('dice_menu'), reply_markup=dice_menu_kb(_), parse_mode='HTML')


@router.callback_query(F.data.startswith('dice:'))
async def play_dice(callback: CallbackQuery, _: callable, db_session=None, db_user=None, state: FSMContext = None, **kwargs):
    mode = callback.data.split('dice:', 1)[1]

    if db_user is None or db_session is None:
        await callback.answer('❌ لطفاً /start بزنید.', show_alert=True)
        return

    if mode == 'classic':
        await callback.message.answer(_('game_bet_prompt').format(min=0, max=1000), parse_mode='HTML')
        if state:
            await state.set_state(GameStates.waiting_dice_bet)
            await state.update_data(mode='classic')
        await callback.answer()
        return

    wager = 50 if mode == 'daily' else 0
    result = await play_classic_dice(db_session, db_user.id, wager=wager)
    if 'error' in result:
        await callback.answer(_('insufficient_funds').format(balance='?'), show_alert=True)
        return

    dice_emoji = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅']
    p = dice_emoji[result['player_roll'] - 1]
    b = dice_emoji[result['opponent_roll'] - 1]
    text = f'🎲 <b>تاس</b>\n━━━━━━━━━━━━\n\nشما: {p} <b>{result["player_roll"]}</b>  vs  ربات: {b} <b>{result["opponent_roll"]}</b>\n\n'
    if result['result'] == 'win':
        text += _('game_won').format(amount=format_number(result['winnings']))
    elif result['result'] == 'lose':
        text += _('game_lost').format(amount=format_number(wager))
    else:
        text += _('game_draw')
    await callback.message.answer(text, parse_mode='HTML')
    await callback.answer()


@router.message(GameStates.waiting_dice_bet)
async def process_dice_bet(message: Message, _: callable, db_session=None, db_user=None, state: FSMContext = None, **kwargs):
    try:
        wager = int(message.text.strip())
        if wager < 0:
            raise ValueError
    except ValueError:
        await message.reply(_('invalid_amount'))
        return
    if db_user is None or db_session is None:
        await message.reply('❌ لطفاً /start بزنید.')
        if state:
            await state.clear()
        return
    result = await play_classic_dice(db_session, db_user.id, wager=wager)
    if 'error' in result:
        await message.reply(_('insufficient_funds').format(balance='?'))
        if state:
            await state.clear()
        return
    dice_emoji = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅']
    p = dice_emoji[result['player_roll'] - 1]
    b = dice_emoji[result['opponent_roll'] - 1]
    text = f'🎲 <b>نتیجه تاس</b>\n━━━━━━━━━━━━\n\nشما: {p} <b>{result["player_roll"]}</b>  vs  ربات: {b} <b>{result["opponent_roll"]}</b>\n\n'
    if result['result'] == 'win':
        text += _('game_won').format(amount=format_number(result['winnings']))
    elif result['result'] == 'lose':
        text += _('game_lost').format(amount=format_number(wager))
    else:
        text += _('game_draw')
    await message.reply(text, parse_mode='HTML')
    if state:
        await state.clear()


# ─── /wheel ───────────────────────────────────────────────
@router.message(Command('wheel'))
async def cmd_wheel(message: Message, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await message.reply('❌ لطفاً /start بزنید.')
        return
    segments = [('💀 باخت', 0), ('🟡 0.5×', 0), ('🟢 1.5×', 0), ('🔵 2×', 0), ('🟣 3×', 0), ('🌟 5×', 0), ('💎 10×', 0)]
    probs = [0.30, 0.05, 0.20, 0.25, 0.15, 0.03, 0.02]
    rand = random.random()
    cumulative = 0.0
    chosen_label, chosen_mult = '💀 باخت', 0
    for i, prob in enumerate(probs):
        cumulative += prob
        if rand <= cumulative:
            chosen_label, chosen_mult = segments[i]
            break
    spin_animation = '🎡 ' + ' → '.join([s[0] for s in random.sample(segments, 4)]) + f' → <b>{chosen_label}</b>'
    outcome = '💀 باختید!' if chosen_mult == 0 else f'🎉 ضریب <b>{chosen_label}</b>!'
    text = f'🎡 <b>چرخ شانس</b>\n━━━━━━━━━━━━\n\n{spin_animation}\n\nنتیجه: {chosen_label}\n\n{outcome}'
    await message.answer(text, parse_mode='HTML')


# ─── /rps ─────────────────────────────────────────────────
@router.message(Command('rps'))
async def cmd_rps(message: Message, _: callable, **kwargs):
    builder = InlineKeyboardBuilder()
    builder.button(text='🪨 سنگ', callback_data='rps:0:rock')
    builder.button(text='📄 کاغذ', callback_data='rps:0:paper')
    builder.button(text='✂️ قیچی', callback_data='rps:0:scissors')
    builder.adjust(3)
    await message.answer(
        '✊ <b>سنگ کاغذ قیچی</b>\n━━━━━━━━━━━━\n\nانتخاب خود را بزنید!',
        parse_mode='HTML',
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith('rps:'))
async def process_rps(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    parts = callback.data.split(':')
    player_choice = parts[2] if len(parts) > 2 else 'rock'
    if db_user is None or db_session is None:
        await callback.answer('❌ لطفاً /start بزنید.', show_alert=True)
        return
    result = await play_rps(db_session, db_user.id, player_choice, wager=0)
    emojis = {'rock': '🪨 سنگ', 'paper': '📄 کاغذ', 'scissors': '✂️ قیچی'}
    p_e = emojis.get(result['player_choice'], '❓')
    b_e = emojis.get(result['bot_choice'], '❓')
    if result['result'] == 'win':
        outcome = '🎉 <b>بردید!</b>'
    elif result['result'] == 'lose':
        outcome = '😔 <b>باختید!</b>'
    else:
        outcome = '🤝 <b>مساوی!</b>'
    text = f'✊ <b>سنگ کاغذ قیچی</b>\n━━━━━━━━━━━━\n\nشما: {p_e}\nربات: {b_e}\n\n{outcome}'
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


# ─── /quiz ────────────────────────────────────────────────
QUIZ_QUESTIONS = [
    ('پایتخت ایران کدام شهر است؟', ['تهران', 'مشهد', 'اصفهان', 'شیراز'], 0),
    ('۷ × ۸ چند است؟', ['۵۴', '۵۶', '۶۴', '۴۸'], 1),
    ('کره زمین به دور خورشید در چند روز می‌گردد؟', ['۳۶۵', '۳۶۰', '۳۵۵', '۳۷۰'], 0),
    ('بزرگ‌ترین اقیانوس جهان کدام است؟', ['اطلس', 'هند', 'آرام', 'منجمد شمالی'], 2),
    ('کدام عنصر سازنده اصلی آب است؟', ['اکسیژن', 'هیدروژن', 'نیتروژن', 'کربن'], 1),
    ('چند ساعت در یک روز وجود دارد؟', ['۱۲', '۲۰', '۲۴', '۴۸'], 2),
    ('سریع‌ترین حیوان جهان کدام است؟', ['شیر', 'یوزپلنگ', 'عقاب', 'اسب'], 1),
    ('اختراع تلفن به چه کسی نسبت داده می‌شود؟', ['ادیسون', 'گراهام بل', 'نیوتن', 'مارکونی'], 1),
    ('۱۰۰ × ۱۰۰ چند است؟', ['۱۰۰۰', '۱۰۰۰۰', '۱۰۰۰۰۰', '۱۰۰'], 1),
    ('در شطرنج وزیر چگونه حرکت می‌کند؟', ['مثل رخ', 'مثل اسب', 'در همه جهات', 'مورب'], 2),
]


@router.message(Command('quiz'))
async def cmd_quiz(message: Message, _: callable, **kwargs):
    q_text, options, correct = random.choice(QUIZ_QUESTIONS)
    builder = InlineKeyboardBuilder()
    for i, opt in enumerate(options):
        builder.button(text=opt, callback_data=f'quiz_ans:{correct}:{i}')
    builder.adjust(2, 2)
    await message.answer(
        f'🧠 <b>کوئیز هوش</b>\n━━━━━━━━━━━━\n\n❓ {q_text}',
        parse_mode='HTML',
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith('quiz_ans:'))
async def quiz_answer(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    parts = callback.data.split(':')
    correct = int(parts[1])
    chosen = int(parts[2])
    is_correct = correct == chosen
    if is_correct:
        await callback.answer('✅ آفرین! جواب درسته! +20 XP', show_alert=True)
        if db_session and db_user:
            from bot.services.user_service import add_xp
            await add_xp(db_session, db_user.id, 20)
    else:
        await callback.answer('❌ اشتباه! جواب درست بود گزینه دیگری!', show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=None)


# ─── /numwar ──────────────────────────────────────────────
@router.message(Command('numwar'))
async def cmd_numwar(message: Message, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await message.reply('❌ لطفاً /start بزنید.')
        return
    player_num = random.randint(1, 100)
    bot_num = random.randint(1, 100)
    if player_num > bot_num:
        result_text = _('game_won').format(amount=50)
        icon = '🏆'
        from bot.services.economy_service import add_coins
        await add_coins(db_session, db_user.id, 50, 'game_win', 'Number War win')
    elif player_num < bot_num:
        result_text = _('game_lost').format(amount=0)
        icon = '💀'
    else:
        result_text = _('game_draw')
        icon = '🤝'
    p_bar = '█' * (player_num // 10) + '░' * (10 - player_num // 10)
    b_bar = '█' * (bot_num // 10) + '░' * (10 - bot_num // 10)
    text = f'🔢 <b>نبرد اعداد</b>\n━━━━━━━━━━━━\n\nشما:  <b>{player_num}</b> [{p_bar}]\nربات: <b>{bot_num}</b> [{b_bar}]\n\n{icon} {result_text}'
    await message.answer(text, parse_mode='HTML')


# ─── /cards ───────────────────────────────────────────────
CARD_RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
CARD_SUITS = ['♠️', '♥️', '♦️', '♣️']


def random_card():
    return random.choice(CARD_RANKS), random.choice(CARD_SUITS)


@router.message(Command('cards'))
async def cmd_cards(message: Message, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await message.reply('❌ لطفاً /start بزنید.')
        return
    p_rank, p_suit = random_card()
    b_rank, b_suit = random_card()
    p_val = CARD_RANKS.index(p_rank)
    b_val = CARD_RANKS.index(b_rank)
    if p_val > b_val:
        result_text = _('game_won').format(amount=40)
        icon = '🏆'
        from bot.services.economy_service import add_coins
        await add_coins(db_session, db_user.id, 40, 'game_win', 'Card game win')
    elif p_val < b_val:
        result_text = _('game_lost').format(amount=0)
        icon = '💀'
    else:
        result_text = _('game_draw')
        icon = '🤝'
    text = f'🃏 <b>نبرد کارت</b>\n━━━━━━━━━━━━\n\nشما:  {p_suit} <b>{p_rank}</b>\nربات: {b_suit} <b>{b_rank}</b>\n\n{icon} {result_text}'
    await message.answer(text, parse_mode='HTML')


# ─── /treasure ────────────────────────────────────────────
@router.message(Command('treasure'))
async def cmd_treasure(message: Message, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await message.reply('❌ لطفاً /start بزنید.')
        return
    spots = ['💎', '💎', '💣', '💣', '💣', '💎', '💣', '💣', '💎']
    random.shuffle(spots)
    chosen = random.choice(spots)
    if chosen == '💎':
        reward = random.randint(30, 150)
        result_text = f'🎉 گنج پیدا کردید! +{reward} سکه'
        from bot.services.economy_service import add_coins
        await add_coins(db_session, db_user.id, reward, 'game_win', 'Treasure hunt win')
    else:
        result_text = '💣 بمب! بدشانسی آوردید!'
    reveal = ' '.join(spots[:5])
    text = f'💎 <b>شکار گنج</b>\n━━━━━━━━━━━━\n\n{reveal}\n\n{result_text}'
    await message.answer(text, parse_mode='HTML')


# ─── /mines ───────────────────────────────────────────────
@router.message(Command('mines'))
async def cmd_mines(message: Message, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await message.reply('❌ لطفاً /start بزنید.')
        return
    grid = ['💣'] * 3 + ['💰'] * 6
    random.shuffle(grid)
    chosen_idx = random.randint(0, 8)
    chosen = grid[chosen_idx]
    if chosen == '💰':
        reward = random.randint(20, 100)
        result_text = f'🎉 مسیر امن! +{reward} سکه'
        from bot.services.economy_service import add_coins
        await add_coins(db_session, db_user.id, reward, 'game_win', 'Mines win')
    else:
        result_text = '💥 مین! باختید!'
    display = grid[:3]
    display[chosen_idx % 3] = chosen
    row = ' '.join(display)
    text = f'💣 <b>مین‌یاب</b>\n━━━━━━━━━━━━\n\n{row}\n\n{result_text}'
    await message.answer(text, parse_mode='HTML')


# ─── /roulette ────────────────────────────────────────────
ROULETTE_NUMBERS = list(range(37))
ROULETTE_RED = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}


@router.message(Command('roulette'))
async def cmd_roulette(message: Message, _: callable, **kwargs):
    builder = InlineKeyboardBuilder()
    builder.button(text='🔴 قرمز (+1.9x)', callback_data='roulette:red:0')
    builder.button(text='⚫ سیاه (+1.9x)', callback_data='roulette:black:0')
    builder.button(text='🟢 صفر (+35x)', callback_data='roulette:zero:0')
    builder.adjust(2, 1)
    await message.answer(
        '🎰 <b>رولت</b>\n━━━━━━━━━━━━\n\nنوع شرط‌بندی خود را انتخاب کنید:',
        parse_mode='HTML',
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith('roulette:'))
async def process_roulette(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    parts = callback.data.split(':')
    bet_type = parts[1]
    if db_user is None or db_session is None:
        await callback.answer('❌ لطفاً /start بزنید.', show_alert=True)
        return
    spin = random.choice(ROULETTE_NUMBERS)
    is_red = spin in ROULETTE_RED
    is_zero = spin == 0
    result_color = '🟢 صفر' if is_zero else ('🔴 قرمز' if is_red else '⚫ سیاه')
    if (bet_type == 'red' and is_red) or (bet_type == 'black' and not is_red and not is_zero):
        result_text = '🎉 بردید! (+1.9x)'
    elif bet_type == 'zero' and is_zero:
        result_text = '💰 جک‌پات! (+35x)'
    else:
        result_text = '😔 باختید!'
    text = f'🎰 <b>رولت</b>\n━━━━━━━━━━━━\n\n🔮 عدد: <b>{spin}</b> — {result_color}\n\n{result_text}'
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


# ─── /stats ───────────────────────────────────────────────
@router.message(Command('stats', 'gstats'))
async def cmd_stats(message: Message, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await message.reply('❌ لطفاً /start بزنید.')
        return
    stats = await get_or_create_game_stats(db_session, db_user.id)
    wins = stats.total_wins or 0
    losses = stats.total_losses or 0
    draws = (stats.total_games or 0) - wins - losses
    text = (
        f'📊 <b>آمار بازی‌های شما</b>\n━━━━━━━━━━━━\n\n'
        f'🏆 برد‌ها: <b>{wins}</b>\n'
        f'💀 باخت‌ها: <b>{losses}</b>\n'
        f'🤝 مساوی‌ها: <b>{max(0, draws)}</b>\n'
        f'💰 کل برده: <b>{format_number(stats.total_coins_won or 0)}</b>'
    )
    await message.answer(text, parse_mode='HTML')
