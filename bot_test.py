"""
GUARDIAN X ULTIMATE — Full Interactive Bot (Debugged & Tested)
"""
import asyncio
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, BotCommand
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

# ─── Languages ────────────────────────────────────────────────────────────────
LANGUAGES = {
    "en": "🇬🇧 English",
    "fa": "🇮🇷 فارسی",
    "ar": "🇸🇦 العربية",
    "tr": "🇹🇷 Türkçe",
    "ru": "🇷🇺 Русский",
    "es": "🇪🇸 Español",
    "fr": "🇫🇷 Français",
    "de": "🇩🇪 Deutsch",
}

# ─── In-memory user store ─────────────────────────────────────────────────────
user_data: dict[int, dict] = {}

def get_user(uid: int) -> dict:
    if uid not in user_data:
        user_data[uid] = {"lang": "en", "coins": 500, "bank": 0, "level": 1, "xp": 0}
    return user_data[uid]

def lang(uid: int) -> str:
    return get_user(uid).get("lang", "en")

def is_fa(uid: int) -> bool:
    return lang(uid) == "fa"

# ─── Safe edit helper ─────────────────────────────────────────────────────────
async def safe_edit(callback: CallbackQuery, text: str, kb=None):
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")

# ─── Texts ────────────────────────────────────────────────────────────────────
def txt(uid: int, key: str) -> str:
    fa_texts = {
        "welcome": (
            "👋 <b>به GUARDIAN X ULTIMATE خوش آمدید!</b>\n\n"
            "🛡️ مدیریت کامل گروه تلگرام شما.\n\n"
            "✅ <b>قابلیت‌ها:</b>\n"
            "🔒 امنیت (۲۰+ ویژگی)\n"
            "⚖️ مدیریت (بن/سکوت/اخطار/اخراج)\n"
            "💰 اقتصاد (سکه، بانک، جوایز روزانه)\n"
            "🎮 بازی‌ها (۱۰ نوع مختلف)\n"
            "⚔️ دوئل و تورنمنت\n"
            "🏅 ۱۰۰+ دستاورد\n"
            "🌍 ۸ زبان\n\n"
            "📌 مرا به گروه خود اضافه کنید!"
        ),
        "main_menu":     "🛡️ <b>GUARDIAN X ULTIMATE</b>\n\nیک گزینه انتخاب کنید:",
        "lang_select":   "🌍 <b>انتخاب زبان</b>\n\nزبان مورد نظرت رو انتخاب کن:",
        "security":      "🔒 <b>پنل امنیتی</b>\n\n۲۰+ ویژگی امنیتی. یک بخش انتخاب کنید:",
        "moderation":    "⚖️ <b>پنل مدیریت</b>\n\nابزارهای مدیریت گروه:",
        "economy":       "💰 <b>سیستم اقتصادی</b>\n\nکیف پول، بانک، جوایز:",
        "games":         "🎮 <b>بازی‌ها</b>\n\nیک بازی انتخاب کنید:",
        "duels":         "⚔️ <b>دوئل‌ها</b>\n\nرقیبت رو به مبارزه دعوت کن!",
        "achievements":  "🏅 <b>دستاوردها</b>\n\n۱۰۰+ دستاورد در ۵ دسته:",
        "stats":         "📊 <b>آمار و جدول امتیازات</b>\n\nیک جدول انتخاب کنید:",
        "settings":      "⚙️ <b>تنظیمات</b>\n\nتنظیمات گروه و ربات:",
        "help":          "❓ <b>راهنما</b>\n\nیک بخش انتخاب کنید:",
        "back":          "◀️ بازگشت",
    }
    en_texts = {
        "welcome": (
            "👋 <b>Welcome to GUARDIAN X ULTIMATE!</b>\n\n"
            "🛡️ Your all-in-one Telegram group manager.\n\n"
            "✅ <b>Features:</b>\n"
            "🔒 Security (20+ features)\n"
            "⚖️ Moderation (ban/mute/warn/kick)\n"
            "💰 Economy (coins, bank, daily rewards)\n"
            "🎮 Games (10 types)\n"
            "⚔️ Duels & Tournaments\n"
            "🏅 100+ Achievements\n"
            "🌍 8 Languages\n\n"
            "📌 Add me to your group to get started!"
        ),
        "main_menu":     "🛡️ <b>GUARDIAN X ULTIMATE</b>\n\nSelect an option:",
        "lang_select":   "🌍 <b>Select Language</b>\n\nChoose your preferred language:",
        "security":      "🔒 <b>Security Panel</b>\n\n20+ features. Select a section:",
        "moderation":    "⚖️ <b>Moderation Panel</b>\n\nGroup management tools:",
        "economy":       "💰 <b>Economy System</b>\n\nWallet, bank, rewards:",
        "games":         "🎮 <b>Games</b>\n\nSelect a game:",
        "duels":         "⚔️ <b>Duels</b>\n\nChallenge others for their coins!",
        "achievements":  "🏅 <b>Achievements</b>\n\n100+ achievements in 5 categories:",
        "stats":         "📊 <b>Stats & Leaderboards</b>\n\nSelect a board:",
        "settings":      "⚙️ <b>Settings</b>\n\nGroup and bot settings:",
        "help":          "❓ <b>Help Center</b>\n\nSelect a section:",
        "back":          "◀️ Back",
    }
    if is_fa(uid):
        return fa_texts.get(key, en_texts.get(key, key))
    return en_texts.get(key, key)

# ─── Keyboards ────────────────────────────────────────────────────────────────
def kb_lang():
    b = InlineKeyboardBuilder()
    for code, label in LANGUAGES.items():
        b.button(text=label, callback_data=f"set_lang:{code}")
    b.adjust(2)
    return b.as_markup()

def kb_back(uid: int, dest: str):
    b = InlineKeyboardBuilder()
    b.button(text=txt(uid, "back"), callback_data=f"nav:{dest}")
    return b.as_markup()

def kb_main(uid: int):
    fa = is_fa(uid)
    b = InlineKeyboardBuilder()
    b.button(text="🔒 امنیت"      if fa else "🔒 Security",     callback_data="nav:security")
    b.button(text="⚖️ مدیریت"     if fa else "⚖️ Moderation",   callback_data="nav:moderation")
    b.button(text="💰 اقتصاد"     if fa else "💰 Economy",       callback_data="nav:economy")
    b.button(text="🎮 بازی‌ها"    if fa else "🎮 Games",         callback_data="nav:games")
    b.button(text="⚔️ دوئل"       if fa else "⚔️ Duels",         callback_data="nav:duels")
    b.button(text="🏅 دستاوردها"  if fa else "🏅 Achievements",  callback_data="nav:achievements")
    b.button(text="📊 آمار"       if fa else "📊 Statistics",    callback_data="nav:stats")
    b.button(text="⚙️ تنظیمات"   if fa else "⚙️ Settings",      callback_data="nav:settings")
    b.button(text="❓ راهنما"     if fa else "❓ Help",           callback_data="nav:help")
    b.button(text="🌍 زبان"       if fa else "🌍 Language",       callback_data="nav:language")
    b.adjust(2, 2, 2, 2, 2)
    return b.as_markup()

def kb_security(uid: int):
    fa = is_fa(uid)
    b = InlineKeyboardBuilder()
    b.button(text="🚫 ضد اسپم"      if fa else "🚫 Anti-Spam",    callback_data="sec:spam")
    b.button(text="🛡️ ضد حمله"      if fa else "🛡️ Anti-Raid",    callback_data="sec:raid")
    b.button(text="🔐 کپچا"         if fa else "🔐 Captcha",       callback_data="sec:captcha")
    b.button(text="🔒 قفل محتوا"    if fa else "🔒 Locks",         callback_data="sec:locks")
    b.button(text="🤖 ضد ربات"      if fa else "🤖 Anti-Bot",      callback_data="sec:antibot")
    b.button(text="📢 ضد تبلیغ"     if fa else "📢 Anti-Ad",       callback_data="sec:antiad")
    b.button(text="🔞 ضد NSFW"      if fa else "🔞 Anti-NSFW",     callback_data="sec:nsfw")
    b.button(text="📵 ضد فوروارد"   if fa else "📵 Anti-Forward",  callback_data="sec:forward")
    b.button(text=txt(uid,"back"),                                   callback_data="nav:main")
    b.adjust(2, 2, 2, 2, 1)
    return b.as_markup()

def kb_moderation(uid: int):
    fa = is_fa(uid)
    b = InlineKeyboardBuilder()
    b.button(text="🚫 بن"          if fa else "🚫 Ban",           callback_data="mod:ban")
    b.button(text="🔇 سکوت"        if fa else "🔇 Mute",          callback_data="mod:mute")
    b.button(text="⚠️ اخطار"       if fa else "⚠️ Warn",          callback_data="mod:warn")
    b.button(text="👢 اخراج"       if fa else "👢 Kick",           callback_data="mod:kick")
    b.button(text="📝 یادداشت"     if fa else "📝 Notes",          callback_data="mod:notes")
    b.button(text="📋 سابقه"       if fa else "📋 History",        callback_data="mod:history")
    b.button(text="🔓 آنبن"        if fa else "🔓 Unban",          callback_data="mod:unban")
    b.button(text="🔊 آنسکوت"      if fa else "🔊 Unmute",         callback_data="mod:unmute")
    b.button(text=txt(uid,"back"),                                   callback_data="nav:main")
    b.adjust(2, 2, 2, 2, 1)
    return b.as_markup()

def kb_economy(uid: int):
    fa = is_fa(uid)
    b = InlineKeyboardBuilder()
    b.button(text="👛 کیف‌پول"     if fa else "👛 Wallet",         callback_data="eco:wallet")
    b.button(text="🎁 جوایز"       if fa else "🎁 Rewards",        callback_data="eco:rewards")
    b.button(text="🏦 بانک"        if fa else "🏦 Bank",           callback_data="eco:bank")
    b.button(text="💸 انتقال"      if fa else "💸 Transfer",        callback_data="eco:transfer")
    b.button(text="🛍️ فروشگاه"    if fa else "🛍️ Shop",           callback_data="eco:shop")
    b.button(text="📜 تاریخچه"     if fa else "📜 History",         callback_data="eco:history")
    b.button(text=txt(uid,"back"),                                   callback_data="nav:main")
    b.adjust(2, 2, 2, 1)
    return b.as_markup()

