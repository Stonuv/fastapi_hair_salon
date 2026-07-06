from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_SECRET_KEY = "change-me-in-production"


class Settings(BaseSettings):
    # ── Приложение ───────────────────────────────────────────────
    app_name: str  = "Барбершоп «Сайтама»"
    debug:    bool = True
    # Дефолт — localhost: наружу на все интерфейсы (0.0.0.0) приложение
    # выставляется явно (например, в docker-compose), а не в dev-режиме.
    host: str = "127.0.0.1"
    port: int = 8000

    # ── База данных ──────────────────────────────────────────────
    # Пример: postgresql://user:password@localhost:5432/barbershop
    database_url: str = "postgresql://postgres:postgres@localhost:5432/barbershop"

    # ── JWT ──────────────────────────────────────────────────────
    secret_key:                  str = _DEFAULT_SECRET_KEY
    algorithm:                   str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 часа

    # ── Bootstrap-код первичной настройки ──────────────────────────
    # POST /api/setup неизбежно публичен (до первого админа его нечем
    # защитить) — без кода первый, кто успеет открыть /setup после деплоя,
    # становится админом. В debug не требуется (удобство локальной разработки);
    # вне debug обязателен — см. _setup_token_required_outside_debug.
    setup_token: str | None = None

    # ── Защита от перебора паролей ────────────────────────────────
    # После N неудачных попыток входа по email вход блокируется на M минут
    # (журнал login_attempts). Запросы сброса пароля лимитируются аналогично.
    login_max_failed_attempts: int = 5
    login_lockout_minutes:     int = 15
    password_reset_max_requests_per_hour: int = 3

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

    @model_validator(mode="after")
    def _no_default_secret_outside_debug(self) -> "Settings":
        # Fail-fast: вне debug-режима приложение не должно молча стартовать
        # с дефолтным секретом — все выданные JWT были бы подделываемы.
        if not self.debug and self.secret_key == _DEFAULT_SECRET_KEY:
            raise RuntimeError(
                "SECRET_KEY не задан: при DEBUG=false задайте собственный "
                "SECRET_KEY через переменную окружения или backend/.env"
            )
        return self

    @model_validator(mode="after")
    def _setup_token_required_outside_debug(self) -> "Settings":
        # Fail-fast: вне debug без кода POST /api/setup стал бы открытой
        # гонкой за права админа для первого, кто найдёт эндпоинт после деплоя.
        if not self.debug and not self.setup_token:
            raise RuntimeError(
                "SETUP_TOKEN не задан: при DEBUG=false задайте SETUP_TOKEN "
                "через переменную окружения или backend/.env — иначе "
                "/api/setup останется открытым для первого встречного"
            )
        return self


settings = Settings()
