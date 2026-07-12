"""AppointmentService.reschedule() — фейковые репозитории, без БД (см.
test_appointment_create_guards.py/test_slots.py за тем же паттерном)."""
import uuid
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.enums import AppointmentStatus, UserRole
from app.services import appointment_service as appointment_service_module
from app.services.appointment_service import AppointmentService

MASTER_USER_ID = uuid.uuid4()
MASTER_ID = uuid.uuid4()
APPOINTMENT_ID = uuid.uuid4()
FUTURE = datetime.now(timezone.utc) + timedelta(days=1)
FUTURE_END = FUTURE + timedelta(minutes=30)
NEW_START = FUTURE + timedelta(hours=2)


def make_appointment(*, status=AppointmentStatus.pending, master_id=MASTER_ID,
                     start_time=FUTURE, end_time=FUTURE_END):
    # Полный набор полей — reschedule() в конце сериализует через
    # AppointmentResponse.model_validate(), которому нужны все вложенные
    # объекты (client/master/service), а не только то, что использует сама
    # бизнес-логика reschedule (client.email/first_name, *_name-свойства).
    client = SimpleNamespace(id=uuid.uuid4(), email="client@example.com",
                             first_name="Иван", last_name="Иванов", phone=None)
    master = SimpleNamespace(id=master_id, first_name="Пётр", last_name="Петров",
                             specialization=None, photo_url=None, coefficient=Decimal("1.00"))
    service = SimpleNamespace(id=uuid.uuid4(), name="Стрижка", description=None,
                              price=Decimal("1000.00"), duration_min=30, is_active=True)
    return SimpleNamespace(
        id=APPOINTMENT_ID, master_id=master_id, client=client, master=master,
        service=service, status=status, start_time=start_time, end_time=end_time,
        final_price=Decimal("1000.00"), created_at=datetime.now(timezone.utc),
        service_name="Стрижка", master_name="Пётр Петров",
    )


class FakeAppointmentRepo:
    def __init__(self, appointment, *, overlap=None):
        self.appointment = appointment
        self.overlap = overlap
        self.updated = None

    def get_by_id(self, appointment_id):
        return self.appointment

    def get_overlapping(self, master_id, start_time, end_time, exclude_id=None):
        return self.overlap

    def update_schedule(self, appointment, start_time, end_time):
        appointment.start_time = start_time
        appointment.end_time = end_time
        self.updated = appointment
        return appointment


class FakeMasterRepo:
    def __init__(self, *, owns=True):
        self.owns = owns

    def get_by_user_id(self, user_id):
        return SimpleNamespace(id=MASTER_ID if self.owns else uuid.uuid4())


class FakeScheduleRepo:
    def get_by_master_and_day(self, master_id, day_of_week):
        return SimpleNamespace(start_time=time(0, 0), end_time=time(23, 59), is_working=True)


def make_service(*, appointment=None, overlap=None, owns_master=True):
    svc = AppointmentService.__new__(AppointmentService)
    svc.db = SimpleNamespace(rollback=lambda: None)
    svc.appointment_repo = FakeAppointmentRepo(appointment or make_appointment(), overlap=overlap)
    svc.master_repo = FakeMasterRepo(owns=owns_master)
    svc.schedule_repo = FakeScheduleRepo()
    return svc


def make_master_user():
    return SimpleNamespace(id=MASTER_USER_ID, role=UserRole.master)


def make_admin_user():
    return SimpleNamespace(id=uuid.uuid4(), role=UserRole.admin)


class TestRescheduleOwnership:
    def test_owning_master_can_reschedule(self, monkeypatch):
        monkeypatch.setattr(appointment_service_module, "send_email", lambda **kw: None)
        svc = make_service()
        result = svc.reschedule(APPOINTMENT_ID, NEW_START, make_master_user())
        assert result.start_time == NEW_START

    def test_other_master_is_rejected(self):
        svc = make_service(owns_master=False)
        with pytest.raises(HTTPException) as exc:
            svc.reschedule(APPOINTMENT_ID, NEW_START, make_master_user())
        assert exc.value.status_code == 403

    def test_admin_can_reschedule_any_appointment(self, monkeypatch):
        monkeypatch.setattr(appointment_service_module, "send_email", lambda **kw: None)
        svc = make_service(owns_master=False)
        result = svc.reschedule(APPOINTMENT_ID, NEW_START, make_admin_user())
        assert result.start_time == NEW_START


class TestRescheduleStatusGuard:
    @pytest.mark.parametrize("status", [AppointmentStatus.done, AppointmentStatus.cancelled])
    def test_terminal_status_is_rejected(self, status):
        svc = make_service(appointment=make_appointment(status=status))
        with pytest.raises(HTTPException) as exc:
            svc.reschedule(APPOINTMENT_ID, NEW_START, make_master_user())
        assert exc.value.status_code == 400

    def test_confirmed_can_be_rescheduled(self, monkeypatch):
        monkeypatch.setattr(appointment_service_module, "send_email", lambda **kw: None)
        svc = make_service(appointment=make_appointment(status=AppointmentStatus.confirmed))
        result = svc.reschedule(APPOINTMENT_ID, NEW_START, make_master_user())
        assert result.start_time == NEW_START


class TestReschedulePastAndOverlap:
    def test_rejects_past_start_time(self):
        svc = make_service()
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        with pytest.raises(HTTPException) as exc:
            svc.reschedule(APPOINTMENT_ID, past, make_master_user())
        assert exc.value.status_code == 400

    def test_rejects_overlapping_slot(self):
        svc = make_service(overlap=SimpleNamespace(id=uuid.uuid4()))
        with pytest.raises(HTTPException) as exc:
            svc.reschedule(APPOINTMENT_ID, NEW_START, make_master_user())
        assert exc.value.status_code == 409


class TestRescheduleSideEffects:
    def test_preserves_original_duration(self, monkeypatch):
        monkeypatch.setattr(appointment_service_module, "send_email", lambda **kw: None)
        svc = make_service()
        result = svc.reschedule(APPOINTMENT_ID, NEW_START, make_master_user())
        assert result.end_time - result.start_time == timedelta(minutes=30)

    def test_notifies_client_by_email(self, monkeypatch):
        sent = []
        monkeypatch.setattr(appointment_service_module, "send_email",
                            lambda **kw: sent.append(kw))
        svc = make_service()
        svc.reschedule(APPOINTMENT_ID, NEW_START, make_master_user())
        assert len(sent) == 1
        assert sent[0]["to"] == "client@example.com"
        assert "перенесена" in sent[0]["subject"].lower()