def kb_games(uid: int):
    fa = is_fa(uid)
    b = InlineKeyboardBuilder()
    b.button(text="🎲 تاس هوشمند"       if fa else "🎲 Smart Dice",       callback_data="game:dice")
    b.button(text="🎡 چرخ شانس"         if fa else "🎡 Lucky Wheel",       callback_data="game:wheel")
    b.button(text="✊ سنگ کاغذ قیچی"    if fa else "✊ Rock Paper Scissors",callback_data="game:rps")
    b.button(text="💣 مین‌ها"           if fa else "💣 Mines",             callback_data="game:mines")
    b.button(text="🧠 مسابقه دانش"      if fa else "🧠 Quiz Battle",        callback_data="game:quiz")
    b.button(text="🃏 بازی کارت"        if fa else "🃏 Card Battle",        callback_data="game:cards")
    b.button(text="🔢 جنگ اعداد"        if fa else "🔢 Number War",         callback_data="game:numwar")
    b.button(text="♟️ شطرنج مینی"       if fa else "♟️ Chess Mini",         callback_data="game:chess")
    b.button(text="🎰 رولت"             if fa else "🎰 Roulette",           callback_data="game:roulette")
    b.button(text="🗺️ گنج‌یابی"        if fa else "🗺️ Treasure Hunt",      callback_data="game:treasure")
    b.button(text=txt(uid,"back"),                                            callback_data="nav:main")
    b.adjust(2, 2, 2, 2, 2, 1)
    return b.as_markup()

def kb_duels(uid: int):
    fa = is_fa(uid)
    b = InlineKeyboardBuilder()
    b.button(text="⚔️ دوئل جدید"    if fa else "⚔️ New Duel",        callback_data="duel:new")
    b.button(text="🏆 تورنمنت"      if fa else "🏆 Tournament",       callback_data="duel:tournament")
    b.button(text="📊 آمار من"      if fa else "📊 My Stats",         callback_data="duel:stats")
    b.button(text="🏅 تاریخچه"      if fa else "🏅 History",          callback_data="duel:history")
    b.button(text=txt(uid,"back"),                                      callback_data="nav:main")
    b.adjust(2, 2, 1)
    return b.as_markup()

def kb_achievements(uid: int):
    fa = is_fa(uid)
    b = InlineKeyboardBuilder()
    b.button(text="🎮 بازی"         if fa else "🎮 Games",            callback_data="ach:games")
    b.button(text="💰 اقتصاد"      if fa else "💰 Economy",           callback_data="ach:economy")
    b.button(text="📊 فعالیت"      if fa else "📊 Activity",          callback_data="ach:activity")
    b.button(text="🤝 جامعه"       if fa else "🤝 Community",         callback_data="ach:community")
    b.button(text="🎪 رویدادها"    if fa else "🎪 Events",            callback_data="ach:events")
    b.button(text=txt(uid,"back"),                                      callback_data="nav:main")
    b.adjust(2, 2, 1, 1)
    return b.as_markup()

def kb_stats(uid: int):
    fa = is_fa(uid)
    b = InlineKeyboardBuilder()
    b.button(text="💰 ثروتمندترین"  if fa else "💰 Richest",          callback_data="stat:rich")
    b.button(text="⭐ بالاترین سطح" if fa else "⭐ Top Levels",        callback_data="stat:levels")
    b.button(text="🏆 بیشترین برد"  if fa else "🏆 Most Wins",         callback_data="stat:wins")
    b.button(text="⚔️ دوئلیست‌ها"  if fa else "⚔️ Top Duelers",       callback_data="stat:duelers")
    b.button(text="🌟 اعتبار"       if fa else "🌟 Reputation",        callback_data="stat:rep")
    b.button(text=txt(uid,"back"),                                      callback_data="nav:main")
    b.adjust(2, 2, 1, 1)
    return b.as_markup()

def kb_settings(uid: int):
    fa = is_fa(uid)
    b = InlineKeyboardBuilder()
    b.button(text="🌍 تغییر زبان"    if fa else "🌍 Language",         callback_data="nav:language")
    b.button(text="👋 پیام خوش‌آمد" if fa else "👋 Welcome Message",   callback_data="cfg:welcome")
    b.button(text="📋 کانال لاگ"    if fa else "📋 Log Channel",       callback_data="cfg:logs")
    b.button(text="⚙️ تنظیمات کلی"  if fa else "⚙️ General",           callback_data="cfg:general")
    b.button(text=txt(uid,"back"),                                       callback_data="nav:main")
    b.adjust(2, 2, 1)
    return b.as_markup()

def kb_help(uid: int):
    fa = is_fa(uid)
    b = InlineKeyboardBuilder()
    b.button(text="📋 دستورات"      if fa else "📋 Commands",          callback_data="help:commands")
    b.button(text="🔒 امنیت"       if fa else "🔒 Security Guide",     callback_data="help:security")
    b.button(text="💰 اقتصاد"      if fa else "💰 Economy Guide",      callback_data="help:economy")
    b.button(text="🎮 بازی‌ها"     if fa else "🎮 Games Guide",        callback_data="help:games")
    b.button(text="⚔️ دوئل"        if fa else "⚔️ Duels Guide",        callback_data="help:duels")
    b.button(text=txt(uid,"back"),                                       callback_data="nav:main")
    b.adjust(2, 2, 1, 1)
    return b.as_markup()

# ─── Section content ──────────────────────────────────────────────────────────
SEC_CONTENT = {
    "spam":    {"fa": "🚫 <b>ضد اسپم</b>\n\n• حذف پیام‌های تکراری\n• محدودیت سرعت پیام\n• فیلتر لینک تبلیغاتی\n• مسدود لینک دعوت\n\n<b>اقدامات:</b> حذف / اخطار / سکوت / بن", "en": "🚫 <b>Anti-Spam</b>\n\n• Delete duplicate messages\n• Rate limiting\n• Filter promo links\n• Block invite links\n\n<b>Actions:</b> Delete / Warn / Mute / Ban"},
    "raid":    {"fa": "🛡️ <b>ضد حمله (Anti-Raid)</b>\n\n• شناسایی ورود گروهی مشکوک\n• قفل خودکار گروه\n• کپچا اجباری برای اعضای جدید\n• محدودیت ورود در بازه زمانی", "en": "🛡️ <b>Anti-Raid</b>\n\n• Detect mass join attacks\n• Auto-lock group\n• Mandatory captcha\n• Join rate limiting"},
    "captcha": {"fa": "🔐 <b>سیستم کپچا</b>\n\nانواع کپچا:\n1️⃣ دکمه‌ای — کلیک برای تأیید\n2️⃣ ریاضی — حل معادله ساده\n3️⃣ سؤالی — پاسخ متنی\n\n⏱️ مهلت پیش‌فرض: ۶۰ ثانیه", "en": "🔐 <b>Captcha System</b>\n\nTypes:\n1️⃣ Button — click to verify\n2️⃣ Math — solve equation\n3️⃣ Question — text answer\n\n⏱️ Default timeout: 60s"},
    "locks":   {"fa": "🔒 <b>قفل محتوا</b>\n\nقفل این نوع محتواها:\n📝 متن  🖼️ عکس  🎥 ویدیو  🎵 صدا\n📄 فایل  🎤 ویس  🎞️ گیف  🖥️ استیکر\n📍 موقعیت  📞 تماس  🗳️ نظرسنجی\n🔗 لینک  👥 دعوت‌نامه  ♻️ فوروارد", "en": "🔒 <b>Content Locks</b>\n\nLock these types:\n📝 Text  🖼️ Photo  🎥 Video  🎵 Audio\n📄 Files  🎤 Voice  🎞️ GIF  🖥️ Sticker\n📍 Location  📞 Contact  🗳️ Poll\n🔗 Links  👥 Invites  ♻️ Forwards"},
    "antibot": {"fa": "🤖 <b>ضد ربات</b>\n\n• بررسی نام کاربری مشکوک\n• بررسی سن اکانت\n• کپچا اجباری برای اکانت‌های جدید\n• لیست سیاه ربات‌های شناخته‌شده", "en": "🤖 <b>Anti-Bot</b>\n\n• Suspicious username check\n• Account age verification\n• Mandatory captcha for new accounts\n• Known bot blacklist"},
    "antiad":  {"fa": "📢 <b>ضد تبلیغ</b>\n\n• مسدود لینک‌های خارجی\n• مسدود دعوت‌نامه کانال\n• مسدود تبلیغ @username\n• مسدود کیبورد اسپم", "en": "📢 <b>Anti-Advertisement</b>\n\n• Block external links\n• Block channel invites\n• Block @username promotion\n• Block keyboard spam"},
    "nsfw":    {"fa": "🔞 <b>ضد محتوای نامناسب</b>\n\n• تشخیص عکس/ویدیوی نامناسب\n• فیلتر کلمات توهین‌آمیز\n• مسدود محتوای بزرگسال", "en": "🔞 <b>Anti-NSFW</b>\n\n• Detect inappropriate photos/videos\n• Filter offensive words\n• Block adult content"},
    "forward": {"fa": "📵 <b>ضد فوروارد</b>\n\n• جلوگیری از فوروارد پیام\n• مسدود فوروارد از کانال‌های خاص\n• فوروارد از ربات مسدود می‌شود", "en": "📵 <b>Anti-Forward</b>\n\n• Prevent message forwarding\n• Block forwards from specific channels\n• Block bot-forwarded messages"},
}

