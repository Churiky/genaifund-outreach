from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # X API v2
    x_bearer_token: str = ""
    x_user_access_token: str = ""

    # Anthropic
    anthropic_api_key: str = ""

    # Database
    database_url: str = "sqlite:///./scribbling.db"

    # Session
    session_secret: str = "change-me-in-production"

    # Send limits
    max_sends_per_run: int = 25
    max_sends_per_day: int = 100
    cooldown_seconds: int = 90

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
