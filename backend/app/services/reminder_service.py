import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models.appointment import Appointment
from ..repositories.appointment_repository import AppointmentRepository
from ..utils.email import send_email

logger = logging.getLogger(__name__)


class ReminderService:
    """Напоминания клиентам за 24 часа и за 2 часа до записи. Опрашивается
    периодически (см. app/scheduler.py — asyncio-луп в процессе бэкенда,
    settings.reminder_poll_interval_seconds), не по расписанию каждой
    конкретной записи — так что окно попадания в 24ч/2ч рубеж определяет
    сам запрос к БД (см. AppointmentRepository.list_due_*_reminders)."""

    def __init__(self, db: Session):
        self.db = db
        self.appointment_repo = AppointmentRepository(db)

    def send_due_reminders(self) -> None:
        now = datetime.now(timezone.utc)
        for appointment in self.appointment_repo.list_due_24h_reminders(now):
            if self._try_send(appointment, hours_label="24 часа"):
                self.appointment_repo.mark_24h_reminder_sent(appointment)
        for appointment in self.appointment_repo.list_due_2h_reminders(now):
            if self._try_send(appointment, hours_label="2 часа"):
                self.appointment_repo.mark_2h_reminder_sent(appointment)
        self.db.commit()

    def _try_send(self, appointment: Appointment, *, hours_label: str) -> bool:
        # send_email() сама никогда не поднимает исключение при сбое SMTP
        # (см. utils/email.py) — try/except здесь только на случай ошибки в
        # сборке письма (например, отсутствующая связь), чтобы одна плохая
        # запись не остановила рассылку остальным в этом же проходе.
        try:
            self._send(appointment, hours_label=hours_label)
        except Exception:
            logger.exception(
                "Не удалось отправить напоминание (%s) для appointment_id=%s",
                hours_label, appointment.id,
            )
            return False
        return True

    def _send(self, appointment: Appointment, *, hours_label: str) -> None:
        when = appointment.start_time.strftime("%d.%m.%Y %H:%M")
        subject = f"Напоминание о записи — через {hours_label}"
        text_body = (
            f"Здравствуйте, {appointment.client.first_name}!\n\n"
            f"Напоминаем: у вас запись в Барбершоп «Сайтама» через {hours_label}.\n\n"
            f"Услуга: {appointment.service_name}\n"
            f"Мастер: {appointment.master_name}\n"
            f"Дата и время: {when}\n\n"
            "Если планы изменились, отменить запись можно в личном кабинете."
        )
        html_body = (
            f"<p>Здравствуйте, {appointment.client.first_name}!</p>"
            f"<p>Напоминаем: у вас запись в Барбершоп «Сайтама» через {hours_label}.</p>"
            f"<p>Услуга: {appointment.service_name}<br>"
            f"Мастер: {appointment.master_name}<br>"
            f"Дата и время: {when}</p>"
            "<p>Если планы изменились, отменить запись можно в личном кабинете.</p>"
        )
        send_email(to=appointment.client.email, subject=subject,
                  text_body=text_body, html_body=html_body)
