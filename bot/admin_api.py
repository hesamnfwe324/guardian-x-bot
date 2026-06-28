import json
import os
from datetime import datetime, timedelta
from aiohttp import web
from sqlalchemy import select, func, and_, or_, desc, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import User, Group, GroupMember, Wallet, Economy, ActionLog
from bot.database.connection import async_session_maker

ADMIN_KEY = os.environ.get("ADMIN_KEY", "")


def require_admin(handler):
    async def wrapper(request):
        key = request.headers.get("X-Admin-Key", "")
        if not ADMIN_KEY or key != ADMIN_KEY:
            return web.json_response({"error": "Unauthorized"}, status=401)
        return await handler(request)
    wrapper.__name__ = handler.__name__
    return wrapper


def _user_to_dict(user, wallet=None, economy=None):
    return {
        "id": str(user.id),
        "username": user.username,
        "firstName": user.first_name,
        "lastName": user.last_name,
        "isBanned": user.is_banned,
        "isPremium": user.is_premium,
        "language": user.language,
        "balance": wallet.balance if wallet else None,
        "xp": economy.total_xp if economy else None,
        "level": economy.level if economy else None,
        "createdAt": user.created_at.isoformat() if user.created_at else None,
        "lastSeen": user.last_seen.isoformat() if user.last_seen else None,
    }


def _group_to_dict(group):
    return {
        "id": str(group.id),
        "title": group.title,
        "username": group.username,
        "type": group.type,
        "isActive": group.is_active,
        "memberCount": group.member_count,
        "language": group.language,
        "createdAt": group.created_at.isoformat() if group.created_at else None,
    }


@require_admin
async def stats_handler(request):
    try:
        async with async_session_maker() as session:
            today = datetime.utcnow() - timedelta(hours=24)

            total_users = await session.scalar(select(func.count()).select_from(User))
            active_today = await session.scalar(
                select(func.count()).select_from(User).where(User.last_seen >= today)
            )
            total_groups = await session.scalar(select(func.count()).select_from(Group))
            banned_users = await session.scalar(
                select(func.count()).select_from(User).where(User.is_banned == True)
            )
            total_messages = await session.scalar(
                select(func.sum(GroupMember.message_count)).select_from(GroupMember)
            ) or 0
            economy_total = await session.scalar(
                select(func.sum(Wallet.balance)).select_from(Wallet)
            ) or 0
            games_played = await session.scalar(
                select(func.count()).select_from(ActionLog).where(ActionLog.action.like("game_%"))
            ) or 0

            return web.json_response({
                "totalUsers": total_users or 0,
                "activeToday": active_today or 0,
                "totalGroups": total_groups or 0,
                "totalMessages": int(total_messages),
                "bannedUsers": banned_users or 0,
                "economyTotal": int(economy_total),
                "gamesPlayed": int(games_played),
                "botUptime": None,
            })
    except Exception as e:
        return web.json_response({
            "totalUsers": 0, "activeToday": 0, "totalGroups": 0,
            "totalMessages": 0, "bannedUsers": 0, "economyTotal": 0,
            "gamesPlayed": 0, "botUptime": None,
        })


@require_admin
async def users_handler(request):
    try:
        page = int(request.rel_url.query.get("page", 1))
        limit = min(int(request.rel_url.query.get("limit", 20)), 100)
        search = request.rel_url.query.get("search", "")
        banned_filter = request.rel_url.query.get("banned", "")
        offset = (page - 1) * limit

        async with async_session_maker() as session:
            query = select(User)
            count_query = select(func.count()).select_from(User)

            if search:
                like = f"%{search}%"
                cond = or_(
                    User.username.ilike(like),
                    User.first_name.ilike(like),
                    cast(User.id, String).contains(search),
                )
                query = query.where(cond)
                count_query = count_query.where(cond)

            if banned_filter == "true":
                query = query.where(User.is_banned == True)
                count_query = count_query.where(User.is_banned == True)
            elif banned_filter == "false":
                query = query.where(User.is_banned == False)
                count_query = count_query.where(User.is_banned == False)

            total = await session.scalar(count_query)
            result = await session.execute(
                query.order_by(desc(User.last_seen)).offset(offset).limit(limit)
            )
            users = result.scalars().all()

            user_ids = [u.id for u in users]
            wallets = {}
            economies = {}
            if user_ids:
                w_res = await session.execute(select(Wallet).where(Wallet.user_id.in_(user_ids)))
                for w in w_res.scalars():
                    wallets[w.user_id] = w
                e_res = await session.execute(select(Economy).where(Economy.user_id.in_(user_ids)))
                for e in e_res.scalars():
                    economies[e.user_id] = e

            return web.json_response({
                "users": [_user_to_dict(u, wallets.get(u.id), economies.get(u.id)) for u in users],
                "total": total or 0,
                "page": page,
                "limit": limit,
            })
    except Exception as e:
        return web.json_response({"users": [], "total": 0, "page": 1, "limit": 20})


