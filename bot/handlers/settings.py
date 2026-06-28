from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.database.models import GroupSettings, WelcomeSettings
from bot.keyboards.main_menu import nav_kb
import structlog

logger = structlog.get_logger()
router = Router()


class WelcomeStates(StatesGroup):
    waiting_message = State()


def settings_kb(_):
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_welcome"),          callback_data="settings:welcome")
    builder.button(text=_("btn_goodbye"),          callback_data="settings:goodbye")
    builder.button(text=_("btn_log_channel"),      callback_data="settings:logs")
    builder.button(text=_("btn_general_settings"), callback_data="settings:general")
    builder.button(text=_("btn_slow_mode"),        callback_data="settings:slowmode")
    builder.button(text=_("btn_auto_delete"),      callback_data="settings:autodel")
    builder.button(text=_("btn_back"),             callback_data="menu:main")
    builder.button(text=_("btn_home"),             callback_data="menu:main")
    builder.adjust(2, 2, 2, 2)
    return builder.as_markup()


def welcome_kb(_, enabled=True):
    builder = InlineKeyboardBuilder()
    icon = "✅" if enabled else "❌"
    label = _("btn_enabled") if enabled else _("btn_disabled")
    builder.button(text=f"{icon} {label}", callback_data="welcome:toggle")
    builder.button(text=_("btn_set_welcome"),       callback_data="welcome:set")
    builder.button(text=_("btn_welcome_variables"), callback_data="welcome:vars")
    builder.button(text=_("btn_preview"),           callback_data="welcome:preview")
    builder.button(text=_("btn_back"),              callback_data="settings:menu")
    builder.button(text=_("btn_home"),              callback_data="menu:main")
    builder.adjust(1, 2, 1, 2)
    return builder.as_markup()


def general_settings_kb(_, gs):
    builder = InlineKeyboardBuilder()
    s = lambda v: "✅" if v else "❌"
    builder.button(text=f"{s(gs.economy_enabled)} {_('btn_economy_toggle')}",callback_data="gs:eco")
    builder.button(text=f"{s(gs.games_enabled)} {_('btn_games_toggle')}",   callback_data="gs:games")
    builder.button(text=f"{s(gs.xp_enabled)} {_('btn_xp_toggle')}",         callback_data="gs:xp")
    builder.button(text=f"{s(gs.reputation_enabled)} {_('btn_rep_toggle')}", callback_data="gs:rep")
    builder.button(text=f"{s(gs.silent_actions)} {_('btn_silent')}",         callback_data="gs:silent")
    builder.button(text=_("btn_max_warns") + f" ({gs.max_warns})",           callback_data="gs:maxwarns")
    builder.button(text=_("btn_warn_action") + f" ({gs.warn_action})",       callback_data="gs:warnaction")
    builder.button(text=_("btn_back"),  callback_data="settings:menu")
    builder.button(text=_("btn_home"),  callback_data="menu:main")
    builder.adjust(2, 2, 1, 2, 2)
    return builder.as_markup()


def slowmode_kb(_):
    builder = InlineKeyboardBuilder()
    for label, secs in [(_("btn_off"), 0), ("10s", 10), ("30s", 30), ("1m", 60), ("5m", 300), ("15m", 900), ("1h", 3600)]:
        builder.button(text=label, callback_data=f"slowmode:{secs}")
    builder.button(text=_("btn_back"), callback_data="settings:menu")
    builder.button(text=_("btn_home"), callback_data="menu:main")
    builder.adjust(4, 3, 2)
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
    text = _("welcome_menu")
    if ws and ws.message:
        text += "\n\n" + _("current_message") + ":\n" + ws.message[:300]
    await callback.message.edit_text(text, reply_markup=welcome_kb(_, enabled=is_enabled), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "welcome:set")
async def set_welcome_start(callback: CallbackQuery, _: callable, state: FSMContext, **kwargs):
    await callback.message.answer(_("welcome_set_prompt"))
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


