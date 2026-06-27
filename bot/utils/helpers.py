from datetime import datetime, timedelta, timezone
from typing import Optional
import math


def format_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m}m {s}s"
    elif seconds < 86400:
        h, rem = divmod(seconds, 3600)
        m = rem // 60
        return f"{h}h {m}m"
    else:
        d, rem = divmod(seconds, 86400)
        h = rem // 3600
        return f"{d}d {h}h"


def parse_duration(text: str) -> Optional[int]:
    text = text.strip().lower()
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
    if text[-1] in units:
        try:
            return int(text[:-1]) * units[text[-1]]
        except ValueError:
            return None
    try:
        return int(text) * 60
    except ValueError:
        return None


def format_number(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def xp_for_level(level: int) -> int:
    return int(100 * (level ** 1.5))


def calculate_level(total_xp: int) -> tuple[int, int, int]:
    level = 1
    while xp_for_level(level + 1) <= total_xp:
        level += 1
    current_level_xp = xp_for_level(level)
    next_level_xp = xp_for_level(level + 1)
    return level, total_xp - current_level_xp, next_level_xp - current_level_xp


def progress_bar(current: int, maximum: int, length: int = 10) -> str:
    if maximum == 0:
        return "░" * length
    filled = int(length * current / maximum)
    return "█" * filled + "░" * (length - filled)


def mention_user(user_id: int, name: str) -> str:
    return f'<a href="tg://user?id={user_id}">{name}</a>'


def get_time_until(target: datetime) -> str:
    now = datetime.now(timezone.utc)
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)
    delta = target - now
    if delta.total_seconds() <= 0:
        return "now"
    return format_duration(int(delta.total_seconds()))


def truncate(text: str, max_len: int = 100) -> str:
    return text if len(text) <= max_len else text[:max_len - 3] + "..."


def safe_username(user) -> str:
    if user.username:
        return f"@{user.username}"
    name = user.first_name or ""
    if user.last_name:
        name += f" {user.last_name}"
    return name.strip() or f"User#{user.id}"
