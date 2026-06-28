import random
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.games import dice_menu_kb, rps_choice_kb, wheel_spin_kb
from bot.services.game_service import play_classic_dice, spin_wheel, play_rps
from bot.services.user_service import get_or_create_game_stats
from bot.utils.helpers import format_number
import structlog

logger = structlog.get_logger()
router = Router()


class GameStates(StatesGroup):
    waiting_dice_bet = State()


# ──── /games ────────────────────────────────────────────────────
@router.message(Command('games'))
async def cmd_games(message: Message, _: callable, **kwargs):
    await message.answer(_('games_menu'), reply_markup=dice_menu_kb(_), parse_mode='HTML')


# ──── /dice ──────────────────────────────────────────────────────
@router.message(Command('dice'))
async def cmd_dice(message: Message, _: callable, **kwargs):
    await message.answer(_('dice_menu'), reply_markup=dice_menu_kb(_), parse_mode='HTML')


@router.callback_query(F.data.startswith('dice:'))
async def play_dice(callback: CallbackQuery, _: callable, db_session=None, db_user=None, state: FSMContext = None, **kwargs):
    mode = callback.data.split('dice:', 1)[1]

    if db_user is None or db_session is None:
        await callback.answer(_('error_generic'), show_alert=True)
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
    text = (
        f"🎲 <b>{_('dice_menu').split(chr(10))[0].strip()}</b>\n"
        f"─────\n\n"
        f"{_('btn_game_dice')}: {p} <b>{result['player_roll']}</b>  vs  🤖: {b} <b>{result['opponent_roll']}</b>\n\n"
    )
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
        await message.reply(_('error_generic'))
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
    text = (
        f"🎲 <b>{_('dice_menu').split(chr(10))[0].strip()}</b>\n"
        f"─────\n\n"
        f"{_('btn_game_dice')}: {p} <b>{result['player_roll']}</b>  vs  🤖: {b} <b>{result['opponent_roll']}</b>\n\n"
    )
    if result['result'] == 'win':
        text += _('game_won').format(amount=format_number(result['winnings']))
    elif result['result'] == 'lose':
        text += _('game_lost').format(amount=format_number(wager))
    else:
        text += _('game_draw')
    await message.reply(text, parse_mode='HTML')
    if state:
        await state.clear()


