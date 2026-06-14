"""Initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

Создаёт все таблицы по barbershop_schema.sql.
Отдельно добавляет:
  - расширение btree_gist (нужно для EXCLUDE)
  - EXCLUDE USING gist на appointments (защита от двойного бронирования)
  - вспомогательную функцию get_appointment_price()
Эти три вещи SQLAlchemy не умеет генерировать автоматически.
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
    # Примечание: ENUM-типы создаются автоматически SQLAlchemy
    # при первом create_table где они используются.
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
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("phone", name="uq_users_phone"),
    )
    op.create_index("idx_users_email", "users", ["email"])

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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_masters_user_id"),
        sa.CheckConstraint("coefficient > 0", name="ck_masters_coefficient_positive"),
    )
    op.create_index("idx_masters_user_id", "masters", ["user_id"])

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
        sa.CheckConstraint("price >= 0",       name="ck_services_price_non_negative"),
        sa.CheckConstraint("duration_min > 0", name="ck_services_duration_positive"),
    )

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
    op.create_index("idx_master_services_master",  "master_services", ["master_id"])
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
    op.create_index("idx_schedules_master_id", "schedules", ["master_id"])

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
    op.create_index("idx_appointments_client", "appointments", ["client_id"])
    op.create_index("idx_appointments_master", "appointments", ["master_id"])
    op.create_index("idx_appointments_time",   "appointments", ["start_time", "end_time"])

    # EXCLUDE USING gist — нельзя выразить через SQLAlchemy, пишем SQL напрямую
    op.execute("""
        ALTER TABLE appointments
        ADD CONSTRAINT no_double_booking
        EXCLUDE USING gist (
            master_id WITH =,
            tstzrange(start_time, end_time, '[)') WITH &&
        )
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
        "idx_notifications_pending", "notifications", ["scheduled_at"],
        postgresql_where=sa.text("status = 'pending'"),
    )

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