MOD_CONTENT = {
    "ban":     {"fa": "🚫 <b>بن کاربر</b>\n\nدستور: <code>/ban @user [دلیل]</code>\nمثال: <code>/ban @user اسپم</code>\n\n• بن دائمی یا موقت\n• ذخیره در سابقه\n• آنبن: <code>/unban @user</code>", "en": "🚫 <b>Ban User</b>\n\nCommand: <code>/ban @user [reason]</code>\nExample: <code>/ban @user spam</code>\n\n• Permanent or temporary\n• Saved in history\n• Unban: <code>/unban @user</code>"},
    "mute":    {"fa": "🔇 <b>سکوت کاربر</b>\n\nدستور: <code>/mute @user [مدت] [دلیل]</code>\nمثال: <code>/mute @user 1h اسپم</code>\n\nمدت‌ها: 30m / 1h / 6h / 1d / 1w\nآنسکوت: <code>/unmute @user</code>", "en": "🔇 <b>Mute User</b>\n\nCommand: <code>/mute @user [time] [reason]</code>\nExample: <code>/mute @user 1h spam</code>\n\nDurations: 30m / 1h / 6h / 1d / 1w\nUnmute: <code>/unmute @user</code>"},
    "warn":    {"fa": "⚠️ <b>سیستم اخطار</b>\n\nدستور: <code>/warn @user [دلیل]</code>\n\n• حداکثر اخطار: ۳ (قابل تنظیم)\n• بعد از حداکثر: بن خودکار\n• مشاهده: <code>/warns @user</code>\n• حذف: <code>/unwarn @user</code>", "en": "⚠️ <b>Warning System</b>\n\nCommand: <code>/warn @user [reason]</code>\n\n• Max warnings: 3 (configurable)\n• After max: auto-ban\n• View: <code>/warns @user</code>\n• Remove: <code>/unwarn @user</code>"},
    "kick":    {"fa": "👢 <b>اخراج کاربر</b>\n\nدستور: <code>/kick @user [دلیل]</code>\n\n• کاربر از گروه خارج می‌شود\n• می‌تواند دوباره وارد شود\n• مناسب برای تخلفات کوچک", "en": "👢 <b>Kick User</b>\n\nCommand: <code>/kick @user [reason]</code>\n\n• User is removed from group\n• They can rejoin\n• Suitable for minor violations"},
    "notes":   {"fa": "📝 <b>یادداشت‌های ادمین</b>\n\nدستور: <code>/note @user [متن]</code>\nمشاهده: <code>/notes @user</code>\n\nیادداشت‌ها فقط برای ادمین‌ها قابل رؤیت است.", "en": "📝 <b>Admin Notes</b>\n\nAdd: <code>/note @user [text]</code>\nView: <code>/notes @user</code>\n\nNotes are only visible to admins."},
    "history": {"fa": "📋 <b>سابقه کاربر</b>\n\nدستور: <code>/history @user</code>\n\nنمایش همه اقدامات: بن، سکوت، اخطار، اخراج.", "en": "📋 <b>User History</b>\n\nCommand: <code>/history @user</code>\n\nShows all actions: bans, mutes, warns, kicks."},
    "unban":   {"fa": "🔓 <b>آنبن کاربر</b>\n\nدستور: <code>/unban @user</code>\n\nکاربر بن‌شده را از لیست سیاه خارج می‌کند.", "en": "🔓 <b>Unban User</b>\n\nCommand: <code>/unban @user</code>\n\nRemoves user from the ban list."},
    "unmute":  {"fa": "🔊 <b>آنسکوت کاربر</b>\n\nدستور: <code>/unmute @user</code>\n\nمحدودیت ارسال پیام کاربر را برمی‌دارد.", "en": "🔊 <b>Unmute User</b>\n\nCommand: <code>/unmute @user</code>\n\nRestores the user's messaging permissions."},
}

GAME_CONTENT = {
    "dice":     {"fa": "🎲 <b>تاس هوشمند — ۱۰ حالت</b>\n\n1️⃣ کلاسیک — بالاترین عدد برنده\n2️⃣ پیش‌بینی — عدد رو حدس بزن\n3️⃣ ضریب شانس — تا ۶× جایزه\n4️⃣ بهترین ۳ — سه دور بازی\n5️⃣ بهترین ۵ — پنج دور بازی\n6️⃣ تورنمنت — رقابت گروهی\n7️⃣ نبرد گروهی — همه شرکت کنند\n8️⃣ چالش روزانه — یک بار در روز\n9️⃣ استریک — بردهای متوالی\n🔟 آرنای VIP — شرط بالا\n\nدستور: <code>/dice [مبلغ]</code>",   "en": "🎲 <b>Smart Dice — 10 Modes</b>\n\n1️⃣ Classic — highest wins\n2️⃣ Prediction — guess the number\n3️⃣ Lucky Multiplier — up to 6×\n4️⃣ Best of 3\n5️⃣ Best of 5\n6️⃣ Tournament mode\n7️⃣ Group Battle\n8️⃣ Daily Challenge\n9️⃣ Streak mode\n🔟 VIP Arena\n\nCommand: <code>/dice [bet]</code>"},
    "wheel":    {"fa": "🎡 <b>چرخ شانس</b>\n\nبچرخان و جایزه بگیر!\n\n❌ ۰× — باخت (۲۰٪)\n➖ 0.5× — نصف شرط (۲۰٪)\n✅ 1× — برگشت شرط (۲۰٪)\n💰 2× — دو برابر (۲۰٪)\n💎 3× — سه برابر (۱۰٪)\n🔥 5× — پنج برابر (۸٪)\n👑 10× — ده برابر (۲٪)\n\nدستور: <code>/wheel [مبلغ]</code>", "en": "🎡 <b>Lucky Wheel</b>\n\nSpin and win!\n\n❌ 0× — lose (20%)\n➖ 0.5× — half back (20%)\n✅ 1× — get back (20%)\n💰 2× — double (20%)\n💎 3× — triple (10%)\n🔥 5× — 5x (8%)\n👑 10× — jackpot (2%)\n\nCommand: <code>/wheel [bet]</code>"},
    "rps":      {"fa": "✊ <b>سنگ کاغذ قیچی</b>\n\nبا ربات یا کاربران دیگر بازی کن!\n\n✊ سنگ — ✂️ قیچی — 📄 کاغذ\n\nدستور: <code>/rps [مبلغ]</code>\nدوئل: <code>/rps @user [مبلغ]</code>", "en": "✊ <b>Rock Paper Scissors</b>\n\nPlay vs bot or other users!\n\n✊ Rock — ✂️ Scissors — 📄 Paper\n\nCommand: <code>/rps [bet]</code>\nDuel: <code>/rps @user [bet]</code>"},
    "mines":    {"fa": "💣 <b>مین‌ها</b>\n\nخانه‌ها رو باز کن، از مین فرار کن!\n\nهر خانه امن = ۱.۲× ضریب\nبه موقع متوقف شو یا همه رو از دست بده!\n\nدستور: <code>/mines [مبلغ]</code>", "en": "💣 <b>Mines</b>\n\nReveal tiles, avoid mines!\n\nEach safe tile = 1.2× multiplier\nCash out in time or lose it all!\n\nCommand: <code>/mines [bet]</code>"},
    "quiz":     {"fa": "🧠 <b>مسابقه دانش</b>\n\nدسته‌های سؤال:\n• علوم، جغرافیا، تاریخ\n• ورزش، سینما، موسیقی\n• فناوری، ادبیات\n\nپاسخ صحیح = سکه + XP\n\nدستور: <code>/quiz</code>", "en": "🧠 <b>Quiz Battle</b>\n\nQuestion categories:\n• Science, Geography, History\n• Sports, Movies, Music\n• Technology, Literature\n\nCorrect answer = coins + XP\n\nCommand: <code>/quiz</code>"},
    "cards":    {"fa": "🃏 <b>بازی کارت</b>\n\nبیشترین مجموع امتیاز کارت برنده!\nبا حریف انسانی یا ربات بازی کن.\n\nدستور: <code>/cards [مبلغ]</code>", "en": "🃏 <b>Card Battle</b>\n\nHighest total card score wins!\nPlay vs human or bot.\n\nCommand: <code>/cards [bet]</code>"},
    "numwar":   {"fa": "🔢 <b>جنگ اعداد</b>\n\nعدد بالاتر برنده است!\nهم‌زمان انتخاب کنید — کسی نمی‌بیند.\n\nدستور: <code>/numwar [مبلغ]</code>", "en": "🔢 <b>Number War</b>\n\nHigher number wins!\nBoth players choose simultaneously.\n\nCommand: <code>/numwar [bet]</code>"},
    "chess":    {"fa": "♟️ <b>شطرنج مینی</b>\n\nرویارویی سریع شطرنجی.\n۵ دقیقه برای هر بازیکن.\n\nدستور: <code>/chess @user</code>", "en": "♟️ <b>Chess Mini</b>\n\nQuick chess battle.\n5 minutes per player.\n\nCommand: <code>/chess @user</code>"},
    "roulette": {"fa": "🎰 <b>رولت امن</b>\n\nهیجان رولت بدون ریسک واقعی!\nروی رنگ یا عدد شرط ببند.\n\nدستور: <code>/roulette [مبلغ]</code>", "en": "🎰 <b>Safe Roulette</b>\n\nRoulette thrill without real risk!\nBet on color or number.\n\nCommand: <code>/roulette [bet]</code>"},
    "treasure": {"fa": "🗺️ <b>گنج‌یابی</b>\n\nقبل از بقیه گنج مخفی رو پیدا کن!\nسرنخ‌ها در گروه ارسال می‌شوند.\n\nدستور: <code>/treasure</code>", "en": "🗺️ <b>Treasure Hunt</b>\n\nFind the hidden treasure first!\nClues are posted in the group.\n\nCommand: <code>/treasure</code>"},
}

