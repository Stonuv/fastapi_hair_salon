"""users/masters/appointments: salon_id + promote existing admin → owner

Revision ID: 0015_salon_scoping
Revises: 0014_user_role_owner
Create Date: 2026-07-25 00:00:00.000002

⚠️ Обязана ехать одним релизом с обновлённым get_current_admin/require_role
(см. backend/app/services/auth_service.py) — как только эта миграция
выполнится, все существующие admin физически становятся owner, и без
обновлённого кода они мгновенно теряют доступ к /api/admin/*. См. ROADMAP.md
§4.7.

Порядок отличается от §4.7 в одном важном месте: промоушен
`role='admin' → 'owner'` выполняется ДО добавления
ck_users_admin_requires_salon, а не после (как в документе). Причина —
CHECK CONSTRAINT в PostgreSQL валидируется по умолчанию против уже
существующих строк: на момент выполнения этой миграции в БД уже есть живой
admin с salon_id ещё NULL (колонка только что добавлена), и добавление
constraint'а в порядке "как в документе" упало бы прямо на нём. Промоушен
сначала убирает role='admin' у всех существующих строк — после него
constraint проверяется вхолостую (role <> 'admin' истинно для всех) и
дальше защищает только новые попытки создать salon-scoped admin без салона.
Конечное состояние БД идентично тому, что описано в §4.7 — отличается
только порядок применения внутри одной транзакции ревизии.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0015_salon_scoping"
down_revision = "0014_user_role_owner"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users.salon_id (nullable — только admin обязан его иметь) ───
    op.add_column(
        "users",
        sa.Column("salon_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("salons.id", ondelete="RESTRICT")),
    )
    op.create_index("ix_users_salon", "users", ["salon_id"],
                    postgresql_where=sa.text("salon_id IS NOT NULL"))

    # ── masters.salon_id / appointments.salon_id (nullable пока) ────
    op.add_column(
        "masters",
        sa.Column("salon_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("salons.id", ondelete="RESTRICT")),
    )
    op.add_column(
        "appointments",
        sa.Column("salon_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("salons.id", ondelete="RESTRICT")),
    )

    # ── Бэкфилл: единственный салон на этот момент истории ──────────
    op.execute("UPDATE masters SET salon_id = (SELECT id FROM salons LIMIT 1)")
    op.execute("UPDATE appointments SET salon_id = (SELECT id FROM salons LIMIT 1)")

    # ── Повышение существующих админов ───────────────────────────────
    # До этой миграции admin был chain-wide (salon-scoping не существовал),
    # значит каждый существующий admin честно становится owner. Новое,
    # salon-scoped значение 'admin' начинает выдаваться только вперёд,
    # явным действием owner'а (см. Фазу B). Должно случиться раньше
    # ck_users_admin_requires_salon — см. docstring модуля.
    op.execute("UPDATE users SET role = 'owner' WHERE role = 'admin'")

    op.create_check_constraint(
        "ck_users_admin_requires_salon", "users",
        "role <> 'admin' OR salon_id IS NOT NULL",
    )

    # ── masters/appointments.salon_id → NOT NULL + индексы ───────────
    op.alter_column("masters", "salon_id", nullable=False)
    op.alter_column("appointments", "salon_id", nullable=False)
    op.create_index("ix_masters_salon", "masters", ["salon_id"])
    op.create_index("ix_appointments_salon", "appointments", ["salon_id"])


def downgrade() -> None:
    # Как и 0014 — не поддерживается. role='owner' → 'admin' необратимо
    # неоднозначно (нельзя отличить исходных admin от owner, созданных уже
    # после этой миграции), а откатить одну 0015 без отката 0014 всё равно
    # нельзя (0014.downgrade сама бросает NotImplementedError). Рефолбэк —
    # восстановление из бэкапа (см. README «Бэкапы»).
    raise NotImplementedError(
        "Откат 0015 не поддерживается — восстанавливайте из бэкапа."
    )
