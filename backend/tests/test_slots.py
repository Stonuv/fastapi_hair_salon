"""Генерация свободных слотов — сервис с фейковыми репозиториями, без БД."""
import uuid
from datetime import date, datetime, time, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.appointment_service import AppointmentService

MASTER_ID = uuid.uuid4()
SERVICE_ID = uuid.uuid4()
TOMORROW = date.today() + timedelta(days=7)


def _dt(t: time) -> datetime:
    return datetime.combine(TOMORROW, t, tzinfo=timezone.utc)


class FakeMasterRepo:
    def __init__(self, active=True, offers_service=True):
        self.active = active
        self.offers = offers_service

    def get_by_id(self, master_id):
        return SimpleNamespace(id=master_id, is_active=self.active)

    def get_master_service(self, master_id, service_id):
        return SimpleNamespace() if self.offers else None


class FakeServiceRepo:
    def __init__(self, duration_min=30, active=True):
        self.duration_min = duration_min
        self.active = active

    def get_by_id(self, service_id):
        return SimpleNamespace(id=service_id, duration_min=self.duration_min,
                               is_active=self.active)


class FakeScheduleRepo:
    def __init__(self, start=time(10), end=time(12), is_working=True, exists=True):
        self.schedule = (SimpleNamespace(start_time=start, end_time=end,
                                         is_working=is_working)
                         if exists else None)

    def get_by_master_and_day(self, master_id, day_of_week):
        return self.schedule


class FakeAppointmentRepo:
    def __init__(self, booked=()):
        # booked: (start, end) или (start, end, id) — id по умолчанию своё
        # для каждой записи, чтобы exclude_appointment_id можно было тестировать.
        self.booked = [b if len(b) == 3 else (*b, uuid.uuid4()) for b in booked]

    def get_by_master_in_range(self, master_id, date_from, date_to):
        return [SimpleNamespace(id=i, start_time=s, end_time=e) for s, e, i in self.booked]


def make_service(*, booked=(), duration_min=30, schedule_kwargs=None,
                 master_repo=None, service_repo=None):
    svc = AppointmentService.__new__(AppointmentService)
    svc.db = None
    svc.master_repo = master_repo or FakeMasterRepo()
    svc.service_repo = service_repo or FakeServiceRepo(duration_min=duration_min)
    svc.schedule_repo = FakeScheduleRepo(**(schedule_kwargs or {}))
    svc.appointment_repo = FakeAppointmentRepo(booked=booked)
    return svc


def slot_times(result):
    return [(s.start_time.timetz().replace(tzinfo=None),
             s.end_time.timetz().replace(tzinfo=None)) for s in result.slots]


class TestSlotGeneration:
    def test_empty_day_yields_full_grid(self):
        result = make_service().get_available_slots(MASTER_ID, TOMORROW, SERVICE_ID)
        assert slot_times(result) == [
            (time(10, 0), time(10, 30)),
            (time(10, 30), time(11, 0)),
            (time(11, 0), time(11, 30)),
            (time(11, 30), time(12, 0)),
        ]

    def test_misaligned_booking_does_not_eat_two_slots(self):
        # Запись 10:15–10:45 не по сетке: следующий слот начинается в 10:45,
        # а не пропадают и 10:00, и 10:30 (ISSUES.md 4.3)
        svc = make_service(booked=[(_dt(time(10, 15)), _dt(time(10, 45)))])
        result = svc.get_available_slots(MASTER_ID, TOMORROW, SERVICE_ID)
        assert slot_times(result) == [
            (time(10, 45), time(11, 15)),
            (time(11, 15), time(11, 45)),
        ]

    def test_booking_overlapping_window_start_blocks_slot(self):
        # Запись, начавшаяся до рабочего окна, но заходящая в него (4.2)
        svc = make_service(booked=[(_dt(time(9, 0)), _dt(time(10, 30)))])
        result = svc.get_available_slots(MASTER_ID, TOMORROW, SERVICE_ID)
        assert slot_times(result)[0] == (time(10, 30), time(11, 0))

    def test_non_working_day_returns_empty(self):
        svc = make_service(schedule_kwargs={"is_working": False})
        result = svc.get_available_slots(MASTER_ID, TOMORROW, SERVICE_ID)
        assert result.slots == []

    def test_no_schedule_returns_empty(self):
        svc = make_service(schedule_kwargs={"exists": False})
        result = svc.get_available_slots(MASTER_ID, TOMORROW, SERVICE_ID)
        assert result.slots == []

    def test_past_slots_filtered_for_today(self):
        svc = make_service(schedule_kwargs={"start": time(0, 0), "end": time(23, 59)})
        result = svc.get_available_slots(MASTER_ID, date.today(), SERVICE_ID)
        now = datetime.now(timezone.utc)
        assert all(s.start_time > now for s in result.slots)

    def test_inactive_master_404(self):
        svc = make_service(master_repo=FakeMasterRepo(active=False))
        with pytest.raises(HTTPException) as exc:
            svc.get_available_slots(MASTER_ID, TOMORROW, SERVICE_ID)
        assert exc.value.status_code == 404

    def test_service_not_offered_400(self):
        svc = make_service(master_repo=FakeMasterRepo(offers_service=False))
        with pytest.raises(HTTPException) as exc:
            svc.get_available_slots(MASTER_ID, TOMORROW, SERVICE_ID)
        assert exc.value.status_code == 400


class TestExcludeAppointmentId:
    def test_excluded_appointment_does_not_block_its_own_slot(self):
        """Перенос записи мастером: текущий слот самой переносимой записи не
        должен считаться занятым при выборе нового времени (self-overlap)."""
        own_id = uuid.uuid4()
        svc = make_service(booked=[(_dt(time(10, 0)), _dt(time(10, 30)), own_id)])
        result = svc.get_available_slots(MASTER_ID, TOMORROW, SERVICE_ID,
                                         exclude_appointment_id=own_id)
        assert slot_times(result) == [
            (time(10, 0), time(10, 30)),
            (time(10, 30), time(11, 0)),
            (time(11, 0), time(11, 30)),
            (time(11, 30), time(12, 0)),
        ]

    def test_other_appointments_still_block_when_excluding_one(self):
        own_id = uuid.uuid4()
        svc = make_service(booked=[
            (_dt(time(10, 0)), _dt(time(10, 30)), own_id),
            (_dt(time(11, 0)), _dt(time(11, 30)), uuid.uuid4()),
        ])
        result = svc.get_available_slots(MASTER_ID, TOMORROW, SERVICE_ID,
                                         exclude_appointment_id=own_id)
        assert slot_times(result) == [
            (time(10, 0), time(10, 30)),
            (time(10, 30), time(11, 0)),
            (time(11, 30), time(12, 0)),
        ]
