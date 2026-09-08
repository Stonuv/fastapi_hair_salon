-- datalogical_model.sql
-- Даталогическая модель БД CMS «Сайтама» -- актуальная схема (13 таблиц,
-- 21 индекс; соответствует состоянию после 15 миграций Alembic,
-- backend/alembic/versions/0001_initial.py -- 0015_salon_scoping.py;
-- derived from backend/app/models/).
--
-- ВНИМАНИЕ: имена объектов приведены к стандарту именования
-- (db_naming_standards.md): таблицы в единственном числе, user вместо
-- зарезервированного слова -- user_account, журнал -- с суффиксом _log,
-- индексы -- с префиксами idx_/uniq_, проверочные ограничения -- chk_.
-- Рабочая схема, создаваемая миграциями Alembic, пока использует прежние
-- имена (users, appointments, ix_*, uq_*, ck_*): этот файл описывает
-- целевое именование для документации и рисунка даталогической модели,
-- а не текущее состояние рабочей БД.
--
-- Назначение: НЕ для применения к рабочей БД проекта (миграции -- Alembic,
-- см. руководство администратора) -- этот файл нужен только для того, чтобы
-- сгенерировать рисунок даталогической модели любым инструментом, читающим
-- обычный SQL DDL. Например:
--   * dbdiagram.io -> Import -> "PostgreSQL" -> вставить этот файл целиком;
--   * DataGrip / DBeaver -> создать пустую БД -> выполнить скрипт ->
--     встроенный "Diagram" на схеме;
--   * pgAdmin -> ERD Tool -> импорт после выполнения скрипта на тестовой БД;
--   * dbml-renderer / SchemaSpy -- аналогично, после выполнения на пустой
--     локальной Postgres (например, во временном docker-контейнере
--     `docker run --rm -e POSTGRES_PASSWORD=x -p 5432:5432 postgres:16`).
--
-- Готовый рисунок из этого скрипта -- заменить им Images/db_diagram.png
-- (подраздел 4.2 записки, рисунок 4).

CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS btree_gist; -- EXCLUDE USING gist на appointment

CREATE TYPE user_role AS ENUM ('client', 'master', 'admin', 'owner');
CREATE TYPE appointment_status AS ENUM ('pending', 'confirmed', 'cancelled', 'done');

-- ── salon ───────────────────────────────────────────────────────────────
CREATE TABLE salon (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(150) NOT NULL,
    slug        VARCHAR(150) NOT NULL,
    address     VARCHAR(300) NOT NULL,
    phone       VARCHAR(20),
    open_time   TIME NOT NULL,
    close_time  TIME NOT NULL,
    photo_url   VARCHAR(500),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_salon_close_after_open CHECK (close_time > open_time)
);
CREATE UNIQUE INDEX uniq_salon_slug ON salon (slug);

-- ── user_account ────────────────────────────────────────────────────────────────
CREATE TABLE user_account (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email               VARCHAR(255),
    password_hash       VARCHAR(255),
    vk_user_id          VARCHAR(64),
    email_verified_at   TIMESTAMPTZ,
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    phone               VARCHAR(20),
    role                user_role NOT NULL DEFAULT 'client',
    salon_id            UUID REFERENCES salon(id) ON DELETE RESTRICT,
    is_blocked          BOOLEAN NOT NULL DEFAULT FALSE,
    token_version       INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_user_account_admin_requires_salon CHECK (role <> 'admin' OR salon_id IS NOT NULL)
);
CREATE UNIQUE INDEX uniq_user_account_email ON user_account (email) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uniq_user_account_phone ON user_account (phone) WHERE deleted_at IS NULL AND phone IS NOT NULL;
CREATE UNIQUE INDEX uniq_user_account_vk_user_id ON user_account (vk_user_id) WHERE deleted_at IS NULL AND vk_user_id IS NOT NULL;
CREATE INDEX idx_user_account_role ON user_account (role);
CREATE INDEX idx_user_account_salon_id ON user_account (salon_id) WHERE salon_id IS NOT NULL;

