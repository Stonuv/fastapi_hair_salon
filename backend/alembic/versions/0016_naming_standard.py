"""Имена объектов схемы приведены к стандарту (zapiska/db_naming_standards.md).

Переименование, и только оно: ни одна таблица, колонка, связь или проверка
не добавляется и не удаляется, данные не трогаются. По стандарту:

  * таблицы -- в единственном числе, зарезервированное слово user заменено
    на user_account, связующая таблица названа по двум сущностям в
    алфавитном порядке (master_service), журнал -- с суффиксом _log;
  * индексы -- idx_ для обычных, uniq_ для уникальных, далее имя таблицы и
    поля в порядке объявления;
  * проверочные ограничения -- chk_, первичные ключи -- pk_,
    внешние -- fk_<дочерняя>_<родительская>.

Ограничение no_double_booking (EXCLUDE USING gist) сохраняет имя: стандарт
не задаёт префикса для этого типа ограничений, а само имя ему не
противоречит (snake_case, латиница, не зарезервировано).

Первичные и внешние ключи PostgreSQL именовал сам (users_pkey,
appointments_client_id_fkey), и после переименования таблиц их имена
остались бы от прежних. Их новые имена не выписаны здесь списком, а
выводятся из системного каталога: имя, которое СУБД сгенерировала при
создании таблицы, зависит от версии и от порядка колонок, и жёсткий
список сломал бы миграцию на схеме, собранной чуть иначе.

Revision ID: 0016_naming_standard
Revises: 0015_salon_scoping
"""
from alembic import op

revision = "0016_naming_standard"
down_revision = "0015_salon_scoping"
branch_labels = None
depends_on = None


# старое имя -> новое
TABLES = [
    ("salons",                    "salon"),
    ("users",                     "user_account"),
    ("masters",                   "master"),
    ("schedules",                 "schedule"),
    ("services",                  "service"),
    ("master_services",           "master_service"),
    ("appointments",              "appointment"),
    ("reviews",                   "review"),
    ("sessions",                  "user_session"),
    ("password_reset_tokens",     "password_reset_token"),
    ("email_verification_tokens", "email_verification_token"),
    ("login_attempts",            "login_attempt_log"),
    ("site_settings",             "site_setting"),
]

INDEXES = [
    ("ix_appointments_client",            "idx_appointment_client_id"),
    ("ix_appointments_master",            "idx_appointment_master_id"),
    ("ix_appointments_salon",             "idx_appointment_salon_id"),
    ("ix_appointments_status",            "idx_appointment_status"),
    ("ix_appointments_time",              "idx_appointment_start_time_end_time"),
    ("ix_email_verification_tokens_user", "idx_email_verification_token_user_id"),
    ("ix_login_attempts_email_created",   "idx_login_attempt_log_email_attempted_created_at"),
    ("ix_masters_salon",                  "idx_master_salon_id"),
    ("ix_password_reset_tokens_user",     "idx_password_reset_token_user_id"),
    ("ix_reviews_master",                 "idx_review_master_id"),
    ("ix_reviews_service",                "idx_review_service_id"),
    ("ix_services_name",                  "idx_service_name"),
    ("ix_sessions_user",                  "idx_user_session_user_id"),
    ("ix_users_role",                     "idx_user_account_role"),
    ("ix_users_salon",                    "idx_user_account_salon_id"),
    ("idx_master_services_service",       "idx_master_service_service_id"),
    ("uq_salons_slug",                    "uniq_salon_slug"),
    ("uq_users_email_active",             "uniq_user_account_email"),
    ("uq_users_phone_active",             "uniq_user_account_phone"),
    ("uq_users_vk_user_id_active",        "uniq_user_account_vk_user_id"),
    ("uq_masters_user_id_active",         "uniq_master_user_id"),
]

