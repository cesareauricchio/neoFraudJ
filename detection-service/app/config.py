from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "neofraudj-detection"
    host: str = "0.0.0.0"
    port: int = 8002
    log_level: str = "info"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neofraudj_secret"
    neo4j_database: str = "neo4j"

    redis_url: str = "redis://localhost:6379"
    redis_stream_name: str = "neofraudj:transactions"


@lru_cache
def get_settings() -> Settings:
    return Settings()
