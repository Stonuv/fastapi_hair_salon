from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Приложение ───────────────────────────────────────────────
    app_name: str  = "Барбершоп «Сайтама»"
    debug:    bool = True

    # ── База данных ──────────────────────────────────────────────
    # Пример: postgresql://user:password@localhost:5432/barbershop
    database_url: str = "postgresql://postgres:postgres@localhost:5432/barbershop"

    # ── JWT ──────────────────────────────────────────────────────
    secret_key:                  str = "change-me-in-production"
    algorithm:                   str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 часа

    # ── Восстановление пароля ─────────────────────────────────────
    # Реальной отправки email нет (нет SMTP-провайдера) — ссылка на
    # сброс пишется в лог сервера, см. services/auth_service.py.
    password_reset_token_expire_minutes: int = 30

    # ── CORS ─────────────────────────────────────────────────────
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
