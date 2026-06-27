from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.database.models import User, Group
from bot.keyboards.main_menu import back_button_kb
from bot.config import settings
from bot.utils.helpers import format_number
import structlog

logger = structlog.get_logger()
router = Router()

_maintenance_mode = False


class OwnerStates(StatesGroup):
    waiting_broadcast = State()


def is_owner(user_id: int) -> bool:
    return user_id == settings.BOT_OWNER_ID


def owner_kb(_=None) -> object:
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Global Broadcast", callback_data="owner:broadcast")
    builder.button(text="📊 Statistics", callback_data="owner:stats")
    builder.button(text=f"{'🟢 Disable' if _maintenance_mode else '🔧 Enable'} Maintenance", callback_data="owner:maintenance")
    builder.button(text="👥 User List", callback_data="owner:users")
    builder.button(text="📱 Group List", callback_data="owner:groups")
    builder.button(text="🚨 Emergency Controls", callback_data="owner:emergency")
    builder.adjust(2, 1, 2, 1)
    return builder.as_markup()


@router.message(Command("owner", "panel"))
async def owner_panel(message: Message, _: callable, **kwargs):
    if not is_owner(message.from_user.id):
        await message.reply(_("error_not_owner"))
        return
    await message.answer(_("owner_panel"), reply_markup=owner_kb(), parse_mode="HTML")


@router.callback_query(F.data == "owner:stats")
async def owner_stats(callback: CallbackQuery, _: callable, db_session: AsyncSession, **kwargs):
    if not is_owner(callback.from_user.id):
        await callback.answer(_("error_not_owner"), show_alert=True)
        return
    user_count = await db_session.scalar(select(func.count()).select_from(User))
    group_count = await db_session.scalar(select(func.count()).select_from(Group))
    text = (
        "📊 <b>Global Statistics</b>\n\n"
        + _("total_users").format(count=format_number(user_count or 0)) + "\n"
        + _("total_groups").format(count=format_number(group_count or 0)) + "\n\n"
        + f"🔧 Maintenance: {'ON' if _maintenance_mode else 'OFF'}"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "owner:menu"))
    await callback.answer()


@router.callback_query(F.data == "owner:broadcast")
async def start_broadcast(callback: CallbackQuery, _: callable, state: FSMContext, **kwargs):
    if not is_owner(callback.from_user.id):
        await callback.answer(_("error_not_owner"), show_alert=True)
        return
    await callback.message.answer("📢 Send the broadcast message:")
    await state.set_state(OwnerStates.waiting_broadcast)
    await callback.answer()


@router.message(OwnerStates.waiting_broadcast)
async def process_broadcast(message: Message, _: callable, db_session: AsyncSession, state: FSMContext, **kwargs):
    if not is_owner(message.from_user.id):
        await state.clear()
        return
    users = await db_session.execute(
        select(User).where(User.is_banned == False).limit(1000)
    )
    users_list = users.scalars().all()
    sent = 0
    failed = 0
    for user in users_list:
        try:
            await message.copy_to(user.id)
            sent += 1
        except Exception:
            failed += 1
    await message.reply(_("broadcast_sent").format(count=sent))
    await state.clear()


@router.callback_query(F.data == "owner:maintenance")
async def toggle_maintenance(callback: CallbackQuery, _: callable, **kwargs):
    global _maintenance_mode
    if not is_owner(callback.from_user.id):
        await callback.answer(_("error_not_owner"), show_alert=True)
        return
    _maintenance_mode = not _maintenance_mode
    if _maintenance_mode:
        await callback.answer(_("maintenance_on"), show_alert=True)
    else:
        await callback.answer(_("maintenance_off"), show_alert=True)


@router.callback_query(F.data == "owner:emergency")
async def emergency_controls(callback: CallbackQuery, _: callable, **kwargs):
    if not is_owner(callback.from_user.id):
        await callback.answer(_("error_not_owner"), show_alert=True)
        return
    text = (
        "🚨 <b>Emergency Controls</b>\n\n"
        "• Enable/disable all security features globally\n"
        "• Force-enable raid protection on all groups\n"
        "• Send emergency broadcast\n"
        "• Flush Redis cache\n"
        "• Restart bot services"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb(_, "owner:menu"))
    await callback.answer()


@router.callback_query(F.data == "owner:menu")
async def owner_menu_back(callback: CallbackQuery, _: callable, **kwargs):
    if not is_owner(callback.from_user.id):
        await callback.answer(_("error_not_owner"), show_alert=True)
        return
    await callback.message.edit_text(_("owner_panel"), reply_markup=owner_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("owner:"))
async def owner_catch_all(callback: CallbackQuery, _: callable, **kwargs):
    if not is_owner(callback.from_user.id):
        await callback.answer(_("error_not_owner"), show_alert=True)
        return
    await callback.answer("Feature coming soon!", show_alert=True)


def get_maintenance_mode() -> bool:
    return _maintenance_mode
