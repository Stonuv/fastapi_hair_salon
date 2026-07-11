import logging
import smtplib
from email.message import EmailMessage

from ..config import settings

logger = logging.getLogger(__name__)


def send_email(*, to: str, subject: str, text_body: str, html_body: str | None = None) -> None:
    """
    Отправляет письмо через SMTP (settings.smtp_*, по умолчанию — локальный
    Mailpit на :1025, без авторизации/TLS). Исключения не пробрасываются —
    вызывающая сторона (например, восстановление пароля) обязана вести себя
    одинаково независимо от результата отправки, чтобы не раскрывать через
    500-ответ, существует ли адрес; ошибка попадает в лог.
    """
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    message["To"] = to
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_user and settings.smtp_password:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)
    except OSError:
        logger.exception("Не удалось отправить письмо на %s через %s:%s",
                         to, settings.smtp_host, settings.smtp_port)