@router.callback_query(F.data == "welcome:preview")
async def welcome_preview(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if not db_group:
        await callback.answer(_("error_group_only"), show_alert=True)
        return
    ws = await db_session.scalar(select(WelcomeSettings).where(WelcomeSettings.group_id == db_group.id))
    if not ws or not ws.message:
        await callback.answer(_("no_welcome_set"), show_alert=True)
        return
    preview = ws.message.replace("{name}", callback.from_user.first_name or "User")
    preview = preview.replace("{group}", callback.message.chat.title or "Group")
    await callback.answer(preview[:200], show_alert=True)


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
    status = _("btn_enabled") if ws.enabled else _("btn_disabled")
    await callback.answer(f"{_('btn_welcome')}: {status}")
    text = _("welcome_menu")
    if ws.message:
        text += "\n\n" + _("current_message") + ":\n" + ws.message[:300]
    await callback.message.edit_text(text, reply_markup=welcome_kb(_, enabled=ws.enabled), parse_mode="HTML")


@router.callback_query(F.data == "settings:goodbye")
async def goodbye_menu(callback: CallbackQuery, _: callable, **kwargs):
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_set_goodbye"),    callback_data="goodbye:set")
    builder.button(text=_("btn_toggle_goodbye"), callback_data="goodbye:toggle")
    builder.button(text=_("btn_back"),           callback_data="settings:menu")
    builder.button(text=_("btn_home"),           callback_data="menu:main")
    builder.adjust(2, 2)
    await callback.message.edit_text(_("goodbye_menu"), reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.in_({"goodbye:set", "goodbye:toggle"}))
async def goodbye_action(callback: CallbackQuery, _: callable, **kwargs):
    await callback.answer(_("feature_coming"), show_alert=True)


@router.callback_query(F.data == "settings:logs")
async def log_channel_menu(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if not db_group:
        await callback.answer(_("error_group_only"), show_alert=True)
        return
    gs = await db_session.scalar(select(GroupSettings).where(GroupSettings.group_id == db_group.id))
    log_id = gs.log_channel_id if gs else None
    status = str(log_id) if log_id else _("not_set")
    text = _("log_channel_menu").format(channel_id=status)
    builder = InlineKeyboardBuilder()
    builder.button(text=_("btn_set_log_channel"), callback_data="logs:set")
    if log_id:
        builder.button(text=_("btn_remove_log_channel"), callback_data="logs:remove")
    builder.button(text=_("btn_log_events"), callback_data="logs:events")
    builder.button(text=_("btn_back"),       callback_data="settings:menu")
    builder.button(text=_("btn_home"),       callback_data="menu:main")
    builder.adjust(2, 1, 2)
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "logs:remove")
async def remove_log_channel(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if not db_group:
        await callback.answer(_("error_group_only"), show_alert=True)
        return
    gs = await db_session.scalar(select(GroupSettings).where(GroupSettings.group_id == db_group.id))
    if gs:
        gs.log_channel_id = None
    await callback.answer(_("log_channel_removed"))


@router.callback_query(F.data == "logs:set")
async def set_log_channel(callback: CallbackQuery, _: callable, **kwargs):
    await callback.answer(_("log_channel_set_hint"), show_alert=True)


@router.callback_query(F.data == "logs:events")
async def log_events_menu(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if not db_group:
        await callback.answer(_("error_group_only"), show_alert=True)
        return
    gs = await db_session.scalar(select(GroupSettings).where(GroupSettings.group_id == db_group.id))
    if not gs:
        gs = GroupSettings(group_id=db_group.id)
        db_session.add(gs)
        await db_session.flush()
    s = lambda v: "✅" if v else "❌"
    builder = InlineKeyboardBuilder()
    for txt, cb, field in [
        (f"{s(gs.log_join)} {_('log_join')}",     "log:join",   "log_join"),
        (f"{s(gs.log_leave)} {_('log_leave')}",   "log:leave",  "log_leave"),
        (f"{s(gs.log_delete)} {_('log_delete')}", "log:delete", "log_delete"),
        (f"{s(gs.log_edit)} {_('log_edit')}",     "log:edit",   "log_edit"),
        (f"{s(gs.log_ban)} {_('log_ban')}",       "log:ban",    "log_ban"),
        (f"{s(gs.log_mute)} {_('log_mute')}",     "log:mute",   "log_mute"),
        (f"{s(gs.log_warn)} {_('log_warn')}",     "log:warn",   "log_warn"),
    ]:
        builder.button(text=txt, callback_data=cb)
    builder.button(text=_("btn_back"), callback_data="settings:logs")
    builder.button(text=_("btn_home"), callback_data="menu:main")
    builder.adjust(2, 2, 2, 1, 2)
    await callback.message.edit_text(_("log_events_menu"), reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("log:"))
async def toggle_log_event(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if not db_group:
        await callback.answer(_("error_group_only"), show_alert=True)
        return
    event = callback.data.split("log:")[1]
    gs = await db_session.scalar(select(GroupSettings).where(GroupSettings.group_id == db_group.id))
    if not gs:
        gs = GroupSettings(group_id=db_group.id)
        db_session.add(gs)
        await db_session.flush()
    field_map = {"join":"log_join","leave":"log_leave","delete":"log_delete","edit":"log_edit","ban":"log_ban","mute":"log_mute","warn":"log_warn"}
    field = field_map.get(event)
    if field:
        setattr(gs, field, not getattr(gs, field))
        status = _("btn_enabled") if getattr(gs, field) else _("btn_disabled")
        await callback.answer(f"{event}: {status}")


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
    await callback.message.edit_text(_("general_settings_menu"), reply_markup=general_settings_kb(_, gs), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gs:"))
async def toggle_general_setting(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if not db_group:
        await callback.answer(_("error_group_only"), show_alert=True)
        return
    key = callback.data.split("gs:")[1]
    gs = await db_session.scalar(select(GroupSettings).where(GroupSettings.group_id == db_group.id))
    if not gs:
        gs = GroupSettings(group_id=db_group.id)
        db_session.add(gs)
        await db_session.flush()
    toggle_map = {"eco":"economy_enabled","games":"games_enabled","xp":"xp_enabled","rep":"reputation_enabled","silent":"silent_actions"}
    if key in toggle_map:
        field = toggle_map[key]
        setattr(gs, field, not getattr(gs, field))
        status = _("btn_enabled") if getattr(gs, field) else _("btn_disabled")
        await callback.answer(status)
        await callback.message.edit_reply_markup(reply_markup=general_settings_kb(_, gs))
    elif key == "maxwarns":
        cycle = [1, 2, 3, 5, 10]
        cur = gs.max_warns or 3
        nxt = cycle[(cycle.index(cur)+1) % len(cycle)] if cur in cycle else 3
        gs.max_warns = nxt
        await callback.answer(f"{_('btn_max_warns')}: {nxt}")
        await callback.message.edit_reply_markup(reply_markup=general_settings_kb(_, gs))
    elif key == "warnaction":
        actions = ["mute", "kick", "ban"]
        cur = gs.warn_action or "mute"
        nxt = actions[(actions.index(cur)+1) % len(actions)] if cur in actions else "mute"
        gs.warn_action = nxt
        await callback.answer(f"{_('btn_warn_action')}: {nxt}")
        await callback.message.edit_reply_markup(reply_markup=general_settings_kb(_, gs))


@router.callback_query(F.data == "settings:slowmode")
async def slowmode_menu(callback: CallbackQuery, _: callable, **kwargs):
    await callback.message.edit_text(_("slowmode_menu"), reply_markup=slowmode_kb(_), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("slowmode:"))
async def set_slowmode(callback: CallbackQuery, _: callable, **kwargs):
    seconds = int(callback.data.split("slowmode:")[1])
    try:
        await callback.bot.set_chat_slow_mode_delay(callback.message.chat.id, seconds)
        label = f"{seconds}s" if seconds else _("btn_off")
        await callback.answer(_("slowmode_set").format(value=label))
    except Exception:
        await callback.answer(_("error_generic"), show_alert=True)


@router.callback_query(F.data == "settings:autodel")
async def autodel_menu(callback: CallbackQuery, _: callable, **kwargs):
    builder = InlineKeyboardBuilder()
    for label, secs in [(_("btn_off"), 0), ("30s", 30), ("1m", 60), ("5m", 300), ("10m", 600), ("30m", 1800)]:
        builder.button(text=label, callback_data=f"autodel:{secs}")
    builder.button(text=_("btn_back"), callback_data="settings:menu")
    builder.button(text=_("btn_home"), callback_data="menu:main")
    builder.adjust(3, 3, 2)
    await callback.message.edit_text(_("autodel_menu"), reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("autodel:"))
async def set_autodel(callback: CallbackQuery, _: callable, db_session: AsyncSession, db_group, **kwargs):
    if not db_group:
        await callback.answer(_("error_group_only"), show_alert=True)
        return
    seconds = int(callback.data.split("autodel:")[1])
    ws = await db_session.scalar(select(WelcomeSettings).where(WelcomeSettings.group_id == db_group.id))
    if not ws:
        ws = WelcomeSettings(group_id=db_group.id)
        db_session.add(ws)
    ws.delete_after = seconds
    label = f"{seconds}s" if seconds else _("btn_off")
    await callback.answer(_("autodel_set").format(value=label))
