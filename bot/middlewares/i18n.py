import json
import os
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, Message, CallbackQuery
import structlog

logger = structlog.get_logger()

LOCALES_DIR = Path(__file__).parent.parent / "locales"
_translations: Dict[str, Dict[str, str]] = {}


def load_translations() -> None:
    for lang_file in LOCALES_DIR.glob("*.json"):
        lang_code = lang_file.stem
        with open(lang_file, "r", encoding="utf-8") as f:
            _translations[lang_code] = json.load(f)
    logger.info("Translations loaded", languages=list(_translations.keys()))


def get_text(lang: str, key: str, **kwargs) -> str:
    translations = _translations.get(lang) or _translations.get("en", {})
    text = translations.get(key) or _translations.get("en", {}).get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text


class I18nMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        lang = "en"

        if user:
            db_user = data.get("db_user")
            if db_user and db_user.language:
                lang = db_user.language
            else:
                tg_lang = getattr(user, "language_code", None) or "en"
                lang = tg_lang[:2] if tg_lang else "en"
                if lang not in _translations:
                    lang = "en"

        def _(key: str, **kwargs) -> str:
            return get_text(lang, key, **kwargs)

        data["_"] = _
        data["lang"] = lang
        return await handler(event, data)
