from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Callable
from bot.database.models import SecuritySettings


def security_menu_kb(_: Callable, security: SecuritySettings) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    def status(enabled: bool) -> str:
        return "✅" if enabled else "❌"

    builder.button(text=f"{status(security.anti_spam)} {_('btn_anti_spam')}", callback_data="sec:anti_spam")
    builder.button(text=f"{status(security.anti_flood)} {_('btn_anti_flood')}", callback_data="sec:anti_flood")
    builder.button(text=f"{status(security.anti_raid)} {_('btn_anti_raid')}", callback_data="sec:anti_raid")
    builder.button(text=f"{status(security.anti_bot)} {_('btn_anti_bot')}", callback_data="sec:anti_bot")
    builder.button(text=f"{status(security.anti_fake)} {_('btn_anti_fake')}", callback_data="sec:anti_fake")
    builder.button(text=f"{status(security.anti_advertisement)} {_('btn_anti_ad')}", callback_data="sec:anti_ad")
    builder.button(text=f"{status(security.anti_link)} {_('btn_anti_link')}", callback_data="sec:anti_link")
    builder.button(text=f"{status(security.anti_mention_spam)} {_('btn_anti_mention')}", callback_data="sec:anti_mention")
    builder.button(text=f"{status(security.anti_forward_spam)} {_('btn_anti_forward')}", callback_data="sec:anti_forward")
    builder.button(text=f"{status(security.anti_emoji_spam)} {_('btn_anti_emoji')}", callback_data="sec:anti_emoji")
    builder.button(text=f"{status(security.anti_hashtag_spam)} {_('btn_anti_hashtag')}", callback_data="sec:anti_hashtag")
    builder.button(text=f"{status(security.anti_phone)} {_('btn_anti_phone')}", callback_data="sec:anti_phone")
    builder.button(text=f"{status(security.anti_scam)} {_('btn_anti_scam')}", callback_data="sec:anti_scam")
    builder.button(text=f"{status(security.anti_crypto_scam)} {_('btn_anti_crypto')}", callback_data="sec:anti_crypto")
    builder.button(text=f"{status(security.anti_nsfw)} {_('btn_anti_nsfw')}", callback_data="sec:anti_nsfw")
    builder.button(text=f"{status(security.anti_invite)} {_('btn_anti_invite')}", callback_data="sec:anti_invite")
    builder.button(text=f"{status(security.anti_channel_promo)} {_('btn_anti_promo')}", callback_data="sec:anti_promo")
    builder.button(text=f"{status(security.anti_mass_join)} {_('btn_anti_mass_join')}", callback_data="sec:anti_mass_join")
    builder.button(text=f"{status(security.captcha_enabled)} {_('btn_captcha')}", callback_data="sec:captcha")
    builder.button(text=_("btn_locks"), callback_data="sec:locks")
    builder.button(text=_("btn_advanced_protection"), callback_data="sec:advanced")
    builder.button(text=f"{'🚨' if security.emergency_mode else '🟢'} {_('btn_emergency')}", callback_data="sec:emergency")
    builder.button(text=_("btn_back"), callback_data="menu:main")
    builder.adjust(2)
    return builder.as_markup()


def locks_menu_kb(_: Callable, security: SecuritySettings) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    def s(v: bool) -> str:
        return "🔒" if v else "🔓"

    locks = [
        (f"{s(security.lock_text)} {_('btn_lock_text')}", "lock:text"),
        (f"{s(security.lock_links)} {_('btn_lock_links')}", "lock:links"),
        (f"{s(security.lock_photos)} {_('btn_lock_photos')}", "lock:photos"),
        (f"{s(security.lock_videos)} {_('btn_lock_videos')}", "lock:videos"),
        (f"{s(security.lock_gifs)} {_('btn_lock_gifs')}", "lock:gifs"),
        (f"{s(security.lock_audio)} {_('btn_lock_audio')}", "lock:audio"),
        (f"{s(security.lock_voice)} {_('btn_lock_voice')}", "lock:voice"),
        (f"{s(security.lock_documents)} {_('btn_lock_docs')}", "lock:docs"),
        (f"{s(security.lock_polls)} {_('btn_lock_polls')}", "lock:polls"),
        (f"{s(security.lock_games)} {_('btn_lock_games')}", "lock:games"),
        (f"{s(security.lock_bots)} {_('btn_lock_bots')}", "lock:bots"),
        (f"{s(security.lock_forwards)} {_('btn_lock_forwards')}", "lock:forwards"),
        (f"{s(security.lock_contacts)} {_('btn_lock_contacts')}", "lock:contacts"),
        (f"{s(security.lock_locations)} {_('btn_lock_locations')}", "lock:locations"),
        (f"{s(security.lock_stickers)} {_('btn_lock_stickers')}", "lock:stickers"),
        (f"{s(security.lock_inline)} {_('btn_lock_inline')}", "lock:inline"),
        (f"{s(security.lock_mentions)} {_('btn_lock_mentions')}", "lock:mentions"),
        (f"{s(security.lock_hashtags)} {_('btn_lock_hashtags')}", "lock:hashtags"),
    ]
    for text, cb in locks:
        builder.button(text=text, callback_data=cb)
    builder.button(text=_("btn_back"), callback_data="sec:menu")
    builder.adjust(2)
    return builder.as_markup()


def captcha_menu_kb(_: Callable, security: SecuritySettings) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    status = "✅" if security.captcha_enabled else "❌"
    builder.button(
        text=f"{status} {'Enable' if not security.captcha_enabled else 'Disable'} Captcha",
        callback_data="captcha:toggle"
    )
    builder.button(text=_("btn_captcha_button"), callback_data="captcha:type:button")
    builder.button(text=_("btn_captcha_math"), callback_data="captcha:type:math")
    builder.button(text=_("btn_captcha_question"), callback_data="captcha:type:question")
    builder.button(text=_("btn_back"), callback_data="sec:menu")
    builder.adjust(1, 3, 1)
    return builder.as_markup()
