"""
Glassmorphism Panel System for Guardian X Telegram Bot
Creates beautiful glass-like UI panels using Unicode box-drawing characters,
emoji borders, and styled text formatting within Telegram chat.
"""

# ─── Glass Panel Decorators ─────────────────────────────────────────────────

# Glass border characters
GLASS_TOP    = "┌─────────────────────────┐"
GLASS_MID    = "│                         │"
GLASS_BOT    = "└─────────────────────────┘"
GLASS_LINE   = "┣━━━━━━━━━━━━━━━━━━━━━━━━━┫"
GLASS_DASH   = "╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌"
GLASS_DOT    = "· · · · · · · · · · · · ·"

# Glass panel emoji accents
ACCENT_BLUE   = "💠"
ACCENT_CYAN   = "🔵"
ACCENT_PURPLE = "🟣"
ACCENT_WHITE  = "⚪"
ACCENT_GLOW   = "✨"
ACCENT_FROST  = "❄️"
ACCENT_CRYSTAL = "🔮"
ACCENT_SHIELD = "🛡️"
ACCENT_STAR   = "⭐"

# Status indicators for glass style
STATUS_ON  = "🟢"
STATUS_OFF = "⚫"
STATUS_LOCKED   = "🔐"
STATUS_UNLOCKED = "🔓"
STATUS_ALERT    = "🔴"
STATUS_WARN     = "🟡"

# Separator styles
SEP_GLOW   = "✦ ───────────────── ✦"
SEP_FROST  = "❅ ───────────────── ❅"
SEP_CRYSTAL = "◈ ───────────────── ◈"
SEP_GLASS  = "░▒▓██▓▒░░▒▓██▓▒░"
SEP_THIN   = "╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌"
SEP_DIAMOND = "◇━━━━━━━━━━━━━━━━━━◇"


def glass_header(title: str, icon: str = "🔮") -> str:
    """Create a glass-style header with title."""
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  {icon} <b>{title}</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}"
    )


def glass_subheader(title: str, icon: str = "🔹") -> str:
    """Create a glass-style sub-header."""
    return f"{icon} <b>{title}</b> {SEP_DIAMOND}"


def glass_footer(hint: str = "") -> str:
    """Create a glass-style footer."""
    parts = [f"{ACCENT_GLOW} {GLASS_BOT}"]
    if hint:
        parts.append(f"{ACCENT_FROST} <i>{hint}</i>")
    return "\n".join(parts)


def glass_separator(style: str = "glow") -> str:
    """Return a glass separator line."""
    styles = {
        "glow": SEP_GLOW,
        "frost": SEP_FROST,
        "crystal": SEP_CRYSTAL,
        "glass": SEP_GLASS,
        "thin": SEP_THIN,
        "diamond": SEP_DIAMOND,
    }
    return styles.get(style, SEP_GLOW)


def glass_status(enabled: bool) -> str:
    """Return glass-style status indicator."""
    return STATUS_ON if enabled else STATUS_OFF


def glass_lock_status(locked: bool) -> str:
    """Return glass-style lock status indicator."""
    return STATUS_LOCKED if locked else STATUS_UNLOCKED


def glass_info_line(label: str, value: str, icon: str = "🔹") -> str:
    """Create a glass-style info line."""
    return f"  {icon} {label}: <b>{value}</b>"


def glass_menu_item(icon: str, label: str) -> str:
    """Format a menu item with glass styling (for button text)."""
    return f"{icon} {label}"


# ─── Pre-built Panel Templates ──────────────────────────────────────────────

