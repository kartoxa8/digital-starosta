from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.excel_builder import build_report
from core.models import Attendance, Group, Lesson, Student, Subject
from web.api.auth import current_telegram_id
from web.api.schedule import require_admin

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/group/{group_id}")
async def export(group_id: int, tg_id: int = Depends(current_telegram_id), db: AsyncSession = Depends(get_db)):
    await require_admin(group_id, tg_id, db)
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(404, "Group not found.")

    students = (await db.execute(select(Student).where(Student.group_id == group_id))).scalars().all()
    lessons = (await db.execute(select(Lesson).where(Lesson.group_id == group_id).order_by(Lesson.opened_at))).scalars().all()
    subjects = {x.id: x for x in (await db.execute(select(Subject).where(Subject.group_id == group_id))).scalars()}
    records = (await db.execute(select(Attendance).join(Lesson).where(Lesson.group_id == group_id))).scalars().all()

    excel_io = build_report(group, list(students), list(lessons), subjects, list(records))
    return StreamingResponse(
        excel_io,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="attendance-{group.name}.xlsx"'},
    )