@require_admin
async def ban_user_handler(request):
    try:
        user_id = int(request.match_info["user_id"])
        body = await request.json()
        reason = body.get("reason", "Admin action")
        async with async_session_maker() as session:
            user = await session.get(User, user_id)
            if not user:
                return web.json_response({"success": False, "message": "User not found"}, status=404)
            user.is_banned = True
            await session.commit()
        return web.json_response({"success": True, "message": f"User {user_id} banned"})
    except Exception as e:
        return web.json_response({"success": False, "message": str(e)}, status=500)


@require_admin
async def unban_user_handler(request):
    try:
        user_id = int(request.match_info["user_id"])
        async with async_session_maker() as session:
            user = await session.get(User, user_id)
            if not user:
                return web.json_response({"success": False, "message": "User not found"}, status=404)
            user.is_banned = False
            await session.commit()
        return web.json_response({"success": True, "message": f"User {user_id} unbanned"})
    except Exception as e:
        return web.json_response({"success": False, "message": str(e)}, status=500)


@require_admin
async def groups_handler(request):
    try:
        page = int(request.rel_url.query.get("page", 1))
        limit = min(int(request.rel_url.query.get("limit", 20)), 100)
        search = request.rel_url.query.get("search", "")
        offset = (page - 1) * limit

        async with async_session_maker() as session:
            query = select(Group)
            count_query = select(func.count()).select_from(Group)
            if search:
                like = f"%{search}%"
                cond = or_(Group.title.ilike(like), Group.username.ilike(like))
                query = query.where(cond)
                count_query = count_query.where(cond)

            total = await session.scalar(count_query)
            result = await session.execute(
                query.order_by(desc(Group.created_at)).offset(offset).limit(limit)
            )
            groups = result.scalars().all()
            return web.json_response({
                "groups": [_group_to_dict(g) for g in groups],
                "total": total or 0,
                "page": page,
                "limit": limit,
            })
    except Exception as e:
        return web.json_response({"groups": [], "total": 0, "page": 1, "limit": 20})


@require_admin
async def economy_leaderboard_handler(request):
    try:
        limit = min(int(request.rel_url.query.get("limit", 20)), 100)
        async with async_session_maker() as session:
            result = await session.execute(
                select(User, Wallet, Economy)
                .join(Wallet, Wallet.user_id == User.id)
                .outerjoin(Economy, Economy.user_id == User.id)
                .order_by(desc(Wallet.balance))
                .limit(limit)
            )
            rows = result.all()
            data = []
            for user, wallet, economy in rows:
                data.append({
                    "userId": str(user.id),
                    "username": user.username,
                    "firstName": user.first_name,
                    "balance": wallet.balance if wallet else 0,
                    "level": economy.level if economy else 1,
                    "xp": economy.total_xp if economy else 0,
                })
            return web.json_response(data)
    except Exception as e:
        return web.json_response([])


@require_admin
async def logs_handler(request):
    try:
        page = int(request.rel_url.query.get("page", 1))
        limit = min(int(request.rel_url.query.get("limit", 50)), 200)
        group_id = request.rel_url.query.get("group_id", "")
        action = request.rel_url.query.get("action", "")
        offset = (page - 1) * limit

        async with async_session_maker() as session:
            query = select(ActionLog)
            count_query = select(func.count()).select_from(ActionLog)
            if group_id:
                query = query.where(ActionLog.group_id == int(group_id))
                count_query = count_query.where(ActionLog.group_id == int(group_id))
            if action:
                query = query.where(ActionLog.action == action)
                count_query = count_query.where(ActionLog.action == action)

            total = await session.scalar(count_query)
            result = await session.execute(
                query.order_by(desc(ActionLog.created_at)).offset(offset).limit(limit)
            )
            logs = result.scalars().all()
            log_list = []
            for log in logs:
                details = log.details or {}
                log_list.append({
                    "id": log.id,
                    "action": log.action,
                    "performedBy": str(log.admin_id) if log.admin_id else "system",
                    "targetId": str(log.user_id) if log.user_id else "",
                    "groupId": str(log.group_id) if log.group_id else "",
                    "reason": details.get("reason") if isinstance(details, dict) else None,
                    "details": str(details) if details else None,
                    "createdAt": log.created_at.isoformat() if log.created_at else None,
                })
            return web.json_response({
                "logs": log_list,
                "total": total or 0,
                "page": page,
                "limit": limit,
            })
    except Exception as e:
        return web.json_response({"logs": [], "total": 0, "page": 1, "limit": 50})


