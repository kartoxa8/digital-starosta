from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from core.config import get_settings
from core.emojis import PremiumEmoji, emoji
from core.models import Group, Student
from bot.keyboards.admin_kb import get_admin_dashboard_kb
from bot.keyboards.common_kb import get_welcome_kb, get_student_kb

router = Router(name="common")


@router.message(CommandStart())
async def cmd_start(message: Message, current_student: Student | None, current_group: Group | None) -> None:
    settings = get_settings()
    args = message.text.split()[1:] if message.text else []
    invite_param = args[0].strip().upper() if args else None

    # Already registered user
    if current_student and current_group:
        role_label = "Head Student (Starosta)" if current_student.role == "owner" else (
            "Deputy" if current_student.role == "deputy" else "Student"
        )
        welcome_icon = emoji(PremiumEmoji.SMILE_WELCOME)
        text = (
            f"{welcome_icon} Welcome back, <b>{current_student.first_name} {current_student.last_name}</b>!\n\n"
            f"Group: <b>{current_group.name}</b> ({current_group.university})\n"
            f"Role: <b>{role_label}</b> | Subgroup: <b>{current_student.subgroup}</b>\n\n"
            f"Use the buttons below to open the portal."
        )

        if current_student.role in ("owner", "deputy"):
            kb = get_admin_dashboard_kb(current_group.id, settings.webapp_base_url)
        else:
            kb = get_student_kb(settings.webapp_base_url, current_group.id)

        await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        return

    # Unregistered user
    welcome_icon = emoji(PremiumEmoji.SMILE_WELCOME)
    info_icon = emoji(PremiumEmoji.INFO_SIGN)
    if invite_param:
        text = (
            f"{welcome_icon} Welcome to <b>Digital Starosta</b>!\n\n"
            f"{info_icon} You were invited with code: <code>{invite_param}</code>.\n\n"
            f"Click the button below to join your academic group and select your subgroup."
        )
    else:
        text = (
            f"{welcome_icon} Welcome to <b>Digital Starosta</b>!\n\n"
            f"The modern university attendance & group management system.\n\n"
            f"Are you the Head Student creating a group, or a student joining with an invite code? "
            f"Open the Mini App to proceed."
        )

    kb = get_welcome_kb(settings.webapp_base_url, invite_code=invite_param)
    await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.message(Command("help"))
async def cmd_help(message: Message, current_student: Student | None, current_group: Group | None) -> None:
    info_icon = emoji(PremiumEmoji.INFO_SIGN)
    if not current_student:
        text = (
            f"{info_icon} <b>Digital Starosta Help</b>\n\n"
            f"• Use /start to launch the Mini App\n"
            f"• Create a new group or join via an invite code"
        )
    elif current_student.role in ("owner", "deputy"):
        text = (
            f"{info_icon} <b>Administrator Commands:</b>\n\n"
            f"• /admin — Open administrative dashboard\n"
            f"• /session — Start a dynamic QR check-in session\n"
            f"• /close — Close the active attendance session\n"
            f"• /roster — View group student list\n"
            f"• /stats — View current attendance summary\n"
            f"• /report — Export attendance matrix to Excel"
        )
    else:
        text = (
            f"{info_icon} <b>Student Commands:</b>\n\n"
            f"• /me — View your personal attendance status & rate\n"
            f"• /start — Launch the Mini App to confirm attendance"
        )

    await message.answer(text, parse_mode=ParseMode.HTML)
