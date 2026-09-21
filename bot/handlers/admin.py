import secrets
from datetime import datetime, timezone
from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy import func, select
from core.config import get_settings
from core.database import SessionLocal
from core.emojis import PremiumEmoji, emoji
from core.excel_builder import build_report
from core.models import Attendance, Group, Lesson, Student, Subject
from bot.keyboards.admin_kb import get_admin_dashboard_kb, get_session_select_kb

router = Router(name="admin")


def require_admin(student: Student | None) -> bool:
    return bool(student and student.role in ("owner", "deputy"))


@router.message(Command("admin"))
async def cmd_admin(message: Message, current_student: Student | None, current_group: Group | None) -> None:
    if not require_admin(current_student) or not current_group:
        await message.answer("Access restricted to Head Students and Deputies.")
        return

    settings = get_settings()
    active_lesson_id = None
    async with SessionLocal() as db:
        stmt = (
            select(Lesson.id)
            .where(Lesson.group_id == current_group.id, Lesson.is_closed.is_(False))
            .order_by(Lesson.opened_at.desc())
        )
        active_lesson_id = (await db.execute(stmt)).scalar_one_or_none()

    icon = emoji(PremiumEmoji.CAMPUS_HOME)
    text = (
        f"{icon} <b>Control Panel — {current_group.name}</b>\n\n"
        f"Invite code: <code>{current_group.invite_code}</code>\n"
        f"Active Session: <b>{'YES' if active_lesson_id else 'None'}</b>\n\n"
        f"Select an action below:"
    )
    kb = get_admin_dashboard_kb(current_group.id, settings.webapp_base_url, active_lesson_id)
    await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.message(Command("session"))
async def cmd_session(message: Message, current_student: Student | None, current_group: Group | None) -> None:
    if not require_admin(current_student) or not current_group:
        await message.answer("Access restricted.")
        return

    async with SessionLocal() as db:
        subjects_stmt = select(Subject).where(Subject.group_id == current_group.id, Subject.is_active.is_(True))
        subjects = (await db.execute(subjects_stmt)).scalars().all()

    if not subjects:
        await message.answer(
            "No subjects defined yet. Add subjects in the Mini App schedule builder first.",
            parse_mode=ParseMode.HTML,
        )
        return

    icon = emoji(PremiumEmoji.TIME_CLOCK)
    text = f"{icon} <b>Launch Attendance Session</b>\n\nChoose the subject and target audience:"
    kb = get_session_select_kb(current_group.id, [(s.id, s.name) for s in subjects])
    await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.message(Command("close"))
async def cmd_close(message: Message, current_student: Student | None, current_group: Group | None) -> None:
    if not require_admin(current_student) or not current_group:
        await message.answer("Access restricted.")
        return

    async with SessionLocal() as db:
        stmt = select(Lesson).where(Lesson.group_id == current_group.id, Lesson.is_closed.is_(False))
        active_lesson = (await db.execute(stmt)).scalar_one_or_none()
        if not active_lesson:
            await message.answer("There is no active attendance session to close.")
            return

        active_lesson.is_closed = True
        active_lesson.closed_at = datetime.now(timezone.utc)
        await db.commit()

    lock_icon = emoji(PremiumEmoji.LOCK_CLOSE)
    await message.answer(f"{lock_icon} Active attendance session #{active_lesson.id} has been closed.", parse_mode=ParseMode.HTML)


@router.message(Command("roster"))
async def cmd_roster(message: Message, current_student: Student | None, current_group: Group | None) -> None:
    if not require_admin(current_student) or not current_group:
        await message.answer("Access restricted.")
        return

    async with SessionLocal() as db:
        stmt = select(Student).where(Student.group_id == current_group.id).order_by(Student.subgroup, Student.last_name)
        students = (await db.execute(stmt)).scalars().all()

    sg1 = [s for s in students if s.subgroup == 1]
    sg2 = [s for s in students if s.subgroup == 2]

    users_icon = emoji(PremiumEmoji.STUDENTS_GROUP)
    lines = [f"{users_icon} <b>Group Roster — {current_group.name}</b>\n"]

    lines.append("<b>Subgroup 1:</b>")
    if sg1:
        for s in sg1:
            badge = " (Head)" if s.role == "owner" else (" (Deputy)" if s.role == "deputy" else "")
            status_tag = f" [{s.status}]" if s.status != "active" else ""
            lines.append(f"• {s.last_name} {s.first_name}{badge}{status_tag}")
    else:
        lines.append("<i>No students in Subgroup 1</i>")

    lines.append("\n<b>Subgroup 2:</b>")
    if sg2:
        for s in sg2:
            badge = " (Head)" if s.role == "owner" else (" (Deputy)" if s.role == "deputy" else "")
            status_tag = f" [{s.status}]" if s.status != "active" else ""
            lines.append(f"• {s.last_name} {s.first_name}{badge}{status_tag}")
    else:
        lines.append("<i>No students in Subgroup 2</i>")

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)


