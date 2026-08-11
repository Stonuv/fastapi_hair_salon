from unittest.mock import MagicMock, patch

from app.utils.email import send_email


def test_port_465_uses_implicit_ssl():
    with patch("app.utils.email.settings") as settings, \
         patch("smtplib.SMTP_SSL") as smtp_ssl, \
         patch("smtplib.SMTP") as smtp_plain:
        settings.smtp_host = "smtp.yandex.ru"
        settings.smtp_port = 465
        settings.smtp_use_tls = True
        settings.smtp_user = "u"
        settings.smtp_password = "p"
        settings.smtp_from_name = "N"
        settings.smtp_from_email = "n@example.com"
        smtp_ssl.return_value.__enter__.return_value = MagicMock()

        send_email(to="a@b.com", subject="s", text_body="b")

        smtp_ssl.assert_called_once()
        smtp_plain.assert_not_called()


def test_port_587_uses_starttls():
    with patch("app.utils.email.settings") as settings, \
         patch("smtplib.SMTP_SSL") as smtp_ssl, \
         patch("smtplib.SMTP") as smtp_plain:
        settings.smtp_host = "smtp.yandex.ru"
        settings.smtp_port = 587
        settings.smtp_use_tls = True
        settings.smtp_user = "u"
        settings.smtp_password = "p"
        settings.smtp_from_name = "N"
        settings.smtp_from_email = "n@example.com"
        conn = MagicMock()
        smtp_plain.return_value.__enter__.return_value = conn

        send_email(to="a@b.com", subject="s", text_body="b")

        smtp_plain.assert_called_once()
        smtp_ssl.assert_not_called()
        conn.starttls.assert_called_once()