@require_admin
async def broadcast_handler(request):
    try:
        body = await request.json()
        message_text = body.get("message", "")
        parse_mode = body.get("parseMode", "HTML")
        if not message_text:
            return web.json_response({"sent": 0, "failed": 0, "total": 0})

        from bot.config import settings
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode as AiogramParseMode

        bot = Bot(
            token=settings.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=AiogramParseMode.HTML),
        )
        async with async_session_maker() as session:
            result = await session.execute(
                select(Group.id).where(Group.is_active == True)
            )
            group_ids = result.scalars().all()

        sent = 0
        failed = 0
        for gid in group_ids:
            try:
                await bot.send_message(gid, message_text)
                sent += 1
            except Exception:
                failed += 1
        await bot.session.close()
        return web.json_response({"sent": sent, "failed": failed, "total": len(group_ids)})
    except Exception as e:
        return web.json_response({"sent": 0, "failed": 0, "total": 0}, status=500)




@require_admin
async def twa_profile_handler(request):
    try:
        user_id = int(request.rel_url.query.get("userId", 0))
        async with async_session_maker() as session:
            from sqlalchemy import select, func, desc
            user = await session.get(User, user_id)
            if not user:
                return web.json_response({"error": "User not found"}, status=404)
            wallet_res = await session.execute(select(Wallet).where(Wallet.user_id == user_id))
            wallet = wallet_res.scalar_one_or_none()
            econ_res = await session.execute(select(Economy).where(Economy.user_id == user_id))
            economy = econ_res.scalar_one_or_none()
            # Get rank
            rank_res = await session.scalar(
                select(func.count()).select_from(Wallet).where(
                    Wallet.balance > (wallet.balance if wallet else 0)
                )
            )
            rank = (rank_res or 0) + 1
            # Daily/weekly availability
            now = datetime.utcnow()
            daily_avail = True
            weekly_avail = True
            if wallet:
                if wallet.last_daily and (now - wallet.last_daily.replace(tzinfo=None)).total_seconds() < 86400:
                    daily_avail = False
                if wallet.last_weekly and (now - wallet.last_weekly.replace(tzinfo=None)).total_seconds() < 7 * 86400:
                    weekly_avail = False
            return web.json_response({
                "userId": str(user.id),
                "username": user.username,
                "firstName": user.first_name,
                "lastName": user.last_name,
                "balance": wallet.balance if wallet else 0,
                "bankBalance": wallet.bank_balance if wallet else 0,
                "level": economy.level if economy else 1,
                "xp": economy.xp if economy else 0,
                "totalXp": economy.total_xp if economy else 0,
                "rank": rank,
                "isPremium": user.is_premium,
                "isBanned": user.is_banned,
                "language": user.language,
                "dailyAvailable": daily_avail,
                "weeklyAvailable": weekly_avail,
                "streakDays": economy.streak_days if economy else 0,
                "referralCount": economy.referral_count if economy else 0,
                "createdAt": user.created_at.isoformat() if user.created_at else None,
            })
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


@require_admin
async def twa_leaderboard_handler(request):
    try:
        limit = min(int(request.rel_url.query.get("limit", 20)), 50)
        async with async_session_maker() as session:
            from sqlalchemy import select, desc
            result = await session.execute(
                select(User, Wallet, Economy)
                .join(Wallet, Wallet.user_id == User.id)
                .outerjoin(Economy, Economy.user_id == User.id)
                .order_by(desc(Wallet.balance))
                .limit(limit)
            )
            rows = result.all()
            data = []
            for i, (user, wallet, economy) in enumerate(rows):
                data.append({
                    "rank": i + 1,
                    "userId": str(user.id),
                    "username": user.username,
                    "firstName": user.first_name,
                    "balance": wallet.balance if wallet else 0,
                    "level": economy.level if economy else 1,
                    "xp": economy.total_xp if economy else 0,
                    "isPremium": user.is_premium,
                })
            return web.json_response(data)
    except Exception as e:
        return web.json_response([])


