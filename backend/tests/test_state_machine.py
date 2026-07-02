"""Машина состояний записи (ALLOWED_TRANSITIONS) и права на переходы."""
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.enums import AppointmentStatus, UserRole
from app.services.appointment_service import (ALLOWED_TRANSITIONS,
                                              AppointmentService)


class TestTransitionTable:
    def test_pending_paths(self):
        assert ALLOWED_TRANSITIONS[AppointmentStatus.pending] == {
            AppointmentStatus.confirmed, AppointmentStatus.cancelled,
        }

    def test_confirmed_paths(self):
        assert ALLOWED_TRANSITIONS[AppointmentStatus.confirmed] == {
            AppointmentStatus.done, AppointmentStatus.cancelled,
        }

    def test_terminal_states_have_no_exits(self):
        assert ALLOWED_TRANSITIONS[AppointmentStatus.done] == set()
        assert ALLOWED_TRANSITIONS[AppointmentStatus.cancelled] == set()

    def test_every_status_is_covered(self):
        assert set(ALLOWED_TRANSITIONS) == set(AppointmentStatus)


def make_service(appointment, own_master_id=None):
    svc = AppointmentService.__new__(AppointmentService)
    svc.db = None
    svc.appointment_repo = SimpleNamespace(
        get_by_id=lambda _id: appointment,
        update_status=lambda a, s: setattr(a, "status", s) or a,
    )
    svc.master_repo = SimpleNamespace(
        get_by_user_id=lambda _uid: (
            SimpleNamespace(id=own_master_id) if own_master_id else None
        ),
    )
    return svc


def make_appointment(status, master_id=None, client_id=None):
    return SimpleNamespace(status=status,
                           master_id=master_id or uuid.uuid4(),
                           client_id=client_id or uuid.uuid4())


class TestUpdateStatus:
    def test_invalid_transition_rejected_400(self):
        appt = make_appointment(AppointmentStatus.done)
        svc = make_service(appt)
        admin = SimpleNamespace(role=UserRole.admin, id=uuid.uuid4())
        with pytest.raises(HTTPException) as exc:
            svc.update_status(uuid.uuid4(), AppointmentStatus.confirmed, admin)
        assert exc.value.status_code == 400
        assert appt.status == AppointmentStatus.done

    def test_foreign_master_rejected_403(self):
        appt = make_appointment(AppointmentStatus.pending)
        svc = make_service(appt, own_master_id=uuid.uuid4())  # другой мастер
        master_user = SimpleNamespace(role=UserRole.master, id=uuid.uuid4())
        with pytest.raises(HTTPException) as exc:
            svc.update_status(uuid.uuid4(), AppointmentStatus.confirmed, master_user)
        assert exc.value.status_code == 403

    def test_missing_appointment_404(self):
        svc = make_service(None)
        admin = SimpleNamespace(role=UserRole.admin, id=uuid.uuid4())
        with pytest.raises(HTTPException) as exc:
            svc.update_status(uuid.uuid4(), AppointmentStatus.confirmed, admin)
        assert exc.value.status_code == 404


class TestCancel:
    def test_foreign_client_rejected_403(self):
        appt = make_appointment(AppointmentStatus.pending)
        svc = make_service(appt)
        with pytest.raises(HTTPException) as exc:
            svc.cancel(uuid.uuid4(), uuid.uuid4())  # чужой client_id
        assert exc.value.status_code == 403

    def test_cancel_terminal_rejected_400(self):
        client_id = uuid.uuid4()
        appt = make_appointment(AppointmentStatus.done, client_id=client_id)
        svc = make_service(appt)
        with pytest.raises(HTTPException) as exc:
            svc.cancel(uuid.uuid4(), client_id)
        assert exc.value.status_code == 400
