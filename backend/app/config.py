from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Tarot Engine v1"
    database_url: str = "sqlite:///./tarot.db"
    allowed_origins: str = "http://localhost:8080,http://127.0.0.1:8080,https://ganna40.github.io"
    auto_seed_curated: bool = True
    auto_seed_demo: bool | None = None
    api_access_key: str | None = None

    # LLM wording provider. The deterministic tarot engine remains authoritative.
    llm_provider: str = "openai_api"

    # OpenAI API provider settings.
    openai_api_key: str | None = None
    openai_model: str | None = None
    openai_timeout_seconds: float = 30.0

    # Local Codex subscription provider settings.
    # Authentication is owned by the Codex CLI (`codex login`), not by this app.
    codex_executable: str = "codex"
    codex_model: str | None = None
    codex_timeout_seconds: float = 120.0

    @property
    def auto_seed_enabled(self) -> bool:
        # AUTO_SEED_DEMO is retained as a compatibility alias for older .env files.
        return self.auto_seed_curated if self.auto_seed_demo is None else self.auto_seed_demo

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
