from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "neofraudj-ingestion"
    host: str = "0.0.0.0"
    port: int = 8001
    log_level: str = "info"

    redis_url: str = "redis://localhost:6379"
    redis_stream_name: str = "neofraudj:transactions"
    redis_stream_maxlen: int = 100_000  # MAXLEN cap for the stream


@lru_cache
def get_settings() -> Settings:
    return Settings()