ACH_CONTENT = {
    "games":     {"fa": "🎮 <b>دستاوردهای بازی</b>\n\n🔓 اولین برد — اولین بازی را ببر\n🔓 ده برد — ۱۰ بازی ببر\n🔓 صد برد — ۱۰۰ بازی ببر ⭐\n🔓 استریک ۵ — ۵ بار متوالی ببر\n🔓 استریک ۱۰ — ۱۰ بار متوالی ببر ⭐\n🔓 قهرمان تاس — ۵۰ بار تاس بینداز\n🔓 استاد چرخ — ۱۰۰ بار چرخ بزن\n🔓 قهرمان دوئل — ۵۰ دوئل ببر ⭐⭐", "en": "🎮 <b>Game Achievements</b>\n\n🔓 First Win\n🔓 10 Wins\n🔓 100 Wins ⭐\n🔓 5 Win Streak\n🔓 10 Win Streak ⭐\n🔓 Dice Master — 50 dice games\n🔓 Wheel Expert — 100 wheel spins\n🔓 Duel Champion — 50 duel wins ⭐⭐"},
    "economy":   {"fa": "💰 <b>دستاوردهای اقتصادی</b>\n\n🔓 اولین سکه — اولین سکه‌ات رو کسب کن\n🔓 ۱۰۰۰ سکه — ۱,۰۰۰ سکه داشته باش\n🔓 ۱۰,۰۰۰ سکه — ۱۰,۰۰۰ سکه داشته باش ⭐\n🔓 میلیونر — ۱,۰۰۰,۰۰۰ سکه ⭐⭐\n🔓 ۷ روز روزانه — ۷ روز پشت سر هم\n🔓 ۳۰ روز روزانه — ۳۰ روز پشت سر هم ⭐\n🔓 بانکدار — ۵۰۰۰ سکه واریز کن", "en": "💰 <b>Economy Achievements</b>\n\n🔓 First Coin\n🔓 1,000 Coins\n🔓 10,000 Coins ⭐\n🔓 Millionaire ⭐⭐\n🔓 7-Day Streak\n🔓 30-Day Streak ⭐\n🔓 Banker — deposit 5,000 coins"},
    "activity":  {"fa": "📊 <b>دستاوردهای فعالیت</b>\n\n🔓 اولین پیام — اولین پیامت در گروه\n🔓 ۱۰۰ پیام — ۱۰۰ پیام ارسال کن\n🔓 ۱,۰۰۰ پیام — ۱,۰۰۰ پیام ⭐\n🔓 سطح ۵ — به سطح ۵ برس\n🔓 سطح ۱۰ — به سطح ۱۰ برس ⭐\n🔓 سطح ۵۰ — به سطح ۵۰ برس ⭐⭐", "en": "📊 <b>Activity Achievements</b>\n\n🔓 First Message\n🔓 100 Messages\n🔓 1,000 Messages ⭐\n🔓 Reach Level 5\n🔓 Reach Level 10 ⭐\n🔓 Reach Level 50 ⭐⭐"},
    "community": {"fa": "🤝 <b>دستاوردهای جامعه</b>\n\n🔓 دوست‌دار — به ۵ نفر اعتبار مثبت بده\n🔓 دعوت‌کننده — ۵ نفر رو دعوت کن\n🔓 محبوب — ۵۰ اعتبار مثبت بگیر ⭐\n🔓 افسانه — ۱۰۰ اعتبار مثبت بگیر ⭐⭐", "en": "🤝 <b>Community Achievements</b>\n\n🔓 Friendly — give 5 positive reps\n🔓 Inviter — invite 5 people\n🔓 Popular — receive 50 reps ⭐\n🔓 Legend — receive 100 reps ⭐⭐"},
    "events":    {"fa": "🎪 <b>دستاوردهای رویداد</b>\n\n🔓 اولین تورنمنت — شرکت در اولین تورنمنت\n🔓 قهرمان تورنمنت — یک تورنمنت ببر ⭐\n🔓 چمپیون بزرگ — ۵ تورنمنت ببر ⭐⭐\n🔓 جشنواره — در رویداد فصلی شرکت کن", "en": "🎪 <b>Event Achievements</b>\n\n🔓 First Tournament\n🔓 Tournament Champion ⭐\n🔓 Grand Champion — 5 wins ⭐⭐\n🔓 Festival Participant"},
}

STAT_CONTENT = {
    "rich":     {"fa": "💰 <b>ثروتمندترین کاربران</b>\n\n🥇 ─ (داده‌ای موجود نیست)\n🥈 ─\n🥉 ─\n\n<i>بازی کنید تا در لیست ظاهر شوید!</i>",    "en": "💰 <b>Richest Users</b>\n\n🥇 — (no data yet)\n🥈 —\n🥉 —\n\n<i>Play games to appear here!</i>"},
    "levels":   {"fa": "⭐ <b>بالاترین سطح‌ها</b>\n\n🥇 ─ (داده‌ای موجود نیست)\n🥈 ─\n🥉 ─\n\n<i>پیام ارسال کنید تا XP کسب کنید!</i>",   "en": "⭐ <b>Top Levels</b>\n\n🥇 — (no data yet)\n🥈 —\n🥉 —\n\n<i>Send messages to earn XP!</i>"},
    "wins":     {"fa": "🏆 <b>بیشترین برد</b>\n\n🥇 ─ (داده‌ای موجود نیست)\n🥈 ─\n🥉 ─\n\n<i>در بازی‌ها شرکت کنید!</i>",              "en": "🏆 <b>Most Wins</b>\n\n🥇 — (no data yet)\n🥈 —\n🥉 —\n\n<i>Play games to rank up!</i>"},
    "duelers":  {"fa": "⚔️ <b>برترین دوئلیست‌ها</b>\n\n🥇 ─ (داده‌ای موجود نیست)\n🥈 ─\n🥉 ─",                                          "en": "⚔️ <b>Top Duelers</b>\n\n🥇 — (no data yet)\n🥈 —\n🥉 —"},
    "rep":      {"fa": "🌟 <b>بالاترین اعتبار</b>\n\n🥇 ─ (داده‌ای موجود نیست)\n🥈 ─\n🥉 ─",                                            "en": "🌟 <b>Top Reputation</b>\n\n🥇 — (no data yet)\n🥈 —\n🥉 —"},
}

HELP_CONTENT = {
    "commands": {
        "fa": (
            "📋 <b>همه دستورات</b>\n\n"
            "💡 <b>بدون / هم کار می‌کند!</b>\n\n"
            "<b>🌐 عمومی:</b>\n"
            "<code>شروع</code> — شروع ربات\n"
            "<code>منو</code> — منوی اصلی\n"
            "<code>کمک</code> — راهنما\n\n"
            "<b>💰 اقتصاد:</b>\n"
            "<code>موجودی</code> — نمایش کیف پول\n"
            "<code>روزانه</code> — جایزه روزانه (۱۰۰ سکه)\n"
            "<code>هفتگی</code> — جایزه هفتگی (۵۰۰ سکه)\n"
            "<code>واریز ۵۰۰</code> — واریز به بانک\n"
            "<code>برداشت ۲۰۰</code> — برداشت از بانک\n\n"
            "<b>🎮 بازی‌ها:</b>\n"
            "<code>/dice 100</code> — تاس با ۱۰۰ سکه\n"
            "<code>/wheel 200</code> — چرخ شانس\n"
            "<code>/mines 150</code> — بازی مین\n"
            "<code>/quiz</code> — مسابقه دانش\n\n"
            "<b>⚔️ دوئل:</b>\n"
            "<code>/duel @user 500</code> — دوئل با شرط\n\n"
            "<b>⚖️ مدیریت (ادمین):</b>\n"
            "<code>/ban @user</code> — بن\n"
            "<code>/mute @user 1h</code> — سکوت\n"
            "<code>/warn @user</code> — اخطار\n"
            "<code>/kick @user</code> — اخراج"
        ),
        "en": (
            "📋 <b>All Commands</b>\n\n"
            "💡 <b>Works without / too!</b>\n\n"
            "<b>🌐 General:</b>\n"
            "<code>start</code> — Start bot\n"
            "<code>menu</code> — Main menu\n"
            "<code>help</code> — Help\n\n"
            "<b>💰 Economy:</b>\n"
            "<code>balance</code> — Check wallet\n"
            "<code>daily</code> — Daily reward (100 coins)\n"
            "<code>weekly</code> — Weekly reward (500 coins)\n"
            "<code>deposit 500</code> — Bank deposit\n"
            "<code>withdraw 200</code> — Bank withdraw\n\n"
            "<b>🎮 Games:</b>\n"
            "<code>/dice 100</code> — Roll dice with 100 bet\n"
            "<code>/wheel 200</code> — Lucky wheel\n"
            "<code>/mines 150</code> — Mines game\n"
            "<code>/quiz</code> — Quiz battle\n\n"
            "<b>⚔️ Duels:</b>\n"
            "<code>/duel @user 500</code> — Duel with bet\n\n"
            "<b>⚖️ Moderation (Admin):</b>\n"
            "<code>/ban @user</code> — Ban\n"
            "<code>/mute @user 1h</code> — Mute\n"
            "<code>/warn @user</code> — Warn\n"
            "<code>/kick @user</code> — Kick"
        ),
    },
    "security": {"fa": "🔒 <b>راهنمای امنیت</b>\n\nمرا به گروه اضافه کن و ادمین کن.\nسپس از منو ← امنیت، همه تنظیمات رو ببین.", "en": "🔒 <b>Security Guide</b>\n\nAdd me to a group and make me admin.\nThen use Menu → Security to configure."},
    "economy":  {"fa": "💰 <b>راهنمای اقتصاد</b>\n\nهر روز جایزه بگیر و سکه جمع کن.\nدر بازی‌ها شرکت کن و سکه‌هات رو چند برابر کن!", "en": "💰 <b>Economy Guide</b>\n\nClaim daily rewards and collect coins.\nPlay games to multiply your coins!"},
    "games":    {"fa": "🎮 <b>راهنمای بازی‌ها</b>\n\nهمه بازی‌ها با شرط سکه کار می‌کنند.\nبرد = دریافت سکه حریف\nباخت = از دست دادن شرط", "en": "🎮 <b>Games Guide</b>\n\nAll games support coin betting.\nWin = take opponent's bet\nLose = lose your bet"},
    "duels":    {"fa": "⚔️ <b>راهنمای دوئل</b>\n\ndستور: <code>/duel @user [مبلغ]</code>\nحریف ۶۰ ثانیه وقت دارد تا قبول کند.\nبرنده همه شرط را می‌برد!", "en": "⚔️ <b>Duels Guide</b>\n\nCommand: <code>/duel @user [bet]</code>\nOpponent has 60s to accept.\nWinner takes all the bet!"},
}

CFG_CONTENT = {
    "welcome": {"fa": "👋 <b>پیام خوش‌آمد</b>\n\nمتغیرها:\n<code>{name}</code> — نام\n<code>{username}</code> — یوزرنیم\n<code>{group}</code> — نام گروه\n<code>{id}</code> — آیدی\n\nدستور: <code>/setwelcome [متن]</code>", "en": "👋 <b>Welcome Message</b>\n\nVariables:\n<code>{name}</code> — Name\n<code>{username}</code> — Username\n<code>{group}</code> — Group name\n<code>{id}</code> — User ID\n\nCommand: <code>/setwelcome [text]</code>"},
    "logs":    {"fa": "📋 <b>کانال لاگ</b>\n\nرویدادهای لاگ:\n✅ ورود/خروج اعضا\n✅ بن/سکوت/اخطار/اخراج\n✅ حذف/ویرایش پیام\n✅ ارتقا/تنزل ادمین\n\nبرای تنظیم: آیدی کانال رو ارسال کن.", "en": "📋 <b>Log Channel</b>\n\nLogged events:\n✅ Join/Leave\n✅ Ban/Mute/Warn/Kick\n✅ Message delete/edit\n✅ Admin promote/demote\n\nTo set: send the channel ID."},
    "general": {"fa": "⚙️ <b>تنظیمات عمومی</b>\n\n• سیستم اقتصادی: ✅\n• بازی‌ها: ✅\n• سیستم XP: ✅\n• حداکثر اخطار: ۳\n• اقدامات بی‌صدا: ❌", "en": "⚙️ <b>General Settings</b>\n\n• Economy system: ✅\n• Games: ✅\n• XP system: ✅\n• Max warnings: 3\n• Silent actions: ❌"},
}

# ─── Router ───────────────────────────────────────────────────────────────────
router = Router()