-- ── master ──────────────────────────────────────────────────────────────
CREATE TABLE master (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    salon_id        UUID NOT NULL REFERENCES salon(id) ON DELETE RESTRICT,
    specialization  VARCHAR(200),
    photo_url       VARCHAR(500),
    coefficient     NUMERIC(4, 2) NOT NULL DEFAULT 1.00,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    CONSTRAINT chk_master_coefficient_positive CHECK (coefficient > 0)
);
CREATE UNIQUE INDEX uniq_master_user_id ON master (user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_master_salon_id ON master (salon_id);

-- ── schedule ────────────────────────────────────────────────────────────
CREATE TABLE schedule (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    master_id    UUID NOT NULL REFERENCES master(id) ON DELETE CASCADE,
    day_of_week  SMALLINT NOT NULL,
    start_time   TIME NOT NULL,
    end_time     TIME NOT NULL,
    is_working   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_schedule_day_of_week CHECK (day_of_week BETWEEN 0 AND 6),
    CONSTRAINT chk_schedule_end_after_start CHECK (end_time > start_time),
    CONSTRAINT uniq_schedule_master_id_day_of_week UNIQUE (master_id, day_of_week)
);

-- ── service ─────────────────────────────────────────────────────────────
CREATE TABLE service (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          VARCHAR(200) NOT NULL,
    description   TEXT,
    price         NUMERIC(10, 2) NOT NULL,
    duration_min  INTEGER NOT NULL,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at    TIMESTAMPTZ,
    CONSTRAINT chk_service_price_non_negative CHECK (price >= 0),
    CONSTRAINT chk_service_duration_positive CHECK (duration_min > 0)
);
CREATE INDEX idx_service_name ON service (name);

-- ── master_service (N:M) ───────────────────────────────────────────────
CREATE TABLE master_service (
    master_id       UUID NOT NULL REFERENCES master(id) ON DELETE CASCADE,
    service_id      UUID NOT NULL REFERENCES service(id) ON DELETE CASCADE,
    price_override  NUMERIC(10, 2),
    PRIMARY KEY (master_id, service_id),
    CONSTRAINT chk_master_service_price_override_non_negative CHECK (price_override >= 0)
);
CREATE INDEX idx_master_service_service_id ON master_service (service_id);

-- ── appointment ─────────────────────────────────────────────────────────
CREATE TABLE appointment (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id              UUID NOT NULL REFERENCES user_account(id) ON DELETE RESTRICT,
    master_id              UUID NOT NULL REFERENCES master(id) ON DELETE RESTRICT,
    service_id             UUID NOT NULL REFERENCES service(id) ON DELETE RESTRICT,
    salon_id               UUID NOT NULL REFERENCES salon(id) ON DELETE RESTRICT,
    start_time             TIMESTAMPTZ NOT NULL,
    end_time               TIMESTAMPTZ NOT NULL,
    final_price            NUMERIC(10, 2) NOT NULL,
    status                 appointment_status NOT NULL DEFAULT 'pending',
    reminder_24h_sent_at   TIMESTAMPTZ,
    reminder_2h_sent_at    TIMESTAMPTZ,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_appointment_end_after_start CHECK (end_time > start_time),
    CONSTRAINT chk_appointment_price_non_negative CHECK (final_price >= 0)
);
CREATE INDEX idx_appointment_client_id ON appointment (client_id);
CREATE INDEX idx_appointment_master_id ON appointment (master_id);
CREATE INDEX idx_appointment_start_time_end_time ON appointment (start_time, end_time);
CREATE INDEX idx_appointment_status ON appointment (status);
CREATE INDEX idx_appointment_salon_id ON appointment (salon_id);

-- Защита от двойного бронирования на уровне СУБД, а не только в коде
-- приложения: два пересекающихся по времени интервала одного мастера
-- физически не могут существовать одновременно в таблице (кроме
-- отменённых записей -- WHERE status <> 'cancelled').
ALTER TABLE appointment
    ADD CONSTRAINT no_double_booking
    EXCLUDE USING gist (
        master_id WITH =,
        tstzrange(start_time, end_time, '[)') WITH &&
    )
    WHERE (status <> 'cancelled');

-- ── review ──────────────────────────────────────────────────────────────
CREATE TABLE review (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id  UUID NOT NULL UNIQUE REFERENCES appointment(id) ON DELETE CASCADE,
    client_id       UUID NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    master_id       UUID NOT NULL REFERENCES master(id) ON DELETE CASCADE,
    service_id      UUID NOT NULL REFERENCES service(id) ON DELETE CASCADE,
    rating          SMALLINT NOT NULL,
    comment         TEXT,
    is_published    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_review_rating_range CHECK (rating BETWEEN 1 AND 5)
);
CREATE INDEX idx_review_master_id ON review (master_id);
CREATE INDEX idx_review_service_id ON review (service_id);

-- ── user_session (refresh-сессии) ───────────────────────────────────────────
CREATE TABLE user_session (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    token_hash  VARCHAR(64) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_user_session_user_id ON user_session (user_id);

-- ── password_reset_token ────────────────────────────────────────────────
CREATE TABLE password_reset_token (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    token_hash  VARCHAR(64) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_password_reset_token_user_id ON password_reset_token (user_id);

-- ── email_verification_token ───────────────────────────────────────────
CREATE TABLE email_verification_token (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    token_hash  VARCHAR(64) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_email_verification_token_user_id ON email_verification_token (user_id);

-- ── login_attempt_log (аудит попыток входа) ────────────────────────────────
CREATE TABLE login_attempt_log (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_attempted  VARCHAR(255) NOT NULL,
    user_id          UUID REFERENCES user_account(id) ON DELETE SET NULL,
    ip_address       VARCHAR(45),
    success          BOOLEAN NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_login_attempt_log_email_attempted_created_at ON login_attempt_log (email_attempted, created_at);

-- ── site_setting (singleton, контент сайта) ────────────────────────────
CREATE TABLE site_setting (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content     JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
