import secrets
import string
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.models import Group, Student
from web.api.auth import current_telegram_id

router = APIRouter(prefix="/api/groups", tags=["groups"])


class CreateGroup(BaseModel):
    name: str = Field(max_length=50)
    university: str = Field(max_length=255)
    first_name: str
    last_name: str
    middle_name: str | None = None
    subgroup: int = Field(default=1, ge=1, le=2)


class JoinGroup(BaseModel):
    invite_code: str
    first_name: str
    last_name: str
    middle_name: str | None = None
    subgroup: int = Field(ge=1, le=2)


class UpdateGroupSettings(BaseModel):
    timezone: str | None = None
    absence_warning_threshold: int | None = Field(default=None, ge=1, le=20)


def generate_code() -> str:
    return "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))


async def get_admin_user(group_id: int, tg_id: int, db: AsyncSession) -> Student:
    user = (
        await db.execute(
            select(Student).where(
                Student.group_id == group_id,
                Student.telegram_id == tg_id,
                Student.role.in_(("owner", "deputy")),
            )
        )
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(403, "Administrator permission required.")
    return user


async def get_owner_user(group_id: int, tg_id: int, db: AsyncSession) -> Student:
    user = (
        await db.execute(
            select(Student).where(
                Student.group_id == group_id,
                Student.telegram_id == tg_id,
                Student.role == "owner",
            )
        )
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(403, "Owner permission required.")
    return user


@router.get("/me")
async def get_my_membership(tg_id: int = Depends(current_telegram_id), db: AsyncSession = Depends(get_db)):
    student = (await db.execute(select(Student).where(Student.telegram_id == tg_id))).scalar_one_or_none()
    if not student:
        return {"registered": False}
    group = await db.get(Group, student.group_id)
    return {
        "registered": True,
        "student": {
            "id": student.id,
            "telegram_id": student.telegram_id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "middle_name": student.middle_name,
            "role": student.role,
            "subgroup": student.subgroup,
            "status": student.status,
        },
        "group": {
            "id": group.id,
            "name": group.name,
            "university": group.university,
            "invite_code": group.invite_code,
            "timezone": group.timezone,
            "absence_warning_threshold": group.absence_warning_threshold,
        },
    }


@router.post("")
async def create_group(payload: CreateGroup, tg_id: int = Depends(current_telegram_id), db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(Student).where(Student.telegram_id == tg_id))).scalar_one_or_none()
    if existing:
        raise HTTPException(409, "Telegram account already belongs to a group.")

    invite = generate_code()
    while (await db.execute(select(Group.id).where(Group.invite_code == invite))).scalar_one_or_none():
        invite = generate_code()

    group = Group(name=payload.name, university=payload.university, invite_code=invite)
    db.add(group)
    await db.flush()

    student = Student(
        group_id=group.id,
        telegram_id=tg_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        middle_name=payload.middle_name,
        subgroup=payload.subgroup,
        role="owner",
    )
    db.add(student)
    await db.commit()

    return {"id": group.id, "name": group.name, "invite_code": invite}


@router.post("/join")
async def join_group(payload: JoinGroup, tg_id: int = Depends(current_telegram_id), db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(Student).where(Student.telegram_id == tg_id))).scalar_one_or_none()
    if existing:
        raise HTTPException(409, "Telegram account already belongs to a group.")

    group = (await db.execute(select(Group).where(Group.invite_code == payload.invite_code.upper()))).scalar_one_or_none()
    if not group:
        raise HTTPException(404, "Invalid invite code.")

    student = Student(
        group_id=group.id,
        telegram_id=tg_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        middle_name=payload.middle_name,
        subgroup=payload.subgroup,
        role="student",
    )
    db.add(student)
    await db.commit()

    return {"group_id": group.id, "group_name": group.name}


@router.get("/{group_id}")
async def get_group(group_id: int, tg_id: int = Depends(current_telegram_id), db: AsyncSession = Depends(get_db)):
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(404, "Group not found.")
    return {
        "id": group.id,
        "name": group.name,
        "university": group.university,
        "invite_code": group.invite_code,
        "timezone": group.timezone,
        "absence_warning_threshold": group.absence_warning_threshold,
    }


@router.patch("/{group_id}")
async def update_group_settings(
    group_id: int,
    payload: UpdateGroupSettings,
    tg_id: int = Depends(current_telegram_id),
    db: AsyncSession = Depends(get_db),
):
    await get_admin_user(group_id, tg_id, db)
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(404, "Group not found.")

    if payload.timezone is not None:
        group.timezone = payload.timezone
    if payload.absence_warning_threshold is not None:
        group.absence_warning_threshold = payload.absence_warning_threshold

    await db.commit()
    return {"status": "success", "timezone": group.timezone, "threshold": group.absence_warning_threshold}


@router.post("/{group_id}/regenerate-code")
async def regenerate_code(group_id: int, tg_id: int = Depends(current_telegram_id), db: AsyncSession = Depends(get_db)):
    await get_owner_user(group_id, tg_id, db)
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(404, "Group not found.")

    invite = generate_code()
    while (await db.execute(select(Group.id).where(Group.invite_code == invite))).scalar_one_or_none():
        invite = generate_code()

    group.invite_code = invite
    await db.commit()
    return {"invite_code": group.invite_code}