@require_admin
async def twa_claim_handler(request):
    try:
        body = await request.json()
        user_id = int(body.get("userId", 0))
        claim_type = body.get("type", "daily")
        async with async_session_maker() as session:
            wallet_res = await session.execute(select(Wallet).where(Wallet.user_id == user_id))
            wallet = wallet_res.scalar_one_or_none()
            if not wallet:
                return web.json_response({"success": False, "message": "User not found in bot", "amount": 0, "nextAvailableAt": None})
            now = datetime.utcnow()
            from bot.config import settings
            if claim_type == "weekly":
                if wallet.last_weekly and (now - wallet.last_weekly.replace(tzinfo=None)).total_seconds() < 7 * 86400:
                    next_at = (wallet.last_weekly.replace(tzinfo=None) + __import__('datetime').timedelta(days=7)).isoformat()
                    return web.json_response({"success": False, "message": "Weekly reward not available yet", "amount": 0, "nextAvailableAt": next_at})
                amount = settings.WEEKLY_REWARD
                wallet.balance += amount
                wallet.last_weekly = now
            else:
                if wallet.last_daily and (now - wallet.last_daily.replace(tzinfo=None)).total_seconds() < 86400:
                    next_at = (wallet.last_daily.replace(tzinfo=None) + __import__('datetime').timedelta(days=1)).isoformat()
                    return web.json_response({"success": False, "message": "Daily reward not available yet", "amount": 0, "nextAvailableAt": next_at})
                amount = settings.DAILY_REWARD
                wallet.balance += amount
                wallet.last_daily = now
            await session.commit()
            next_at = (now + __import__('datetime').timedelta(days=7 if claim_type == "weekly" else 1)).isoformat()
            return web.json_response({"success": True, "message": f"{'Weekly' if claim_type == 'weekly' else 'Daily'} reward claimed! +{amount} coins", "amount": amount, "nextAvailableAt": next_at})
    except Exception as e:
        return web.json_response({"success": False, "message": str(e), "amount": 0, "nextAvailableAt": None}, status=500)


@require_admin
async def twa_game_stats_handler(request):
    try:
        user_id = int(request.rel_url.query.get("userId", 0))
        async with async_session_maker() as session:
            from bot.database.models import DuelStats, GameStats as GameStatsModel
            try:
                duel_res = await session.execute(select(DuelStats).where(DuelStats.user_id == user_id))
                duel = duel_res.scalar_one_or_none()
                game_res = await session.execute(select(GameStatsModel).where(GameStatsModel.user_id == user_id))
                game = game_res.scalar_one_or_none()
                won = duel.wins if duel else 0
                lost = duel.losses if duel else 0
                total = won + lost
                return web.json_response({
                    "userId": str(user_id),
                    "duelsWon": won,
                    "duelsLost": lost,
                    "gamesPlayed": game.total_games if game else 0,
                    "totalWinnings": duel.total_won if duel else 0,
                    "winRate": round(won / total * 100, 1) if total > 0 else 0,
                })
            except Exception:
                return web.json_response({"userId": str(user_id), "duelsWon": 0, "duelsLost": 0, "gamesPlayed": 0, "totalWinnings": 0, "winRate": 0})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

def setup_admin_routes(app):
    app.router.add_get("/admin/stats", stats_handler)
    app.router.add_get("/admin/users", users_handler)
    app.router.add_post("/admin/users/{user_id}/ban", ban_user_handler)
    app.router.add_post("/admin/users/{user_id}/unban", unban_user_handler)
    app.router.add_get("/admin/groups", groups_handler)
    app.router.add_get("/admin/economy/leaderboard", economy_leaderboard_handler)
    app.router.add_get("/admin/logs", logs_handler)
    app.router.add_post("/admin/broadcast", broadcast_handler)
    app.router.add_get("/admin/twa/profile", twa_profile_handler)
    app.router.add_get("/admin/twa/leaderboard", twa_leaderboard_handler)
    app.router.add_post("/admin/twa/claim", twa_claim_handler)
    app.router.add_get("/admin/twa/game-stats", twa_game_stats_handler)
