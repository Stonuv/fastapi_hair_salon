"""user_role: add 'owner' enum value

Revision ID: 0014_user_role_owner
Revises: 0013_salons
Create Date: 2026-07-25 00:00:00.000001

Намеренно единственная строка в этой ревизии — ничего больше. PostgreSQL
запрещает использовать значение enum, добавленное ALTER TYPE ... ADD VALUE,
в той же транзакции, где оно добавлено. env.py теперь коммитит каждую
ревизию отдельно (transaction_per_migration=True) — 0015 (следующая)
уже увидит 'owner' закоммиченным и сможет им пользоваться. См. ROADMAP.md §4.7.
"""
from alembic import op

revision = "0014_user_role_owner"
down_revision = "0013_salons"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE 'owner'")


def downgrade() -> None:
    # PostgreSQL не поддерживает удаление значения enum напрямую (потребовало
    # бы пересоздать тип и перелить колонку) — и 0015 к этому моменту уже
    # использует 'owner' в данных (роль повышенных admin), так что откат
    # этой ревизии в отрыве от отката 0015 всё равно бы не имел смысла.
    raise NotImplementedError(
        "Откат добавления enum-значения 'owner' не поддерживается — "
        "откатывайте вместе с 0015 (см. её downgrade) через восстановление из бэкапа."
    )
