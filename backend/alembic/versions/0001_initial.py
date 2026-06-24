"""Initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

Создаёт все таблицы для CMS барбершопа. Отдельно добавляет вещи,
которые SQLAlchemy не умеет генерировать автоматически:
  - расширение btree_gist (нужно для EXCLUDE)
  - EXCLUDE USING gist на appointments (защита от двойного бронирования,
    действует только для НЕ отменённых записей — отменённая запись не
    должна блокировать повторное бронирование того же слота)
  - частичные unique-индексы для email/phone/user_id мастера —
    уникальность действует только среди "живых" (deleted_at IS NULL) строк,
    иначе мягко удалённая запись навсегда блокирует повторное использование
  - вспомогательную функцию get_appointment_price()
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Расширение для EXCLUDE USING gist ────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    # ── users ─────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id",            postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("email",         sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("first_name",    sa.String(100), nullable=False),
        sa.Column("last_name",     sa.String(100), nullable=False),
        sa.Column("phone",         sa.String(20)),
        sa.Column("role",          sa.Enum("client", "master", "admin",
                                           name="user_role"),
                  nullable=False, server_default="client"),
        sa.Column("created_at",    sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("deleted_at",    sa.DateTime(timezone=True)),
    )
    op.create_index("uq_users_email_active", "users", ["email"], unique=True,
                    postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("uq_users_phone_active", "users", ["phone"], unique=True,
                    postgresql_where=sa.text("deleted_at IS NULL AND phone IS NOT NULL"))
    op.create_index("ix_users_role", "users", ["role"])

    # ── masters ───────────────────────────────────────────────────
    op.create_table(
        "masters",
        sa.Column("id",             postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id",        postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("specialization", sa.String(200)),
        sa.Column("photo_url",      sa.String(500)),
        sa.Column("coefficient",    sa.Numeric(4, 2), nullable=False,
                  server_default="1.00"),
        sa.Column("is_active",      sa.Boolean, nullable=False,
                  server_default="true"),
        sa.Column("deleted_at",     sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.CheckConstraint("coefficient > 0", name="ck_masters_coefficient_positive"),
    )
    op.create_index("uq_masters_user_id_active", "masters", ["user_id"], unique=True,
                    postgresql_where=sa.text("deleted_at IS NULL"))

    # ── services ──────────────────────────────────────────────────
    op.create_table(
        "services",
        sa.Column("id",           postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name",         sa.String(200), nullable=False),
        sa.Column("description",  sa.Text),
        sa.Column("price",        sa.Numeric(10, 2), nullable=False),
        sa.Column("duration_min", sa.Integer, nullable=False),
        sa.Column("is_active",    sa.Boolean, nullable=False,
                  server_default="true"),
        sa.Column("deleted_at",   sa.DateTime(timezone=True)),
        sa.CheckConstraint("price >= 0",       name="ck_services_price_non_negative"),
        sa.CheckConstraint("duration_min > 0", name="ck_services_duration_positive"),
    )
    op.create_index("ix_services_name", "services", ["name"])

    # ── master_services ───────────────────────────────────────────
    op.create_table(
        "master_services",
        sa.Column("master_id",      postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("service_id",     postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("price_override", sa.Numeric(10, 2)),
        sa.ForeignKeyConstraint(["master_id"],  ["masters.id"],  ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("master_id", "service_id"),
        sa.CheckConstraint("price_override >= 0",
                           name="ck_master_services_price_override_non_negative"),
    )
    op.create_index("idx_master_services_service", "master_services", ["service_id"])

    # ── schedules ─────────────────────────────────────────────────
    op.create_table(
        "schedules",
        sa.Column("id",          postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("master_id",   postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("day_of_week", sa.SmallInteger, nullable=False),
        sa.Column("start_time",  sa.Time, nullable=False),
        sa.Column("end_time",    sa.Time, nullable=False),
        sa.Column("is_working",  sa.Boolean, nullable=False, server_default="true"),
        sa.ForeignKeyConstraint(["master_id"], ["masters.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("master_id", "day_of_week",
                            name="uq_schedules_master_day"),
        sa.CheckConstraint("day_of_week BETWEEN 0 AND 6",
                           name="ck_schedules_day_of_week"),
        sa.CheckConstraint("end_time > start_time",
                           name="ck_schedules_end_after_start"),
    )

    # ── appointments ──────────────────────────────────────────────
    op.create_table(
        "appointments",
        sa.Column("id",          postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id",   postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("master_id",   postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("service_id",  postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_time",  sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time",    sa.DateTime(timezone=True), nullable=False),
        sa.Column("final_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("status",
                  sa.Enum("pending", "confirmed", "cancelled", "done",
                          name="appointment_status"),
                  nullable=False, server_default="pending"),
        sa.Column("created_at",  sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["client_id"],  ["users.id"],    ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["master_id"],  ["masters.id"],  ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("end_time > start_time",
                           name="ck_appointments_end_after_start"),
        sa.CheckConstraint("final_price >= 0",
                           name="ck_appointments_price_non_negative"),
    )
    op.create_index("ix_appointments_client", "appointments", ["client_id"])
    op.create_index("ix_appointments_master", "appointments", ["master_id"])
    op.create_index("ix_appointments_time",   "appointments", ["start_time", "end_time"])
    op.create_index("ix_appointments_status", "appointments", ["status"])

    # EXCLUDE USING gist — нельзя выразить через SQLAlchemy, пишем SQL напрямую.
    # WHERE (status <> 'cancelled') — отменённая запись не блокирует слот навсегда.
    op.execute("""
        ALTER TABLE appointments
        ADD CONSTRAINT no_double_booking
        EXCLUDE USING gist (
            master_id WITH =,
            tstzrange(start_time, end_time, '[)') WITH &&
        )
        WHERE (status <> 'cancelled')
    """)

    # ── notifications ─────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id",             postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("appointment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type",
                  sa.Enum("confirmation", "reminder_24h", "reminder_1h", "cancellation",
                          name="notification_type"),
                  nullable=False),
        sa.Column("channel",
                  sa.Enum("email", "messenger", name="notification_channel"),
                  nullable=False, server_default="email"),
        sa.Column("scheduled_at",  sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at",       sa.DateTime(timezone=True)),
        sa.Column("status",
                  sa.Enum("pending", "sent", "failed", name="notification_status"),
                  nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"],
                                ondelete="CASCADE"),
        sa.UniqueConstraint("appointment_id", "type", "channel",
                            name="uq_notifications_appointment_type_channel"),
    )
    op.create_index(
        "ix_notifications_pending", "notifications", ["scheduled_at"],
        postgresql_where=sa.text("status = 'pending'"),
    )

    # ── reviews ───────────────────────────────────────────────────
    op.create_table(
        "reviews",
        sa.Column("id",             postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("appointment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_id",      postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("master_id",      postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("service_id",     postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating",         sa.SmallInteger, nullable=False),
        sa.Column("comment",        sa.Text),
        sa.Column("is_published",   sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at",     sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"],      ["users.id"],        ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["master_id"],      ["masters.id"],      ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_id"],     ["services.id"],     ondelete="CASCADE"),
        sa.UniqueConstraint("appointment_id", name="uq_reviews_appointment"),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating_range"),
    )
    op.create_index("ix_reviews_master",  "reviews", ["master_id"])
    op.create_index("ix_reviews_service", "reviews", ["service_id"])

    # ── password_reset_tokens ─────────────────────────────────────
    op.create_table(
        "password_reset_tokens",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id",    postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at",    sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token_hash", name="uq_password_reset_tokens_hash"),
    )
    op.create_index("ix_password_reset_tokens_user", "password_reset_tokens", ["user_id"])

    # ── login_attempts ────────────────────────────────────────────
    op.create_table(
        "login_attempts",
        sa.Column("id",              postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("email_attempted", sa.String(255), nullable=False),
        sa.Column("user_id",         postgresql.UUID(as_uuid=True)),
        sa.Column("ip_address",      sa.String(45)),
        sa.Column("success",         sa.Boolean, nullable=False),
        sa.Column("created_at",      sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_login_attempts_email_created", "login_attempts",
                    ["email_attempted", "created_at"])

    # ── Функция расчёта финальной цены ───────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION get_appointment_price(
            p_master_id  UUID,
            p_service_id UUID
        )
        RETURNS NUMERIC(10, 2)
        LANGUAGE sql
        STABLE
        AS $$
            SELECT COALESCE(
                ms.price_override,
                s.price * m.coefficient
            )
            FROM master_services ms
            JOIN services s ON s.id = ms.service_id
            JOIN masters  m ON m.id = ms.master_id
            WHERE ms.master_id  = p_master_id
              AND ms.service_id = p_service_id;
        $$
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS get_appointment_price")
    op.drop_table("login_attempts")
    op.drop_table("password_reset_tokens")
    op.drop_table("reviews")
    op.drop_table("notifications")
    op.execute("ALTER TABLE appointments DROP CONSTRAINT IF EXISTS no_double_booking")
    op.drop_table("appointments")
    op.drop_table("schedules")
    op.drop_table("master_services")
    op.drop_table("services")
    op.drop_table("masters")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS notification_status")
    op.execute("DROP TYPE IF EXISTS notification_channel")
    op.execute("DROP TYPE IF EXISTS notification_type")
    op.execute("DROP TYPE IF EXISTS appointment_status")
    op.execute("DROP TYPE IF EXISTS user_role")
