from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Callable
from bot.database.models import SecuritySettings
from bot.utils.glass_panel import glass_status, glass_lock_status


def security_menu_kb(_: Callable, security: SecuritySettings) -> InlineKeyboardMarkup:
    """Glass-styled security menu with crystal status indicators."""
    builder = InlineKeyboardBuilder()

    # Anti-spam features (row of 2)
    builder.button(text=f"{glass_status(security.anti_spam)} ◈ ضد اسپم", callback_data="sec:anti_spam")
    builder.button(text=f"{glass_status(security.anti_flood)} ◈ ضع فلود", callback_data="sec:anti_flood")
    builder.button(text=f"{glass_status(security.anti_raid)} ◈ ضع رید", callback_data="sec:anti_raid")
    builder.button(text=f"{glass_status(security.anti_bot)} ◈ ضع ربات", callback_data="sec:anti_bot")
    builder.button(text=f"{glass_status(security.anti_fake)} ◈ ضع فیک", callback_data="sec:anti_fake")
    builder.button(text=f"{glass_status(security.anti_advertisement)} ◈ ضع تبلیغ", callback_data="sec:anti_ad")
    # Anti-content features
    builder.button(text=f"{glass_status(security.anti_link)} ◈ ضع لینک", callback_data="sec:anti_link")
    builder.button(text=f"{glass_status(security.anti_mention_spam)} ◈ ضع منشن", callback_data="sec:anti_mention")
    builder.button(text=f"{glass_status(security.anti_forward_spam)} ◈ ضع فوروارد", callback_data="sec:anti_forward")
    builder.button(text=f"{glass_status(security.anti_emoji_spam)} ◈ ضع ایموجی", callback_data="sec:anti_emoji")
    builder.button(text=f"{glass_status(security.anti_hashtag_spam)} ◈ ضع هشتگ", callback_data="sec:anti_hashtag")
    builder.button(text=f"{glass_status(security.anti_phone)} ◈ ضع شماره", callback_data="sec:anti_phone")
    # Protection features
    builder.button(text=f"{glass_status(security.anti_scam)} ◈ ضع کلاهبرداری", callback_data="sec:anti_scam")
    builder.button(text=f"{glass_status(security.anti_crypto_scam)} ◈ ضع کریپتو", callback_data="sec:anti_crypto")
    builder.button(text=f"{glass_status(security.anti_nsfw)} ◈ ضع نامناسب", callback_data="sec:anti_nsfw")
    builder.button(text=f"{glass_status(security.anti_invite)} ◈ ضع دعوت‌نامه", callback_data="sec:anti_invite")
    builder.button(text=f"{glass_status(security.anti_channel_promo)} ◈ ضع تبلیغ کانال", callback_data="sec:anti_promo")
    builder.button(text=f"{glass_status(security.anti_mass_join)} ◈ ضع ورود انبوه", callback_data="sec:anti_mass_join")
    # Special features
    builder.button(text=f"{glass_status(security.captcha_enabled)} ◈ کپچا", callback_data="sec:captcha")
    builder.button(text="🔐 ◈ قفل‌ها", callback_data="sec:locks")
    builder.button(text="⚔️ ◈ حفاظت پیشرفته", callback_data="sec:advanced")
    # Emergency mode
    em_icon = "🔴" if security.emergency_mode else "🟢"
    builder.button(text=f"{em_icon} ◈ حالت اضطراری", callback_data="sec:emergency")
    # Back
    builder.button(text="🔙 ◈ بازگشت", callback_data="menu:main")
    builder.adjust(2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1)
    return builder.as_markup()


def locks_menu_kb(_: Callable, security: SecuritySettings) -> InlineKeyboardMarkup:
    """Glass-styled locks menu with lock/unlock crystal indicators."""
    builder = InlineKeyboardBuilder()

    locks = [
        (f"{glass_lock_status(security.lock_text)} ◈ متن", "lock:text"),
        (f"{glass_lock_status(security.lock_links)} ◈ لینک", "lock:links"),
        (f"{glass_lock_status(security.lock_photos)} ◈ عکس", "lock:photos"),
        (f"{glass_lock_status(security.lock_videos)} ◈ ویدئو", "lock:videos"),
        (f"{glass_lock_status(security.lock_gifs)} ◈ گیف", "lock:gifs"),
        (f"{glass_lock_status(security.lock_audio)} ◈ صوت", "lock:audio"),
        (f"{glass_lock_status(security.lock_voice)} ◈ صدا", "lock:voice"),
        (f"{glass_lock_status(security.lock_documents)} ◈ سند", "lock:docs"),
        (f"{glass_lock_status(security.lock_polls)} ◈ نظرسنجی", "lock:polls"),
        (f"{glass_lock_status(security.lock_games)} ◈ بازی", "lock:games"),
        (f"{glass_lock_status(security.lock_bots)} ◈ ربات", "lock:bots"),
        (f"{glass_lock_status(security.lock_forwards)} ◈ فوروارد", "lock:forwards"),
        (f"{glass_lock_status(security.lock_contacts)} ◈ مخاطب", "lock:contacts"),
        (f"{glass_lock_status(security.lock_locations)} ◈ موقعیت", "lock:locations"),
        (f"{glass_lock_status(security.lock_stickers)} ◈ استیکر", "lock:stickers"),
        (f"{glass_lock_status(security.lock_inline)} ◈ اینلاین", "lock:inline"),
        (f"{glass_lock_status(security.lock_mentions)} ◈ منشن", "lock:mentions"),
        (f"{glass_lock_status(security.lock_hashtags)} ◈ هشتگ", "lock:hashtags"),
    ]
    for text, cb in locks:
        builder.button(text=text, callback_data=cb)
    builder.button(text="🔙 ◈ بازگشت", callback_data="sec:menu")
    builder.adjust(2)
    return builder.as_markup()


def captcha_menu_kb(_: Callable, security: SecuritySettings) -> InlineKeyboardMarkup:
    """Glass-styled captcha menu."""
    builder = InlineKeyboardBuilder()
    status_icon = glass_status(security.captcha_enabled)
    toggle_text = 'غیرفعال' if security.captcha_enabled else 'فعال'
    builder.button(
        text=f"{status_icon} ◈ {toggle_text} کپچا",
        callback_data="captcha:toggle"
    )
    builder.button(text="🔘 ◈ دکمه‌ای", callback_data="captcha:type:button")
    builder.button(text="🔢 ◈ ریاضی", callback_data="captcha:type:math")
    builder.button(text="❓ ◈ سؤالی", callback_data="captcha:type:question")
    builder.button(text="🔙 ◈ بازگشت", callback_data="sec:menu")
    builder.adjust(1, 3, 1)
    return builder.as_markup()
