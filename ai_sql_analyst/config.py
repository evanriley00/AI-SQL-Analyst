from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="AI SQL Analyst", alias="AI_SQL_ANALYST_APP_NAME")
    host: str = Field(default="127.0.0.1", alias="AI_SQL_ANALYST_HOST")
    port: int = Field(default=8000, alias="AI_SQL_ANALYST_PORT")
    data_dir: Path = Field(default=PROJECT_ROOT / "data", alias="AI_SQL_ANALYST_DATA_DIR")
    db_path: Path = Field(
        default=PROJECT_ROOT / "data" / "demo_warehouse.db",
        alias="AI_SQL_ANALYST_DB_PATH",
    )
    query_log_path: Path = Field(
        default=PROJECT_ROOT / "data" / "query_log.jsonl",
        alias="AI_SQL_ANALYST_QUERY_LOG_PATH",
    )
    max_query_rows: int = Field(default=100, alias="AI_SQL_ANALYST_MAX_QUERY_ROWS")
    database_backend: str = Field(default="sqlite", alias="AI_SQL_ANALYST_DATABASE_BACKEND")
    postgres_dsn: str = Field(
        default="postgresql://ai_sql:ai_sql_password@localhost:5432/ai_sql_analyst",
        alias="AI_SQL_ANALYST_POSTGRES_DSN",
    )
    api_keys: str = Field(default="dev-api-key", alias="AI_SQL_ANALYST_API_KEYS")
    browser_api_key: str = Field(default="dev-api-key", alias="AI_SQL_ANALYST_BROWSER_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    model_name: str = Field(default="gpt-5-mini", alias="AI_SQL_ANALYST_MODEL")

    def allowed_api_keys(self) -> set[str]:
        return {key.strip() for key in self.api_keys.split(",") if key.strip()}


settings = Settings()