# ──── /wheel ────────────────────────────────────────────────────
@router.message(Command('wheel'))
async def cmd_wheel(message: Message, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await message.reply(_('error_generic'))
        return
    segments = [('💀', 0), ('🟡 0.5×', 0), ('🟢 1.5×', 0), ('🔵 2×', 0), ('🟣 3×', 0), ('🌟 5×', 0), ('💎 10×', 0)]
    probs = [0.30, 0.05, 0.20, 0.25, 0.15, 0.03, 0.02]
    rand = random.random()
    cumulative = 0.0
    chosen_label, chosen_mult = '💀', 0
    for i, prob in enumerate(probs):
        cumulative += prob
        if rand <= cumulative:
            chosen_label, chosen_mult = segments[i]
            break
    spin_animation = '🎡 ' + ' → '.join([s[0] for s in random.sample(segments, 4)]) + f' → <b>{chosen_label}</b>'
    if chosen_mult == 0:
        outcome = _('game_lost').format(amount=0)
    else:
        outcome = _('game_won').format(amount=chosen_mult)
    text = (
        f"🎡 <b>{_('btn_game_wheel')}</b>\n"
        f"─────\n\n"
        f"{spin_animation}\n\n"
        f"{'🎯' if chosen_mult > 0 else '💀'} {chosen_label}\n\n"
        f"{outcome}"
    )
    await message.answer(text, parse_mode='HTML')


# ──── /rps ───────────────────────────────────────────────────────
@router.message(Command('rps'))
async def cmd_rps(message: Message, _: callable, **kwargs):
    await message.answer(
        f"✊ <b>{_('btn_game_rps')}</b>\n─────\n\n{_('rps_choose')}",
        parse_mode='HTML',
        reply_markup=rps_choice_kb(_, match_id=0),
    )


@router.callback_query(F.data.startswith('rps:'))
async def process_rps(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    parts = callback.data.split(':')
    player_choice = parts[2] if len(parts) > 2 else 'rock'
    if db_user is None or db_session is None:
        await callback.answer(_('error_generic'), show_alert=True)
        return
    result = await play_rps(db_session, db_user.id, player_choice, wager=0)
    emojis = {'rock': _('btn_rock'), 'paper': _('btn_paper'), 'scissors': _('btn_scissors')}
    p_e = emojis.get(result['player_choice'], '❓')
    b_e = emojis.get(result['bot_choice'], '❓')
    if result['result'] == 'win':
        outcome = _('game_won').format(amount=0)
    elif result['result'] == 'lose':
        outcome = _('game_lost').format(amount=0)
    else:
        outcome = _('game_draw')
    text = (
        f"✊ <b>{_('btn_game_rps')}</b>\n"
        f"─────\n\n"
        f"👤: {p_e}\n🤖: {b_e}\n\n"
        f"{outcome}"
    )
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


# ──── /quiz ──────────────────────────────────────────────────────
QUIZ_QUESTIONS = [
    ("❓ What is 7 × 8?", ['54', '56', '64', '48'], 1),
    ("❓ How many hours in a day?", ['12', '20', '24', '48'], 2),
    ("❓ What is 100 × 100?", ['1000', '10000', '100000', '100'], 1),
    ("❓ What is the chemical symbol for water?", ['H2O', 'CO2', 'NaCl', 'O2'], 0),
    ("❓ Which planet is closest to the Sun?", ['Venus', 'Mercury', 'Earth', 'Mars'], 1),
    ("❓ What is the speed of light approximately?", ['300 km/s', '300,000 km/s', '30,000 km/s', '3,000 km/s'], 1),
    ("❓ How many continents are there?", ['5', '6', '7', '8'], 2),
    ("❓ What year did World War II end?", ['1943', '1944', '1945', '1946'], 2),
    ("❓ What is √144?", ['10', '11', '12', '14'], 2),
    ("❓ Which element has atomic number 1?", ['Helium', 'Hydrogen', 'Oxygen', 'Carbon'], 1),
]


@router.message(Command('quiz'))
async def cmd_quiz(message: Message, _: callable, **kwargs):
    q_text, options, correct = random.choice(QUIZ_QUESTIONS)
    builder = InlineKeyboardBuilder()
    for i, opt in enumerate(options):
        builder.button(text=opt, callback_data=f'quiz_ans:{correct}:{i}')
    builder.adjust(2, 2)
    await message.answer(
        f"🧠 <b>{_('btn_game_quiz')}</b>\n─────\n\n{q_text}",
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
        await callback.answer(_('quiz_correct'), show_alert=True)
        if db_session and db_user:
            from bot.services.user_service import add_xp
            await add_xp(db_session, db_user.id, 20)
    else:
        await callback.answer(_('quiz_wrong'), show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=None)


# ──── /numwar ────────────────────────────────────────────────────
@router.message(Command('numwar'))
async def cmd_numwar(message: Message, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await message.reply(_('error_generic'))
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
    text = (
        f"🔢 <b>{_('btn_game_numwar')}</b>\n"
        f"─────\n\n"
        f"👤:  <b>{player_num}</b> [{p_bar}]\n"
        f"🤖: <b>{bot_num}</b> [{b_bar}]\n\n"
        f"{icon} {result_text}"
    )
    await message.answer(text, parse_mode='HTML')


# ──── /cards ─────────────────────────────────────────────────────
CARD_RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
CARD_SUITS = ['♠️', '♥️', '♦️', '♣️']


def random_card():
    return random.choice(CARD_RANKS), random.choice(CARD_SUITS)


@router.message(Command('cards'))
async def cmd_cards(message: Message, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await message.reply(_('error_generic'))
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
    text = (
        f"🃏 <b>{_('btn_game_cards')}</b>\n"
        f"─────\n\n"
        f"👤:  {p_suit} <b>{p_rank}</b>\n"
        f"🤖: {b_suit} <b>{b_rank}</b>\n\n"
        f"{icon} {result_text}"
    )
    await message.answer(text, parse_mode='HTML')


# ──── /treasure ──────────────────────────────────────────────────
@router.message(Command('treasure'))
async def cmd_treasure(message: Message, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await message.reply(_('error_generic'))
        return
    spots = ['💎', '💎', '💣', '💣', '💣', '💎', '💣', '💣', '💎']
    random.shuffle(spots)
    chosen = random.choice(spots)
    if chosen == '💎':
        reward = random.randint(30, 150)
        result_text = _('treasure_found').format(amount=reward)
        from bot.services.economy_service import add_coins
        await add_coins(db_session, db_user.id, reward, 'game_win', 'Treasure hunt win')
    else:
        result_text = _('treasure_bomb')
    reveal = ' '.join(spots[:5])
    text = (
        f"💎 <b>{_('btn_game_treasure')}</b>\n"
        f"─────\n\n"
        f"{reveal}\n\n"
        f"{result_text}"
    )
    await message.answer(text, parse_mode='HTML')


# ──── /mines ─────────────────────────────────────────────────────
@router.message(Command('mines'))
async def cmd_mines(message: Message, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await message.reply(_('error_generic'))
        return
    grid = ['💣'] * 3 + ['💰'] * 6
    random.shuffle(grid)
    chosen_idx = random.randint(0, 8)
    chosen = grid[chosen_idx]
    if chosen == '💰':
        reward = random.randint(20, 100)
        result_text = _('mines_safe').format(amount=reward)
        from bot.services.economy_service import add_coins
        await add_coins(db_session, db_user.id, reward, 'game_win', 'Mines win')
    else:
        result_text = _('mines_boom')
    display = grid[:3]
    display[chosen_idx % 3] = chosen
    row = ' '.join(display)
    text = (
        f"💣 <b>{_('btn_game_mines')}</b>\n"
        f"─────\n\n"
        f"{row}\n\n"
        f"{result_text}"
    )
    await message.answer(text, parse_mode='HTML')


# ──── /roulette ──────────────────────────────────────────────────
ROULETTE_NUMBERS = list(range(37))
ROULETTE_RED = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}


@router.message(Command('roulette'))
async def cmd_roulette(message: Message, _: callable, **kwargs):
    builder = InlineKeyboardBuilder()
    builder.button(text=_('roulette_red').format(mult='1.9×'), callback_data='roulette:red:0')
    builder.button(text=_('roulette_black').format(mult='1.9×'), callback_data='roulette:black:0')
    builder.button(text=_('roulette_zero').format(mult='35×'), callback_data='roulette:zero:0')
    builder.adjust(2, 1)
    await message.answer(
        f"🎰 <b>{_('btn_game_roulette')}</b>\n─────\n\n{_('roulette_choose')}",
        parse_mode='HTML',
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith('roulette:'))
async def process_roulette(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    parts = callback.data.split(':')
    bet_type = parts[1]
    if db_user is None or db_session is None:
        await callback.answer(_('error_generic'), show_alert=True)
        return
    spin = random.choice(ROULETTE_NUMBERS)
    is_red = spin in ROULETTE_RED
    is_zero = spin == 0
    if is_zero:
        result_color = _('roulette_zero_label')
    elif is_red:
        result_color = _('roulette_red_label')
    else:
        result_color = _('roulette_black_label')

    if (bet_type == 'red' and is_red) or (bet_type == 'black' and not is_red and not is_zero):
        result_text = _('roulette_win').format(mult='1.9×')
    elif bet_type == 'zero' and is_zero:
        result_text = _('roulette_jackpot').format(mult='35×')
    else:
        result_text = _('roulette_lose')
    text = (
        f"🎰 <b>{_('btn_game_roulette')}</b>\n"
        f"─────\n\n"
        f"🔮 {_('roulette_number')}: <b>{spin}</b> — {result_color}\n\n"
        f"{result_text}"
    )
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


# ──── /stats ─────────────────────────────────────────────────────
@router.message(Command('stats', 'gstats'))
async def cmd_stats(message: Message, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await message.reply(_('error_generic'))
        return
    stats = await get_or_create_game_stats(db_session, db_user.id)
    wins = stats.total_wins or 0
    losses = stats.total_losses or 0
    draws = (stats.total_games or 0) - wins - losses
    text = (
        f"📊 <b>{_('game_stats_title')}</b>\n"
        f"─────\n\n"
        f"🏆 {_('wins_label')}: <b>{wins}</b>\n"
        f"💀 {_('losses_label')}: <b>{losses}</b>\n"
        f"🤝 {_('draws_label')}: <b>{max(0, draws)}</b>\n"
        f"💰 {_('total_coins_label')}: <b>{format_number(stats.total_coins_won or 0)}</b>"
    )
    await message.answer(text, parse_mode='HTML')


# ─────
# GAME MENU CALLBACK HANDLERS — Make inline buttons fully functional
# ─────

@router.callback_query(F.data == "game:dice")
async def game_dice(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(_('dice_menu'), reply_markup=dice_menu_kb(_), parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data == "game:quiz")
async def game_quiz(callback: CallbackQuery, _: callable, **kwargs):
    q_text, options, correct = random.choice(QUIZ_QUESTIONS)
    builder = InlineKeyboardBuilder()
    for i, opt in enumerate(options):
        builder.button(text=opt, callback_data=f'quiz_ans:{correct}:{i}')
    builder.adjust(2, 2)
    await callback.message.edit_text(
        f"🧠 <b>{_('btn_game_quiz')}</b>\n─────\n\n{q_text}",
        parse_mode='HTML',
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data == "game:treasure")
async def game_treasure(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await callback.answer(_('error_generic'), show_alert=True)
        return
    spots = ['💎', '💎', '💣', '💣', '💣', '💎', '💣', '💣', '💎']
    random.shuffle(spots)
    chosen = random.choice(spots)
    if chosen == '💎':
        reward = random.randint(30, 150)
        result_text = _('treasure_found').format(amount=reward)
        from bot.services.economy_service import add_coins
        await add_coins(db_session, db_user.id, reward, 'game_win', 'Treasure hunt win')
    else:
        result_text = _('treasure_bomb')
    reveal = ' '.join(spots[:5])
    text = (
        f"💎 <b>{_('btn_game_treasure')}</b>\n"
        f"─────\n\n"
        f"{reveal}\n\n"
        f"{result_text}"
    )
    from bot.keyboards.main_menu import nav_kb
    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=nav_kb(_, "menu:games", "game:treasure"))
    await callback.answer()


@router.callback_query(F.data == "game:wheel")
async def game_wheel(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await callback.answer(_('error_generic'), show_alert=True)
        return
    segments = [('💀', 0), ('🟡 0.5×', 0), ('🟢 1.5×', 0), ('🔵 2×', 0), ('🟣 3×', 0), ('🌟 5×', 0), ('💎 10×', 0)]
    probs = [0.30, 0.05, 0.20, 0.25, 0.15, 0.03, 0.02]
    rand = random.random()
    cumulative = 0.0
    chosen_label, chosen_mult = '💀', 0
    for i, prob in enumerate(probs):
        cumulative += prob
        if rand <= cumulative:
            chosen_label, chosen_mult = segments[i]
            break
    spin_animation = '🎡 ' + ' → '.join([s[0] for s in random.sample(segments, 4)]) + f' → <b>{chosen_label}</b>'
    if chosen_mult == 0:
        outcome = _('game_lost').format(amount=0)
    else:
        outcome = _('game_won').format(amount=chosen_mult)
    text = (
        f"🎡 <b>{_('btn_game_wheel')}</b>\n"
        f"─────\n\n"
        f"{spin_animation}\n\n"
        f"{'🎯' if chosen_mult > 0 else '💀'} {chosen_label}\n\n"
        f"{outcome}"
    )
    from bot.keyboards.main_menu import nav_kb
    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=nav_kb(_, "menu:games", "game:wheel"))
    await callback.answer()


@router.callback_query(F.data == "game:cards")
async def game_cards(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await callback.answer(_('error_generic'), show_alert=True)
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
    text = (
        f"🃏 <b>{_('btn_game_cards')}</b>\n"
        f"─────\n\n"
        f"👤:  {p_suit} <b>{p_rank}</b>\n"
        f"🤖: {b_suit} <b>{b_rank}</b>\n\n"
        f"{icon} {result_text}"
    )
    from bot.keyboards.main_menu import nav_kb
    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=nav_kb(_, "menu:games", "game:cards"))
    await callback.answer()


@router.callback_query(F.data == "game:numwar")
async def game_numwar(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await callback.answer(_('error_generic'), show_alert=True)
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
    text = (
        f"🔢 <b>{_('btn_game_numwar')}</b>\n"
        f"─────\n\n"
        f"👤:  <b>{player_num}</b> [{p_bar}]\n"
        f"🤖: <b>{bot_num}</b> [{b_bar}]\n\n"
        f"{icon} {result_text}"
    )
    from bot.keyboards.main_menu import nav_kb
    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=nav_kb(_, "menu:games", "game:numwar"))
    await callback.answer()


@router.callback_query(F.data == "game:rps")
async def game_rps(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(
        f"👊 <b>{_('btn_game_rps')}</b>\n─────\n\n{_('rps_choose')}",
        parse_mode='HTML',
        reply_markup=rps_choice_kb(_, match_id=0),
    )
    await callback.answer()


@router.callback_query(F.data == "game:mines")
async def game_mines(callback: CallbackQuery, _: callable, db_session=None, db_user=None, **kwargs):
    if db_user is None or db_session is None:
        await callback.answer(_('error_generic'), show_alert=True)
        return
    grid = ['💣'] * 3 + ['💰'] * 6
    random.shuffle(grid)
    chosen_idx = random.randint(0, 8)
    chosen = grid[chosen_idx]
    if chosen == '💰':
        reward = random.randint(20, 100)
        result_text = _('mines_safe').format(amount=reward)
        from bot.services.economy_service import add_coins
        await add_coins(db_session, db_user.id, reward, 'game_win', 'Mines win')
    else:
        result_text = _('mines_boom')
    display = grid[:3]
    display[chosen_idx % 3] = chosen
    row = ' '.join(display)
    text = (
        f"💣 <b>{_('btn_game_mines')}</b>\n"
        f"─────\n\n"
        f"{row}\n\n"
        f"{result_text}"
    )
    from bot.keyboards.main_menu import nav_kb
    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=nav_kb(_, "menu:games", "game:mines"))
    await callback.answer()


@router.callback_query(F.data == "game:chess")
async def game_chess(callback: CallbackQuery, _: callable, **kwargs):
    text = (
        f"♟️ <b>{_('btn_game_chess')}</b>\n"
        f"─────\n\n"
        f"{_('feature_coming')}"
    )
    from bot.keyboards.main_menu import nav_kb
    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=nav_kb(_, "menu:games", "game:chess"))
    await callback.answer()


@router.callback_query(F.data == "game:roulette")
async def game_roulette(callback: CallbackQuery, _: callable, **kwargs):
    builder = InlineKeyboardBuilder()
    builder.button(text=_('roulette_red').format(mult='1.9×'), callback_data='roulette:red:0')
    builder.button(text=_('roulette_black').format(mult='1.9×'), callback_data='roulette:black:0')
    builder.button(text=_('roulette_zero').format(mult='35×'), callback_data='roulette:zero:0')
    builder.adjust(2, 1)
    await callback.message.edit_text(
        f"🎰 <b>{_('btn_game_roulette')}</b>\n─────\n\n{_('roulette_choose')}",
        parse_mode='HTML',
        reply_markup=builder.as_markup(),
    )
    await callback.answer()
