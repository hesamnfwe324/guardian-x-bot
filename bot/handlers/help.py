from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from bot.keyboards.main_menu import back_button_kb
import structlog

logger = structlog.get_logger()
router = Router()


def build_help_text(_: callable) -> str:
    """Build i18n help text using the _() callable."""
    return (
        f"  ❓ <b>{_('help_center_title')}</b>\n"
        f"  💰 <b>{_('help_section_economy')}</b>\n"
        f"  /wallet — {_('help_cmd_wallet')}\n"
        f"  /daily — {_('help_cmd_daily')}\n"
        f"  /weekly — {_('help_cmd_weekly')}\n"
        f"  /monthly — {_('help_cmd_monthly')}\n"
        f"  /deposit — {_('help_cmd_deposit')}\n"
        f"  /withdraw — {_('help_cmd_withdraw')}\n"
        f"  /transfer — {_('help_cmd_transfer')}\n"
        f"  /referral — {_('help_cmd_referral')}\n"
        f"  /achievements — {_('help_cmd_achievements')}\n\n"
        f"  🎮 <b>{_('help_section_games')}</b>\n"
        f"  /dice — {_('help_cmd_dice')}\n"
        f"  /rps — {_('help_cmd_rps')}\n"
        f"  /quiz — {_('help_cmd_quiz')}\n"
        f"  /wheel — {_('help_cmd_wheel')}\n"
        f"  /numwar — {_('help_cmd_numwar')}\n"
        f"  /cards — {_('help_cmd_cards')}\n"
        f"  /treasure — {_('help_cmd_treasure')}\n"
        f"  /mines — {_('help_cmd_mines')}\n"
        f"  /roulette — {_('help_cmd_roulette')}\n\n"
        f"  🛡️ <b>{_('help_section_security')}</b>\n"
        f"  /security — {_('help_cmd_security')}\n"
        f"  /lock — {_('help_cmd_lock')}\n"
        f"  /unlock — {_('help_cmd_unlock')}\n\n"
        f"  🔨 <b>{_('help_section_moderation')}</b>\n"
        f"  /ban — {_('help_cmd_ban')}\n"
        f"  /unban — {_('help_cmd_unban')}\n"
        f"  /kick — {_('help_cmd_kick')}\n"
        f"  /mute — {_('help_cmd_mute')}\n"
        f"  /unmute — {_('help_cmd_unmute')}\n"
        f"  /warn — {_('help_cmd_warn')}\n"
        f"  /unwarn — {_('help_cmd_unwarn')}\n"
        f"  /warns — {_('help_cmd_warns')}\n"
        f"  /history — {_('help_cmd_history')}\n\n"
        f"  ⚙️ <b>{_('help_section_settings')}</b>\n"
        f"  /settings — {_('help_cmd_settings')}\n\n"
        f"  ℹ️ <b>{_('help_section_other')}</b>\n"
        f"  /language — {_('help_cmd_language')}\n"
        f"  /stats — {_('help_cmd_stats')}\n"
        f"  /help — {_('help_cmd_help')}\n\n"
        f"  <i>{_('help_hint')}</i>"
    )


@router.message(Command('help'))
async def cmd_help(message: Message, _: callable, **kwargs):
    await message.answer(build_help_text(_), parse_mode='HTML')


@router.callback_query(F.data == "menu:help")
async def menu_help(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(
        build_help_text(_),
        parse_mode='HTML',
        reply_markup=back_button_kb(_, 'menu:main'),
    )
    await callback.answer()
