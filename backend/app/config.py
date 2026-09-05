from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Tarot Engine v1"
    database_url: str = "sqlite:///./tarot.db"
    allowed_origins: str = "http://localhost:8080,http://127.0.0.1:8080,https://ganna40.github.io"
    auto_seed_demo: bool = True
    openai_api_key: str | None = None
    openai_model: str | None = None
    openai_timeout_seconds: float = 30.0

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
