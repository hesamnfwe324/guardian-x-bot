from typing import Callable


LANG_FLAGS = {
    "en": "🇬🇧",
    "fa": "🇮🇷",
    "ar": "🇸🇦",
    "tr": "🇹🇷",
    "ru": "🇷🇺",
    "es": "🇪🇸",
    "fr": "🇫🇷",
    "de": "🇩🇪",
}


def language_selection_kb(_ = None):
    return None


def main_menu_kb(_):
    return None


def group_main_menu_kb(_):
    return None


def back_button_kb(_, back_cb="menu:main"):
    return None


def nav_kb(_, back_cb="menu:main", refresh_cb=None):
    return None


def confirm_cancel_kb(_, confirm_cb="", cancel_cb="menu:main"):
    return None
