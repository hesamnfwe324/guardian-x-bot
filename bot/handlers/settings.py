from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.database.models import GroupSettings, WelcomeSettings
from bot.keyboards.main_menu import back_button_kb
import structlog

logger = structlog.get_logger()
router = Router()


class WelcomeStates(StatesGroup):
    waiting_message = State()


def settings_kb(_) -> object:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_welcome"), callback_data="settings:welcome")
    builder.button(text=_("btn_log_channel"), callback_data="settings:logs")
    builder.button(text=_("btn_general_settings"), callback_data="settings:general")
    builder.button(text=_("btn_back"), callback_data="menu:main")
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def welcome_kb(_, enabled: bool = True) -> object:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_set_welcome"), callback_data="welcome:set")
    builder.button(text=_("btn_welcome_variables"), callback_data="welcome:vars")
    builder.button(text="✅ Enabled" if enabled else "❌ Disabled", callback_data="welcome:toggle")
    builder.button(text=_("btn_back"), callback_data="settings:menu")
    builder.adjust(2, 1, 1)
    return builder.as_markup()


@router.callback_query(F.data == "menu:settings")
async def settings_menu(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(_("settings_menu"), reply_markup=settings_kb(_), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "settings:menu")
async def settings_menu_back(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(_("settings_menu"), reply_markup=settings_kb(_), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "settings:welcome")
async def welcome_menu(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if not db_group:
        await callback.answer(_("error_group_only"), show_alert=True)
        return
    ws = await db_session.scalar(select(WelcomeSettings).where(WelcomeSettings.group_id == db_group.id))
    is_enabled = bool(ws and ws.enabled)
    status = "✅ Enabled" if is_enabled else "❌ Disabled"
    text = _("welcome_menu") + f"\nStatus: {status}"
    if ws and ws.message:
        text += f"\n\n<b>Current Message:</b>\n{ws.message[:200]}"
    await callback.message.edit_text(text, reply_markup=welcome_kb(_, enabled=is_enabled), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "welcome:set")
async def set_welcome_start(callback: CallbackQuery, _: callable, state: FSMContext, **kwargs):
    await callback.message.answer(
        "✏️ Send the new welcome message.\n\n" + _("welcome_variables")
    )
    await state.set_state(WelcomeStates.waiting_message)
    await callback.answer()


@router.message(WelcomeStates.waiting_message)
async def save_welcome_message(message: Message, _: callable, db_session: AsyncSession, db_group, state: FSMContext, **kwargs):
    if not db_group:
        await state.clear()
        return
    ws = await db_session.scalar(select(WelcomeSettings).where(WelcomeSettings.group_id == db_group.id))
    if not ws:
        ws = WelcomeSettings(group_id=db_group.id, message=message.text)
        db_session.add(ws)
    else:
        ws.message = message.text
    await message.reply(_("welcome_set"))
    await state.clear()


@router.callback_query(F.data == "welcome:vars")
async def welcome_variables(callback: CallbackQuery, _: callable, **kwargs):
    await callback.answer(_("welcome_variables"), show_alert=True)


@router.callback_query(F.data == "welcome:toggle")
async def toggle_welcome(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if not db_group:
        await callback.answer(_("error_group_only"), show_alert=True)
        return
    ws = await db_session.scalar(select(WelcomeSettings).where(WelcomeSettings.group_id == db_group.id))
    if not ws:
        ws = WelcomeSettings(group_id=db_group.id, enabled=True)
        db_session.add(ws)
    else:
        ws.enabled = not ws.enabled
    status = "✅ Enabled" if ws.enabled else "❌ Disabled"
    await callback.answer(f"Welcome: {status}")


@router.callback_query(F.data == "settings:general")
async def general_settings(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if not db_group:
        await callback.answer(_("error_group_only"), show_alert=True)
        return
    gs = await db_session.scalar(select(GroupSettings).where(GroupSettings.group_id == db_group.id))
    if not gs:
        gs = GroupSettings(group_id=db_group.id)
        db_session.add(gs)
        await db_session.flush()

    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"{'✅' if gs.economy_enabled else '❌'} Economy",
        callback_data="gsetting:economy"
    )
    builder.button(
        text=f"{'✅' if gs.games_enabled else '❌'} Games",
        callback_data="gsetting:games"
    )
    builder.button(
        text=f"{'✅' if gs.xp_enabled else '❌'} XP System",
        callback_data="gsetting:xp"
    )
    builder.button(
        text=f"{'✅' if gs.silent_actions else '❌'} Silent Actions",
        callback_data="gsetting:silent"
    )
    builder.button(text=f"Max Warns: {gs.max_warns}", callback_data="gsetting:maxwarns")
    builder.button(text=_("btn_back"), callback_data="settings:menu")
    builder.adjust(2, 2, 1, 1)
    await callback.message.edit_text("⚙️ <b>General Settings</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gsetting:"))
async def toggle_gsetting(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if not db_group:
        await callback.answer(_("error_group_only"), show_alert=True)
        return
    setting = callback.data.split("gsetting:", 1)[1]
    gs = await db_session.scalar(select(GroupSettings).where(GroupSettings.group_id == db_group.id))
    if not gs:
        gs = GroupSettings(group_id=db_group.id)
        db_session.add(gs)
        await db_session.flush()
    if setting == "economy":
        gs.economy_enabled = not gs.economy_enabled
        await callback.answer(f"Economy: {'✅' if gs.economy_enabled else '❌'}")
    elif setting == "games":
        gs.games_enabled = not gs.games_enabled
        await callback.answer(f"Games: {'✅' if gs.games_enabled else '❌'}")
    elif setting == "xp":
        gs.xp_enabled = not gs.xp_enabled
        await callback.answer(f"XP: {'✅' if gs.xp_enabled else '❌'}")
    elif setting == "silent":
        gs.silent_actions = not gs.silent_actions
        await callback.answer(f"Silent Actions: {'✅' if gs.silent_actions else '❌'}")
    elif setting == "maxwarns":
        gs.max_warns = 3 if gs.max_warns == 5 else 5 if gs.max_warns == 3 else 3
        await callback.answer(f"Max Warns: {gs.max_warns}")


@router.callback_query(F.data == "settings:logs")
async def log_settings(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if not db_group:
        await callback.answer(_("error_group_only"), show_alert=True)
        return
    gs = await db_session.scalar(select(GroupSettings).where(GroupSettings.group_id == db_group.id))
    if not gs:
        gs = GroupSettings(group_id=db_group.id)
        db_session.add(gs)
        await db_session.flush()

    builder = InlineKeyboardBuilder()
    log_toggles = [
        (f"{'✅' if gs.log_join else '❌'} Join Logs", "log:join"),
        (f"{'✅' if gs.log_leave else '❌'} Leave Logs", "log:leave"),
        (f"{'✅' if gs.log_delete else '❌'} Delete Logs", "log:delete"),
        (f"{'✅' if gs.log_edit else '❌'} Edit Logs", "log:edit"),
        (f"{'✅' if gs.log_ban else '❌'} Ban Logs", "log:ban"),
        (f"{'✅' if gs.log_mute else '❌'} Mute Logs", "log:mute"),
        (f"{'✅' if gs.log_warn else '❌'} Warn Logs", "log:warn"),
        (f"{'✅' if gs.log_promote else '❌'} Promote Logs", "log:promote"),
    ]
    for text, cb in log_toggles:
        builder.button(text=text, callback_data=cb)
    builder.button(text="📋 Set Log Channel", callback_data="log:set_channel")
    builder.button(text=_("btn_back"), callback_data="settings:menu")
    builder.adjust(2)
    await callback.message.edit_text("📋 <b>Logging Settings</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("log:"))
async def toggle_log(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if not db_group:
        await callback.answer(_("error_group_only"), show_alert=True)
        return
    log_type = callback.data.split("log:", 1)[1]
    gs = await db_session.scalar(select(GroupSettings).where(GroupSettings.group_id == db_group.id))
    if not gs:
        gs = GroupSettings(group_id=db_group.id)
        db_session.add(gs)
        await db_session.flush()

    field_map = {
        "join": "log_join", "leave": "log_leave", "delete": "log_delete",
        "edit": "log_edit", "ban": "log_ban", "mute": "log_mute",
        "warn": "log_warn", "promote": "log_promote",
    }
    if log_type in field_map:
        field = field_map[log_type]
        current = getattr(gs, field, True)
        setattr(gs, field, not current)
        status = "✅" if not current else "❌"
        await callback.answer(f"{log_type}: {status}")
