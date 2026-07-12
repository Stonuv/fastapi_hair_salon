"""Единое время работы салона (ISSUES #36) — жёсткая граница и для
расписаний мастеров (MasterService), и для самих записей (AppointmentService,
бэкстоп на случай расписаний, заведённых раньше). Фейковые репозитории, без БД."""
import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.schemas.appointment import AppointmentCreate
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.services.appointment_service import AppointmentService
from app.services.master_service import MasterService

MASTER_ID = uuid.uuid4()
SERVICE_ID = uuid.uuid4()
CLIENT_ID = uuid.uuid4()

BUSINESS_HOURS = SimpleNamespace(open_time=time(9, 0), close_time=time(20, 0))


class FakeSiteSettingsService:
    def get(self):
        return SimpleNamespace(business_hours=BUSINESS_HOURS)


# ── MasterService.set_schedule / update_schedule ────────────────────


class FakeScheduleRepoForMaster:
    def __init__(self, existing=None):
        self.existing = existing
        self.saved = None

    def get_by_master_and_day(self, master_id, day_of_week):
        return self.existing

    def create(self, master_id, data):
        self.saved = data
        return SimpleNamespace(id=uuid.uuid4(), master_id=master_id, day_of_week=data.day_of_week,
                               start_time=data.start_time, end_time=data.end_time,
                               is_working=data.is_working)

    def update(self, schedule, data):
        self.saved = data
        for field in ("start_time", "end_time", "is_working"):
            value = getattr(data, field, None)
            if value is not None:
                setattr(schedule, field, value)
        return schedule


def make_master_service(*, existing=None):
    svc = MasterService.__new__(MasterService)
    svc.master_repo = SimpleNamespace(get_by_id=lambda mid: SimpleNamespace(id=mid))
    svc.schedule_repo = FakeScheduleRepoForMaster(existing=existing)
    svc.site_settings_service = FakeSiteSettingsService()
    return svc


class TestSetScheduleBusinessHours:
    def test_rejects_start_before_salon_opens(self):
        svc = make_master_service()
        data = ScheduleCreate(day_of_week=0, start_time=time(8, 0), end_time=time(18, 0))
        with pytest.raises(HTTPException) as exc:
            svc.set_schedule(MASTER_ID, data)
        assert exc.value.status_code == 400
        assert "времени работы салона" in exc.value.detail

    def test_rejects_end_after_salon_closes(self):
        """Regression: барбершоп закрывается в 20:00 — мастер не должен
        мочь задать себе расписание до 21:00."""
        svc = make_master_service()
        data = ScheduleCreate(day_of_week=0, start_time=time(10, 0), end_time=time(21, 0))
        with pytest.raises(HTTPException) as exc:
            svc.set_schedule(MASTER_ID, data)
        assert exc.value.status_code == 400

    def test_accepts_schedule_within_business_hours(self):
        svc = make_master_service()
        data = ScheduleCreate(day_of_week=0, start_time=time(9, 0), end_time=time(20, 0))
        result = svc.set_schedule(MASTER_ID, data)
        assert result.start_time == time(9, 0)

    def test_day_off_is_not_checked_against_business_hours(self):
        """is_working=False — время передаётся, но день выходной, проверка
        часов работы салона не должна на это реагировать."""
        svc = make_master_service()
        data = ScheduleCreate(day_of_week=0, start_time=time(22, 0), end_time=time(23, 0), is_working=False)
        result = svc.set_schedule(MASTER_ID, data)
        assert result.is_working is False


class TestUpdateScheduleBusinessHours:
    def test_rejects_partial_update_pushing_past_close(self):
        existing = SimpleNamespace(id=uuid.uuid4(), master_id=MASTER_ID, day_of_week=0, start_time=time(9, 0), end_time=time(18, 0), is_working=True)
        svc = make_master_service(existing=existing)
        with pytest.raises(HTTPException) as exc:
            svc.update_schedule(MASTER_ID, 0, ScheduleUpdate(end_time=time(21, 0)))
        assert exc.value.status_code == 400

    def test_accepts_partial_update_within_bounds(self):
        existing = SimpleNamespace(id=uuid.uuid4(), master_id=MASTER_ID, day_of_week=0, start_time=time(9, 0), end_time=time(18, 0), is_working=True)
        svc = make_master_service(existing=existing)
        result = svc.update_schedule(MASTER_ID, 0, ScheduleUpdate(end_time=time(19, 0)))
        assert result.end_time == time(19, 0)

    def test_marking_day_off_skips_business_hours_check(self):
        existing = SimpleNamespace(id=uuid.uuid4(), master_id=MASTER_ID, day_of_week=0, start_time=time(9, 0), end_time=time(18, 0), is_working=True)
        svc = make_master_service(existing=existing)
        # is_working=False сам по себе не проходит валидацию end>start (нет
        # смысла её проверять для выходного) — но и часы работы салона не
        # должны блокировать это обновление.
        result = svc.update_schedule(MASTER_ID, 0, ScheduleUpdate(is_working=False))
        assert result.is_working is False


