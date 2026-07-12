"""sessions: refresh-token table for per-device login/logout

Revision ID: 0009_sessions
Revises: 0008_users_vk_oauth
Create Date: 2026-07-12 00:00:00.000000

Заменяет модель "logout инвалидирует все токены разом" (token_version) на
полноценные сессии: каждый вход создаёт строку с SHA-256 хешем refresh-
токена, logout удаляет ровно эту строку (остальные устройства не
затрагиваются). token_version сохраняется как отдельный механизм для
событий безопасности (смена/сброс пароля, блокировка) — их обработчики
теперь дополнительно чистят все sessions пользователя.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0009_sessions"
down_revision = "0008_users_vk_oauth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id",    postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token_hash", name="uq_sessions_token_hash"),
    )
    op.create_index("ix_sessions_user", "sessions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_sessions_user", table_name="sessions")
    op.drop_table("sessions")
