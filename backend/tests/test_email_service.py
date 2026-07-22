import smtplib
import socket
from unittest.mock import MagicMock, patch
import pytest

from app.core.config import Settings
from app.services.email_service import EmailService, _html_to_plain_text, send_password_reset_email


def test_html_to_plain_text_conversion():
    html = "<h1>Welcome</h1><p>Hello <b>World</b>!</p><br><a href='https://example.com'>Click here</a>"
    plain = _html_to_plain_text(html)
    assert "Welcome" in plain
    assert "Hello World!" in plain
    assert "Click here" in plain
    assert "<h1>" not in plain


def test_email_service_configuration_detection():
    # Unconfigured settings
    unconfigured_settings = Settings(
        BREVO_SMTP_SERVER="",
        BREVO_SMTP_USERNAME="",
        BREVO_SMTP_PASSWORD="",
        SMTP_HOST="",
        SMTP_USER="",
        SMTP_PASSWORD=""
    )
    unconfigured_service = EmailService(settings_config=unconfigured_settings)
    assert unconfigured_service.is_configured is False
    status = unconfigured_service.validate_smtp_configuration()
    assert status["configured"] is False
    assert status["mode"] == "console_fallback"

    # Brevo configured settings
    brevo_settings = Settings(
        BREVO_SMTP_SERVER="smtp-relay.brevo.com",
        BREVO_SMTP_PORT=587,
        BREVO_SMTP_USERNAME="brevo_user@example.com",
        BREVO_SMTP_PASSWORD="secret_brevo_key",
        MAIL_FROM="noreply@expenseflow.ai"
    )
    brevo_service = EmailService(settings_config=brevo_settings)
    assert brevo_service.is_configured is True
    assert brevo_service.settings.effective_smtp_server == "smtp-relay.brevo.com"
    assert brevo_service.settings.effective_smtp_port == 587
    assert brevo_service.settings.effective_mail_from == "noreply@expenseflow.ai"

    status_configured = brevo_service.validate_smtp_configuration()
    assert status_configured["configured"] is True
    assert status_configured["mode"] == "smtp"


def test_send_email_console_fallback():
    unconfigured_settings = Settings(
        BREVO_SMTP_SERVER="",
        BREVO_SMTP_USERNAME="",
        BREVO_SMTP_PASSWORD=""
    )
    service = EmailService(settings_config=unconfigured_settings)
    
    # Unconfigured send_email should return True via console logging fallback
    res = service.send_email(
        to_email="test@example.com",
        subject="Test Fallback",
        html_content="<p>Test Content</p>"
    )
    assert res is True


@patch("smtplib.SMTP")
def test_send_email_smtp_success(mock_smtp_cls):
    mock_server = MagicMock()
    mock_smtp_cls.return_value.__enter__.return_value = mock_server

    configured_settings = Settings(
        BREVO_SMTP_SERVER="smtp-relay.brevo.com",
        BREVO_SMTP_PORT=587,
        BREVO_SMTP_USERNAME="brevo_user@example.com",
        BREVO_SMTP_PASSWORD="secret_brevo_key",
        MAIL_FROM="noreply@expenseflow.ai"
    )
    service = EmailService(settings_config=configured_settings)

    success = service.send_email(
        to_email="recipient@example.com",
        subject="Welcome to ExpenseFlow",
        html_content="<h1>Welcome</h1><p>Your ledger is ready.</p>"
    )

    assert success is True
    mock_smtp_cls.assert_called_once_with("smtp-relay.brevo.com", 587, timeout=15)
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("brevo_user@example.com", "secret_brevo_key")
    mock_server.sendmail.assert_called_once()


@patch("smtplib.SMTP")
@patch("time.sleep", return_value=None)
def test_send_email_smtp_retry_recovery(mock_sleep, mock_smtp_cls):
    mock_server = MagicMock()
    # First attempt raises socket timeout, second attempt succeeds
    mock_smtp_cls.return_value.__enter__.side_effect = [
        socket.timeout("Connection timed out"),
        mock_server
    ]

    configured_settings = Settings(
        BREVO_SMTP_SERVER="smtp-relay.brevo.com",
        BREVO_SMTP_PORT=587,
        BREVO_SMTP_USERNAME="brevo_user",
        BREVO_SMTP_PASSWORD="password"
    )
    service = EmailService(settings_config=configured_settings)

    success = service.send_email(
        to_email="recipient@example.com",
        subject="Retry Test",
        html_content="<p>Retry</p>",
        retries=3
    )

    assert success is True
    assert mock_smtp_cls.call_count == 2
    mock_sleep.assert_called_once_with(1.0)


@patch("smtplib.SMTP")
@patch("time.sleep", return_value=None)
def test_send_email_smtp_exhaust_retries(mock_sleep, mock_smtp_cls):
    mock_smtp_cls.return_value.__enter__.side_effect = smtplib.SMTPException("SMTP Server Unavailable")

    configured_settings = Settings(
        BREVO_SMTP_SERVER="smtp-relay.brevo.com",
        BREVO_SMTP_PORT=587,
        BREVO_SMTP_USERNAME="brevo_user",
        BREVO_SMTP_PASSWORD="password"
    )
    service = EmailService(settings_config=configured_settings)

    success = service.send_email(
        to_email="recipient@example.com",
        subject="Failure Test",
        html_content="<p>Failure</p>",
        retries=3
    )

    assert success is False
    assert mock_smtp_cls.call_count == 3


def test_backward_compatible_function_export():
    with patch("app.services.email_service.email_service.send_email", return_value=True) as mock_send:
        res = send_password_reset_email("user@example.com", "reset-token-123")
        assert res is True
        mock_send.assert_called_once()
