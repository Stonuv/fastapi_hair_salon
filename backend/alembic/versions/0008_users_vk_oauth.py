"""users: nullable password_hash + vk_user_id (VK ID OAuth)

Revision ID: 0008_users_vk_oauth
Revises: 0007_users_token_version
Create Date: 2026-07-11 00:00:00.000000

VK ID login создаёт пользователей без пароля (password_hash становится
опциональным) и привязывает VK-аккаунт через vk_user_id — уникальность,
как у email/phone, обеспечена частичным индексом (WHERE deleted_at IS NULL),
чтобы мягко удалённый пользователь не блокировал повторную привязку.
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_users_vk_oauth"
down_revision = "0007_users_token_version"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=True)
    op.add_column("users", sa.Column("vk_user_id", sa.String(64), nullable=True))
    op.create_index(
        "uq_users_vk_user_id_active", "users", ["vk_user_id"], unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND vk_user_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_users_vk_user_id_active", table_name="users")
    op.drop_column("users", "vk_user_id")
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=False)
