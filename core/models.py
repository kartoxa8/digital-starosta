from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, SmallInteger, String, Time, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase): pass

class Group(Base):
    __tablename__ = "groups"
    id: Mapped[int] = mapped_column(primary_key=True); name: Mapped[str] = mapped_column(String(50)); university: Mapped[str] = mapped_column(String(255)); invite_code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Moscow"); absence_warning_threshold: Mapped[int] = mapped_column(default=3); created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    students: Mapped[list["Student"]] = relationship(back_populates="group", cascade="all, delete-orphan")

class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True); group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), index=True); telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100)); last_name: Mapped[str] = mapped_column(String(100)); middle_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="student"); subgroup: Mapped[int] = mapped_column(SmallInteger); status: Mapped[str] = mapped_column(String(20), default="active"); created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    group: Mapped[Group] = relationship(back_populates="students")

class Subject(Base):
    __tablename__ = "subjects"
    id: Mapped[int] = mapped_column(primary_key=True); group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE")); name: Mapped[str] = mapped_column(String(255)); teacher_name: Mapped[str | None] = mapped_column(String(255), nullable=True); is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class ScheduleTemplate(Base):
    __tablename__ = "schedule_templates"
    id: Mapped[int] = mapped_column(primary_key=True); group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE")); subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE")); day_of_week: Mapped[int] = mapped_column(SmallInteger); pair_number: Mapped[int] = mapped_column(SmallInteger); start_time: Mapped[object] = mapped_column(Time); end_time: Mapped[object] = mapped_column(Time); subgroup: Mapped[int] = mapped_column(SmallInteger, default=0); week_type: Mapped[str] = mapped_column(String(20), default="all"); classroom: Mapped[str | None] = mapped_column(String(50), nullable=True); campus_latitude: Mapped[float | None] = mapped_column(Float, nullable=True); campus_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

class Lesson(Base):
    __tablename__ = "lessons"
    id: Mapped[int] = mapped_column(primary_key=True); group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE")); subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE")); subgroup: Mapped[int] = mapped_column(SmallInteger); created_by_student_id: Mapped[int] = mapped_column(ForeignKey("students.id")); opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now()); closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True); is_closed: Mapped[bool] = mapped_column(Boolean, default=False); secret_salt: Mapped[str] = mapped_column(String(64)); geo_latitude: Mapped[float | None] = mapped_column(Float, nullable=True); geo_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

class Attendance(Base):
    __tablename__ = "attendance"; __table_args__ = (UniqueConstraint("lesson_id", "student_id", name="unique_student_lesson"),)
    id: Mapped[int] = mapped_column(primary_key=True); lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True); student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE")); scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now()); latitude: Mapped[float | None] = mapped_column(Float, nullable=True); longitude: Mapped[float | None] = mapped_column(Float, nullable=True); distance_meters: Mapped[float | None] = mapped_column(Float, nullable=True); status: Mapped[str] = mapped_column(String(20), default="present")
