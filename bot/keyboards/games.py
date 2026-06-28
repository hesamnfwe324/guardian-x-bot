from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Callable


def games_menu_kb(_: Callable) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    games = [
        (_("btn_dice"), "game:dice"),
        (_("btn_quiz"), "game:quiz"),
        (_("btn_treasure"), "game:treasure"),
        (_("btn_wheel"), "game:wheel"),
        (_("btn_cards"), "game:cards"),
        (_("btn_numwar"), "game:numwar"),
        (_("btn_rps"), "game:rps"),
        (_("btn_mines"), "game:mines"),
        (_("btn_chess"), "game:chess"),
        (_("btn_roulette"), "game:roulette"),
    ]
    for text, cb in games:
        builder.button(text=text, callback_data=cb)
    builder.button(text=_("btn_back"), callback_data="menu:main")
    builder.adjust(2)
    return builder.as_markup()


def dice_menu_kb(_: Callable) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    modes = [
        (_("btn_classic_dice"), "dice:classic"),
        (_("btn_prediction_dice"), "dice:prediction"),
        (_("btn_lucky_mult"), "dice:lucky_mult"),
        (_("btn_best_of_3"), "dice:best3"),
        (_("btn_best_of_5"), "dice:best5"),
        (_("btn_tournament_dice"), "dice:tournament"),
        (_("btn_group_battle"), "dice:group_battle"),
        (_("btn_daily_challenge"), "dice:daily"),
        (_("btn_dice_streak"), "dice:streak"),
        (_("btn_vip_arena"), "dice:vip"),
    ]
    for text, cb in modes:
        builder.button(text=text, callback_data=cb)
    builder.button(text=_("btn_back"), callback_data="menu:games")
    builder.adjust(2)
    return builder.as_markup()


def game_action_kb(_: Callable, game_type: str, match_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_game_stats"), callback_data=f"gstats:{game_type}")
    builder.button(text=_("btn_game_rankings"), callback_data=f"grank:{game_type}")
    builder.button(text=_("btn_back"), callback_data="menu:games")
    builder.adjust(2, 1)
    return builder.as_markup()


def join_game_kb(_: Callable, match_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_join_game"), callback_data=f"game_join:{match_id}")
    builder.button(text=_("btn_cancel"), callback_data=f"game_cancel:{match_id}")
    builder.adjust(2)
    return builder.as_markup()


def rps_choice_kb(_: Callable, match_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_rock"), callback_data=f"rps:{match_id}:rock")
    builder.button(text=_("btn_paper"), callback_data=f"rps:{match_id}:paper")
    builder.button(text=_("btn_scissors"), callback_data=f"rps:{match_id}:scissors")
    builder.adjust(3)
    return builder.as_markup()


def wheel_spin_kb(_: Callable, match_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_spin_wheel"), callback_data=f"wheel_spin:{match_id}")
    builder.adjust(1)
    return builder.as_markup()


def mines_board_kb(board: list, match_id: int, rows: int = 5, cols: int = 5) -> InlineKeyboardMarkup:
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
