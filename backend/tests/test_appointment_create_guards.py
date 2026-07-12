"""AppointmentService.create() — лимит активных записей и запрет самозаписи
мастера. Фейковые репозитории, без БД (см. test_slots.py за тем же паттерном)."""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.schemas.appointment import AppointmentCreate
from app.services import appointment_service as appointment_service_module
from app.services.appointment_service import AppointmentService

MASTER_USER_ID = uuid.uuid4()
MASTER_ID = uuid.uuid4()
SERVICE_ID = uuid.uuid4()
CLIENT_ID = uuid.uuid4()
FUTURE = datetime.now(timezone.utc) + timedelta(days=1)


class FakeAppointmentRepo:
    def __init__(self, active_count=0):
        self.active_count = active_count

    def count_active_for_client(self, client_id):
        return self.active_count


class FakeMasterRepo:
    def get_by_id(self, master_id):
        return SimpleNamespace(id=master_id, user_id=MASTER_USER_ID, is_active=True,
                               coefficient=Decimal("1.00"))

    def get_master_service(self, master_id, service_id):
        return SimpleNamespace(price_override=None)


class FakeServiceRepo:
    def get_by_id(self, service_id):
        return SimpleNamespace(id=service_id, duration_min=30, is_active=True,
                               price=Decimal("1000.00"))


def make_service(*, active_count=0):
    svc = AppointmentService.__new__(AppointmentService)
    svc.db = None
    svc.appointment_repo = FakeAppointmentRepo(active_count=active_count)
    svc.master_repo = FakeMasterRepo()
    svc.service_repo = FakeServiceRepo()
    svc.schedule_repo = SimpleNamespace()
    return svc


def make_data(master_id=MASTER_ID):
    return AppointmentCreate(master_id=master_id, service_id=SERVICE_ID, start_time=FUTURE)


class TestActiveAppointmentLimit:
    def test_rejects_at_limit_before_touching_master_or_schedule(self, monkeypatch):
        monkeypatch.setattr(appointment_service_module.settings,
                            "max_active_appointments_per_client", 5)
        svc = make_service(active_count=5)
        with pytest.raises(HTTPException) as exc:
            svc.create(CLIENT_ID, make_data())
        assert exc.value.status_code == 400
        assert "активных записей" in exc.value.detail

    def test_allows_when_under_limit(self, monkeypatch):
        monkeypatch.setattr(appointment_service_module.settings,
                            "max_active_appointments_per_client", 5)
        svc = make_service(active_count=4)
        # Ниже лимита — лимит-проверка не должна бросать; следующая проверка
        # (self-booking) тоже пройдёт, значит create() дойдёт до schedule_repo
        # (FakeScheduleRepo не сконфигурирован здесь — падение будет уже на
        # другом шаге, что подтверждает: лимит не был причиной отказа).
        with pytest.raises(AttributeError):
            svc.create(CLIENT_ID, make_data())


class TestMasterCannotBookSelf:
    def test_rejects_when_client_is_the_master(self, monkeypatch):
        monkeypatch.setattr(appointment_service_module.settings,
                            "max_active_appointments_per_client", 5)
        svc = make_service(active_count=0)
        with pytest.raises(HTTPException) as exc:
            svc.create(MASTER_USER_ID, make_data())
        assert exc.value.status_code == 400
        assert "себе" in exc.value.detail
