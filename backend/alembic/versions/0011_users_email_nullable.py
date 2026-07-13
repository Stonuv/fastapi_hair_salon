"""users: email nullable (VK signup without email)

Revision ID: 0011_users_email_nullable
Revises: 0010_appointment_reminders
Create Date: 2026-07-13 00:00:00.000000

VK ID отдаёт email не всегда (пользователь может не привязать его к
аккаунту VK) — раньше это блокировало регистрацию (vk_email_required).
Теперь такой пользователь заводится с email=NULL и указывает email позже,
при оформлении первой записи (см. AppointmentService/routes/appointments.py).
Уникальный индекс uq_users_email_active не страдает — Postgres не считает
NULL равным NULL, так что несколько пользователей с email=NULL уживаются.
"""
from alembic import op
import sqlalchemy as sa

revision = "0011_users_email_nullable"
down_revision = "0010_appointment_reminders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "email", existing_type=sa.String(255), nullable=True)


def downgrade() -> None:
    op.alter_column("users", "email", existing_type=sa.String(255), nullable=False)
