from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.keyboards.main_menu import back_button_kb
import structlog

logger = structlog.get_logger()
router = Router()


def help_kb(_) -> object:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_help_security"), callback_data="help:security")
    builder.button(text=_("btn_help_moderation"), callback_data="help:moderation")
    builder.button(text=_("btn_help_economy"), callback_data="help:economy")
    builder.button(text=_("btn_help_games"), callback_data="help:games")
    builder.button(text=_("btn_back"), callback_data="menu:main")
    builder.button(text=_("btn_support"), url="https://t.me/VPS24H")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


@router.callback_query(F.data == "menu:help")
async def help_menu(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(_("help_menu"), reply_markup=help_kb(_), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "help:security")
async def help_security(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(
        _("help_security_text"),
        reply_markup=back_button_kb(_, "menu:help"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "help:moderation")
async def help_moderation(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(
        _("help_moderation_text"),
        reply_markup=back_button_kb(_, "menu:help"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "help:economy")
async def help_economy(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(
        _("help_economy_text"),
        reply_markup=back_button_kb(_, "menu:help"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "help:games")
async def help_games(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(
        _("help_games_text"),
        reply_markup=back_button_kb(_, "menu:help"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "help:gameslist")
async def help_gameslist(callback: CallbackQuery, _: callable, **kwargs):
    text = (
        "🎮 <b>لیست بازی‌ها</b>\n━━━━━━━━━━━━\n\n"
        "1️⃣ 🎲 <b>تاس هوشمند</b> — چندین حالت مختلف\n"
        "2️⃣ 🧠 <b>کوئیز هوش</b> — سوالات فارسی + XP\n"
        "3️⃣ 🗺️ <b>شکار گنج</b> — پاداش تصادفی\n"
        "4️⃣ 🎡 <b>چرخ شانس</b> — ضریب‌های جذاب\n"
        "5️⃣ 🃏 <b>نبرد کارت</b> — کارت بالاتر برنده\n"
        "6️⃣ 🔢 <b>نبرد اعداد</b> — عدد بزرگ‌تر برنده\n"
        "7️⃣ ✊ <b>سنگ کاغذ قیچی</b> — کلاسیک!\n"
        "8️⃣ 💣 <b>مین‌یاب</b> — خانه‌ها رو کشف کن\n"
        "9️⃣ ♟️ <b>شطرنج سریع</b> — مهره‌ها می‌جنگند\n"
        "🔟 🎰 <b>رولت</b> — شانست رو امتحان کن\n\n"
        "🎯 همه بازی‌ها: سکه • XP • آمار • رتبه‌بندی"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:help"))
    await callback.answer()


@router.callback_query(F.data == "help:duels")
async def help_duels(callback: CallbackQuery, _: callable, **kwargs):
    text = (
        "⚔️ <b>مبارزه و تورنمنت</b>\n━━━━━━━━━━━━\n\n"
        "<b>مبارزه:</b>\n"
        "• با /duel @user [شرط] به مبارزه دعوت کنید\n"
        "• بازنده شرط را از دست می‌دهد\n"
        "• آمار مبارزات ذخیره می‌شود\n"
        "• ریسه پیروزی پاداش ویژه دارد\n\n"
        "<b>تورنمنت:</b>\n"
        "• تورنمنت‌های خودکار و برنامه‌ریزی شده\n"
        "• حق شرکت = جایزه\n"
        "• سیستم حذفی عادلانه\n"
        "• ۳ نفر اول جوایز ویژه می‌گیرند"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:help"))
    await callback.answer()


@router.callback_query(F.data == "help:achievements")
async def help_achievements(callback: CallbackQuery, _: callable, **kwargs):
    text = (
        "🏅 <b>سیستم دستاوردها</b>\n━━━━━━━━━━━━\n\n"
        "بیش از ۱۰۰ دستاورد در ۵ دسته:\n\n"
        "🎮 <b>بازی‌ها</b> — بُرد، ریسه، تخصص\n"
        "💰 <b>اقتصاد</b> — پس‌انداز، هزینه، رکوردها\n"
        "📊 <b>فعالیت</b> — پیام، جوایز، سطح\n"
        "🤝 <b>جامعه</b> — دعوت، اعتبار، مشارکت\n"
        "🎪 <b>رویدادها</b> — تورنمنت، چالش‌های فصلی\n\n"
        "هر دستاورد: سکه + XP + امتیاز دستاورد"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:help"))
    await callback.answer()


@router.callback_query(F.data == "help:commands")
async def help_commands(callback: CallbackQuery, _: callable, **kwargs):
    text = (
        "📋 <b>همه دستورات</b>\n━━━━━━━━━━━━\n\n"
        "<b>مدیریت (فقط ادمین):</b>\n"
        "/ban @user — بن دائم\n"
        "/unban @user — رفع بن\n"
        "/kick @user — اخراج\n"
        "/mute @user — بی‌صدا\n"
        "/unmute @user — رفع بی‌صدا\n"
        "/warn @user — اخطار\n"
        "/warns @user — مشاهده اخطارها\n\n"
        "<b>اقتصاد:</b>\n"
        "/balance یا /wallet — موجودی\n"
        "/daily — جایزه روزانه\n\n"
        "<b>بازی:</b>\n"
        "/duel @user [شرط] — مبارزه\n\n"
        "<b>عمومی:</b>\n"
        "/start — شروع ربات\n"
        "/menu — منوی اصلی\n"
        "/help — راهنما"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "menu:help"))
    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message, _: callable, **kwargs):
    await message.answer(_("help_menu"), reply_markup=help_kb(_), parse_mode="HTML")
