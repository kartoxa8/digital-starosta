from enum import StrEnum


class PremiumEmoji(StrEnum):
    SETTINGS = "5870982283724328568"
    PROFILE = "5870994129244131212"
    STUDENTS_GROUP = "5870772616305839506"
    USER_APPROVED = "5891207662678317861"
    USER_DISMISSED = "5893192487324880883"
    FILE_EXCEL = "5870528606328852614"
    SMILE_WELCOME = "5870764288364252592"
    CHART_GROWTH = "5870930636742595124"
    STATISTICS = "5870921681735781843"
    CAMPUS_HOME = "5873147866364514353"
    LOCK_CLOSE = "6037249452824072506"
    LOCK_OPEN = "6037496202990194718"
    BROADCAST = "6039422865189638057"
    CHECK_SUCCESS = "5870633910337015697"
    CROSS_FAIL = "5870657884844462243"
    WARNING_ALERT = "5870931487146119264"
    EDIT_PEN = "5870676941614354370"
    TRASH_REMOVE = "5870875489362513438"
    LINK_URL = "5769289093221454192"
    INFO_SIGN = "6028435952299413210"
    DOWNLOAD = "6039802767931871481"
    TIME_CLOCK = "5983150113483134607"
    GEO_POINT = "6042011682497106307"
    CALENDAR = "5890937706803894250"
    SYNC_RELOAD = "5345906554510012647"


# Mapping to fallback standard Unicode characters for non-supporting clients
FALLBACKS = {
    PremiumEmoji.SETTINGS: "⚙",
    PremiumEmoji.PROFILE: "👤",
    PremiumEmoji.STUDENTS_GROUP: "👥",
    PremiumEmoji.USER_APPROVED: "✅",
    PremiumEmoji.USER_DISMISSED: "❌",
    PremiumEmoji.FILE_EXCEL: "📁",
    PremiumEmoji.SMILE_WELCOME: "🙂",
    PremiumEmoji.CHART_GROWTH: "📈",
    PremiumEmoji.STATISTICS: "📊",
    PremiumEmoji.CAMPUS_HOME: "🏫",
    PremiumEmoji.LOCK_CLOSE: "🔒",
    PremiumEmoji.LOCK_OPEN: "🔓",
    PremiumEmoji.BROADCAST: "📣",
    PremiumEmoji.CHECK_SUCCESS: "✅",
    PremiumEmoji.CROSS_FAIL: "❌",
    PremiumEmoji.WARNING_ALERT: "⚠️",
    PremiumEmoji.EDIT_PEN: "✏️",
    PremiumEmoji.TRASH_REMOVE: "🗑️",
    PremiumEmoji.LINK_URL: "🔗",
    PremiumEmoji.INFO_SIGN: "ℹ️",
    PremiumEmoji.DOWNLOAD: "📥",
    PremiumEmoji.TIME_CLOCK: "⏰",
    PremiumEmoji.GEO_POINT: "📍",
    PremiumEmoji.CALENDAR: "📅",
    PremiumEmoji.SYNC_RELOAD: "🔄",
}


def emoji(value: PremiumEmoji, fallback: str | None = None) -> str:
    fb = fallback if fallback is not None else FALLBACKS.get(value, "•")
    return f'<tg-emoji emoji-id="{value}">{fb}</tg-emoji>'
