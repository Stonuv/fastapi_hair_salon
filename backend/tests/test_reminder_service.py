"""ReminderService.send_due_reminders() — фейковый репозиторий, без БД."""
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.services import reminder_service as reminder_service_module
from app.services.reminder_service import ReminderService


def make_appointment(**overrides):
    client = SimpleNamespace(first_name="Иван", email="client@example.com")
    defaults = {
        "id": uuid.uuid4(),
        "client": client,
        "service_name": "Стрижка",
        "master_name": "Пётр Петров",
        "start_time": datetime.now(timezone.utc) + timedelta(hours=20),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_service(*, due_24h=None, due_2h=None):
    svc = ReminderService.__new__(ReminderService)
    svc.db = SimpleNamespace(commit=lambda: None)
    calls = {"marked_24h": [], "marked_2h": []}

    svc.appointment_repo = SimpleNamespace(
        list_due_24h_reminders=lambda now: due_24h or [],
        list_due_2h_reminders=lambda now: due_2h or [],
        mark_24h_reminder_sent=lambda apt: calls["marked_24h"].append(apt.id),
        mark_2h_reminder_sent=lambda apt: calls["marked_2h"].append(apt.id),
    )
    svc._calls = calls
    return svc


class TestSendDueReminders:
    def test_sends_and_marks_24h_reminder(self, monkeypatch):
        sent = []
        monkeypatch.setattr(reminder_service_module, "send_email",
                            lambda **kwargs: sent.append(kwargs))
        apt = make_appointment()
        svc = make_service(due_24h=[apt])
        svc.send_due_reminders()

        assert len(sent) == 1
        assert sent[0]["to"] == "client@example.com"
        assert "24 часа" in sent[0]["subject"]
        assert svc._calls["marked_24h"] == [apt.id]
        assert svc._calls["marked_2h"] == []

    def test_sends_and_marks_2h_reminder(self, monkeypatch):
        sent = []
        monkeypatch.setattr(reminder_service_module, "send_email",
                            lambda **kwargs: sent.append(kwargs))
        apt = make_appointment(start_time=datetime.now(timezone.utc) + timedelta(hours=1))
        svc = make_service(due_2h=[apt])
        svc.send_due_reminders()

        assert len(sent) == 1
        assert "2 часа" in sent[0]["subject"]
        assert svc._calls["marked_2h"] == [apt.id]
        assert svc._calls["marked_24h"] == []

    def test_does_not_mark_sent_when_send_fails(self, monkeypatch):
        """Ошибка при сборке/отправке письма не должна помечать напоминание
        отправленным — иначе клиент молча не получит его вообще."""
        def boom(**kwargs):
            raise RuntimeError("smtp exploded")
        monkeypatch.setattr(reminder_service_module, "send_email", boom)
        apt = make_appointment()
        svc = make_service(due_24h=[apt])
        svc.send_due_reminders()  # не должно бросить исключение наружу

        assert svc._calls["marked_24h"] == []

    def test_one_failure_does_not_block_remaining_appointments(self, monkeypatch):
        good = make_appointment()
        bad = make_appointment(client=None)  # bad.client.first_name -> AttributeError
        sent = []

        def maybe_boom(**kwargs):
            sent.append(kwargs)
        monkeypatch.setattr(reminder_service_module, "send_email", maybe_boom)

        svc = make_service(due_24h=[bad, good])
        svc.send_due_reminders()

        assert svc._calls["marked_24h"] == [good.id]
        assert len(sent) == 1
        assert sent[0]["to"] == "client@example.com"

    def test_no_due_reminders_is_a_noop(self):
        svc = make_service()
        svc.send_due_reminders()
        assert svc._calls["marked_24h"] == []
        assert svc._calls["marked_2h"] == []
