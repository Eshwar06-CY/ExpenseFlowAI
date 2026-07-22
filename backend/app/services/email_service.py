import logging
import re
import smtplib
import socket
import time
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional

from app.core.config import Settings, settings

logger = logging.getLogger(__name__)


def _html_to_plain_text(html: str) -> str:
    """Convert HTML string to plain text for fallback email bodies."""
    if not html:
        return ""
    text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'</p>', '\n\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    return '\n'.join(line.strip() for line in text.splitlines() if line.strip())


class EmailService:
    """
    Production-ready email infrastructure service for ExpenseFlowAI.
    Supports Brevo and standard SMTP providers with HTML rendering, plain text fallback,
    connection timeouts, structured logging, and retry logic for transient failures.
    """

    def __init__(self, settings_config: Optional[Settings] = None):
        self.settings = settings_config or settings

    @property
    def is_configured(self) -> bool:
        return self.settings.is_smtp_configured

    def validate_smtp_configuration(self) -> Dict[str, Any]:
        """
        Validate current SMTP configuration during application startup.
        Logs status and returns configuration summary.
        Does NOT raise exception or crash application if unconfigured in development.
        """
        server = self.settings.effective_smtp_server
        port = self.settings.effective_smtp_port
        user = self.settings.effective_smtp_username
        mail_from = self.settings.effective_mail_from

        if not self.is_configured:
            logger.warning(
                "SMTP email service is NOT configured (Missing BREVO_SMTP_SERVER/USER/PASSWORD). "
                "Outbound emails will be logged to console in fallback mode."
            )
            return {
                "status": "unconfigured",
                "mode": "console_fallback",
                "server": server,
                "port": port,
                "configured": False
            }

        logger.info(
            "SMTP email infrastructure initialized (Server=%s:%s | User=%s | MailFrom=%s)",
            server, port, user, mail_from
        )
        return {
            "status": "configured",
            "mode": "smtp",
            "server": server,
            "port": port,
            "mail_from": mail_from,
            "configured": True
        }

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        sender_name: Optional[str] = None,
        sender_email: Optional[str] = None,
        timeout: int = 15,
        retries: int = 3
    ) -> bool:
        """
        Send an HTML email with optional plain-text fallback via SMTP (Brevo / generic).
        Handles transient SMTP failures with exponential retries.
        Falls back to logging when SMTP is not configured.
        """
        from_email = sender_email or self.settings.effective_mail_from or "noreply@expenseflow.ai"
        from_name = sender_name or self.settings.EMAILS_FROM_NAME or "ExpenseFlow AI"
        plain_text = text_content or _html_to_plain_text(html_content)

        # Fallback to console logging if SMTP credentials are missing
        if not self.is_configured:
            logger.info("=" * 60)
            logger.info("[EMAIL CONSOLE FALLBACK]")
            logger.info("To:      %s", to_email)
            logger.info("From:    %s <%s>", from_name, from_email)
            logger.info("Subject: %s", subject)
            logger.info("Body:\n%s", plain_text)
            logger.info("=" * 60)
            return True

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = to_email

        msg.attach(MIMEText(plain_text, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        server_host = self.settings.effective_smtp_server
        server_port = self.settings.effective_smtp_port
        smtp_user = self.settings.effective_smtp_username
        smtp_password = self.settings.effective_smtp_password

        attempt = 0
        backoff = 1.0

        while attempt < retries:
            attempt += 1
            try:
                if server_port == 465:
                    with smtplib.SMTP_SSL(server_host, server_port, timeout=timeout) as server:
                        server.login(smtp_user, smtp_password)
                        server.sendmail(from_email, to_email, msg.as_string())
                else:
                    with smtplib.SMTP(server_host, server_port, timeout=timeout) as server:
                        server.ehlo()
                        server.starttls()
                        server.ehlo()
                        server.login(smtp_user, smtp_password)
                        server.sendmail(from_email, to_email, msg.as_string())

                logger.info("Successfully sent email to %s (Subject: '%s')", to_email, subject)
                return True

            except (smtplib.SMTPException, socket.timeout, OSError, ConnectionError) as exc:
                logger.warning(
                    "SMTP attempt %d/%d failed to send email to %s: %s",
                    attempt, retries, to_email, exc
                )
                if attempt < retries:
                    time.sleep(backoff)
                    backoff *= 2.0
                else:
                    logger.error(
                        "Exhausted all %d retries sending email to %s (Subject: '%s'). Error: %s",
                        retries, to_email, subject, exc
                    )
                    logger.info("Fallback email trace for %s:\n%s", to_email, plain_text)
                    return False
            except Exception as exc:
                logger.error("Unexpected error sending email to %s: %s", to_email, exc, exc_info=True)
                return False

        return False

    def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        reset_url: Optional[str] = None
    ) -> bool:
        """
        Send a password reset email using the configured template.
        Retained for backward compatibility.
        """
        url = reset_url or f"{self.settings.FRONTEND_URL}/reset-password?token={reset_token}"
        subject = "Reset Your Password — ExpenseFlow AI"

        html_body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 520px; margin: 0 auto; padding: 40px 20px;">
            <div style="text-align: center; margin-bottom: 32px;">
                <div style="display: inline-block; width: 48px; height: 48px; background: linear-gradient(135deg, #2563eb, #06b6d4); border-radius: 12px; line-height: 48px; font-size: 20px; font-weight: bold; color: white;">E</div>
                <h2 style="margin: 16px 0 4px; color: #1a1a2e; font-size: 22px;">Reset Your Password</h2>
                <p style="color: #6b7280; font-size: 14px; margin: 0;">ExpenseFlow AI</p>
            </div>
            <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 32px; text-align: center;">
                <p style="color: #374151; font-size: 14px; line-height: 1.6; margin: 0 0 24px;">
                    We received a request to reset the password for your account. Click the button below to choose a new password.
                </p>
                <a href="{url}" style="display: inline-block; background: linear-gradient(135deg, #2563eb, #06b6d4); color: white; text-decoration: none; padding: 12px 32px; border-radius: 8px; font-weight: 600; font-size: 14px;">
                    Reset Password
                </a>
                <p style="color: #9ca3af; font-size: 12px; margin: 24px 0 0; line-height: 1.5;">
                    This link expires in {self.settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes.<br>
                    If you did not request a password reset, you can safely ignore this email.
                </p>
            </div>
            <p style="color: #d1d5db; font-size: 11px; text-align: center; margin-top: 24px;">
                &copy; ExpenseFlow AI &mdash; Your Fintech Ledger Workspace
            </p>
        </div>
        """

        plain_text = f"Reset your password by opening the following link: {url}\nThis link expires in {self.settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes."

        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_body,
            text_content=plain_text
        )


    def send_password_changed_email(
        self,
        to_email: str,
        change_time: Optional[datetime] = None
    ) -> bool:
        """
        Send a security notification email confirming password reset.
        Does NOT contain the password. Includes timestamp and support recommendation.
        """
        timestamp_str = (change_time or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M:%S UTC")
        subject = "Security Alert: Your Password Was Changed — ExpenseFlow AI"

        html_body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 520px; margin: 0 auto; padding: 40px 20px;">
            <div style="text-align: center; margin-bottom: 32px;">
                <div style="display: inline-block; width: 48px; height: 48px; background: linear-gradient(135deg, #2563eb, #06b6d4); border-radius: 12px; line-height: 48px; font-size: 20px; font-weight: bold; color: white;">E</div>
                <h2 style="margin: 16px 0 4px; color: #1a1a2e; font-size: 22px;">Password Changed Successfully</h2>
                <p style="color: #6b7280; font-size: 14px; margin: 0;">ExpenseFlow AI Security Notice</p>
            </div>
            <div style="background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 32px; text-align: left;">
                <p style="color: #374151; font-size: 14px; line-height: 1.6; margin: 0 0 16px;">
                    This is a confirmation that the password for your ExpenseFlow AI account (<strong>{to_email}</strong>) was changed on <strong>{timestamp_str}</strong>.
                </p>
                <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 16px; margin: 20px 0; border-radius: 4px;">
                    <p style="color: #991b1b; font-size: 13px; font-weight: 600; margin: 0 0 4px;">Didn't make this change?</p>
                    <p style="color: #b91c1c; font-size: 12px; margin: 0;">
                        If you did not perform this action, your account may be compromised. Please contact support immediately or initiate a new password reset.
                    </p>
                </div>
            </div>
            <p style="color: #9ca3af; font-size: 11px; text-align: center; margin-top: 24px;">
                &copy; ExpenseFlow AI &mdash; Official Security Notification
            </p>
        </div>
        """

        plain_text = (
            f"Security Notification: Your ExpenseFlow AI password for {to_email} was changed on {timestamp_str}.\n\n"
            f"If you did not perform this change, please contact support immediately."
        )

        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_body,
            text_content=plain_text
        )

    def send_verification_email(
        self,
        to_email: str,
        verification_token: str,
        verification_url: Optional[str] = None
    ) -> bool:
        """
        Send an email verification message containing a 24-hour verification token URL.
        """
        url = verification_url or f"{self.settings.FRONTEND_URL}/verify-email?token={verification_token}"
        subject = "Verify Your Email Address — ExpenseFlow AI"

        html_body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 520px; margin: 0 auto; padding: 40px 20px;">
            <div style="text-align: center; margin-bottom: 32px;">
                <div style="display: inline-block; width: 48px; height: 48px; background: linear-gradient(135deg, #2563eb, #06b6d4); border-radius: 12px; line-height: 48px; font-size: 20px; font-weight: bold; color: white;">E</div>
                <h2 style="margin: 16px 0 4px; color: #1a1a2e; font-size: 22px;">Welcome to ExpenseFlow AI</h2>
                <p style="color: #6b7280; font-size: 14px; margin: 0;">Please verify your email address</p>
            </div>
            <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 32px; text-align: center;">
                <p style="color: #374151; font-size: 14px; line-height: 1.6; margin: 0 0 24px;">
                    Thank you for signing up for ExpenseFlow AI. Click the button below to verify your email address and activate full account privileges.
                </p>
                <a href="{url}" style="display: inline-block; background: linear-gradient(135deg, #2563eb, #06b6d4); color: white; text-decoration: none; padding: 12px 32px; border-radius: 8px; font-weight: 600; font-size: 14px;">
                    Verify Email Address
                </a>
                <p style="color: #9ca3af; font-size: 12px; margin: 24px 0 0; line-height: 1.5;">
                    This verification link expires in 24 hours.<br>
                    If you did not create an account with ExpenseFlow AI, you can safely ignore this email.
                </p>
            </div>
            <p style="color: #d1d5db; font-size: 11px; text-align: center; margin-top: 24px;">
                &copy; ExpenseFlow AI &mdash; Your Fintech Ledger Workspace
            </p>
        </div>
        """

        plain_text = (
            f"Welcome to ExpenseFlow AI!\n\n"
            f"Please verify your email address by opening the following link:\n{url}\n\n"
            f"This link expires in 24 hours."
        )

        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_body,
            text_content=plain_text
        )


# Singleton instance
email_service = EmailService()


# Backward-compatible function exports
def send_password_reset_email(to_email: str, reset_token: str, reset_url: Optional[str] = None) -> bool:
    return email_service.send_password_reset_email(to_email=to_email, reset_token=reset_token, reset_url=reset_url)


def send_password_changed_email(to_email: str, change_time: Optional[datetime] = None) -> bool:
    return email_service.send_password_changed_email(to_email=to_email, change_time=change_time)


def send_verification_email(to_email: str, verification_token: str, verification_url: Optional[str] = None) -> bool:
    return email_service.send_verification_email(to_email=to_email, verification_token=verification_token, verification_url=verification_url)