# (таблица уже под НОВЫМ именем, старое имя ограничения, новое имя)
CONSTRAINTS = [
    ("appointment",    "ck_appointments_end_after_start",    "chk_appointment_end_after_start"),
    ("appointment",    "ck_appointments_price_non_negative", "chk_appointment_price_non_negative"),
    ("master",         "ck_masters_coefficient_positive",    "chk_master_coefficient_positive"),
    ("master_service", "ck_master_services_price_override_non_negative",
                       "chk_master_service_price_override_non_negative"),
    ("review",         "ck_reviews_rating_range",            "chk_review_rating_range"),
    ("review",         "uq_reviews_appointment",             "uniq_review_appointment_id"),
    ("salon",          "ck_salons_close_after_open",         "chk_salon_close_after_open"),
    ("schedule",       "ck_schedules_day_of_week",           "chk_schedule_day_of_week"),
    ("schedule",       "ck_schedules_end_after_start",       "chk_schedule_end_after_start"),
    ("schedule",       "uq_schedules_master_day",            "uniq_schedule_master_id_day_of_week"),
    ("service",        "ck_services_duration_positive",      "chk_service_duration_positive"),
    ("service",        "ck_services_price_non_negative",     "chk_service_price_non_negative"),
    ("user_account",   "ck_users_admin_requires_salon",      "chk_user_account_admin_requires_salon"),
]

# Первичные и внешние ключи: имена берём из pg_constraint по типу
# ограничения, а не по предполагаемому шаблону. contype='p' -- первичный
# ключ, 'f' -- внешний; confrelid даёт таблицу, на которую он ссылается,
# что и требуется для fk_<дочерняя>_<родительская>. quote_ident экранирует
# имя на случай, если СУБД когда-то выдала имя, требующее кавычек.
RENAME_PK_FK = """
DO $$
DECLARE
    r RECORD;
    new_name TEXT;
BEGIN
    FOR r IN
        SELECT c.conname,
               c.contype,
               t.relname            AS table_name,
               ft.relname           AS referred_table
          FROM pg_constraint c
          JOIN pg_class t  ON t.oid  = c.conrelid
          LEFT JOIN pg_class ft ON ft.oid = c.confrelid
          JOIN pg_namespace n ON n.oid = t.relnamespace
         WHERE n.nspname = current_schema()
           AND c.contype IN ('p', 'f')
    LOOP
        IF r.contype = 'p' THEN
            new_name := 'pk_' || r.table_name;
        ELSE
            new_name := 'fk_' || r.table_name || '_' || r.referred_table;
        END IF;

        IF r.conname IS DISTINCT FROM new_name THEN
            EXECUTE format('ALTER TABLE %I RENAME CONSTRAINT %I TO %I',
                           r.table_name, r.conname, new_name);
        END IF;
    END LOOP;
END $$
"""

# Обратная операция: вернуть системные имена PostgreSQL (<таблица>_pkey и
# <таблица>_<колонка>_fkey). Имя колонки внешнего ключа берётся из conkey.
RESTORE_PK_FK = """
DO $$
DECLARE
    r RECORD;
    new_name TEXT;
BEGIN
    FOR r IN
        SELECT c.conname,
               c.contype,
               t.relname AS table_name,
               (SELECT a.attname
                  FROM pg_attribute a
                 WHERE a.attrelid = c.conrelid
                   AND a.attnum = c.conkey[1]) AS first_column
          FROM pg_constraint c
          JOIN pg_class t ON t.oid = c.conrelid
          JOIN pg_namespace n ON n.oid = t.relnamespace
         WHERE n.nspname = current_schema()
           AND c.contype IN ('p', 'f')
    LOOP
        IF r.contype = 'p' THEN
            new_name := r.table_name || '_pkey';
        ELSE
            new_name := r.table_name || '_' || r.first_column || '_fkey';
        END IF;

        IF r.conname IS DISTINCT FROM new_name THEN
            EXECUTE format('ALTER TABLE %I RENAME CONSTRAINT %I TO %I',
                           r.table_name, r.conname, new_name);
        END IF;
    END LOOP;
END $$
"""


def upgrade() -> None:
    # Порядок важен: таблицы переименовываются первыми, дальше ограничения
    # адресуются уже по новым именам таблиц. Индексы к таблице не
    # привязаны по имени -- ALTER INDEX работает в любом порядке.
    for old, new in TABLES:
        op.execute(f"ALTER TABLE {old} RENAME TO {new}")
    for old, new in INDEXES:
        op.execute(f"ALTER INDEX {old} RENAME TO {new}")
    for table, old, new in CONSTRAINTS:
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {old} TO {new}")
    op.execute(RENAME_PK_FK)


def downgrade() -> None:
    op.execute(RESTORE_PK_FK)
    for table, old, new in CONSTRAINTS:
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {new} TO {old}")
    for old, new in INDEXES:
        op.execute(f"ALTER INDEX {new} RENAME TO {old}")
    for old, new in TABLES:
        op.execute(f"ALTER TABLE {new} RENAME TO {old}")
