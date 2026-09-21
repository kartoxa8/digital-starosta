import hashlib
import hmac
import math
import time
from urllib.parse import parse_qsl


def generate_totp_token(lesson_id: int, secret_salt: str, window_seconds: int = 5) -> tuple[str, int]:
    window = int(time.time() // window_seconds)
    payload = f"{lesson_id}:{window}".encode()
    return hmac.new(secret_salt.encode(), payload, hashlib.sha256).hexdigest()[:16], window


def verify_totp_token(lesson_id: int, secret_salt: str, token: str, client_window: int, window_seconds: int = 5) -> bool:
    current = int(time.time() // window_seconds)
    if client_window not in (current, current - 1):
        return False
    expected = hmac.new(secret_salt.encode(), f"{lesson_id}:{client_window}".encode(), hashlib.sha256).hexdigest()[:16]
    return hmac.compare_digest(token, expected)


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict[str, str] | None:
    values = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = values.pop("hash", None)
    if not received_hash or not bot_token:
        return None
    check = "\n".join(f"{key}={value}" for key, value in sorted(values.items()))
    key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(key, check.encode(), hashlib.sha256).hexdigest()
    return values if hmac.compare_digest(expected, received_hash) else None
