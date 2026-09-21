import json
from fastapi import Header, HTTPException, status
from core.config import get_settings
from core.security import validate_telegram_init_data


async def current_telegram_id(x_telegram_init_data: str = Header(...)) -> int:
    verified = validate_telegram_init_data(x_telegram_init_data, get_settings().bot_token)
    if not verified or "user" not in verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram WebApp authentication.")
    try:
        return int(json.loads(verified["user"])["id"])
    except (ValueError, KeyError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=401, detail="Invalid Telegram user data.") from error
