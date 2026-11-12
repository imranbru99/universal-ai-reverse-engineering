from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "REVERSEFORGE AI"
    environment: str = "development"
    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    database_url: str = "postgresql+psycopg://reverseforge:reverseforge@localhost:5432/reverseforge"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "reverseforge"
    s3_region: str = "us-east-1"

    web_origin: str = "http://localhost:3000"
    api_public_url: str = "http://localhost:8000"
    demo_target_url: str = "http://localhost:3100"

    ai_api_key: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-4o-mini"

    default_max_depth: int = 4
    default_max_pages: int = 40
    default_max_minutes: int = 10

    export_dir: str = "/app/exports"


@lru_cache
def get_settings() -> Settings:
    return Settings()
