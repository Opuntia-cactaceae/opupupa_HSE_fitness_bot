from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    POSTGRES_DSN: str
    TELEGRAM_BOT_TOKEN: str
    WEATHER_API_KEY: str | None = None
    FOOD_API_KEY: str | None = None
    FATSECRET_CONSUMER_KEY: str | None = None
    FATSECRET_CONSUMER_SECRET: str | None = None
    AI_API_KEY: str | None = None

settings = Settings()