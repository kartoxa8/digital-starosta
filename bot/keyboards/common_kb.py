from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from core.emojis import PremiumEmoji


def get_welcome_kb(webapp_base_url: str, invite_code: str | None = None) -> InlineKeyboardMarkup:
    url = f"{webapp_base_url}?join={invite_code}" if invite_code else webapp_base_url
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Open Digital Starosta",
                web_app=WebAppInfo(url=url),
                icon_custom_emoji_id=PremiumEmoji.CAMPUS_HOME,
            )
        ]
    ])


def get_student_kb(webapp_base_url: str, group_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Open Mini App",
                web_app=WebAppInfo(url=f"{webapp_base_url}?group_id={group_id}"),
                icon_custom_emoji_id=PremiumEmoji.CAMPUS_HOME,
            )
        ],
        [
            InlineKeyboardButton(
                text="My Attendance Status",
                callback_data="student_profile",
                icon_custom_emoji_id=PremiumEmoji.PROFILE,
            )
        ]
    ])
