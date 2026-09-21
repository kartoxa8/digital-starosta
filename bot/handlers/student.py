from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from core.database import SessionLocal
from core.emojis import PremiumEmoji, emoji
from core.models import Attendance, Group, Lesson, Student

router = Router(name="student")


@router.message(Command("me"))
@router.message(Command("profile"))
async def cmd_profile(
    message: Message,
    current_student: Student | None = None,
    current_group: Group | None = None,
) -> None:
    if not current_student or not current_group:
        await message.answer("You are not registered in any academic group yet. Use /start to join.")
        return

    text = await build_student_profile_text(current_student, current_group)
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "student_profile")
async def callback_profile(
    callback: CallbackQuery,
    current_student: Student | None = None,
    current_group: Group | None = None,
) -> None:
    if not current_student or not current_group:
        await callback.answer("Registration not found.", show_alert=True)
        return

    text = await build_student_profile_text(current_student, current_group)
    if callback.message:
        await callback.message.answer(text, parse_mode=ParseMode.HTML)
    await callback.answer()


async def build_student_profile_text(student: Student, group: Group) -> str:
    async with SessionLocal() as db:
        # Lessons applicable to student's subgroup (0 or student.subgroup)
        lessons_stmt = (
            select(Lesson)
            .where(Lesson.group_id == group.id, Lesson.subgroup.in_((0, student.subgroup)))
        )
        applicable_lessons = (await db.execute(lessons_stmt)).scalars().all()
        applicable_ids = [l.id for l in applicable_lessons]

        attended_count = 0
        if applicable_ids:
            att_stmt = (
                select(Attendance)
                .where(Attendance.student_id == student.id, Attendance.lesson_id.in_(applicable_ids))
            )
            attended_records = (await db.execute(att_stmt)).scalars().all()
            attended_count = len(attended_records)

    total_held = len(applicable_lessons)
    absences = total_held - attended_count
    rate = (attended_count / total_held * 100) if total_held > 0 else 100.0

    profile_icon = emoji(PremiumEmoji.PROFILE)
    role_name = "Head Student (Starosta)" if student.role == "owner" else ("Deputy" if student.role == "deputy" else "Student")

    lines = [
        f"{profile_icon} <b>Student Profile</b>\n",
        f"Name: <b>{student.last_name} {student.first_name}</b>",
        f"Group: <b>{group.name}</b> ({group.university})",
        f"Subgroup: <b>{student.subgroup}</b> | Role: <b>{role_name}</b>",
        f"Status: <b>{student.status.capitalize()}</b>\n",
        f"• Classes Held for Subgroup: <b>{total_held}</b>",
        f"• Attended: <b>{attended_count}</b>",
        f"• Unexcused Absences: <b>{absences}</b>",
        f"• Attendance Rate: <b>{rate:.1f}%</b>",
    ]

    if absences >= group.absence_warning_threshold:
        alert_icon = emoji(PremiumEmoji.WARNING_ALERT)
        lines.append(f"\n{alert_icon} <b>Truancy Warning:</b> You have exceeded the absence threshold ({group.absence_warning_threshold}). Contact your Head Student.")

    return "\n".join(lines)
