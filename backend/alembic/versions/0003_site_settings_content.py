"""Site settings content (CMS)

Revision ID: 0003_site_settings_content
Revises: 0002_site_settings
Create Date: 2026-06-24 00:00:00.000000

Заменяет узкоспециальный hero_photo_url на общую JSONB-колонку content,
которая хранит весь редактируемый текст сайта (шапка/главная/футер) —
см. SiteContent в schemas/site_settings.py. Существующее значение
hero_photo_url переносится в content.hero.photo_url.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_site_settings_content"
down_revision = "0002_site_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "site_settings",
        sa.Column("content", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.execute("""
        UPDATE site_settings
        SET content = jsonb_build_object('hero', jsonb_build_object('photo_url', hero_photo_url))
        WHERE hero_photo_url IS NOT NULL
    """)
    op.drop_column("site_settings", "hero_photo_url")


def downgrade() -> None:
    op.add_column("site_settings", sa.Column("hero_photo_url", sa.String(2048)))
    op.execute("""
        UPDATE site_settings
        SET hero_photo_url = content -> 'hero' ->> 'photo_url'
    """)
    op.drop_column("site_settings", "content")
