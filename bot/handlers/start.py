from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.main_menu import language_selection_kb, main_menu_kb
from bot.services.user_service import set_user_language
from bot.config import settings
import structlog

logger = structlog.get_logger()
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, _: callable, db_session=None, db_user=None, lang: str = "en", **kwargs):
    if message.chat.type != "private":
        return

    args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if args.startswith("ref_") and db_session and db_user:
        try:
            referrer_id = int(args[4:])
            if referrer_id != message.from_user.id:
                from bot.services.economy_service import process_referral
                rewarded = await process_referral(
                    db_session,
                    referrer_id=referrer_id,
                    new_user_id=db_user.id,
                )
                if rewarded:
                    logger.info("Referral reward granted", new_user=message.from_user.id, referrer=referrer_id)
        except Exception:
            logger.warning("Failed to process referral", args=args)

    await message.answer(
        _("select_language"),
        reply_markup=language_selection_kb(),
    )


@router.callback_query(F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery, _: callable, lang: str = "en", db_session=None, db_user=None, **kwargs):
    selected_lang = callback.data.split(":")[1]
    if selected_lang not in settings.SUPPORTED_LANGUAGES:
        await callback.answer("Invalid language", show_alert=True)
        return

    if db_session and db_user:
        try:
            await set_user_language(db_session, callback.from_user.id, selected_lang)
            db_user.language = selected_lang
        except Exception as e:
            logger.warning("Could not save language to DB", error=str(e))

    from bot.middlewares.i18n import get_text
    new_ = lambda key, **kw: get_text(selected_lang, key, **kw)

    await callback.message.edit_text(
        new_("welcome_bot"),
        reply_markup=main_menu_kb(new_),
        parse_mode="HTML",
    )
    await callback.answer(new_("language_set"))


@router.callback_query(F.data == "menu:main")
async def main_menu(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(
        _("main_menu"),
        reply_markup=main_menu_kb(_),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:language")
async def change_language(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(
        _("select_language"),
        reply_markup=language_selection_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:channel")
async def channel_info(callback: CallbackQuery, _: callable, **kwargs):
    from bot.keyboards.main_menu import back_button_kb
    await callback.message.edit_text(
        "📢 <b>Official Channel</b>\n\n"
        "Stay updated with Guardian X news, updates and announcements!\n\n"
        "🔔 Join our channel to get the latest features and tips.",
        reply_markup=back_button_kb(_),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:tournaments")
async def tournaments_menu(callback: CallbackQuery, _: callable, **kwargs):
    from bot.keyboards.main_menu import back_button_kb
    await callback.message.edit_text(
        "🏆 <b>Tournaments</b>\n\n"
        "🚧 <b>Coming Soon!</b>\n\n"
        "Compete with other groups in exciting tournaments!\n"
        "• 🎮 Game tournaments\n"
        "• ⚡ Duel championships\n"
        "• 🏅 Prize pools & rewards",
        reply_markup=back_button_kb(_),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("menu"))
async def cmd_menu(message: Message, _: callable, **kwargs):
    if message.chat.type != "private":
        return
    await message.answer(
        _("main_menu"),
        reply_markup=main_menu_kb(_),
        parse_mode="HTML",
    )
