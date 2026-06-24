"""Site settings

Revision ID: 0002_site_settings
Revises: 0001_initial
Create Date: 2026-06-24 00:00:00.000000

Singleton-таблица для глобальных настроек сайта (сейчас — только
фото в шапке главной страницы, которое раньше выбиралось автоматически
из фото мастеров). Строка создаётся лениво в SiteSettingsService.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_site_settings"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "site_settings",
        sa.Column("id",             postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("hero_photo_url", sa.String(2048)),
        sa.Column("created_at",     sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )


def downgrade() -> None:
    op.drop_table("site_settings")
