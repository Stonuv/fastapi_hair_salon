"""Валидация схем: пароли (лимит bcrypt), расписание, таймзоны, деньги."""
import uuid
from datetime import time, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.appointment import AppointmentCreate
from app.schemas.auth import PasswordResetConfirm
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.schemas.service import ServiceCreate, ServiceResponse
from app.schemas.user import UserCreate


def _user(password: str) -> UserCreate:
    return UserCreate(email="a@b.c", first_name="Имя", last_name="Фамилия",
                      password=password)


class TestPasswordLimits:
    def test_short_password_rejected(self):
        with pytest.raises(ValidationError):
            _user("1234567")

    def test_long_password_rejected(self):
        # bcrypt 5.x бросает ValueError на >72 байта — схема должна отсечь раньше
        with pytest.raises(ValidationError):
            _user("x" * 73)

    def test_multibyte_password_over_72_bytes_rejected(self):
        # 40 кириллических символов = 80 байт UTF-8 при длине строки 40
        with pytest.raises(ValidationError):
            _user("я" * 40)

    def test_valid_password_accepted(self):
        assert _user("правильный-пароль").password

    def test_reset_confirm_uses_same_limits(self):
        with pytest.raises(ValidationError):
            PasswordResetConfirm(token="t", new_password="x" * 100)


class TestScheduleValidation:
    def test_create_rejects_end_before_start(self):
        with pytest.raises(ValidationError):
            ScheduleCreate(day_of_week=0, start_time=time(20), end_time=time(9))

    def test_update_rejects_inverted_pair(self):
        with pytest.raises(ValidationError):
            ScheduleUpdate(start_time=time(20), end_time=time(9))

    def test_update_midnight_pair_not_skipped_by_truthiness(self):
        # time(0, 0) — falsy; валидатор обязан сравнивать через is not None
        with pytest.raises(ValidationError):
            ScheduleUpdate(start_time=time(0, 0), end_time=time(0, 0))

    def test_update_single_field_allowed(self):
        assert ScheduleUpdate(end_time=time(18)).end_time == time(18)


class TestAppointmentCreateTimezone:
    def test_naive_datetime_rejected(self):
        with pytest.raises(ValidationError):
            AppointmentCreate(master_id=uuid.uuid4(), service_id=uuid.uuid4(),
                              start_time="2026-07-10T10:00:00")

    def test_aware_datetime_normalized_to_utc(self):
        appt = AppointmentCreate(master_id=uuid.uuid4(), service_id=uuid.uuid4(),
                                 start_time="2026-07-10T10:00:00+03:00")
        assert appt.start_time.tzinfo == timezone.utc
        assert appt.start_time.hour == 7


class TestMoney:
    def test_price_is_decimal(self):
        svc = ServiceCreate(name="Стрижка", price=1500.5, duration_min=30)
        assert isinstance(svc.price, Decimal)

    def test_more_than_two_decimal_places_rejected(self):
        with pytest.raises(ValidationError):
            ServiceCreate(name="Стрижка", price=Decimal("10.123"), duration_min=30)

    def test_json_serializes_as_number_not_string(self):
        resp = ServiceResponse(id=uuid.uuid4(), name="Стрижка", description=None,
                               price=Decimal("1500.00"), duration_min=30,
                               is_active=True)
        assert '"price":1500.0' in resp.model_dump_json()
