from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from core.emojis import PremiumEmoji


def get_admin_dashboard_kb(group_id: int, webapp_base_url: str, active_lesson_id: int | None = None) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="Open Control Panel",
                web_app=WebAppInfo(url=f"{webapp_base_url}?group_id={group_id}"),
                icon_custom_emoji_id=PremiumEmoji.CAMPUS_HOME,
            )
        ],
    ]

    if active_lesson_id:
        buttons.append([
            InlineKeyboardButton(
                text="Classroom QR Presenter",
                url=f"{webapp_base_url}/presenter/{active_lesson_id}",
                icon_custom_emoji_id=PremiumEmoji.SYNC_RELOAD,
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                text="Close Current Session",
                callback_data=f"close_lesson:{active_lesson_id}",
                icon_custom_emoji_id=PremiumEmoji.LOCK_CLOSE,
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="Start Lesson Session",
                callback_data=f"start_session_prompt:{group_id}",
                icon_custom_emoji_id=PremiumEmoji.LOCK_OPEN,
            )
        ])

    buttons.extend([
        [
            InlineKeyboardButton(
                text="Group Roster",
                callback_data=f"roster:{group_id}",
                icon_custom_emoji_id=PremiumEmoji.STUDENTS_GROUP,
            ),
            InlineKeyboardButton(
                text="Quick Statistics",
                callback_data=f"stats:{group_id}",
                icon_custom_emoji_id=PremiumEmoji.STATISTICS,
            ),
        ],
        [
            InlineKeyboardButton(
                text="Send Excel Attendance to Chat",
                callback_data=f"export_excel:{group_id}",
                icon_custom_emoji_id=PremiumEmoji.DOWNLOAD,
            )
        ],
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_session_select_kb(group_id: int, subjects: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    buttons = []
    for subj_id, subj_name in subjects[:6]:  # Show top 6
        buttons.append([
            InlineKeyboardButton(
                text=f"{subj_name} (All)",
                callback_data=f"launch_lesson:{group_id}:{subj_id}:0",
                icon_custom_emoji_id=PremiumEmoji.USER_APPROVED,
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                text=f"{subj_name} (Subgroup 1)",
                callback_data=f"launch_lesson:{group_id}:{subj_id}:1",
                icon_custom_emoji_id=PremiumEmoji.PROFILE,
            ),
            InlineKeyboardButton(
                text=f"{subj_name} (Subgroup 2)",
                callback_data=f"launch_lesson:{group_id}:{subj_id}:2",
                icon_custom_emoji_id=PremiumEmoji.PROFILE,
            ),
        ])
    buttons.append([
        InlineKeyboardButton(
            text="Cancel",
            callback_data=f"admin_panel:{group_id}",
            icon_custom_emoji_id=PremiumEmoji.CROSS_FAIL,
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
