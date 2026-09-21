import secrets
from datetime import datetime, time, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.models import Lesson, ScheduleTemplate, Student, Subject
from web.api.auth import current_telegram_id

router = APIRouter(prefix="/api/schedule", tags=["schedule"])


class SubjectIn(BaseModel):
    group_id: int
    name: str = Field(min_length=1, max_length=255)
    teacher_name: str | None = None


class TemplateIn(BaseModel):
    group_id: int
    subject_id: int
    day_of_week: int = Field(ge=1, le=7)
    pair_number: int = Field(ge=1, le=8)
    start_time: str  # Format: "09:00"
    end_time: str    # Format: "10:35"
    subgroup: int = Field(default=0, ge=0, le=2)
    week_type: str = Field(default="all", pattern="^(all|numerator|denominator)$")
    classroom: str | None = None
    campus_latitude: float | None = None
    campus_longitude: float | None = None


class StartLesson(BaseModel):
    subject_id: int
    subgroup: int = Field(default=0, ge=0, le=2)
    geo_latitude: float | None = None
    geo_longitude: float | None = None


async def require_admin(group_id: int, tg_id: int, db: AsyncSession) -> Student:
    actor = (
        await db.execute(
            select(Student).where(
                Student.group_id == group_id,
                Student.telegram_id == tg_id,
                Student.role.in_(("owner", "deputy")),
            )
        )
    ).scalar_one_or_none()
    if not actor:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Administrator permission required.")
    return actor


@router.get("/groups/{group_id}/subjects")
async def list_subjects(group_id: int, tg_id: int = Depends(current_telegram_id), db: AsyncSession = Depends(get_db)):
    subjects = (
        await db.execute(
            select(Subject).where(Subject.group_id == group_id, Subject.is_active.is_(True)).order_by(Subject.name)
        )
    ).scalars().all()
    return [{"id": s.id, "name": s.name, "teacher_name": s.teacher_name} for s in subjects]


@router.post("/subjects")
async def add_subject(payload: SubjectIn, tg_id: int = Depends(current_telegram_id), db: AsyncSession = Depends(get_db)):
    await require_admin(payload.group_id, tg_id, db)
    item = Subject(group_id=payload.group_id, name=payload.name, teacher_name=payload.teacher_name)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": item.id, "name": item.name, "teacher_name": item.teacher_name}


@router.get("/groups/{group_id}/templates")
async def list_templates(group_id: int, tg_id: int = Depends(current_telegram_id), db: AsyncSession = Depends(get_db)):
    templates = (
        await db.execute(
            select(ScheduleTemplate, Subject.name.label("subject_name"), Subject.teacher_name)
            .join(Subject, ScheduleTemplate.subject_id == Subject.id)
            .where(ScheduleTemplate.group_id == group_id)
            .order_by(ScheduleTemplate.day_of_week, ScheduleTemplate.pair_number)
        )
    ).all()

    result = []
    for t, subj_name, teacher in templates:
        result.append({
            "id": t.id,
            "subject_id": t.subject_id,
            "subject_name": subj_name,
            "teacher_name": teacher,
            "day_of_week": t.day_of_week,
            "pair_number": t.pair_number,
            "start_time": t.start_time.strftime("%H:%M") if isinstance(t.start_time, time) else str(t.start_time),
            "end_time": t.end_time.strftime("%H:%M") if isinstance(t.end_time, time) else str(t.end_time),
            "subgroup": t.subgroup,
            "week_type": t.week_type,
            "classroom": t.classroom,
            "campus_latitude": t.campus_latitude,
            "campus_longitude": t.campus_longitude,
        })
    return result


@router.post("/templates")
async def add_template(payload: TemplateIn, tg_id: int = Depends(current_telegram_id), db: AsyncSession = Depends(get_db)):
    await require_admin(payload.group_id, tg_id, db)

    # Parse time strings
    st_parts = [int(p) for p in payload.start_time.split(":")]
    et_parts = [int(p) for p in payload.end_time.split(":")]
    start_t = time(hour=st_parts[0], minute=st_parts[1])
    end_t = time(hour=et_parts[0], minute=et_parts[1])

    item = ScheduleTemplate(
        group_id=payload.group_id,
        subject_id=payload.subject_id,
        day_of_week=payload.day_of_week,
        pair_number=payload.pair_number,
        start_time=start_t,
        end_time=end_t,
        subgroup=payload.subgroup,
        week_type=payload.week_type,
        classroom=payload.classroom,
        campus_latitude=payload.campus_latitude,
        campus_longitude=payload.campus_longitude,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": item.id, "status": "created"}


@router.get("/groups/{group_id}/active-lesson")
async def get_active_lesson(group_id: int, tg_id: int = Depends(current_telegram_id), db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Lesson, Subject.name.label("subject_name"), Subject.teacher_name)
        .join(Subject, Lesson.subject_id == Subject.id)
        .where(Lesson.group_id == group_id, Lesson.is_closed.is_(False))
        .order_by(Lesson.opened_at.desc())
    )
    active = (await db.execute(stmt)).first()
    if not active:
        return {"has_active": False}

    lesson, subj_name, teacher = active
    return {
        "has_active": True,
        "lesson": {
            "id": lesson.id,
            "subject_id": lesson.subject_id,
            "subject_name": subj_name,
            "teacher_name": teacher,
            "subgroup": lesson.subgroup,
            "opened_at": lesson.opened_at.isoformat() if lesson.opened_at else None,
            "geo_latitude": lesson.geo_latitude,
            "geo_longitude": lesson.geo_longitude,
        },
    }


@router.post("/groups/{group_id}/lessons")
async def start_lesson(
    group_id: int,
    payload: StartLesson,
    tg_id: int = Depends(current_telegram_id),
    db: AsyncSession = Depends(get_db),
):
    actor = await require_admin(group_id, tg_id, db)
    subject = await db.get(Subject, payload.subject_id)
    if not subject or subject.group_id != group_id:
        raise HTTPException(404, "Subject not found in this group.")

    # Close any currently active lesson in this group
    active_stmt = select(Lesson).where(Lesson.group_id == group_id, Lesson.is_closed.is_(False))
    active_lessons = (await db.execute(active_stmt)).scalars().all()
    for al in active_lessons:
        al.is_closed = True
        al.closed_at = datetime.now(timezone.utc)

    lesson = Lesson(
        group_id=group_id,
        subject_id=payload.subject_id,
        subgroup=payload.subgroup,
        created_by_student_id=actor.id,
        secret_salt=secrets.token_hex(32),
        geo_latitude=payload.geo_latitude,
        geo_longitude=payload.geo_longitude,
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return {"lesson_id": lesson.id, "presenter_url": f"/presenter/{lesson.id}"}


@router.post("/lessons/{lesson_id}/close")
async def close_lesson(lesson_id: int, tg_id: int = Depends(current_telegram_id), db: AsyncSession = Depends(get_db)):
    lesson = await db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found.")
    await require_admin(lesson.group_id, tg_id, db)
    lesson.is_closed = True
    lesson.closed_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "closed", "lesson_id": lesson.id}