def panel_welcome(name: str) -> str:
    """Glass-styled welcome panel for /start."""
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  🔮 <b>GUARDIAN X ULTIMATE</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  👋 سلام <b>{name}</b>!\n\n"
        f"  🤖 ربات مدیریت و سرگرمی پیشرفته\n"
        f"  گروه‌های تلگرام\n\n"
        f"  {ACCENT_CRYSTAL} از منوی شیشه‌ای زیر انتخاب کنید:\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_welcome_en(name: str) -> str:
    """Glass-styled welcome panel for /start (English)."""
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  🔮 <b>GUARDIAN X ULTIMATE</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  👋 Hello <b>{name}</b>!\n\n"
        f"  🤖 Advanced group management\n"
        f"  & entertainment bot\n\n"
        f"  {ACCENT_CRYSTAL} Choose from the glass panel below:\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_group(title: str) -> str:
    """Glass-styled group admin panel header."""
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  🛡️ <b>GUARDIAN X</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  ⚡ <i>پنل مدیریت شیشه‌ای</i>\n"
        f"  🏠 گروه: <b>{title}</b>\n\n"
        f"  {ACCENT_CRYSTAL} یک دسته‌بندی انتخاب کنید:\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_group_en(title: str) -> str:
    """Glass-styled group admin panel header (English)."""
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  🛡️ <b>GUARDIAN X</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  ⚡ <i>Glass Admin Panel</i>\n"
        f"  🏠 Group: <b>{title}</b>\n\n"
        f"  {ACCENT_CRYSTAL} Select a category:\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_security() -> str:
    """Glass-styled security center panel."""
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  🛡️ <b>مرکز امنیت شیشه‌ای</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  🔮 تنظیمات امنیتی گروه را مدیریت کنید\n"
        f"  {ACCENT_FROST} وضعیت هر امکان مشاهده می‌شود\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_security_en() -> str:
    """Glass-styled security center panel (English)."""
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  🛡️ <b>Glass Security Center</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  🔮 Manage your group security settings\n"
        f"  {ACCENT_FROST} Each feature shows its current status\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_locks() -> str:
    """Glass-styled lock system panel."""
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  🔐 <b>سیستم قفل شیشه‌ای</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  🔮 قفل‌های محتوا را مدیریت کنید\n"
        f"  {ACCENT_FROST} وضعیت قفل هر نوع محتوا\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_locks_en() -> str:
    """Glass-styled lock system panel (English)."""
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  🔐 <b>Glass Lock System</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  🔮 Toggle content locks\n"
        f"  {ACCENT_FROST} Each lock shows its status\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_captcha(status: str) -> str:
    """Glass-styled captcha panel."""
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  🔑 <b>تنظیمات کپچا</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  🔮 نوع کپچا را انتخاب کنید\n"
        f"  {ACCENT_FROST} وضعیت: {status}\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_captcha_en(status: str) -> str:
    """Glass-styled captcha panel (English)."""
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  🔑 <b>Captcha Settings</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  🔮 Choose captcha type\n"
        f"  {ACCENT_FROST} Status: {status}\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_economy() -> str:
    """Glass-styled economy panel."""
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  💰 <b>اقتصاد شیشه‌ای</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  🔮 سکه‌ها و جوایز خود را مدیریت کنید\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_economy_en() -> str:
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  💰 <b>Glass Economy</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  🔮 Manage your coins and rewards\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_games() -> str:
    """Glass-styled games panel."""
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  🎮 <b>سرگرمی شیشه‌ای</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  🔮 یک بازی انتخاب کنید\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_games_en() -> str:
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  🎮 <b>Glass Entertainment</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  🔮 Choose a game to play\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_moderation() -> str:
    """Glass-styled moderation panel."""
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  ⚖️ <b>مدیریت شیشه‌ای</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  🔮 یک اقدام مدیریتی انتخاب کنید\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_moderation_en() -> str:
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  ⚖️ <b>Glass Moderation</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  🔮 Select a moderation action\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_settings() -> str:
    """Glass-styled settings panel."""
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  ⚙️ <b>مرکز کنترل شیشه‌ای</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  🔮 تنظیمات گروه را پیکربندی کنید\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_settings_en() -> str:
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  ⚙️ <b>Glass Control Center</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  🔮 Configure your group settings\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_statistics() -> str:
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  📊 <b>آمار شیشه‌ای</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  🔮 رتبه‌بندی‌ها و آمار گروه\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_reputation() -> str:
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  🌟 <b>شهرت شیشه‌ای</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  🔮 سیستم اعتبار گروه\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_help() -> str:
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  ❓ <b>مرکز راهنما شیشه‌ای</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  🔮 یک موضوع برای اطلاعات بیشتر انتخاب کنید\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_tournaments() -> str:
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  🏆 <b>تورنمنت شیشه‌ای</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  🔮 با کاربران رقابت کنید و جایزه ببرید\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )


def panel_duels() -> str:
    return (
        f"{ACCENT_GLOW} {GLASS_TOP}\n"
        f"  ⚔️ <b>دوئل شیشه‌ای</b>\n"
        f"{ACCENT_GLOW} {GLASS_LINE}\n"
        f"  🔮 با کاربران مبارزه کنید\n"
        f"{ACCENT_GLOW} {GLASS_BOT}"
    )
