"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://axon:axon@localhost:5432/axon"

    # AI Services
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    firecrawl_api_key: str = ""

    # Application
    env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # Optional services
    redis_url: str | None = None

    # Feature flags
    enable_paper_ingestion: bool = True
    enable_feedback_collection: bool = True

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

