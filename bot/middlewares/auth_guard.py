from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from sqlalchemy import select
from core.database import SessionLocal
from core.models import Group, Student


class AuthGuardMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user: User | None = getattr(event, "from_user", None)
        if not user:
            return await handler(event, data)

        async with SessionLocal() as db:
            stmt = select(Student).where(Student.telegram_id == user.id)
            student = (await db.execute(stmt)).scalar_one_or_none()

            group = None
            if student:
                group = await db.get(Group, student.group_id)

            data["current_student"] = student
            data["current_group"] = group

        return await handler(event, data)
