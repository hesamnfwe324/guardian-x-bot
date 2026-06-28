from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession
from bot.config import settings
from bot.middlewares.i18n import get_text
import structlog

logger = structlog.get_logger()
router = Router()


COMMANDS_FA = (
    "U0001f44b سلام {name}!

"
    "U0001f4cb دستورات موجود:

"
    "U0001f4b0 اقتصاد:
"
    "  /wallet — کیف پول
"
    "  /daily — جایزه روزانه
"
    "  /weekly — جایزه هفتگی
"
    "  /monthly — جایزه ماهانه
"
    "  /transfer — انتقال سکه
"
    "  /referral — لینک دعوت

"
    "U0001f3ae بازی‌ها:
"
    "  /dice — تاس
"
    "  /rps — سنگ کاغذ قیچی
"
    "  /quiz — مسابقه
"
    "  /wheel — چرخ شانس
"
    "  /roulette — رولت
"
    "  /duel — دوئل

"
    "U0001f6e1️ مدیریت (در گروه):
"
    "  /security — تنظیمات امنیتی
"
    "  /settings — تنظیمات گروه
"
    "  /stats — آمار گروه
"
    "  /language — تغییر زبان

"
    "❓ راهنما:
"
    "  /help — لیست کامل دستورات"
)


COMMANDS_EN = (
    "U0001f44b Hello {name}!

"
    "U0001f4cb Available commands:

"
    "U0001f4b0 Economy:
"
    "  /wallet — wallet and balance
"
    "  /daily — daily reward
"
    "  /weekly — weekly reward
"
    "  /monthly — monthly reward
"
    "  /transfer — transfer coins
"
    "  /referral — referral link

"
    "U0001f3ae Games:
"
    "  /dice — dice roll
"
    "  /rps — rock paper scissors
"
    "  /quiz — quiz game
"
    "  /wheel — wheel of fortune
"
    "  /roulette — roulette
"
    "  /duel — duel

"
    "U0001f6e1️ Management (in group):
"
    "  /security — security settings
"
    "  /settings — group settings
"
    "  /stats — group statistics
"
    "  /language — change language

"
    "❓ Help:
"
    "  /help — full command list"
)


def _get_commands(lang: str, name: str) -> str:
    if lang == "fa":
        return COMMANDS_FA.format(name=name)
    return COMMANDS_EN.format(name=name)


def _detect_lang(telegram_lang: str | None) -> str:
    """Auto-detect language from Telegram locale, default to fa."""
    if not telegram_lang:
        return "fa"
    code = telegram_lang.split("-")[0].lower()
    if code in settings.SUPPORTED_LANGUAGES:
        return code
    return "fa"


@router.message(CommandStart())
async def cmd_start(message: Message, _: callable, db_session: AsyncSession = None, db_user=None, **kwargs):
    if message.chat.type != "private":
        title = message.chat.title or "Group"
        group_text = _("group_panel_title").replace("{title}", title)
        await message.answer(group_text, parse_mode="HTML")
        return

    # Handle referral
    if db_session and db_user:
        args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
        if args.startswith("ref_"):
            try:
                referrer_id = int(args[4:])
                if referrer_id != message.from_user.id:
                    from bot.services.economy_service import process_referral
                    await process_referral(db_session, referrer_id=referrer_id, new_user_id=db_user.id)
            except Exception:
                pass

    # Determine language (auto-detect if not set)
    if db_user and db_user.language:
        lang = db_user.language
    else:
        lang = _detect_lang(message.from_user.language_code)
        # Save detected language
        if db_session and db_user:
            db_user.language = lang
            try:
                await db_session.flush()
            except Exception:
                pass

    name = message.from_user.first_name or "User"
    await message.answer(_get_commands(lang, name))


@router.message(Command("language", "lang"))
async def cmd_language(message: Message, _: callable, db_session: AsyncSession = None, db_user=None, **kwargs):
    """Show available languages as text list."""
    text = (
        "U0001f310 زبان خود را انتخاب کنید / Select your language:

"
        "/setlang_fa — U0001f1eeU0001f1f7 فارسی
"
        "/setlang_en — U0001f1ecU0001f1e7 English
"
        "/setlang_ar — U0001f1f8U0001f1e6 عربی
"
        "/setlang_tr — U0001f1f9U0001f1f7 Türkçe
"
        "/setlang_ru — U0001f1f7U0001f1fa Русский
"
    )
    await message.answer(text)


@router.message(F.text.startswith("/setlang_"))
async def set_language_cmd(message: Message, _: callable, db_session: AsyncSession = None, db_user=None, **kwargs):
    lang = message.text.replace("/setlang_", "").strip()
    if lang not in settings.SUPPORTED_LANGUAGES:
        await message.answer("❌ زبان نامعتبر است.")
        return
    if db_session and db_user:
        db_user.language = lang
        try:
            await db_session.flush()
        except Exception:
            pass
    name = message.from_user.first_name or "User"
    await message.answer(_get_commands(lang, name))


# Graceful fallback for old inline button callbacks
@router.callback_query(F.data.startswith("lang:"))
async def lang_callback_fallback(callback: CallbackQuery, db_session: AsyncSession = None, db_user=None, **kwargs):
    lang = callback.data.split(":")[1]
    if lang in settings.SUPPORTED_LANGUAGES and db_session and db_user:
        db_user.language = lang
        try:
            await db_session.flush()
        except Exception:
            pass
    name = callback.from_user.first_name or "User"
    text = _get_commands(lang if lang in settings.SUPPORTED_LANGUAGES else "fa", name)
    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data.startswith("menu:"))
async def menu_fallback(callback: CallbackQuery, **kwargs):
    await callback.answer()


@router.callback_query(F.data == "group:main")
async def group_main_refresh(callback: CallbackQuery, **kwargs):
    await callback.answer()
