from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.models import Attendance, Group, Lesson, Student
from web.api.auth import current_telegram_id

router = APIRouter(prefix="/api/students", tags=["students"])


class StudentEdit(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    subgroup: int | None = Field(default=None, ge=1, le=2)
    status: str | None = Field(default=None, pattern="^(active|expelled|academic_leave)$")


async def admin_for(group_id: int, tg_id: int, db: AsyncSession) -> Student:
    actor = (
        await db.execute(
            select(Student).where(
                Student.telegram_id == tg_id,
                Student.group_id == group_id,
                Student.role.in_(("owner", "deputy")),
            )
        )
    ).scalar_one_or_none()
    if not actor:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Administrator permission required.")
    return actor


@router.get("/group/{group_id}")
async def roster(group_id: int, tg_id: int = Depends(current_telegram_id), db: AsyncSession = Depends(get_db)):
    # Verify membership
    member = (await db.execute(select(Student).where(Student.group_id == group_id, Student.telegram_id == tg_id))).scalar_one_or_none()
    if not member:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a member of this group.")

    users = (
        await db.execute(
            select(Student).where(Student.group_id == group_id).order_by(Student.subgroup, Student.last_name)
        )
    ).scalars().all()

    # Calculate absences and total lessons for each student
    group = await db.get(Group, group_id)
    threshold = group.absence_warning_threshold if group else 3

    lessons = (await db.execute(select(Lesson).where(Lesson.group_id == group_id))).scalars().all()
    attendances = (await db.execute(select(Attendance).join(Lesson).where(Lesson.group_id == group_id))).scalars().all()

    att_map = {(a.lesson_id, a.student_id) for a in attendances}

    result = []
    for u in users:
        applicable = [l for l in lessons if l.subgroup in (0, u.subgroup)]
        attended = sum(1 for l in applicable if (l.id, u.id) in att_map)
        absences = len(applicable) - attended
        rate = round((attended / len(applicable) * 100), 1) if applicable else 100.0

        result.append({
            "id": u.id,
            "telegram_id": u.telegram_id,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "middle_name": u.middle_name,
            "name": f"{u.last_name} {u.first_name}" + (f" {u.middle_name}" if u.middle_name else ""),
            "subgroup": u.subgroup,
            "role": u.role,
            "status": u.status,
            "classes_held": len(applicable),
            "absences": absences,
            "attendance_rate": rate,
            "at_risk": absences >= threshold and u.status == "active",
        })

    return result


@router.patch("/{student_id}")
async def edit_student(
    student_id: int,
    payload: StudentEdit,
    tg_id: int = Depends(current_telegram_id),
    db: AsyncSession = Depends(get_db),
):
    target = await db.get(Student, student_id)
    if not target:
        raise HTTPException(404, "Student not found.")
    await admin_for(target.group_id, tg_id, db)

    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(target, key, value)

    await db.commit()
    return {"status": "updated", "student_id": target.id}


@router.post("/{student_id}/set-deputy")
async def appoint_deputy(
    student_id: int,
    tg_id: int = Depends(current_telegram_id),
    db: AsyncSession = Depends(get_db),
):
    target = await db.get(Student, student_id)
    if not target or target.status != "active":
        raise HTTPException(404, "Active student not found.")

    actor = await admin_for(target.group_id, tg_id, db)
    if actor.role != "owner":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the Head Student can appoint a Deputy.")

    # Automatically demote any existing deputy
    await db.execute(
        update(Student)
        .where(Student.group_id == target.group_id, Student.role == "deputy")
        .values(role="student")
    )

    target.role = "deputy"
    await db.commit()
    return {
        "status": "success",
        "message": f"{target.first_name} {target.last_name} has been appointed as Deputy.",
    }


@router.delete("/attendance/{attendance_id}")
async def delete_attendance(
    attendance_id: int,
    tg_id: int = Depends(current_telegram_id),
    db: AsyncSession = Depends(get_db),
):
    """Fast Visual Audit: Head Student removes a rogue check-in entry."""
    att = await db.get(Attendance, attendance_id)
    if not att:
        raise HTTPException(404, "Attendance record not found.")

    lesson = await db.get(Lesson, att.lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found.")

    await admin_for(lesson.group_id, tg_id, db)

    await db.delete(att)
    await db.commit()
    return {"status": "deleted", "attendance_id": attendance_id}
