from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://grepointel:change-me@postgres:5432/grepointel"
    redis_url: str = "redis://redis:6379/0"
    cors_origins: str = "http://localhost:13100"
    snapshot_interval_hours: int = 2
    scheduler_enabled: bool = True

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
