from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # ── Приложение ───────────────────────────────────────────────
    app_name: str  = "Барбершоп «Сайтама»"
    debug:    bool = True

    # ── База данных ──────────────────────────────────────────────
    # Пример: postgresql://user:password@localhost:5432/barbershop
    database_url: str = "postgresql://postgres:postgres@localhost:5432/barbershop"

    # ── JWT ──────────────────────────────────────────────────────
    secret_key:           str = "change-me-in-production"
    algorithm:            str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 часа

    # ── CORS ─────────────────────────────────────────────────────
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    class Config:
        env_file = ".env"


settings = Settings()
