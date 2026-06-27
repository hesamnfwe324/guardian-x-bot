import json
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
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
    # اول از fa.json، سپس en.json، آخر key رو برمی‌گردونه
    lang_dict = _translations.get(lang) or {}
    en_dict = _translations.get("en") or {}
    text = lang_dict.get(key) or en_dict.get(key) or key
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
        lang = "en"
        user = data.get("event_from_user")

        if user:
            db_user = data.get("db_user")
            if db_user is not None:
                # زبان ذخیره‌شده در DB را بخوان
                user_lang = getattr(db_user, "language", None)
                if user_lang and user_lang in _translations:
                    lang = user_lang
                else:
                    # اگه زبان کاربر تلگرام در ترجمه‌ها هست استفاده کن
                    tg_lang = (getattr(user, "language_code", None) or "en")[:2]
                    lang = tg_lang if tg_lang in _translations else "en"
            else:
                tg_lang = (getattr(user, "language_code", None) or "en")[:2]
                lang = tg_lang if tg_lang in _translations else "en"

        def _(key: str, **kwargs) -> str:
            return get_text(lang, key, **kwargs)

        data["_"] = _
        data["lang"] = lang
        return await handler(event, data)
