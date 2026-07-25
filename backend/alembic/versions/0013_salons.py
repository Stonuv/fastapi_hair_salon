"""salons table + backfill "Салон №1"

Revision ID: 0013_salons
Revises: 0012_email_verification
Create Date: 2026-07-25 00:00:00.000000

Первый шаг функционала "Сеть парикмахерских" (см. ROADMAP.md §4). Только
создаёт таблицу и бэкфиллит ровно одну строку из уже сохранённого
site_settings.content — поведение приложения не меняется, таблицу пока
никто не читает. salon_id на users/masters/appointments и повышение
существующих admin до owner — в 0015 (обязательно после 0014, которая
добавляет само значение enum 'owner' в отдельной транзакции — см. env.py
и ROADMAP.md §4.7).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0013_salons"
down_revision = "0012_email_verification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "salons",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name",       sa.String(150), nullable=False),
        sa.Column("slug",       sa.String(150), nullable=False),
        sa.Column("address",    sa.String(300), nullable=False),
        sa.Column("phone",      sa.String(20)),
        sa.Column("open_time",  sa.Time, nullable=False),
        sa.Column("close_time", sa.Time, nullable=False),
        sa.Column("photo_url",  sa.String(500)),
        sa.Column("is_active",  sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.CheckConstraint("close_time > open_time", name="ck_salons_close_after_open"),
    )
    op.create_index("uq_salons_slug", "salons", ["slug"], unique=True)

    # Бэкфилл "Салон №1" из уже сохранённого контента сайта — если он есть.
    # SiteSettings создаётся лениво (см. models/site_settings.py), на свежей
    # БД до первого /api/setup строки может не быть вовсе — тогда content = {}
    # и все поля берут дефолт ниже. business_hours.open_time/close_time
    # сохранены как ISO-строки ("09:00:00") — SiteSettingsService.update()
    # сериализует через model_dump(mode="json").
    bind = op.get_bind()
    row = bind.execute(sa.text("SELECT content FROM site_settings LIMIT 1")).fetchone()
    content = (row[0] if row else None) or {}
    header = content.get("header") or {}
    footer = content.get("footer") or {}
    business_hours = content.get("business_hours") or {}

    bind.execute(
        sa.text(
            "INSERT INTO salons (name, slug, address, open_time, close_time) "
            "VALUES (:name, 'salon-1', :address, CAST(:open_time AS TIME), CAST(:close_time AS TIME))"
        ),
        {
            "name": header.get("brand_name") or "Салон №1",
            "address": footer.get("address") or "Адрес не указан",
            "open_time": business_hours.get("open_time") or "09:00:00",
            "close_time": business_hours.get("close_time") or "20:00:00",
        },
    )


def downgrade() -> None:
    op.drop_index("uq_salons_slug", table_name="salons")
    op.drop_table("salons")
