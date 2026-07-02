"""created_at for masters and schedules

Revision ID: 0004_masters_schedules_created_at
Revises: 0003_site_settings_content
Create Date: 2026-07-02 00:00:00.000000

Выравнивает timestamps: masters и schedules — единственные таблицы без
created_at (TimestampMixin). Существующие строки получают now() через
server_default, как и во всех остальных таблицах.
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_masters_schedules_created_at"
down_revision = "0003_site_settings_content"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("masters", "schedules"):
        op.add_column(
            table,
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )


def downgrade() -> None:
    for table in ("masters", "schedules"):
        op.drop_column(table, "created_at")
