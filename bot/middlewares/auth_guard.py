from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update, User
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
        # Extract user across Update, Message, CallbackQuery or data context
        user: User | None = data.get("event_from_user")
        if not user:
            if isinstance(event, Update):
                if event.message:
                    user = event.message.from_user
                elif event.callback_query:
                    user = event.callback_query.from_user
            elif isinstance(event, (Message, CallbackQuery)):
                user = event.from_user
            else:
                user = getattr(event, "from_user", None)

        student: Student | None = None
        group: Group | None = None

        if user:
            async with SessionLocal() as db:
                stmt = select(Student).where(Student.telegram_id == user.id)
                student = (await db.execute(stmt)).scalar_one_or_none()

                if student:
                    group = await db.get(Group, student.group_id)

        # Always guarantee keys exist in handler kwargs
        data["current_student"] = student
        data["current_group"] = group

        return await handler(event, data)
