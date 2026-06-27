from datetime import datetime
from typing import Optional
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, Index, UniqueConstraint, func
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    username = Column(String(64), nullable=True, index=True)
    first_name = Column(String(256), nullable=False)
    last_name = Column(String(256), nullable=True)
    language = Column(String(8), default="en", nullable=False)
    is_bot = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())

    wallet = relationship("Wallet", back_populates="user", uselist=False)
    economy = relationship("Economy", back_populates="user", uselist=False)
    reputation = relationship("Reputation", back_populates="user", uselist=False)
    achievements = relationship("UserAchievement", back_populates="user")
    missions = relationship("UserMission", back_populates="user")
    duel_stats = relationship("DuelStats", back_populates="user", uselist=False)
    game_stats = relationship("GameStats", back_populates="user", uselist=False)
    referrals_made = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer")


class Group(Base):
    __tablename__ = "groups"

    id = Column(BigInteger, primary_key=True)
    title = Column(String(256), nullable=False)
    username = Column(String(64), nullable=True, index=True)
    type = Column(String(32), nullable=False, default="group")
    language = Column(String(8), default="en", nullable=False)
    is_active = Column(Boolean, default=True)
    member_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    settings = relationship("GroupSettings", back_populates="group", uselist=False)
    security = relationship("SecuritySettings", back_populates="group", uselist=False)
    welcome = relationship("WelcomeSettings", back_populates="group", uselist=False)
    members = relationship("GroupMember", back_populates="group")
    warnings = relationship("Warning", back_populates="group")
    notes = relationship("UserNote", back_populates="group")
    logs = relationship("ActionLog", back_populates="group")
    stats = relationship("GroupStats", back_populates="group", uselist=False)


class GroupMember(Base):
    __tablename__ = "group_members"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id"),
        Index("ix_group_members_group_user", "group_id", "user_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(32), default="member")
    custom_role = Column(String(64), nullable=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    is_muted = Column(Boolean, default=False)
    mute_until = Column(DateTime(timezone=True), nullable=True)
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(Text, nullable=True)
    warn_count = Column(Integer, default=0)
    message_count = Column(Integer, default=0)
    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    coins_earned = Column(Integer, default=0)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    is_trusted = Column(Boolean, default=False)
    is_whitelisted = Column(Boolean, default=False)
    is_blacklisted = Column(Boolean, default=False)

    group = relationship("Group", back_populates="members")
    user = relationship("User")


class GroupSettings(Base):
    __tablename__ = "group_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"), unique=True)
    log_channel_id = Column(BigInteger, nullable=True)
    log_join = Column(Boolean, default=True)
    log_leave = Column(Boolean, default=True)
    log_delete = Column(Boolean, default=True)
    log_edit = Column(Boolean, default=True)
    log_ban = Column(Boolean, default=True)
    log_mute = Column(Boolean, default=True)
    log_warn = Column(Boolean, default=True)
    log_promote = Column(Boolean, default=True)
    log_demote = Column(Boolean, default=True)
    log_settings = Column(Boolean, default=True)
    economy_enabled = Column(Boolean, default=True)
    games_enabled = Column(Boolean, default=True)
    xp_enabled = Column(Boolean, default=True)
    reputation_enabled = Column(Boolean, default=True)
    silent_actions = Column(Boolean, default=False)
    max_warns = Column(Integer, default=3)
    warn_action = Column(String(16), default="mute")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    group = relationship("Group", back_populates="settings")


class SecuritySettings(Base):
    __tablename__ = "security_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"), unique=True)

    anti_spam = Column(Boolean, default=True)
    anti_flood = Column(Boolean, default=True)
    flood_limit = Column(Integer, default=5)
    flood_window = Column(Integer, default=10)
    flood_action = Column(String(16), default="mute")

    anti_raid = Column(Boolean, default=False)
    anti_raid_threshold = Column(Integer, default=10)
    anti_raid_window = Column(Integer, default=60)

    anti_bot = Column(Boolean, default=True)
    anti_fake = Column(Boolean, default=False)
    anti_advertisement = Column(Boolean, default=True)
    anti_link = Column(Boolean, default=False)
    anti_mention_spam = Column(Boolean, default=True)
    anti_mention_limit = Column(Integer, default=5)
    anti_username_spam = Column(Boolean, default=False)
    anti_forward_spam = Column(Boolean, default=False)
    anti_emoji_spam = Column(Boolean, default=False)
    anti_emoji_limit = Column(Integer, default=10)
    anti_hashtag_spam = Column(Boolean, default=False)
    anti_phone = Column(Boolean, default=False)
    anti_scam = Column(Boolean, default=True)
    anti_crypto_scam = Column(Boolean, default=True)
    anti_nsfw = Column(Boolean, default=True)
    anti_invite = Column(Boolean, default=True)
    anti_channel_promo = Column(Boolean, default=True)
    anti_mass_join = Column(Boolean, default=False)
    anti_mass_leave = Column(Boolean, default=False)

    spam_action = Column(String(16), default="delete")
    link_action = Column(String(16), default="delete")
    bot_action = Column(String(16), default="kick")

    captcha_enabled = Column(Boolean, default=False)
    captcha_type = Column(String(16), default="button")
    captcha_timeout = Column(Integer, default=60)

    quarantine_mode = Column(Boolean, default=False)
    emergency_mode = Column(Boolean, default=False)
    join_rate_limit = Column(Integer, default=0)

    lock_text = Column(Boolean, default=False)
    lock_links = Column(Boolean, default=False)
    lock_photos = Column(Boolean, default=False)
    lock_videos = Column(Boolean, default=False)
    lock_gifs = Column(Boolean, default=False)
    lock_audio = Column(Boolean, default=False)
    lock_voice = Column(Boolean, default=False)
    lock_documents = Column(Boolean, default=False)
    lock_polls = Column(Boolean, default=False)
    lock_games = Column(Boolean, default=False)
    lock_bots = Column(Boolean, default=False)
    lock_forwards = Column(Boolean, default=False)
    lock_contacts = Column(Boolean, default=False)
    lock_locations = Column(Boolean, default=False)
    lock_stickers = Column(Boolean, default=False)
    lock_inline = Column(Boolean, default=False)
    lock_mentions = Column(Boolean, default=False)
    lock_hashtags = Column(Boolean, default=False)

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    group = relationship("Group", back_populates="security")


