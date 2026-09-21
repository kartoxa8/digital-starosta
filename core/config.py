from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    bot_token: str = ""
    database_url: str = "sqlite+aiosqlite:///./digital_starosta.db"
    webapp_base_url: str = "http://localhost:8000"
    checkin_radius_meters: float = 150.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
