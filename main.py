import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from aiogram import Bot, Dispatcher
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from core.config import get_settings
from core.database import SessionLocal, engine
from core.models import Attendance, Base, Lesson, Student
from core.security import generate_totp_token
from bot.handlers import main_router
from bot.middlewares.auth_guard import AuthGuardMiddleware
from web.api import checkin, export, groups, schedule, students

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("digital_starosta")
ROOT = Path(__file__).parent

bot: Bot | None = None
dp: Dispatcher | None = None
bot_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global bot, dp, bot_task
    # Initialize database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Launch aiogram bot background polling if configured
    settings = get_settings()
    if settings.bot_token and settings.bot_token.strip() and settings.bot_token != "replace-me":
        try:
            bot = Bot(token=settings.bot_token)
            dp = Dispatcher()
            dp.update.middleware(AuthGuardMiddleware())
            dp.include_router(main_router)
            bot_task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))
            logger.info("Telegram Bot polling started successfully.")
        except Exception as e:
            logger.error(f"Failed to start Telegram Bot: {e}")
    else:
        logger.warning(
            "BOT_TOKEN is empty or placeholder ('replace-me'). "
            "Running FastAPI web server without active Telegram bot polling."
        )

    yield

    # Graceful shutdown
    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass
    if bot:
        await bot.session.close()


app = FastAPI(title="Digital Starosta", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=ROOT / "web/static"), name="static")

for router in (groups.router, students.router, schedule.router, checkin.router, export.router):
    app.include_router(router)


@app.get("/")
async def mini_app():
    return FileResponse(ROOT / "web/templates/index.html")


@app.get("/presenter/{lesson_id}")
async def presenter_view(lesson_id: int):
    return FileResponse(ROOT / "web/static/presenter.html")


@app.get("/api/presenter/{lesson_id}")
async def presenter_token(lesson_id: int):
    async with SessionLocal() as db:
        lesson = await db.get(Lesson, lesson_id)
        if not lesson or lesson.is_closed:
            return {"closed": True}
        token, window = generate_totp_token(lesson.id, lesson.secret_salt)
        count = (
            await db.execute(
                select(func.count(Attendance.id)).where(Attendance.lesson_id == lesson_id)
            )
        ).scalar_one()
        return {
            "lesson_id": lesson_id,
            "token": token,
            "window": window,
            "count": count,
            "closed": False,
        }


@app.get("/api/presenter/{lesson_id}/attendees")
async def presenter_attendees(lesson_id: int):
    async with SessionLocal() as db:
        stmt = (
            select(Attendance, Student.first_name, Student.last_name, Student.subgroup)
            .join(Student, Attendance.student_id == Student.id)
            .where(Attendance.lesson_id == lesson_id)
            .order_by(Attendance.scanned_at.desc())
        )
        records = (await db.execute(stmt)).all()
        return [
            {
                "id": a.id,
                "student_name": f"{last} {first}",
                "subgroup": sg,
                "scanned_at": a.scanned_at.strftime("%H:%M:%S") if a.scanned_at else "",
                "distance_meters": round(a.distance_meters) if a.distance_meters is not None else None,
            }
            for a, first, last, sg in records
        ]


@app.delete("/api/presenter/{lesson_id}/attendees/{attendance_id}")
async def delete_presenter_attendee(lesson_id: int, attendance_id: int):
    async with SessionLocal() as db:
        att = await db.get(Attendance, attendance_id)
        if not att or att.lesson_id != lesson_id:
            return JSONResponse(status_code=404, content={"detail": "Attendance record not found"})
        await db.delete(att)
        await db.commit()
        return {"status": "deleted", "attendance_id": attendance_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
