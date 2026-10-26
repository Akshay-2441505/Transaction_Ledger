from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/ledger_db"
    )
    TEST_DATABASE_URL: Optional[str] = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/ledger_test_db"
    )
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    @field_validator("DATABASE_URL", "TEST_DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        # Normalize standard postgres:// or postgresql:// to postgresql+psycopg://
        if v.startswith("postgres://"):
            v = "postgresql+psycopg://" + v[len("postgres://") :]
        elif v.startswith("postgresql://") and not v.startswith("postgresql+"):
            v = "postgresql+psycopg://" + v[len("postgresql://") :]

        # If connecting to hosted Supabase / cloud database and sslmode is not set, require SSL
        if any(cloud in v for cloud in ["supabase.co", "supabase.com", "neon.tech", "pooler.supabase.com"]) and "sslmode=" not in v:
            delimiter = "&" if "?" in v else "?"
            v = f"{v}{delimiter}sslmode=require"

        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
