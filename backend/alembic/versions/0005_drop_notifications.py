"""Drop unused notifications subsystem and get_appointment_price()

Revision ID: 0005_drop_notifications
Revises: 0004_masters_sched_created_at
Create Date: 2026-07-02 00:00:00.000000

Подсистема уведомлений (таблица, три enum-типа) была спроектирована «на
вырост», но ни один сервис/роут никогда не создавал уведомления, а воркера
для отправки нет — мёртвая схема только вводила в заблуждение (ISSUES.md 6.1).
Заодно удаляется SQL-функция get_appointment_price(): цена всегда считается
в Python (AppointmentService), вторая реализация той же формулы могла
разойтись с первой (6.2).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_drop_notifications"
down_revision = "0004_masters_sched_created_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_notifications_pending", table_name="notifications")
    op.drop_table("notifications")
    op.execute("DROP TYPE IF EXISTS notification_status")
    op.execute("DROP TYPE IF EXISTS notification_channel")
    op.execute("DROP TYPE IF EXISTS notification_type")
    op.execute("DROP FUNCTION IF EXISTS get_appointment_price")


def downgrade() -> None:
    # Восстанавливаем схему в том виде, в каком её создавала 0001_initial
    # (без get_appointment_price — функция была мёртвой с самого начала).
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("appointment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type",
                  sa.Enum("confirmation", "reminder_24h", "reminder_1h", "cancellation",
                          name="notification_type"),
                  nullable=False),
        sa.Column("channel",
                  sa.Enum("email", "messenger", name="notification_channel"),
                  nullable=False, server_default="email"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
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