class WelcomeSettings(Base):
    __tablename__ = "welcome_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"), unique=True)
    enabled = Column(Boolean, default=True)
    message = Column(Text, nullable=True)
    media_type = Column(String(16), nullable=True)
    media_file_id = Column(String(256), nullable=True)
    button_text = Column(String(64), nullable=True)
    button_url = Column(String(256), nullable=True)
    delete_after = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    group = relationship("Group", back_populates="welcome")


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    balance = Column(BigInteger, default=0)
    bank_balance = Column(BigInteger, default=0)
    total_earned = Column(BigInteger, default=0)
    total_spent = Column(BigInteger, default=0)
    last_daily = Column(DateTime(timezone=True), nullable=True)
    last_weekly = Column(DateTime(timezone=True), nullable=True)
    last_monthly = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="wallet")
    transactions = relationship("Transaction", back_populates="wallet")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_wallet_id", "wallet_id"),
        Index("ix_transactions_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id", ondelete="CASCADE"))
    amount = Column(BigInteger, nullable=False)
    type = Column(String(32), nullable=False)
    description = Column(Text, nullable=True)
    reference_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    wallet = relationship("Wallet", back_populates="transactions")


class Economy(Base):
    __tablename__ = "economy"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    xp = Column(BigInteger, default=0)
    level = Column(Integer, default=1)
    total_xp = Column(BigInteger, default=0)
    streak_days = Column(Integer, default=0)
    last_streak_date = Column(DateTime(timezone=True), nullable=True)
    referral_count = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="economy")


class Reputation(Base):
    __tablename__ = "reputation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    positive = Column(Integer, default=0)
    negative = Column(Integer, default=0)
    last_given = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="reputation")


class Warning(Base):
    __tablename__ = "warnings"
    __table_args__ = (
        Index("ix_warnings_group_user", "group_id", "user_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"))
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    admin_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    group = relationship("Group", back_populates="warnings")
    user = relationship("User", foreign_keys=[user_id])
    admin = relationship("User", foreign_keys=[admin_id])


class UserNote(Base):
    __tablename__ = "user_notes"
    __table_args__ = (
        Index("ix_user_notes_group_user", "group_id", "user_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"))
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    admin_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    group = relationship("Group", back_populates="notes")
    user = relationship("User", foreign_keys=[user_id])
    admin = relationship("User", foreign_keys=[admin_id])


class ActionLog(Base):
    __tablename__ = "action_logs"
    __table_args__ = (
        Index("ix_action_logs_group_id", "group_id"),
        Index("ix_action_logs_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"))
    user_id = Column(BigInteger, nullable=True)
    admin_id = Column(BigInteger, nullable=True)
    action = Column(String(64), nullable=False)
    details = Column(JSONB, nullable=True)
    message_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    group = relationship("Group", back_populates="logs")


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    category = Column(String(32), nullable=False)
    name_key = Column(String(128), nullable=False)
    description_key = Column(String(256), nullable=False)
    icon = Column(String(8), nullable=True)
    points = Column(Integer, default=10)
    reward_coins = Column(Integer, default=0)
    reward_xp = Column(Integer, default=0)
    requirement_type = Column(String(32), nullable=False)
    requirement_value = Column(Integer, default=1)

    user_achievements = relationship("UserAchievement", back_populates="achievement")


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="CASCADE"))
    earned_at = Column(DateTime(timezone=True), server_default=func.now())
    progress = Column(Integer, default=0)

    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")


class Mission(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    type = Column(String(16), nullable=False)
    name_key = Column(String(128), nullable=False)
    description_key = Column(String(256), nullable=False)
    icon = Column(String(8), nullable=True)
    reward_coins = Column(Integer, default=0)
    reward_xp = Column(Integer, default=0)
    requirement_type = Column(String(32), nullable=False)
    requirement_value = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)

    user_missions = relationship("UserMission", back_populates="mission")


