from bot.database.connection import get_session, create_tables, close_db
from bot.database.models import (
    Base, User, Group, GroupMember, GroupSettings, SecuritySettings,
    WelcomeSettings, Wallet, Transaction, Economy, Reputation, Warning,
    UserNote, ActionLog, Achievement, UserAchievement, Mission, UserMission,
    DuelStats, Duel, GameStats, GameMatch, Tournament, TournamentParticipant,
    Referral, GroupStats, ScheduledPost, ShopItem, UserShopItem,
    CaptchaChallenge,
)

__all__ = [
    "engine", "async_session_maker", "get_session", "create_tables", "close_db",
    "Base", "User", "Group", "GroupMember", "GroupSettings", "SecuritySettings",
    "WelcomeSettings", "Wallet", "Transaction", "Economy", "Reputation",
    "Warning", "UserNote", "ActionLog", "Achievement", "UserAchievement",
    "Mission", "UserMission", "DuelStats", "Duel", "GameStats", "GameMatch",
    "Tournament", "TournamentParticipant", "Referral", "GroupStats",
    "ScheduledPost", "ShopItem", "UserShopItem", "CaptchaChallenge",
]


def __getattr__(name):
    """Lazily provide engine and async_session_maker from connection module."""
    if name in ("engine", "async_session_maker"):
        from bot.database.connection import engine as _engine, async_session_maker as _sm
        if name == "engine":
            return _engine
        return _sm
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
