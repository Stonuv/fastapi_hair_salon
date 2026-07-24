"""EXCLUDE USING gist (no_double_booking) — единственная гарантия от
двойного бронирования, которую до этой фазы проверяли только вручную на
стенде (см. docstring conftest.py)."""
import asyncio
from datetime import timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.models.appointment import Appointment
from app.models.enums import UserRole
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.appointment import AppointmentCreate
from app.schemas.user import UserCreate
from app.services.auth_service import hash_password

from .conftest import TEST_PASSWORD, next_weekday_at

pytestmark = pytest.mark.integration


def _make_client(db_session, suffix: str):
    user = UserRepository(db_session).create(
        UserCreate(
            email=f"client-{suffix}@example.com",
            first_name="Клиент", last_name=suffix, password=TEST_PASSWORD,
        ),
        hash_password(TEST_PASSWORD),
        role=UserRole.client,
    )
    db_session.commit()
    return user


def test_exclusion_constraint_rejects_overlapping_appointment(db_session, bookable_setup):
    """Прямая проверка на уровне репозитория, в обход сервисного
    pre-flight-чека (AppointmentService.get_overlapping) — доказывает, что
    пересечение физически невозможно на уровне БД, а не только что сервис
    вежливо отказывает при последовательных запросах."""
    client_a = _make_client(db_session, "a")
    client_b = _make_client(db_session, "b")
    repo = AppointmentRepository(db_session)

    start = next_weekday_at(weekday=0, hour=10)
    end = start + timedelta(minutes=bookable_setup.service.duration_min)
    repo.create(
        client_a.id,
        AppointmentCreate(
            master_id=bookable_setup.master.id,
            service_id=bookable_setup.service.id,
            start_time=start,
        ),
        end, bookable_setup.service.price,
    )
    db_session.commit()

    # Частичное пересечение (сдвиг на полслота), не точное совпадение —
    # EXCLUDE должен ловить пересечение диапазонов, а не только дубликат.
    overlap_start = start + timedelta(minutes=30)
    overlap_end = overlap_start + timedelta(minutes=bookable_setup.service.duration_min)

    with pytest.raises(IntegrityError) as exc_info:
        repo.create(
            client_b.id,
            AppointmentCreate(
                master_id=bookable_setup.master.id,
                service_id=bookable_setup.service.id,
                start_time=overlap_start,
            ),
            overlap_end, bookable_setup.service.price,
        )
    db_session.rollback()

    assert exc_info.value.orig.diag.constraint_name == "no_double_booking"


@pytest.mark.anyio
async def test_concurrent_booking_requests_only_one_succeeds(client, db_session, bookable_setup):
    """Две одновременные HTTP-заявки на один и тот же слот. Второй ответ не
    должен быть 500 ни при каком раскладе гонки: либо pre-flight-чек успевает
    поймать конфликт (409), либо ловится IntegrityError от самого констрейнта
    после гонки (тоже 409, см. AppointmentService.create). В обоих случаях в
    БД должна остаться ровно одна запись на этот слот."""
    start = next_weekday_at(weekday=0, hour=14)

    tokens = []
    for suffix in ("a", "b"):
        resp = await client.post("/api/auth/register", json={
            "email": f"racer-{suffix}@example.com",
            "first_name": "Гонщик", "last_name": suffix,
            "password": TEST_PASSWORD,
        })
        assert resp.status_code == 201
        tokens.append(resp.json()["access_token"])

    payload = {
        "master_id": str(bookable_setup.master.id),
        "service_id": str(bookable_setup.service.id),
        "start_time": start.isoformat(),
    }

    responses = await asyncio.gather(*(
        client.post("/api/appointments", json=payload,
                    headers={"Authorization": f"Bearer {token}"})
        for token in tokens
    ))

    statuses = sorted(r.status_code for r in responses)
    assert statuses == [201, 409], f"unexpected statuses: {[r.text for r in responses]}"

    count = db_session.execute(
        select(func.count()).where(
            Appointment.master_id == bookable_setup.master.id,
            Appointment.start_time == start,
        )
    ).scalar_one()
    assert count == 1