class UserMission(Base):
    __tablename__ = "user_missions"
    __table_args__ = (
        UniqueConstraint("user_id", "mission_id", "period"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    mission_id = Column(Integer, ForeignKey("missions.id", ondelete="CASCADE"))
    period = Column(String(32), nullable=False)
    progress = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="missions")
    mission = relationship("Mission", back_populates="user_missions")


class DuelStats(Base):
    __tablename__ = "duel_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    coins_won = Column(BigInteger, default=0)
    coins_lost = Column(BigInteger, default=0)
    win_streak = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="duel_stats")


class Duel(Base):
    __tablename__ = "duels"
    __table_args__ = (
        Index("ix_duels_group_id", "group_id"),
        Index("ix_duels_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, nullable=False)
    challenger_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    opponent_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    wager = Column(BigInteger, default=0)
    game_type = Column(String(32), default="dice")
    status = Column(String(16), default="pending")
    winner_id = Column(BigInteger, nullable=True)
    challenger_score = Column(Float, nullable=True)
    opponent_score = Column(Float, nullable=True)
    message_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    challenger = relationship("User", foreign_keys=[challenger_id])
    opponent = relationship("User", foreign_keys=[opponent_id])


class GameStats(Base):
    __tablename__ = "game_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    total_games = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    total_losses = Column(Integer, default=0)
    total_coins_bet = Column(BigInteger, default=0)
    total_coins_won = Column(BigInteger, default=0)
    dice_wins = Column(Integer, default=0)
    quiz_wins = Column(Integer, default=0)
    wheel_wins = Column(Integer, default=0)
    rps_wins = Column(Integer, default=0)
    mines_wins = Column(Integer, default=0)
    card_wins = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="game_stats")


class GameMatch(Base):
    __tablename__ = "game_matches"
    __table_args__ = (
        Index("ix_game_matches_group_id", "group_id"),
        Index("ix_game_matches_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, nullable=False)
    game_type = Column(String(32), nullable=False)
    player1_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    player2_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    wager = Column(BigInteger, default=0)
    winner_id = Column(BigInteger, nullable=True)
    data = Column(JSONB, nullable=True)
    status = Column(String(16), default="active")
    message_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    player1 = relationship("User", foreign_keys=[player1_id])
    player2 = relationship("User", foreign_keys=[player2_id])


class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    game_type = Column(String(32), nullable=False)
    type = Column(String(16), default="scheduled")
    status = Column(String(16), default="pending")
    max_players = Column(Integer, default=8)
    entry_fee = Column(BigInteger, default=0)
    prize_pool = Column(BigInteger, default=0)
    data = Column(JSONB, nullable=True)
    starts_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    participants = relationship("TournamentParticipant", back_populates="tournament")


class TournamentParticipant(Base):
    __tablename__ = "tournament_participants"
    __table_args__ = (
        UniqueConstraint("tournament_id", "user_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"))
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    score = Column(Integer, default=0)
    placement = Column(Integer, nullable=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    tournament = relationship("Tournament", back_populates="participants")
    user = relationship("User")


class Referral(Base):
    __tablename__ = "referrals"
    __table_args__ = (
        UniqueConstraint("referrer_id", "referred_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    referred_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    reward_given = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_made")
    referred = relationship("User", foreign_keys=[referred_id])


class GroupStats(Base):
    __tablename__ = "group_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"), unique=True)
    total_messages = Column(BigInteger, default=0)
    total_joins = Column(Integer, default=0)
    total_leaves = Column(Integer, default=0)
    total_bans = Column(Integer, default=0)
    peak_members = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    group = relationship("Group", back_populates="stats")


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"
    __table_args__ = (
        Index("ix_scheduled_posts_group_id", "group_id"),
        Index("ix_scheduled_posts_scheduled_at", "scheduled_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, nullable=False)
    content = Column(Text, nullable=True)
    media_type = Column(String(16), nullable=True)
    media_file_id = Column(String(256), nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(64), nullable=True)
    is_sent = Column(Boolean, default=False)
    created_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ShopItem(Base):
    __tablename__ = "shop_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False)
    name_key = Column(String(128), nullable=False)
    description_key = Column(String(256), nullable=True)
    category = Column(String(32), nullable=False)
    price = Column(Integer, nullable=False)
    icon = Column(String(8), nullable=True)
    is_active = Column(Boolean, default=True)

    purchases = relationship("UserShopItem", back_populates="item")


class UserShopItem(Base):
    __tablename__ = "user_shop_items"
    __table_args__ = (
        UniqueConstraint("user_id", "item_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    item_id = Column(Integer, ForeignKey("shop_items.id", ondelete="CASCADE"))
    quantity = Column(Integer, default=1)
    is_equipped = Column(Boolean, default=False)
    purchased_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    item = relationship("ShopItem", back_populates="purchases")


class CaptchaChallenge(Base):
    __tablename__ = "captcha_challenges"
    __table_args__ = (
        Index("ix_captcha_group_user", "group_id", "user_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    challenge_type = Column(String(16), nullable=False)
    answer = Column(String(64), nullable=True)
    message_id = Column(BigInteger, nullable=True)
    is_solved = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
