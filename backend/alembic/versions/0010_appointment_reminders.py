"""appointments: reminder_24h_sent_at / reminder_2h_sent_at

Revision ID: 0010_appointment_reminders
Revises: 0009_sessions
Create Date: 2026-07-12 00:00:00.000000

Напоминания клиентам за 24ч/2ч до записи (ReminderService, опрашивается
asyncio-лупом в процессе бэкенда — см. app/scheduler.py). NULL — ещё не
отправлено; иначе метка времени отправки. Пойнтово на appointments, а не
отдельная таблица "уведомлений" — та уже была и её снесли неиспользуемой
(см. 0005_drop_notifications).
"""
from alembic import op
import sqlalchemy as sa

revision = "0010_appointment_reminders"
down_revision = "0009_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("appointments", sa.Column("reminder_24h_sent_at", sa.DateTime(timezone=True)))
    op.add_column("appointments", sa.Column("reminder_2h_sent_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    op.drop_column("appointments", "reminder_2h_sent_at")
    op.drop_column("appointments", "reminder_24h_sent_at")