@router.message(Command("stats"))
async def cmd_stats(message: Message, current_student: Student | None, current_group: Group | None) -> None:
    if not require_admin(current_student) or not current_group:
        await message.answer("Access restricted.")
        return

    async with SessionLocal() as db:
        total_students = (await db.execute(select(func.count(Student.id)).where(Student.group_id == current_group.id, Student.status == "active"))).scalar_one()
        total_lessons = (await db.execute(select(func.count(Lesson.id)).where(Lesson.group_id == current_group.id))).scalar_one()
        total_attendances = (await db.execute(select(func.count(Attendance.id)).join(Lesson).where(Lesson.group_id == current_group.id))).scalar_one()

    stat_icon = emoji(PremiumEmoji.STATISTICS)
    text = (
        f"{stat_icon} <b>Attendance Overview — {current_group.name}</b>\n\n"
        f"• Active Students: <b>{total_students}</b>\n"
        f"• Classes Conducted: <b>{total_lessons}</b>\n"
        f"• Total Verified Check-ins: <b>{total_attendances}</b>\n"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(Command("report"))
async def cmd_report(message: Message, current_student: Student | None, current_group: Group | None) -> None:
    if not require_admin(current_student) or not current_group:
        await message.answer("Access restricted.")
        return
    await generate_and_send_excel(message, current_group)


# Callback Query Handlers
@router.callback_query(F.data.startswith("export_excel:"))
async def callback_export_excel(callback: CallbackQuery, current_student: Student | None, current_group: Group | None) -> None:
    if not require_admin(current_student) or not current_group:
        await callback.answer("Access denied.", show_alert=True)
        return
    await callback.answer("Generating spreadsheet...")
    if callback.message:
        await generate_and_send_excel(callback.message, current_group)


@router.callback_query(F.data.startswith("close_lesson:"))
async def callback_close_lesson(callback: CallbackQuery, current_student: Student | None, current_group: Group | None) -> None:
    if not require_admin(current_student) or not current_group:
        await callback.answer("Access denied.", show_alert=True)
        return

    lesson_id = int(callback.data.split(":")[1])
    async with SessionLocal() as db:
        lesson = await db.get(Lesson, lesson_id)
        if lesson and not lesson.is_closed:
            lesson.is_closed = True
            lesson.closed_at = datetime.now(timezone.utc)
            await db.commit()

    await callback.answer("Session closed.", show_alert=True)
    if callback.message:
        settings = get_settings()
        kb = get_admin_dashboard_kb(current_group.id, settings.webapp_base_url, None)
        await callback.message.edit_reply_markup(reply_markup=kb)


@router.callback_query(F.data.startswith("start_session_prompt:"))
async def callback_start_prompt(callback: CallbackQuery, current_student: Student | None, current_group: Group | None) -> None:
    if not require_admin(current_student) or not current_group:
        await callback.answer("Access denied.", show_alert=True)
        return

    async with SessionLocal() as db:
        subjects_stmt = select(Subject).where(Subject.group_id == current_group.id, Subject.is_active.is_(True))
        subjects = (await db.execute(subjects_stmt)).scalars().all()

    if not subjects:
        await callback.answer("No subjects found. Add subjects in the Mini App first.", show_alert=True)
        return

    icon = emoji(PremiumEmoji.TIME_CLOCK)
    kb = get_session_select_kb(current_group.id, [(s.id, s.name) for s in subjects])
    if callback.message:
        await callback.message.edit_text(
            f"{icon} <b>Launch Attendance Session</b>\n\nChoose the subject and target audience:",
            reply_markup=kb,
            parse_mode=ParseMode.HTML,
        )
    await callback.answer()


@router.callback_query(F.data.startswith("launch_lesson:"))
async def callback_launch_lesson(callback: CallbackQuery, current_student: Student | None, current_group: Group | None) -> None:
    if not require_admin(current_student) or not current_group:
        await callback.answer("Access denied.", show_alert=True)
        return

    parts = callback.data.split(":")
    group_id, subject_id, subgroup = int(parts[1]), int(parts[2]), int(parts[3])

    async with SessionLocal() as db:
        subject = await db.get(Subject, subject_id)
        if not subject:
            await callback.answer("Subject not found.", show_alert=True)
            return

        lesson = Lesson(
            group_id=group_id,
            subject_id=subject_id,
            subgroup=subgroup,
            created_by_student_id=current_student.id,
            secret_salt=secrets.token_hex(32),
        )
        db.add(lesson)
        await db.commit()
        await db.refresh(lesson)

    settings = get_settings()
    presenter_url = f"{settings.webapp_base_url}/presenter/{lesson.id}"
    open_icon = emoji(PremiumEmoji.LOCK_OPEN)
    sync_icon = emoji(PremiumEmoji.SYNC_RELOAD)

    sg_text = "All Group" if subgroup == 0 else f"Subgroup {subgroup}"
    text = (
        f"{open_icon} <b>Session Launched!</b>\n\n"
        f"Subject: <b>{subject.name}</b> ({sg_text})\n"
        f"Session ID: <code>{lesson.id}</code>\n\n"
        f"{sync_icon} <a href='{presenter_url}'><b>Open Classroom Presenter Screen</b></a>\n"
        f"Display this screen on your classroom projector or tablet."
    )
    kb = get_admin_dashboard_kb(group_id, settings.webapp_base_url, active_lesson_id=lesson.id)

    if callback.message:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    await callback.answer("Session started!")


@router.callback_query(F.data.startswith("admin_panel:"))
async def callback_admin_panel(callback: CallbackQuery, current_student: Student | None, current_group: Group | None) -> None:
    if not require_admin(current_student) or not current_group:
        await callback.answer("Access denied.", show_alert=True)
        return

    settings = get_settings()
    active_lesson_id = None
    async with SessionLocal() as db:
        stmt = (
            select(Lesson.id)
            .where(Lesson.group_id == current_group.id, Lesson.is_closed.is_(False))
            .order_by(Lesson.opened_at.desc())
        )
        active_lesson_id = (await db.execute(stmt)).scalar_one_or_none()

    icon = emoji(PremiumEmoji.CAMPUS_HOME)
    text = (
        f"{icon} <b>Control Panel — {current_group.name}</b>\n\n"
        f"Invite code: <code>{current_group.invite_code}</code>\n"
        f"Active Session: <b>{'YES' if active_lesson_id else 'None'}</b>\n\n"
        f"Select an action below:"
    )
    kb = get_admin_dashboard_kb(current_group.id, settings.webapp_base_url, active_lesson_id)
    if callback.message:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    await callback.answer()


@router.callback_query(F.data.startswith("roster:"))
async def callback_roster(callback: CallbackQuery, current_student: Student | None, current_group: Group | None) -> None:
    if not require_admin(current_student) or not current_group:
        await callback.answer("Access denied.", show_alert=True)
        return
    if callback.message:
        await cmd_roster(callback.message, current_student, current_group)
    await callback.answer()


@router.callback_query(F.data.startswith("stats:"))
async def callback_stats(callback: CallbackQuery, current_student: Student | None, current_group: Group | None) -> None:
    if not require_admin(current_student) or not current_group:
        await callback.answer("Access denied.", show_alert=True)
        return
    if callback.message:
        await cmd_stats(callback.message, current_student, current_group)
    await callback.answer()


async def generate_and_send_excel(message: Message, group: Group) -> None:
    async with SessionLocal() as db:
        students = (await db.execute(select(Student).where(Student.group_id == group.id))).scalars().all()
        lessons = (await db.execute(select(Lesson).where(Lesson.group_id == group.id).order_by(Lesson.opened_at))).scalars().all()
        subjects = {x.id: x for x in (await db.execute(select(Subject).where(Subject.group_id == group.id))).scalars()}
        records = (await db.execute(select(Attendance).join(Lesson).where(Lesson.group_id == group.id))).scalars().all()

    excel_io = build_report(group, list(students), list(lessons), subjects, list(records))
    doc = BufferedInputFile(excel_io.getvalue(), filename=f"attendance-{group.name}.xlsx")
    file_icon = emoji(PremiumEmoji.FILE_EXCEL)
    await message.answer_document(
        document=doc,
        caption=f"{file_icon} <b>Attendance Matrix — {group.name}</b>\nIncludes Sheet 1: Matrix and Sheet 2: GPS Audit Trail.",
        parse_mode=ParseMode.HTML,
    )
