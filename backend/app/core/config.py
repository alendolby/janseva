from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./janaseva.db"
    jwt_secret: str = Field(min_length=32)
    token_minutes: int = 30
    demo_mode: bool = False
    redis_url: str = "redis://redis:6379/0"
    storage_mode: str = "local"
    storage_endpoint: str = "http://minio:9000"
    storage_access_key: str = ""
    storage_secret_key: str = ""
    storage_bucket: str = "janaseva"
    upload_dir: str = "./uploads"
    max_upload_bytes: int = 10 * 1024 * 1024
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    rate_limit: int = 120
    rate_limit_backend: str = "memory"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_tls: bool = True

@lru_cache
def settings():
    return Settings()
