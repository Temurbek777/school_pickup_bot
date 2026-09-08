from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserService


class UserSyncMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        user: User = data.get("event_from_user")
        db: AsyncSession = data.get("db")

        if user and db and not user.is_bot:
            user_service = UserService(db)
            await user_service.register_or_update_parent(
                telegram_id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                username=user.username
            )

        return await handler(event, data)