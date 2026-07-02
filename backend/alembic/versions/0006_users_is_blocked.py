"""users.is_blocked — блокировка аккаунта (ТЗ 4.2 MIN)

Revision ID: 0006_users_is_blocked
Revises: 0005_drop_notifications
Create Date: 2026-07-02 00:00:00.000000

Блокировка — не мягкое удаление: аккаунт и история остаются, но вход
и действия по уже выданному токену запрещены (проверяется в login и
get_current_user).
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_users_is_blocked"
down_revision = "0005_drop_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_blocked", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("users", "is_blocked")
