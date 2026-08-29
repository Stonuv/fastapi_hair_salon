-- datalogical_model.sql
-- Даталогическая модель БД CMS «Сайтама» -- актуальная схема (13 таблиц,
-- соответствует состоянию после 15 миграций Alembic, backend/alembic/versions/
-- 0001_initial.py -- 0015_salon_scoping.py; derived from backend/app/models/).
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
-- Готовый рисунок из этого скрипта -- вставить вместо рамки-заглушки в
-- main.tex (раздел 7.2, Images/datalogical_model.png).

CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS btree_gist; -- EXCLUDE USING gist на appointments

CREATE TYPE user_role AS ENUM ('client', 'master', 'admin', 'owner');
CREATE TYPE appointment_status AS ENUM ('pending', 'confirmed', 'cancelled', 'done');

-- ── salons ───────────────────────────────────────────────────────────────
CREATE TABLE salons (
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
    CONSTRAINT ck_salons_close_after_open CHECK (close_time > open_time)
);
CREATE UNIQUE INDEX uq_salons_slug ON salons (slug);

-- ── users ────────────────────────────────────────────────────────────────
CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email               VARCHAR(255),
    password_hash       VARCHAR(255),
    vk_user_id          VARCHAR(64),
    email_verified_at   TIMESTAMPTZ,
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    phone               VARCHAR(20),
    role                user_role NOT NULL DEFAULT 'client',
    salon_id            UUID REFERENCES salons(id) ON DELETE RESTRICT,
    is_blocked          BOOLEAN NOT NULL DEFAULT FALSE,
    token_version       INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT ck_users_admin_requires_salon CHECK (role <> 'admin' OR salon_id IS NOT NULL)
);
CREATE UNIQUE INDEX uq_users_email_active ON users (email) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uq_users_phone_active ON users (phone) WHERE deleted_at IS NULL AND phone IS NOT NULL;
CREATE UNIQUE INDEX uq_users_vk_user_id_active ON users (vk_user_id) WHERE deleted_at IS NULL AND vk_user_id IS NOT NULL;
CREATE INDEX ix_users_role ON users (role);
CREATE INDEX ix_users_salon ON users (salon_id) WHERE salon_id IS NOT NULL;

-- ── masters ──────────────────────────────────────────────────────────────
CREATE TABLE masters (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    salon_id        UUID NOT NULL REFERENCES salons(id) ON DELETE RESTRICT,
    specialization  VARCHAR(200),
    photo_url       VARCHAR(500),
    coefficient     NUMERIC(4, 2) NOT NULL DEFAULT 1.00,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    CONSTRAINT ck_masters_coefficient_positive CHECK (coefficient > 0)
);
CREATE UNIQUE INDEX uq_masters_user_id_active ON masters (user_id) WHERE deleted_at IS NULL;

-- ── schedules ────────────────────────────────────────────────────────────
CREATE TABLE schedules (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    master_id    UUID NOT NULL REFERENCES masters(id) ON DELETE CASCADE,
    day_of_week  SMALLINT NOT NULL,
    start_time   TIME NOT NULL,
    end_time     TIME NOT NULL,
    is_working   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_schedules_day_of_week CHECK (day_of_week BETWEEN 0 AND 6),
    CONSTRAINT ck_schedules_end_after_start CHECK (end_time > start_time),
    CONSTRAINT uq_schedules_master_day UNIQUE (master_id, day_of_week)
);

-- ── services ─────────────────────────────────────────────────────────────
CREATE TABLE services (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          VARCHAR(200) NOT NULL,
    description   TEXT,
    price         NUMERIC(10, 2) NOT NULL,
    duration_min  INTEGER NOT NULL,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at    TIMESTAMPTZ,
    CONSTRAINT ck_services_price_non_negative CHECK (price >= 0),
    CONSTRAINT ck_services_duration_positive CHECK (duration_min > 0)
);
CREATE INDEX ix_services_name ON services (name);

