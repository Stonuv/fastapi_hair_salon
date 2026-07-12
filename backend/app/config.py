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
    access_token_expire_minutes: int = 60  # 1 час
    # Access-токен для SPA доставляется httpOnly-cookie с флагом Secure —
    # это НЕ то же самое, что debug: локальный docker-compose уже гоняет
    # DEBUG=false, но сам по себе поднимает только plain HTTP (README —
    # TLS ожидается на внешнем терминаторе). Secure=true ломает cookie на
    # голом HTTP, поэтому включается отдельной переменной, только когда
    # перед приложением реально стоит TLS-терминатор.
    cookie_secure: bool = False

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
    password_reset_token_expire_minutes: int = 30

    # ── Бронирование ─────────────────────────────────────────────
    # Верхняя граница на количество одновременных незавершённых (pending/
    # confirmed) записей клиента — без неё ничто не мешает забронировать
    # неограниченное число слотов подряд.
    max_active_appointments_per_client: int = 5

    # ── Email (SMTP) ─────────────────────────────────────────────
    # Дефолты нацелены на локальный Mailpit (docker-compose.dev.yml —
    # SMTP :1025, веб-интерфейс на :8025, авторизация не нужна). Для
    # прод-провайдера (Yandex/Mail.ru/SendGrid/...) переопределяются через
    # окружение: обычно потребуются smtp_user/smtp_password/smtp_use_tls.
    smtp_host:      str  = "localhost"
    smtp_port:      int  = 1025
    smtp_user:      str | None = None
    smtp_password:  str | None = None
    smtp_use_tls:   bool = False
    smtp_from_email: str = "no-reply@saitama-barbershop.local"
    smtp_from_name:  str = "Барбершоп «Сайтама»"
    # Базовый URL SPA — нужен для ссылки сброса пароля в письме (не то же
    # самое, что cors_origins, хотя обычно совпадает с одним из значений).
    frontend_base_url: str = "http://localhost:5173"

    # ── VK ID (OAuth 2.1 + PKCE) ───────────────────────────────────
    # vk_client_id не задан → кнопка "Войти через VK" не работает (см.
    # GET /api/auth/vk/enabled) — приложение при этом всё равно стартует,
    # OAuth в задании факультативен. Получить client_id/secret: id.vk.com/business
    # (redirect URI приложения — тот же, что и vk_redirect_uri ниже; VK ID
    # разрешает localhost на этапе разработки).
    vk_client_id:     str | None = None
    vk_client_secret: str | None = None
    vk_redirect_uri:  str = "http://localhost:8000/api/auth/vk/callback"

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