# ── AppointmentService._validate_within_schedule (бэкстоп) ─────────


class FakeScheduleRepoForAppointment:
    """Расписание мастера шире часов работы салона — как будто заведено
    до появления настройки (#36) — проверяем, что бэкстоп на уровне самой
    записи всё равно не даёт забронировать длинную услугу перед закрытием."""
    def get_by_master_and_day(self, master_id, day_of_week):
        return SimpleNamespace(start_time=time(8, 0), end_time=time(21, 0), is_working=True)


def make_fake_appointment(**overrides):
    client = SimpleNamespace(id=CLIENT_ID, email="client@example.com",
                             first_name="Иван", last_name="Иванов", phone=None)
    master = SimpleNamespace(id=MASTER_ID, first_name="Пётр", last_name="Петров",
                             specialization=None, photo_url=None, coefficient=Decimal("1.00"))
    service = SimpleNamespace(id=SERVICE_ID, name="Стрижка", description=None,
                              price=Decimal("1000.00"), duration_min=90, is_active=True)
    defaults = dict(
        id=uuid.uuid4(), client=client, master=master, service=service,
        status="pending", final_price=Decimal("1000.00"), created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_appointment_service():
    svc = AppointmentService.__new__(AppointmentService)
    svc.db = None
    created = {}

    def fake_create(client_id, data, end_time, final_price):
        created["appointment"] = make_fake_appointment(start_time=data.start_time, end_time=end_time)
        return created["appointment"]

    svc.appointment_repo = SimpleNamespace(
        count_active_for_client=lambda cid: 0,
        get_overlapping=lambda *a, **kw: None,
        create=fake_create,
        get_by_id=lambda aid: created["appointment"],
    )
    svc.master_repo = SimpleNamespace(
        get_by_id=lambda mid: SimpleNamespace(id=mid, user_id=uuid.uuid4(), is_active=True,
                                              coefficient=Decimal("1.00")),
        get_master_service=lambda mid, sid: SimpleNamespace(price_override=None),
    )
    svc.service_repo = SimpleNamespace(
        get_by_id=lambda sid: SimpleNamespace(id=sid, duration_min=90, is_active=True,
                                              price=Decimal("1000.00")),
    )
    svc.schedule_repo = FakeScheduleRepoForAppointment()
    svc.site_settings_service = FakeSiteSettingsService()
    return svc


def _next_weekday_at(hour, minute, weekday):
    """Ближайшая будущая дата с заданным днём недели (0=пн) и временем UTC."""
    d = date.today() + timedelta(days=1)
    while d.weekday() != weekday:
        d += timedelta(days=1)
    return datetime.combine(d, time(hour, minute), tzinfo=timezone.utc)


class TestAppointmentBackstop:
    def test_rejects_long_service_ending_after_salon_closes(self):
        """Regression (issue #36): барбершоп закрывается в 20:00, услуга 90
        минут в 19:30 закончилась бы в 21:00 — должно быть отклонено, даже
        если расписание САМОГО мастера (заведённое раньше) это разрешает."""
        svc = make_appointment_service()
        start = _next_weekday_at(19, 30, weekday=0)
        data = AppointmentCreate(master_id=MASTER_ID, service_id=SERVICE_ID, start_time=start)
        with pytest.raises(HTTPException) as exc:
            svc.create(CLIENT_ID, data)
        assert exc.value.status_code == 400
        assert "времени работы салона" in exc.value.detail

    def test_accepts_service_within_business_hours(self):
        svc = make_appointment_service()
        start = _next_weekday_at(18, 0, weekday=0)  # 18:00 + 90 мин = 19:30, до закрытия
        data = AppointmentCreate(master_id=MASTER_ID, service_id=SERVICE_ID, start_time=start)
        result = svc.create(CLIENT_ID, data)
        assert result.start_time == start