# ─── /start ───────────────────────────────────────────────────────────────────
@router.message(Command("start"))
async def cmd_start(message: Message):
    uid = message.from_user.id
    print(f"[/start] uid={uid}")
    await message.answer(txt(uid, "lang_select"), reply_markup=kb_lang(), parse_mode="HTML")

@router.message(Command("menu"))
async def cmd_menu(message: Message):
    uid = message.from_user.id
    print(f"[/menu] uid={uid}")
    await message.answer(txt(uid, "main_menu"), reply_markup=kb_main(uid), parse_mode="HTML")

@router.message(Command("help"))
async def cmd_help(message: Message):
    uid = message.from_user.id
    print(f"[/help] uid={uid}")
    await message.answer(txt(uid, "help"), reply_markup=kb_help(uid), parse_mode="HTML")

# ─── Plain text commands (no / needed) ───────────────────────────────────────
CMDS = {
    # فارسی
    "شروع":"start","منو":"menu","کمک":"help","راهنما":"help",
    "موجودی":"balance","کیف پول":"balance","کیف‌پول":"balance","والت":"balance",
    "روزانه":"daily","جایزه روزانه":"daily",
    "هفتگی":"weekly","جایزه هفتگی":"weekly",
    "ماهانه":"monthly","جایزه ماهانه":"monthly",
    "بازی":"games","بازی‌ها":"games","بازیها":"games",
    "آمار":"stats","جدول":"stats","لیدربورد":"stats",
    "دستاورد":"achievements","دستاوردها":"achievements","افتخارات":"achievements",
    "تنظیمات":"settings","امنیت":"security","مدیریت":"moderation",
    "زبان":"language","اقتصاد":"economy","دوئل":"duels","دوئلها":"duels",
    # English
    "start":"start","menu":"menu","help":"help","balance":"balance",
    "wallet":"balance","daily":"daily","weekly":"weekly","monthly":"monthly",
    "games":"games","stats":"stats","achievements":"achievements",
    "settings":"settings","security":"security","moderation":"moderation",
    "language":"language","economy":"economy","duels":"duels",
}

@router.message(F.text & ~F.text.startswith("/"))
async def plain_cmd(message: Message):
    uid = message.from_user.id
    raw = (message.text or "").strip()
    cmd = CMDS.get(raw) or CMDS.get(raw.lower())
    print(f"[plain_text] uid={uid} text='{raw}' cmd={cmd}")
    if not cmd:
        return

    fa = is_fa(uid)
    u = get_user(uid)

    if cmd == "start":
        await message.answer(txt(uid, "lang_select"), reply_markup=kb_lang(), parse_mode="HTML")

    elif cmd == "menu":
        await message.answer(txt(uid, "main_menu"), reply_markup=kb_main(uid), parse_mode="HTML")

    elif cmd == "help":
        await message.answer(txt(uid, "help"), reply_markup=kb_help(uid), parse_mode="HTML")

    elif cmd == "balance":
        await message.answer(
            (f"👛 <b>کیف پول</b>\n\n💵 نقدی: <b>{u['coins']:,} سکه</b>\n🏦 بانک: <b>{u['bank']:,} سکه</b>\n💎 مجموع: <b>{u['coins']+u['bank']:,} سکه</b>\n⭐ سطح: <b>{u['level']}</b>" if fa else
             f"👛 <b>Wallet</b>\n\n💵 Cash: <b>{u['coins']:,} coins</b>\n🏦 Bank: <b>{u['bank']:,} coins</b>\n💎 Total: <b>{u['coins']+u['bank']:,} coins</b>\n⭐ Level: <b>{u['level']}</b>"),
            reply_markup=kb_back(uid, "economy"), parse_mode="HTML"
        )

    elif cmd == "daily":
        u["coins"] += 100
        await message.answer(
            (f"🌅 <b>جایزه روزانه</b>\n\n✅ +۱۰۰ سکه دریافت کردید!\n💰 موجودی: <b>{u['coins']:,} سکه</b>" if fa else
             f"🌅 <b>Daily Reward</b>\n\n✅ +100 coins received!\n💰 Balance: <b>{u['coins']:,} coins</b>"),
            parse_mode="HTML"
        )

    elif cmd == "weekly":
        u["coins"] += 500
        await message.answer(
            (f"📅 <b>جایزه هفتگی</b>\n\n✅ +۵۰۰ سکه دریافت کردید!\n💰 موجودی: <b>{u['coins']:,} سکه</b>" if fa else
             f"📅 <b>Weekly Reward</b>\n\n✅ +500 coins received!\n💰 Balance: <b>{u['coins']:,} coins</b>"),
            parse_mode="HTML"
        )

    elif cmd == "monthly":
        u["coins"] += 2000
        await message.answer(
            (f"🗓️ <b>جایزه ماهانه</b>\n\n✅ +۲,۰۰۰ سکه دریافت کردید!\n💰 موجودی: <b>{u['coins']:,} سکه</b>" if fa else
             f"🗓️ <b>Monthly Reward</b>\n\n✅ +2,000 coins received!\n💰 Balance: <b>{u['coins']:,} coins</b>"),
            parse_mode="HTML"
        )

    elif cmd == "games":
        await message.answer(txt(uid, "games"), reply_markup=kb_games(uid), parse_mode="HTML")

    elif cmd == "stats":
        await message.answer(txt(uid, "stats"), reply_markup=kb_stats(uid), parse_mode="HTML")

    elif cmd == "achievements":
        await message.answer(txt(uid, "achievements"), reply_markup=kb_achievements(uid), parse_mode="HTML")

    elif cmd == "settings":
        await message.answer(txt(uid, "settings"), reply_markup=kb_settings(uid), parse_mode="HTML")

    elif cmd == "security":
        await message.answer(txt(uid, "security"), reply_markup=kb_security(uid), parse_mode="HTML")

    elif cmd == "moderation":
        await message.answer(txt(uid, "moderation"), reply_markup=kb_moderation(uid), parse_mode="HTML")

    elif cmd == "economy":
        await message.answer(txt(uid, "economy"), reply_markup=kb_economy(uid), parse_mode="HTML")

    elif cmd == "duels":
        await message.answer(txt(uid, "duels"), reply_markup=kb_duels(uid), parse_mode="HTML")

    elif cmd == "language":
        await message.answer(txt(uid, "lang_select"), reply_markup=kb_lang(), parse_mode="HTML")

# ─── Language selection ───────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("set_lang:"))
async def cb_set_lang(callback: CallbackQuery):
    uid = callback.from_user.id
    code = callback.data.split("set_lang:")[1]
    get_user(uid)["lang"] = code
    print(f"[set_lang] uid={uid} lang={code}")
    await callback.answer(f"✅ {LANGUAGES[code]}")
    await safe_edit(callback, txt(uid, "welcome"), kb_main(uid))

# ─── Navigation ───────────────────────────────────────────────────────────────
NAV_MAP = {
    "main":         lambda uid: (txt(uid, "main_menu"),    kb_main(uid)),
    "security":     lambda uid: (txt(uid, "security"),     kb_security(uid)),
    "moderation":   lambda uid: (txt(uid, "moderation"),   kb_moderation(uid)),
    "economy":      lambda uid: (txt(uid, "economy"),      kb_economy(uid)),
    "games":        lambda uid: (txt(uid, "games"),        kb_games(uid)),
    "duels":        lambda uid: (txt(uid, "duels"),        kb_duels(uid)),
    "achievements": lambda uid: (txt(uid, "achievements"), kb_achievements(uid)),
    "stats":        lambda uid: (txt(uid, "stats"),        kb_stats(uid)),
    "settings":     lambda uid: (txt(uid, "settings"),     kb_settings(uid)),
    "help":         lambda uid: (txt(uid, "help"),         kb_help(uid)),
    "language":     lambda uid: (txt(uid, "lang_select"),  kb_lang()),
}

@router.callback_query(F.data.startswith("nav:"))
async def cb_nav(callback: CallbackQuery):
    uid = callback.from_user.id
    dest = callback.data.split("nav:")[1]
    print(f"[nav] uid={uid} dest={dest}")
    fn = NAV_MAP.get(dest)
    if fn:
        text, kb = fn(uid)
        await safe_edit(callback, text, kb)
    await callback.answer()

# ─── Security ─────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("sec:"))
async def cb_sec(callback: CallbackQuery):
    uid = callback.from_user.id
    key = callback.data.split("sec:")[1]
    print(f"[sec] uid={uid} key={key}")
    c = SEC_CONTENT.get(key, {})
    text = c.get("fa" if is_fa(uid) else "en", "Coming soon!")
    await safe_edit(callback, text, kb_back(uid, "security"))
    await callback.answer()

# ─── Moderation ───────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("mod:"))
async def cb_mod(callback: CallbackQuery):
    uid = callback.from_user.id
    key = callback.data.split("mod:")[1]
    print(f"[mod] uid={uid} key={key}")
    c = MOD_CONTENT.get(key, {})
    text = c.get("fa" if is_fa(uid) else "en", "Coming soon!")
    await safe_edit(callback, text, kb_back(uid, "moderation"))
    await callback.answer()

