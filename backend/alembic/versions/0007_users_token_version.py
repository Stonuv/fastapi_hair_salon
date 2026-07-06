"""users.token_version — отзыв ранее выданных JWT

Revision ID: 0007_users_token_version
Revises: 0006_users_is_blocked
Create Date: 2026-07-06 00:00:00.000000

Закрывает признанный компромисс "JWT без отзыва" (README): значение
зашивается в payload токена при выдаче и сверяется в get_current_user на
каждый запрос. Инкремент — при logout, смене/сбросе пароля и блокировке.
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_users_token_version"
down_revision = "0006_users_is_blocked"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("token_version", sa.Integer(), nullable=False,
                  server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("users", "token_version")
