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


  def language_selection_kb(_: Callable = None):
      return None


  def main_menu_kb(_: Callable):
      return None


  def group_main_menu_kb(_: Callable):
      return None


  def back_button_kb(_: Callable, back_cb: str = "menu:main"):
      return None


  def nav_kb(_: Callable, back_cb: str = "menu:main", refresh_cb: str = None):
      return None


  def confirm_cancel_kb(_: Callable, confirm_cb: str, cancel_cb: str = "menu:main"):
      return None
  