# ─── Economy ──────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("eco:"))
async def cb_eco(callback: CallbackQuery):
    uid = callback.from_user.id
    key = callback.data.split("eco:")[1]
    fa = is_fa(uid)
    u = get_user(uid)
    print(f"[eco] uid={uid} key={key}")

    if key == "wallet":
        text = (f"👛 <b>کیف پول</b>\n\n💵 نقدی: <b>{u['coins']:,} سکه</b>\n🏦 بانک: <b>{u['bank']:,} سکه</b>\n💎 مجموع: <b>{u['coins']+u['bank']:,} سکه</b>\n⭐ سطح: <b>{u['level']}</b>"
                if fa else f"👛 <b>Wallet</b>\n\n💵 Cash: <b>{u['coins']:,} coins</b>\n🏦 Bank: <b>{u['bank']:,} coins</b>\n💎 Total: <b>{u['coins']+u['bank']:,} coins</b>\n⭐ Level: <b>{u['level']}</b>")
        await safe_edit(callback, text, kb_back(uid, "economy"))

    elif key == "rewards":
        text = ("🎁 <b>جوایز</b>\n\n🌅 روزانه: ۱۰۰ سکه (هر ۲۴ ساعت)\n📅 هفتگی: ۵۰۰ سکه (هر ۷ روز)\n🗓️ ماهانه: ۲,۰۰۰ سکه (هر ۳۰ روز)\n\n🔥 استریک ۷ روز = ۲× روزانه\n🔥 استریک ۳۰ روز = ۵× روزانه\n\nدستورات:\n<code>روزانه</code> | <code>هفتگی</code> | <code>ماهانه</code>"
                if fa else "🎁 <b>Rewards</b>\n\n🌅 Daily: 100 coins (every 24h)\n📅 Weekly: 500 coins (every 7d)\n🗓️ Monthly: 2,000 coins (every 30d)\n\n🔥 7-day streak = 2× daily\n🔥 30-day streak = 5× daily\n\nCommands:\n<code>daily</code> | <code>weekly</code> | <code>monthly</code>")
        await safe_edit(callback, text, kb_back(uid, "economy"))

    elif key == "bank":
        text = ("🏦 <b>بانک</b>\n\n💰 موجودی بانک: <b>{:,} سکه</b>\n\nواریز: <code>واریز [مبلغ]</code>\nبرداشت: <code>برداشت [مبلغ]</code>\n\n📈 سود روزانه: ۵٪ (حداکثر ۱۰,۰۰۰ سکه)\n🔒 پول در بانک از باخت در بازی محافظت می‌شود.".format(u['bank'])
                if fa else "🏦 <b>Bank</b>\n\n💰 Bank Balance: <b>{:,} coins</b>\n\nDeposit: <code>deposit [amount]</code>\nWithdraw: <code>withdraw [amount]</code>\n\n📈 Daily interest: 5% (max 10,000 coins)\n🔒 Bank coins are safe from game losses.".format(u['bank']))
        await safe_edit(callback, text, kb_back(uid, "economy"))

    elif key == "transfer":
        text = ("💸 <b>انتقال سکه</b>\n\nدستور: <code>/transfer @user [مبلغ]</code>\nمثال: <code>/transfer @user 500</code>\n\n• کارمزد: ۵٪\n• حداقل: ۱۰ سکه\n• حداکثر روزانه: ۱۰,۰۰۰ سکه"
                if fa else "💸 <b>Transfer Coins</b>\n\nCommand: <code>/transfer @user [amount]</code>\nExample: <code>/transfer @user 500</code>\n\n• Fee: 5%\n• Min: 10 coins\n• Daily max: 10,000 coins")
        await safe_edit(callback, text, kb_back(uid, "economy"))

    elif key == "shop":
        text = ("🛍️ <b>فروشگاه پاداش</b>\n\n🏷️ مدال‌ها — از ۵۰۰ سکه\n🎭 عنوان‌ها — از ۱,۰۰۰ سکه\n🖼️ قاب پروفایل — از ۲,۰۰۰ سکه\n📦 جعبه شانس — ۳۰۰ سکه\n🌟 بوست XP — ۱,۵۰۰ سکه\n\n<i>بزودی فعال می‌شود!</i>"
                if fa else "🛍️ <b>Reward Shop</b>\n\n🏷️ Badges — from 500 coins\n🎭 Titles — from 1,000 coins\n🖼️ Profile Frames — from 2,000 coins\n📦 Loot Box — 300 coins\n🌟 XP Boost — 1,500 coins\n\n<i>Coming soon!</i>")
        await safe_edit(callback, text, kb_back(uid, "economy"))

    elif key == "history":
        text = ("📜 <b>تاریخچه تراکنش‌ها</b>\n\n<i>هنوز تراکنشی ثبت نشده است.\nجایزه روزانه بگیرید یا در بازی شرکت کنید!</i>"
                if fa else "📜 <b>Transaction History</b>\n\n<i>No transactions yet.\nClaim a daily reward or play a game!</i>")
        await safe_edit(callback, text, kb_back(uid, "economy"))

    await callback.answer()

# ─── Games ────────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("game:"))
async def cb_game(callback: CallbackQuery):
    uid = callback.from_user.id
    key = callback.data.split("game:")[1]
    print(f"[game] uid={uid} key={key}")
    c = GAME_CONTENT.get(key, {})
    text = c.get("fa" if is_fa(uid) else "en", "🎮 Coming soon!")
    await safe_edit(callback, text, kb_back(uid, "games"))
    await callback.answer()

# ─── Duels ────────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("duel:"))
async def cb_duel(callback: CallbackQuery):
    uid = callback.from_user.id
    key = callback.data.split("duel:")[1]
    fa = is_fa(uid)
    print(f"[duel] uid={uid} key={key}")
    u = get_user(uid)

    texts = {
        "new":        {"fa": "⚔️ <b>دوئل جدید</b>\n\nدستور: <code>/duel @user [مبلغ]</code>\nمثال: <code>/duel @user 500</code>\n\n• حریف ۶۰ ثانیه فرصت قبول دارد\n• بازی تصادفی انتخاب می‌شود\n• برنده همه شرط را می‌برد!\n• ۱۰ برد متوالی = مدال ویژه 🏅", "en": "⚔️ <b>New Duel</b>\n\nCommand: <code>/duel @user [bet]</code>\nExample: <code>/duel @user 500</code>\n\n• Opponent has 60s to accept\n• Random game is selected\n• Winner takes all!\n• 10 win streak = special medal 🏅"},
        "tournament": {"fa": "🏆 <b>تورنمنت</b>\n\nرقابت گروهی با جایزه!\n\n• ورودیه جمع‌آوری می‌شود\n• سیستم مرحله‌ای (bracket)\n• 🥇 ۶۰٪ — 🥈 ۳۰٪ — 🥉 ۱۰٪\n\nدستور: <code>/tournament</code>", "en": "🏆 <b>Tournament</b>\n\nGroup competition with prizes!\n\n• Entry fee collected as prize pool\n• Bracket system\n• 🥇 60% — 🥈 30% — 🥉 10%\n\nCommand: <code>/tournament</code>"},
        "stats":      {"fa": f"📊 <b>آمار دوئل‌های شما</b>\n\n⚔️ کل دوئل‌ها: 0\n🏆 برد: 0\n💀 باخت: 0\n🤝 مساوی: 0\n🔥 استریک برد: 0\n💰 سکه برده: 0\n💸 سکه باخته: 0", "en": f"📊 <b>Your Duel Stats</b>\n\n⚔️ Total: 0\n🏆 Wins: 0\n💀 Losses: 0\n🤝 Draws: 0\n🔥 Win Streak: 0\n💰 Coins Won: 0\n💸 Coins Lost: 0"},
        "history":    {"fa": "🏅 <b>تاریخچه دوئل‌ها</b>\n\n<i>هنوز دوئلی انجام نداده‌اید.\nبا دستور /duel @user رقیبی را دعوت کنید!</i>", "en": "🏅 <b>Duel History</b>\n\n<i>No duels yet.\nUse /duel @user to challenge someone!</i>"},
    }
    c = texts.get(key, {})
    text = c.get("fa" if fa else "en", "Coming soon!")
    await safe_edit(callback, text, kb_back(uid, "duels"))
    await callback.answer()

# ─── Achievements ─────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("ach:"))
async def cb_ach(callback: CallbackQuery):
    uid = callback.from_user.id
    key = callback.data.split("ach:")[1]
    print(f"[ach] uid={uid} key={key}")
    c = ACH_CONTENT.get(key, {})
    text = c.get("fa" if is_fa(uid) else "en", "Coming soon!")
    await safe_edit(callback, text, kb_back(uid, "achievements"))
    await callback.answer()

# ─── Stats ────────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("stat:"))
async def cb_stat(callback: CallbackQuery):
    uid = callback.from_user.id
    key = callback.data.split("stat:")[1]
    print(f"[stat] uid={uid} key={key}")
    c = STAT_CONTENT.get(key, {})
    text = c.get("fa" if is_fa(uid) else "en", "Coming soon!")
    await safe_edit(callback, text, kb_back(uid, "stats"))
    await callback.answer()

# ─── Help ─────────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("help:"))
async def cb_help(callback: CallbackQuery):
    uid = callback.from_user.id
    key = callback.data.split("help:")[1]
    print(f"[help] uid={uid} key={key}")
    c = HELP_CONTENT.get(key, {})
    text = c.get("fa" if is_fa(uid) else "en", "Coming soon!")
    await safe_edit(callback, text, kb_back(uid, "help"))
    await callback.answer()

# ─── Settings ─────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("cfg:"))
async def cb_cfg(callback: CallbackQuery):
    uid = callback.from_user.id
    key = callback.data.split("cfg:")[1]
    print(f"[cfg] uid={uid} key={key}")
    c = CFG_CONTENT.get(key, {})
    text = c.get("fa" if is_fa(uid) else "en", "Coming soon!")
    await safe_edit(callback, text, kb_back(uid, "settings"))
    await callback.answer()

# ─── In-memory moderation store ──────────────────────────────────────────────
from datetime import datetime, timedelta, timezone
import re as _re

banned: dict[int, set[int]] = {}   # chat_id -> {user_ids}
muted:  dict[int, dict[int, datetime]] = {}  # chat_id -> {user_id: until}
warns:  dict[int, dict[int, list[str]]] = {}  # chat_id -> {user_id: [reasons]}
MAX_WARNS = 3

def _banned(cid, uid): return uid in banned.get(cid, set())
def _muted(cid, uid):
    until = muted.get(cid, {}).get(uid)
    if until and until > datetime.now(timezone.utc): return True
    if until: muted.get(cid, {}).pop(uid, None)
    return False

def parse_duration(s: str) -> timedelta | None:
    m = _re.match(r'^(\d+)(s|m|h|d|w)$', (s or '').strip().lower())
    if not m: return None
    n, u = int(m.group(1)), m.group(2)
    return {'s': timedelta(seconds=n), 'm': timedelta(minutes=n),
            'h': timedelta(hours=n),   'd': timedelta(days=n),
            'w': timedelta(weeks=n)}[u]

def mention(user) -> str:
    name = user.full_name or user.first_name or str(user.id)
    return f'<a href="tg://user?id={user.id}">{name}</a>'

async def get_target(message: Message):
    """Return target user from reply or @mention in command args."""
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user, message.reply_to_message
    return None, None

async def is_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        m = await bot.get_chat_member(chat_id, user_id)
        return m.status in ('administrator', 'creator')
    except Exception:
        return False

def reason_from(text: str, cmd: str) -> str:
    parts = text.split(None, 2)
    for i, p in enumerate(parts):
        if p.lower().lstrip('/') == cmd.lower().lstrip('/'):
            return ' '.join(parts[i+1:]) if len(parts) > i+1 else ''
    return ''

def _fa(uid): return is_fa(uid)

