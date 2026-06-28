from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Callable


def games_menu_kb(_: Callable) -> InlineKeyboardMarkup:
    """Beautiful i18n games menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text=_('btn_game_dice'),     callback_data="game:dice")
    builder.button(text=_('btn_game_quiz'),      callback_data="game:quiz")
    builder.button(text=_('btn_game_treasure'), callback_data="game:treasure")
    builder.button(text=_('btn_game_wheel'),    callback_data="game:wheel")
    builder.button(text=_('btn_game_cards'),    callback_data="game:cards")
    builder.button(text=_('btn_game_numwar'),   callback_data="game:numwar")
    builder.button(text=_('btn_game_rps'),      callback_data="game:rps")
    builder.button(text=_('btn_game_mines'),    callback_data="game:mines")
    builder.button(text=_('btn_game_chess'),    callback_data="game:chess")
    builder.button(text=_('btn_game_roulette'), callback_data="game:roulette")
    builder.button(text=_('btn_back'),          callback_data="menu:main")
    builder.adjust(2)
    return builder.as_markup()


def dice_menu_kb(_: Callable) -> InlineKeyboardMarkup:
    """Beautiful i18n dice menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text=_('btn_dice_classic'),    callback_data="dice:classic")
    builder.button(text=_('btn_dice_prediction'), callback_data="dice:prediction")
    builder.button(text=_('btn_dice_lucky'),     callback_data="dice:lucky_mult")
    builder.button(text=_('btn_dice_best3'),     callback_data="dice:best3")
    builder.button(text=_('btn_dice_best5'),     callback_data="dice:best5")
    builder.button(text=_('btn_dice_tournament'),callback_data="dice:tournament")
    builder.button(text=_('btn_dice_group'),     callback_data="dice:group_battle")
    builder.button(text=_('btn_dice_daily'),     callback_data="dice:daily")
    builder.button(text=_('btn_dice_streak'),    callback_data="dice:streak")
    builder.button(text=_('btn_dice_vip'),       callback_data="dice:vip")
    builder.button(text=_('btn_back'),           callback_data="menu:games")
    builder.adjust(2)
    return builder.as_markup()


def game_action_kb(_: Callable, game_type: str, match_id: int) -> InlineKeyboardMarkup:
    """Beautiful i18n game action buttons."""
    builder = InlineKeyboardBuilder()
    builder.button(text=_('btn_game_stats'),   callback_data=f"gstats:{game_type}")
    builder.button(text=_('btn_game_ranking'), callback_data=f"grank:{game_type}")
    builder.button(text=_('btn_back'),         callback_data="menu:games")
    builder.adjust(2, 1)
    return builder.as_markup()


def join_game_kb(_: Callable, match_id: int) -> InlineKeyboardMarkup:
    """Beautiful i18n join/decline game."""
    builder = InlineKeyboardBuilder()
    builder.button(text=_('btn_join'),   callback_data=f"game_join:{match_id}")
    builder.button(text=_('btn_decline'),callback_data=f"game_cancel:{match_id}")
    builder.adjust(2)
    return builder.as_markup()


def rps_choice_kb(_: Callable, match_id: int) -> InlineKeyboardMarkup:
    """Beautiful i18n RPS choice."""
    builder = InlineKeyboardBuilder()
    builder.button(text=_('btn_rock'),    callback_data=f"rps:{match_id}:rock")
    builder.button(text=_('btn_paper'),   callback_data=f"rps:{match_id}:paper")
    builder.button(text=_('btn_scissors'),callback_data=f"rps:{match_id}:scissors")
    builder.adjust(3)
    return builder.as_markup()


def wheel_spin_kb(_: Callable, match_id: int) -> InlineKeyboardMarkup:
    """Beautiful i18n wheel spin."""
    builder = InlineKeyboardBuilder()
    builder.button(text=_('btn_spin'), callback_data=f"wheel_spin:{match_id}")
    builder.adjust(1)
    return builder.as_markup()


def mines_board_kb(board: list, match_id: int, rows: int = 5, cols: int = 5) -> InlineKeyboardMarkup:
    """Minesweeper board — uses universal emoji symbols (no text)."""
    builder = InlineKeyboardBuilder()
    for r in range(rows):
        for c in range(cols):
            cell = board[r][c] if board else None
            if cell is None:
                text = "⬜"
            elif cell:
                text = "💣"
            else:
                text = "💎"
            builder.button(text=text, callback_data=f"mines:{match_id}:{r}:{c}")
    builder.adjust(cols)
    return builder.as_markup()
