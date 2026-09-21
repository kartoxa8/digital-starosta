from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import get_settings
from core.database import get_db
from core.models import Attendance, Lesson, Student
from core.security import calculate_haversine_distance, verify_totp_token
from web.api.auth import current_telegram_id

router = APIRouter(prefix="/api/checkin", tags=["checkin"])
class CheckinPayload(BaseModel): lesson_id: int; token: str; window: int; latitude: float; longitude: float
@router.post("")
async def checkin(payload: CheckinPayload, tg_id: int = Depends(current_telegram_id), db: AsyncSession = Depends(get_db)):
    lesson = await db.get(Lesson, payload.lesson_id)
    if not lesson or lesson.is_closed: raise HTTPException(400, "Registration session is closed.")
    student = (await db.execute(select(Student).where(Student.telegram_id == tg_id, Student.group_id == lesson.group_id))).scalar_one_or_none()
    if not student or student.status != "active": raise HTTPException(403, "Student record is not active.")
    if lesson.subgroup and lesson.subgroup != student.subgroup: raise HTTPException(403, "Student belongs to another subgroup.")
    if not verify_totp_token(lesson.id, lesson.secret_salt, payload.token, payload.window): raise HTTPException(400, "QR code expired. Rescan the screen.")
    distance = 0.0
    if lesson.geo_latitude is not None and lesson.geo_longitude is not None:
        distance = calculate_haversine_distance(payload.latitude, payload.longitude, lesson.geo_latitude, lesson.geo_longitude)
        if distance > get_settings().checkin_radius_meters: raise HTTPException(403, f"Location verification failed: {int(distance)}m from classroom.")
    db.add(Attendance(lesson_id=lesson.id, student_id=student.id, latitude=payload.latitude, longitude=payload.longitude, distance_meters=distance))
    try: await db.commit()
    except IntegrityError: await db.rollback(); raise HTTPException(409, "Attendance already registered.")
    return {"status": "success", "distance_meters": round(distance), "student_name": f"{student.first_name} {student.last_name}"}