# ─── /ban ──────────────────────────────────────────────────────────────────────
@router.message(Command('ban'))
async def cmd_ban(message: Message):
    uid = message.from_user.id
    fa  = _fa(uid)
    target, rep_msg = await get_target(message)

    if not target:
        await message.reply('⚠️ روی پیام کاربر ریپلای کن و بنویس /ban [دلیل]' if fa else
                            '⚠️ Reply to a user\'s message and type /ban [reason]')
        return

    if message.chat.type == 'private':
        await message.reply('⚠️ این دستور فقط در گروه کار می‌کنه.' if fa else
                            '⚠️ This command only works in groups.')
        return

    if not await is_admin(message.bot, message.chat.id, uid):
        await message.reply('❌ شما ادمین نیستید.' if fa else '❌ You are not an admin.')
        return

    if await is_admin(message.bot, message.chat.id, target.id):
        await message.reply('❌ نمی‌توانید ادمین را بن کنید.' if fa else '❌ Cannot ban an admin.')
        return

    reason = reason_from(message.text or '', 'ban') or ('بدون دلیل' if fa else 'No reason')
    cid = message.chat.id

    try:
        await message.bot.ban_chat_member(cid, target.id)
        banned.setdefault(cid, set()).add(target.id)
        print(f'[ban] admin={uid} target={target.id} reason={reason}')
        await message.reply(
            f'🚫 <b>{"بن شد" if fa else "Banned"}</b>\n\n'
            f'👤 {"کاربر" if fa else "User"}: {mention(target)}\n'
            f'👮 {"ادمین" if fa else "Admin"}: {mention(message.from_user)}\n'
            f'📝 {"دلیل" if fa else "Reason"}: {reason}\n'
            f'🕐 {"زمان" if fa else "Time"}: {datetime.now().strftime("%H:%M:%S")}',
            parse_mode='HTML'
        )
        try: await rep_msg.delete()
        except Exception: pass
    except Exception as e:
        await message.reply(f'❌ {"خطا" if fa else "Error"}: {e}')

# ─── /unban ────────────────────────────────────────────────────────────────────
@router.message(Command('unban'))
async def cmd_unban(message: Message):
    uid = message.from_user.id
    fa  = _fa(uid)
    target, _ = await get_target(message)

    if not target:
        await message.reply('⚠️ روی پیام کاربر ریپلای کن.' if fa else '⚠️ Reply to a user\'s message.')
        return
    if not await is_admin(message.bot, message.chat.id, uid):
        await message.reply('❌ شما ادمین نیستید.' if fa else '❌ You are not an admin.')
        return

    cid = message.chat.id
    try:
        await message.bot.unban_chat_member(cid, target.id, only_if_banned=True)
        banned.get(cid, set()).discard(target.id)
        await message.reply(
            f'✅ <b>{"آنبن شد" if fa else "Unbanned"}</b>\n\n'
            f'👤 {"کاربر" if fa else "User"}: {mention(target)}',
            parse_mode='HTML'
        )
    except Exception as e:
        await message.reply(f'❌ {"خطا" if fa else "Error"}: {e}')

# ─── /mute ─────────────────────────────────────────────────────────────────────
@router.message(Command('mute'))
async def cmd_mute(message: Message):
    uid = message.from_user.id
    fa  = _fa(uid)
    target, _ = await get_target(message)

    if not target:
        await message.reply('⚠️ روی پیام کاربر ریپلای کن و بنویس /mute [مدت] [دلیل]\nمثال: /mute 1h اسپم' if fa else
                            '⚠️ Reply to a user\'s message.\nExample: /mute 1h spam')
        return
    if message.chat.type == 'private':
        await message.reply('⚠️ این دستور فقط در گروه کار می‌کنه.' if fa else '⚠️ Groups only.')
        return
    if not await is_admin(message.bot, message.chat.id, uid):
        await message.reply('❌ شما ادمین نیستید.' if fa else '❌ You are not an admin.')
        return
    if await is_admin(message.bot, message.chat.id, target.id):
        await message.reply('❌ نمی‌توانید ادمین را سکوت کنید.' if fa else '❌ Cannot mute an admin.')
        return

    parts = (message.text or '').split()[1:]  # drop /mute
    duration_str = parts[0] if parts else '1h'
    reason_parts = parts[1:] if len(parts) > 1 else []

    delta = parse_duration(duration_str)
    if not delta:
        reason_parts = [duration_str] + reason_parts
        delta = timedelta(hours=1)
        duration_str = '1h'

    reason = ' '.join(reason_parts) or ('بدون دلیل' if fa else 'No reason')
    until  = datetime.now(timezone.utc) + delta
    cid    = message.chat.id

    from aiogram.types import ChatPermissions
    no_perms = ChatPermissions(
        can_send_messages=False, can_send_media_messages=False,
        can_send_polls=False, can_send_other_messages=False,
        can_add_web_page_previews=False,
    )

    try:
        await message.bot.restrict_chat_member(cid, target.id, permissions=no_perms,
                                               until_date=until)
        muted.setdefault(cid, {})[target.id] = until
        print(f'[mute] admin={uid} target={target.id} duration={duration_str} reason={reason}')
        await message.reply(
            f'🔇 <b>{"سکوت شد" if fa else "Muted"}</b>\n\n'
            f'👤 {"کاربر" if fa else "User"}: {mention(target)}\n'
            f'👮 {"ادمین" if fa else "Admin"}: {mention(message.from_user)}\n'
            f'⏱️ {"مدت" if fa else "Duration"}: {duration_str}\n'
            f'📅 {"تا" if fa else "Until"}: {until.strftime("%Y-%m-%d %H:%M")} UTC\n'
            f'📝 {"دلیل" if fa else "Reason"}: {reason}',
            parse_mode='HTML'
        )
    except Exception as e:
        await message.reply(f'❌ {"خطا" if fa else "Error"}: {e}')

# ─── /unmute ───────────────────────────────────────────────────────────────────
@router.message(Command('unmute'))
async def cmd_unmute(message: Message):
    uid = message.from_user.id
    fa  = _fa(uid)
    target, _ = await get_target(message)

    if not target:
        await message.reply('⚠️ روی پیام کاربر ریپلای کن.' if fa else '⚠️ Reply to a user\'s message.')
        return
    if not await is_admin(message.bot, message.chat.id, uid):
        await message.reply('❌ شما ادمین نیستید.' if fa else '❌ You are not an admin.')
        return

    cid = message.chat.id
    from aiogram.types import ChatPermissions
    full_perms = ChatPermissions(
        can_send_messages=True, can_send_media_messages=True,
        can_send_polls=True, can_send_other_messages=True,
        can_add_web_page_previews=True, can_change_info=False,
        can_invite_users=True, can_pin_messages=False,
    )
    try:
        await message.bot.restrict_chat_member(cid, target.id, permissions=full_perms)
        muted.get(cid, {}).pop(target.id, None)
        await message.reply(
            f'🔊 <b>{"سکوت برداشته شد" if fa else "Unmuted"}</b>\n\n'
            f'👤 {"کاربر" if fa else "User"}: {mention(target)}',
            parse_mode='HTML'
        )
    except Exception as e:
        await message.reply(f'❌ {"خطا" if fa else "Error"}: {e}')

# ─── /kick ─────────────────────────────────────────────────────────────────────
@router.message(Command('kick'))
async def cmd_kick(message: Message):
    uid = message.from_user.id
    fa  = _fa(uid)
    target, rep_msg = await get_target(message)

    if not target:
        await message.reply('⚠️ روی پیام کاربر ریپلای کن و بنویس /kick [دلیل]' if fa else
                            '⚠️ Reply to a user\'s message and type /kick [reason]')
        return
    if message.chat.type == 'private':
        await message.reply('⚠️ این دستور فقط در گروه کار می‌کنه.' if fa else '⚠️ Groups only.')
        return
    if not await is_admin(message.bot, message.chat.id, uid):
        await message.reply('❌ شما ادمین نیستید.' if fa else '❌ You are not an admin.')
        return
    if await is_admin(message.bot, message.chat.id, target.id):
        await message.reply('❌ نمی‌توانید ادمین را اخراج کنید.' if fa else '❌ Cannot kick an admin.')
        return

    reason = reason_from(message.text or '', 'kick') or ('بدون دلیل' if fa else 'No reason')
    cid = message.chat.id
    try:
        await message.bot.ban_chat_member(cid, target.id)
        await message.bot.unban_chat_member(cid, target.id)
        print(f'[kick] admin={uid} target={target.id} reason={reason}')
        await message.reply(
            f'👢 <b>{"اخراج شد" if fa else "Kicked"}</b>\n\n'
            f'👤 {"کاربر" if fa else "User"}: {mention(target)}\n'
            f'👮 {"ادمین" if fa else "Admin"}: {mention(message.from_user)}\n'
            f'📝 {"دلیل" if fa else "Reason"}: {reason}\n'
            f'💡 {"می‌تواند دوباره وارد شود" if fa else "Can rejoin"}',
            parse_mode='HTML'
        )
    except Exception as e:
        await message.reply(f'❌ {"خطا" if fa else "Error"}: {e}')

# ─── /warn ─────────────────────────────────────────────────────────────────────
@router.message(Command('warn'))
async def cmd_warn(message: Message):
    uid = message.from_user.id
    fa  = _fa(uid)
    target, _ = await get_target(message)

    if not target:
        await message.reply('⚠️ روی پیام کاربر ریپلای کن و بنویس /warn [دلیل]' if fa else
                            '⚠️ Reply to a user\'s message and type /warn [reason]')
        return
    if not await is_admin(message.bot, message.chat.id, uid):
        await message.reply('❌ شما ادمین نیستید.' if fa else '❌ You are not an admin.')
        return
    if await is_admin(message.bot, message.chat.id, target.id):
        await message.reply('❌ نمی‌توانید به ادمین اخطار دهید.' if fa else '❌ Cannot warn an admin.')
        return

    reason = reason_from(message.text or '', 'warn') or ('بدون دلیل' if fa else 'No reason')
    cid = message.chat.id
    warns.setdefault(cid, {}).setdefault(target.id, []).append(reason)
    count  = len(warns[cid][target.id])
    print(f'[warn] admin={uid} target={target.id} count={count} reason={reason}')

    bar = '🔴' * count + '⚪' * (MAX_WARNS - count)
    text = (
        f'⚠️ <b>اخطار</b>\n\n'
        f'👤 {"کاربر" if fa else "User"}: {mention(target)}\n'
        f'👮 {"ادمین" if fa else "Admin"}: {mention(message.from_user)}\n'
        f'📝 {"دلیل" if fa else "Reason"}: {reason}\n'
        f'🔢 {"اخطارها" if fa else "Warns"}: {bar} ({count}/{MAX_WARNS})'
    )

    if count >= MAX_WARNS:
        try:
            await message.bot.ban_chat_member(cid, target.id)
            banned.setdefault(cid, set()).add(target.id)
            warns[cid][target.id] = []
            text += f'\n\n🚫 <b>{"بن خودکار — حداکثر اخطار رسید!" if fa else "Auto-banned — max warns reached!"}</b>'
        except Exception as e:
            text += f'\n⚠️ Auto-ban failed: {e}'

    await message.reply(text, parse_mode='HTML')

