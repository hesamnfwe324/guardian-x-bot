from typing import Any, Awaitable, Callable, Dict
  from aiogram import BaseMiddleware
  from aiogram.types import TelegramObject, Message, CallbackQuery, Update
  from sqlalchemy.ext.asyncio import AsyncSession
  from sqlalchemy import select
  from bot.database.connection import async_session_maker
  from bot.database.models import User, Group, GroupMember, SecuritySettings
  import structlog

  logger = structlog.get_logger()


  class DatabaseMiddleware(BaseMiddleware):
      async def __call__(
          self,
          handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
          event: TelegramObject,
          data: Dict[str, Any],
      ) -> Any:
          handler_was_called = False
          try:
              async with async_session_maker() as session:
                  data["db_session"] = session

                  user = data.get("event_from_user")
                  if user and not user.is_bot:
                      try:
                          db_user = await self._get_or_create_user(session, user)
                          data["db_user"] = db_user
                      except Exception as e:
                          logger.warning("Could not get/create user in DB", error=str(e))

                  chat = None
                  if isinstance(event, Update):
                      if event.message:
                          chat = event.message.chat
                      elif event.callback_query and event.callback_query.message:
                          chat = event.callback_query.message.chat
                      elif event.chat_member:
                          chat = event.chat_member.chat
                      elif event.my_chat_member:
                          chat = event.my_chat_member.chat
                  elif isinstance(event, Message):
                      chat = event.chat
                  elif isinstance(event, CallbackQuery) and event.message:
                      chat = event.message.chat

                  if chat and chat.type in ("group", "supergroup"):
                      try:
                          db_group = await self._get_or_create_group(session, chat)
                          data["db_group"] = db_group

                          security = await session.scalar(
                              select(SecuritySettings).where(SecuritySettings.group_id == chat.id)
                          )
                          if not security:
                              security = SecuritySettings(group_id=chat.id)
                              session.add(security)
                              await session.commit()
                              await session.refresh(security)
                          data["group_security"] = security

                          if user and not user.is_bot:
                              member = await self._get_or_create_member(session, chat.id, user.id)
                              data["db_member"] = member
                      except Exception as e:
                          logger.warning("Could not load group data from DB", error=str(e))

                  handler_was_called = True
                  result = await handler(event, data)
                  await session.commit()
                  return result

          except Exception as err:
              if handler_was_called:
                  # خطا از handler بود نه از DB — دوباره اجرا نکن
                  raise
              # خطا از اتصال DB بود — بدون DB اجرا کن
              logger.error("DB session failed — running handler without DB", error=str(err))
              data["db_session"] = None
              data["db_user"] = None
              return await handler(event, data)

      async def _get_or_create_user(self, session: AsyncSession, tg_user) -> User:
          user = await session.get(User, tg_user.id)
          if not user:
              user = User(
                  id=tg_user.id,
                  username=tg_user.username,
                  first_name=tg_user.first_name or "User",
                  last_name=tg_user.last_name,
                  is_bot=tg_user.is_bot,
                  is_premium=getattr(tg_user, "is_premium", False) or False,
              )
              session.add(user)
              await session.flush()
          else:
              user.username = tg_user.username
              user.first_name = tg_user.first_name or "User"
              user.last_name = tg_user.last_name
              from datetime import datetime, timezone
              user.last_seen = datetime.now(timezone.utc)
          return user

      async def _get_or_create_group(self, session: AsyncSession, chat) -> Group:
          group = await session.get(Group, chat.id)
          if not group:
              group = Group(
                  id=chat.id,
                  title=chat.title or "Unknown",
                  username=chat.username,
                  type=chat.type,
              )
              session.add(group)
              await session.flush()
          else:
              group.title = chat.title or group.title
              group.username = chat.username
          return group

      async def _get_or_create_member(
          self, session: AsyncSession, group_id: int, user_id: int
      ) -> GroupMember:
          from sqlalchemy import and_
          member = await session.scalar(
              select(GroupMember).where(
                  and_(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
              )
          )
          if not member:
              member = GroupMember(group_id=group_id, user_id=user_id)
              session.add(member)
              await session.flush()
          return member
  