-- ── master_services (N:M) ───────────────────────────────────────────────
CREATE TABLE master_services (
    master_id       UUID NOT NULL REFERENCES masters(id) ON DELETE CASCADE,
    service_id      UUID NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    price_override  NUMERIC(10, 2),
    PRIMARY KEY (master_id, service_id),
    CONSTRAINT ck_master_services_price_override_non_negative CHECK (price_override >= 0)
);
CREATE INDEX idx_master_services_service ON master_services (service_id);

-- ── appointments ─────────────────────────────────────────────────────────
CREATE TABLE appointments (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id              UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    master_id              UUID NOT NULL REFERENCES masters(id) ON DELETE RESTRICT,
    service_id             UUID NOT NULL REFERENCES services(id) ON DELETE RESTRICT,
    salon_id               UUID NOT NULL REFERENCES salons(id) ON DELETE RESTRICT,
    start_time             TIMESTAMPTZ NOT NULL,
    end_time               TIMESTAMPTZ NOT NULL,
    final_price            NUMERIC(10, 2) NOT NULL,
    status                 appointment_status NOT NULL DEFAULT 'pending',
    reminder_24h_sent_at   TIMESTAMPTZ,
    reminder_2h_sent_at    TIMESTAMPTZ,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_appointments_end_after_start CHECK (end_time > start_time),
    CONSTRAINT ck_appointments_price_non_negative CHECK (final_price >= 0)
);
CREATE INDEX ix_appointments_client ON appointments (client_id);
CREATE INDEX ix_appointments_master ON appointments (master_id);
CREATE INDEX ix_appointments_time ON appointments (start_time, end_time);
CREATE INDEX ix_appointments_status ON appointments (status);

-- Защита от двойного бронирования на уровне СУБД, а не только в коде
-- приложения: два пересекающихся по времени интервала одного мастера
-- физически не могут существовать одновременно в таблице (кроме
-- отменённых записей -- WHERE status <> 'cancelled').
ALTER TABLE appointments
    ADD CONSTRAINT no_double_booking
    EXCLUDE USING gist (
        master_id WITH =,
        tstzrange(start_time, end_time, '[)') WITH &&
    )
    WHERE (status <> 'cancelled');

-- ── reviews ──────────────────────────────────────────────────────────────
CREATE TABLE reviews (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id  UUID NOT NULL UNIQUE REFERENCES appointments(id) ON DELETE CASCADE,
    client_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    master_id       UUID NOT NULL REFERENCES masters(id) ON DELETE CASCADE,
    service_id      UUID NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    rating          SMALLINT NOT NULL,
    comment         TEXT,
    is_published    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_reviews_rating_range CHECK (rating BETWEEN 1 AND 5)
);
CREATE INDEX ix_reviews_master ON reviews (master_id);
CREATE INDEX ix_reviews_service ON reviews (service_id);

-- ── sessions (refresh-сессии) ───────────────────────────────────────────
CREATE TABLE sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(64) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_sessions_user ON sessions (user_id);

-- ── password_reset_tokens ────────────────────────────────────────────────
CREATE TABLE password_reset_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(64) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_password_reset_tokens_user ON password_reset_tokens (user_id);

-- ── email_verification_tokens ───────────────────────────────────────────
CREATE TABLE email_verification_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(64) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_email_verification_tokens_user ON email_verification_tokens (user_id);

-- ── login_attempts (аудит попыток входа) ────────────────────────────────
CREATE TABLE login_attempts (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_attempted  VARCHAR(255) NOT NULL,
    user_id          UUID REFERENCES users(id) ON DELETE SET NULL,
    ip_address       VARCHAR(45),
    success          BOOLEAN NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_login_attempts_email_created ON login_attempts (email_attempted, created_at);

-- ── site_settings (singleton, контент сайта) ────────────────────────────
CREATE TABLE site_settings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content     JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
