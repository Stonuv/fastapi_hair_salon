"""users: email_verified_at + email_verification_tokens table

Revision ID: 0012_email_verification
Revises: 0011_users_email_nullable
Create Date: 2026-07-14 00:00:00.000000

Подтверждение email при регистрации — тот же паттерн, что и
password_reset_tokens (0009 sessions / password reset): в БД хранится
только SHA-256 хеш токена, сама ссылка уходит письмом. NULL в
email_verified_at — email ещё не подтверждён; иначе метка времени
подтверждения (тот же приём, что reminder_*_sent_at из 0010). Email,
полученный от VK ID через OAuth, считается подтверждённым сразу — VK уже
доказал владение аккаунтом (см. vk_oauth_service); подтверждение письмом
нужно только для email, введённого пользователем вручную (обычная
регистрация или последующая смена email в профиле).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0012_email_verification"
down_revision = "0011_users_email_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True)))

    op.create_table(
        "email_verification_tokens",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id",    postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at",    sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token_hash", name="uq_email_verification_tokens_token_hash"),
    )
    op.create_index("ix_email_verification_tokens_user", "email_verification_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_email_verification_tokens_user", table_name="email_verification_tokens")
    op.drop_table("email_verification_tokens")
    op.drop_column("users", "email_verified_at")