# ─── /unwarn ───────────────────────────────────────────────────────────────────
@router.message(Command('unwarn'))
async def cmd_unwarn(message: Message):
    uid = message.from_user.id
    fa  = _fa(uid)
    target, _ = await get_target(message)

    if not target:
        await message.reply('⚠️ روی پیام کاربر ریپلای کن.' if fa else '⚠️ Reply to a user\'s message.')
        return
    if not await is_admin(message.bot, message.chat.id, uid):
        await message.reply('❌ شما ادمین نیستید.' if fa else '❌ You are not an admin.')
        return

    cid = message.chat.id
    w = warns.get(cid, {}).get(target.id, [])
    if w:
        warns[cid][target.id].pop()
        count = len(warns[cid][target.id])
    else:
        count = 0

    bar = '🔴' * count + '⚪' * (MAX_WARNS - count)
    await message.reply(
        f'✅ <b>{"اخطار حذف شد" if fa else "Warning Removed"}</b>\n\n'
        f'👤 {"کاربر" if fa else "User"}: {mention(target)}\n'
        f'🔢 {"اخطارها" if fa else "Warns"}: {bar} ({count}/{MAX_WARNS})',
        parse_mode='HTML'
    )

# ─── /warns ────────────────────────────────────────────────────────────────────
@router.message(Command('warns'))
async def cmd_warns(message: Message):
    uid = message.from_user.id
    fa  = _fa(uid)
    target, _ = await get_target(message)

    if not target:
        await message.reply('⚠️ روی پیام کاربر ریپلای کن.' if fa else '⚠️ Reply to a user\'s message.')
        return

    cid = message.chat.id
    w = warns.get(cid, {}).get(target.id, [])
    count = len(w)
    bar = '🔴' * count + '⚪' * (MAX_WARNS - count)

    if w:
        reasons = '\n'.join(f'{i+1}. {r}' for i, r in enumerate(w))
        text = (
            f'📋 <b>{"اخطارهای" if fa else "Warnings for"} {mention(target)}</b>\n\n'
            f'🔢 {bar} ({count}/{MAX_WARNS})\n\n'
            f'{"دلایل" if fa else "Reasons"}:\n{reasons}'
        )
    else:
        text = (
            f'✅ <b>{mention(target)}</b> {"هیچ اخطاری ندارد." if fa else "has no warnings."}'
        )
    await message.reply(text, parse_mode='HTML')

# ─── /ro (read-only / تنها‌خوان) ───────────────────────────────────────────────
@router.message(Command('ro'))
async def cmd_ro(message: Message):
    uid = message.from_user.id
    fa  = _fa(uid)
    target, _ = await get_target(message)

    if not target:
        await message.reply('⚠️ روی پیام کاربر ریپلای کن.' if fa else '⚠️ Reply to a user\'s message.')
        return
    if message.chat.type == 'private':
        await message.reply('⚠️ فقط در گروه.' if fa else '⚠️ Groups only.')
        return
    if not await is_admin(message.bot, message.chat.id, uid):
        await message.reply('❌ شما ادمین نیستید.' if fa else '❌ You are not an admin.')
        return

    parts = (message.text or '').split()[1:]
    duration_str = parts[0] if parts else '1h'
    delta = parse_duration(duration_str) or timedelta(hours=1)
    until = datetime.now(timezone.utc) + delta
    cid   = message.chat.id

    from aiogram.types import ChatPermissions
    ro_perms = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
    )
    try:
        await message.bot.restrict_chat_member(cid, target.id, permissions=ro_perms, until_date=until)
        await message.reply(
            f'📖 <b>{"حالت فقط خواندنی" if fa else "Read-only mode"}</b>\n\n'
            f'👤 {mention(target)}\n'
            f'⏱️ {duration_str}',
            parse_mode='HTML'
        )
    except Exception as e:
        await message.reply(f'❌ {e}')

# ─── /pin and /unpin ────────────────────────────────────────────────────────────
@router.message(Command('pin'))
async def cmd_pin(message: Message):
    uid = message.from_user.id
    fa  = _fa(uid)
    if not message.reply_to_message:
        await message.reply('⚠️ روی پیامی که میخای پین بشه ریپلای کن.' if fa else '⚠️ Reply to the message you want to pin.')
        return
    if not await is_admin(message.bot, message.chat.id, uid):
        await message.reply('❌ شما ادمین نیستید.' if fa else '❌ You are not an admin.')
        return
    try:
        await message.bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id)
        await message.reply('📌 <b>پین شد!</b>' if fa else '📌 <b>Pinned!</b>', parse_mode='HTML')
    except Exception as e:
        await message.reply(f'❌ {e}')

@router.message(Command('unpin'))
async def cmd_unpin(message: Message):
    uid = message.from_user.id
    fa  = _fa(uid)
    if not await is_admin(message.bot, message.chat.id, uid):
        await message.reply('❌ شما ادمین نیستید.' if fa else '❌ You are not an admin.')
        return
    try:
        if message.reply_to_message:
            await message.bot.unpin_chat_message(message.chat.id, message.reply_to_message.message_id)
        else:
            await message.bot.unpin_chat_message(message.chat.id)
        await message.reply('📌 <b>پین برداشته شد.</b>' if fa else '📌 <b>Unpinned.</b>', parse_mode='HTML')
    except Exception as e:
        await message.reply(f'❌ {e}')

# ─── /del (delete replied message) ─────────────────────────────────────────────
@router.message(Command('del'))
async def cmd_del(message: Message):
    uid = message.from_user.id
    fa  = _fa(uid)
    if not message.reply_to_message:
        await message.reply('⚠️ روی پیامی که میخای حذف بشه ریپلای کن.' if fa else '⚠️ Reply to the message to delete.')
        return
    if not await is_admin(message.bot, message.chat.id, uid):
        await message.reply('❌ شما ادمین نیستید.' if fa else '❌ You are not an admin.')
        return
    try:
        await message.reply_to_message.delete()
        await message.delete()
    except Exception as e:
        await message.reply(f'❌ {e}')

# ─── /info ──────────────────────────────────────────────────────────────────────
@router.message(Command('info'))
async def cmd_info(message: Message):
    uid = message.from_user.id
    fa  = _fa(uid)
    target, _ = await get_target(message)
    t = target or message.from_user

    cid   = message.chat.id
    w     = warns.get(cid, {}).get(t.id, [])
    is_bn = _banned(cid, t.id)
    is_mt = _muted(cid, t.id)

    status_fa  = ('🚫 بن' if is_bn else ('🔇 سکوت' if is_mt else '✅ عادی'))
    status_en  = ('🚫 Banned' if is_bn else ('🔇 Muted' if is_mt else '✅ Active'))

    name = t.full_name or t.first_name or str(t.id)
    uname = f'@{t.username}' if t.username else ('ندارد' if fa else 'None')

    await message.reply(
        f'👤 <b>{"اطلاعات کاربر" if fa else "User Info"}</b>\n\n'
        f'🪪 {"نام" if fa else "Name"}: {name}\n'
        f'🔗 {"یوزرنیم" if fa else "Username"}: {uname}\n'
        f'🆔 ID: <code>{t.id}</code>\n'
        f'🤖 {"ربات" if fa else "Bot"}: {"بله" if t.is_bot else ("خیر" if fa else "No")}\n'
        f'📊 {"وضعیت" if fa else "Status"}: {status_fa if fa else status_en}\n'
        f'⚠️ {"اخطار" if fa else "Warns"}: {len(w)}/{MAX_WARNS}',
        parse_mode='HTML'
    )

# ─── Reply-based plain text moderation ────────────────────────────────────────
MOD_PLAIN = {
    'بن': 'ban', 'بن کن': 'ban',
    'سکوت': 'mute', 'سکوت کن': 'mute', 'میوت': 'mute',
    'اخراج': 'kick', 'اخراج کن': 'kick',
    'اخطار': 'warn', 'اخطار بده': 'warn',
    'آنبن': 'unban', 'رفع بن': 'unban',
    'آنسکوت': 'unmute', 'رفع سکوت': 'unmute',
    'اخطارها': 'warns', 'اخطار ها': 'warns',
    'اینفو': 'info', 'مشخصات': 'info',
    'حذف': 'del', 'پاک کن': 'del',
}

@router.message(F.text & F.reply_to_message & ~F.text.startswith('/'))
async def reply_mod_plain(message: Message):
    uid  = message.from_user.id
    raw  = (message.text or '').strip()
    parts = raw.split()
    cmd   = MOD_PLAIN.get(raw.lower()) or MOD_PLAIN.get(parts[0].lower() if parts else '')
    if not cmd:
        return

    # Delegate to the matching command handler by faking the message text
    message.text = f'/{cmd} ' + ' '.join(parts[1:])
    handlers = {
        'ban': cmd_ban, 'unban': cmd_unban, 'mute': cmd_mute,
        'unmute': cmd_unmute, 'kick': cmd_kick, 'warn': cmd_warn,
        'unwarn': cmd_unwarn, 'warns': cmd_warns, 'info': cmd_info,
        'del': cmd_del,
    }
    fn = handlers.get(cmd)
    if fn:
        await fn(message)

# ─── Main ─────────────────────────────────────────────────────────────────────
async def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN is not set!")
        return

    print("━" * 50)
    print("  GUARDIAN X ULTIMATE — Starting...")
    print("━" * 50)

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # Register bot commands for Telegram command menu
    await bot.set_my_commands([
        BotCommand(command="start", description="🚀 شروع / Start"),
        BotCommand(command="menu",  description="📋 منوی اصلی / Main Menu"),
        BotCommand(command="help",  description="❓ راهنما / Help"),
    ])

    me = await bot.get_me()
    print(f"✅ Bot: @{me.username}")
    print(f"✅ Name: {me.first_name}")
    print(f"✅ Polling started — drop_pending_updates=True")
    print("━" * 50)
    print("Send /start or type: شروع / منو / موجودی / روزانه ...")
    print("━" * 50)

    await dp.start_polling(bot, drop_pending_updates=True, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped.")
