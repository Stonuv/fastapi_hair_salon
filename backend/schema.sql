-- Барбершоп «Сайтама» — полная схема базы данных (PostgreSQL 16+).
--
-- Сгенерировано по факту применения всех Alembic-миграций
-- (backend/alembic/versions/0001..0007) — это снимок итоговой схемы,
-- а не замена миграций. Для реального развёртывания используйте
-- `alembic upgrade head`; этот файл — читаемый обзор структуры БД,
-- пригодный для импорта в dbdiagram.io (Import from SQL → PostgreSQL).

-- ── Расширения ──────────────────────────────────────────────────────
-- Нужно в реальной БД для EXCLUDE USING gist на appointment ниже
-- (индексация uuid + range в одном GiST-индексе). Оставлено как
-- комментарий-ссылка — сам EXCLUDE не является отношением PK/FK и
-- ER-диаграммой не визуализируется, см. примечание у appointment.
-- CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ── Перечисления ────────────────────────────────────────────────────
CREATE TYPE user_role AS ENUM ('client', 'master', 'admin');
CREATE TYPE appointment_status AS ENUM ('pending', 'confirmed', 'cancelled', 'done');


-- ── user_account ───────────────────────────────────────────────────────────
-- Soft delete через deleted_at; уникальность email/phone обеспечивается
-- частичными индексами (WHERE deleted_at IS NULL), а не UNIQUE-колонкой,
-- иначе email удалённого пользователя навсегда блокирует повторную
-- регистрацию. token_version инкрементируется при logout / смене
-- пароля / блокировке — реальный механизм отзыва ранее выданных JWT.
CREATE TABLE user_account (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email          varchar(255) NOT NULL,
    password_hash  varchar(255) NOT NULL,
    first_name     varchar(100) NOT NULL,
    last_name      varchar(100) NOT NULL,
    phone          varchar(20),
    role           user_role NOT NULL DEFAULT 'client',
    is_blocked     boolean NOT NULL DEFAULT false,
    token_version  integer NOT NULL DEFAULT 0,
    deleted_at     timestamptz,
    created_at     timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX uniq_user_account_email ON user_account (email) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uniq_user_account_phone ON user_account (phone) WHERE deleted_at IS NULL AND phone IS NOT NULL;
CREATE INDEX idx_user_account_role ON user_account (role);


-- ── master ─────────────────────────────────────────────────────────
-- 1:1 профиль поверх user_account с role = 'master'. coefficient умножает
-- базовую цену услуги (see master_service.price_override для
-- override конкретной услуги у конкретного мастера).
CREATE TABLE master (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        uuid NOT NULL REFERENCES user_account (id) ON DELETE CASCADE,
    specialization varchar(200),
    photo_url      varchar(500),
    coefficient    numeric(4, 2) NOT NULL DEFAULT 1.00 CHECK (coefficient > 0),
    is_active      boolean NOT NULL DEFAULT true,
    deleted_at     timestamptz,
    created_at     timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX uniq_master_user_id ON master (user_id) WHERE deleted_at IS NULL;


-- ── service ────────────────────────────────────────────────────────
-- is_active — витринный флаг публикации, не связан с soft delete
-- (deleted_at) — это отдельные, независимые состояния.
CREATE TABLE service (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name          varchar(200) NOT NULL,
    description   text,
    price         numeric(10, 2) NOT NULL CHECK (price >= 0),
    duration_min  integer NOT NULL CHECK (duration_min > 0),
    is_active     boolean NOT NULL DEFAULT true,
    deleted_at    timestamptz
);

CREATE INDEX idx_service_name ON service (name);


-- ── master_service ─────────────────────────────────────────────────
-- M:N между master и service; price_override переопределяет
-- price * coefficient для конкретной пары мастер-услуга.
CREATE TABLE master_service (
    master_id      uuid NOT NULL REFERENCES master (id) ON DELETE CASCADE,
    service_id     uuid NOT NULL REFERENCES service (id) ON DELETE CASCADE,
    price_override numeric(10, 2) CHECK (price_override >= 0),
    PRIMARY KEY (master_id, service_id)
);

CREATE INDEX idx_master_service_service_id ON master_service (service_id);


-- ── schedule ───────────────────────────────────────────────────────
-- Рабочие часы мастера по дням недели (0=пн..6=вс — см.
-- day_of_week в UserRole/enums.py на стороне приложения).
-- start_time/end_time — время в "настенном" времени салона (UTC).
CREATE TABLE schedule (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    master_id    uuid NOT NULL REFERENCES master (id) ON DELETE CASCADE,
    day_of_week  smallint NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time   time NOT NULL,
    end_time     time NOT NULL,
    is_working   boolean NOT NULL DEFAULT true,
    created_at   timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uniq_schedule_master_id_day_of_week UNIQUE (master_id, day_of_week),
    CHECK (end_time > start_time)
);


-- ── appointment ────────────────────────────────────────────────────
-- Центральная бизнес-таблица. final_price снимается на момент
-- создания записи и не пересчитывается при изменении цены услуги.
-- RESTRICT на client/master/service — историю записей нельзя
-- "выбить" удалением связанной сущности.
--
-- no_double_booking — DB-уровневая, race-condition-proof защита от
-- пересечения записей одного мастера (проверка в приложении в
-- AppointmentRepository.get_overlapping() — это лишь pre-flight для
-- аккуратного текста ошибки). WHERE status <> 'cancelled' обязателен:
-- без него отменённая запись навсегда блокирует этот же слот.
CREATE TABLE appointment (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id    uuid NOT NULL REFERENCES user_account (id) ON DELETE RESTRICT,
    master_id    uuid NOT NULL REFERENCES master (id) ON DELETE RESTRICT,
    service_id   uuid NOT NULL REFERENCES service (id) ON DELETE RESTRICT,
    start_time   timestamptz NOT NULL,
    end_time     timestamptz NOT NULL,
    final_price  numeric(10, 2) NOT NULL CHECK (final_price >= 0),
    status       appointment_status NOT NULL DEFAULT 'pending',
    created_at   timestamptz NOT NULL DEFAULT now(),
    CHECK (end_time > start_time)
    -- + DB-уровневая EXCLUDE USING gist (master_id WITH =,
    --   tstzrange(start_time, end_time, '[)') WITH &&) WHERE status <> 'cancelled'
    --   race-condition-proof защита от пересечения записей одного мастера.
    --   Не выражается как PK/FK/UNIQUE, поэтому не включена в DDL —
    --   ER-диаграмма её всё равно не отобразит. Реальная реализация:
    --   alembic/versions/0001_initial.py.
);

CREATE INDEX idx_appointment_client_id ON appointment (client_id);
CREATE INDEX idx_appointment_master_id ON appointment (master_id);
CREATE INDEX idx_appointment_status ON appointment (status);
CREATE INDEX idx_appointment_start_time_end_time ON appointment (start_time, end_time);


-- ── review ─────────────────────────────────────────────────────────
-- 1:1 с завершённой (done) записью; master_id/service_id
-- денормализованы из appointment, чтобы списки отзывов мастера/услуги
-- не требовали join. is_published — модерация админом.
CREATE TABLE review (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id uuid NOT NULL UNIQUE REFERENCES appointment (id) ON DELETE CASCADE,
    client_id      uuid NOT NULL REFERENCES user_account (id) ON DELETE CASCADE,
    master_id      uuid NOT NULL REFERENCES master (id) ON DELETE CASCADE,
    service_id     uuid NOT NULL REFERENCES service (id) ON DELETE CASCADE,
    rating         smallint NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment        text,
    is_published   boolean NOT NULL DEFAULT true,
    created_at     timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_review_master_id ON review (master_id);
CREATE INDEX idx_review_service_id ON review (service_id);


-- ── password_reset_token ───────────────────────────────────────────
-- Хранится только SHA-256 хэш токена, не сырое значение.
CREATE TABLE password_reset_token (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL REFERENCES user_account (id) ON DELETE CASCADE,
    token_hash  varchar(64) NOT NULL UNIQUE,
    expires_at  timestamptz NOT NULL,
    used_at     timestamptz,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_password_reset_token_user_id ON password_reset_token (user_id);


-- ── login_attempt_log ──────────────────────────────────────────────────
-- Аудит-лог для rate-limiting логина (5 неудач / 15 минут / email).
-- user_id nullable — неудачный логин может не соответствовать
-- никакому существующему аккаунту.
CREATE TABLE login_attempt_log (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email_attempted   varchar(255) NOT NULL,
    user_id           uuid REFERENCES user_account (id) ON DELETE SET NULL,
    ip_address        varchar(45),
    success           boolean NOT NULL,
    created_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_login_attempt_log_email_attempted_created_at ON login_attempt_log (email_attempted, created_at);


-- ── site_setting ───────────────────────────────────────────────────
-- Singleton-строка с редактируемым контентом сайта (CMS), формат
-- содержимого описан в Pydantic-схеме SiteContent на стороне
-- приложения, а не в структуре БД — сама колонка это просто JSONB.
CREATE TABLE site_setting (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    content     jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at  timestamptz NOT NULL DEFAULT now()
);
