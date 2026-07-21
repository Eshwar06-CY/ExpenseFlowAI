import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger(__name__)


def send_password_reset_email(to_email: str, reset_token: str, reset_url: str | None = None) -> bool:
    """
    Send a password reset email with the given token.
    If SMTP is not configured, logs the reset link to the console and returns True.
    Returns True on success, False on SMTP failure.
    """
    reset_url = reset_url or f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    # If SMTP is not configured, fall back to console logging
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.info("=" * 60)
        logger.info("PASSWORD RESET LINK (SMTP not configured)")
        logger.info(f"  Email: {to_email}")
        logger.info(f"  URL:   {reset_url}")
        logger.info("=" * 60)
        return True

    from_email = settings.EMAILS_FROM_EMAIL or settings.SMTP_USER
    from_name = settings.EMAILS_FROM_NAME

    # Build HTML email
    html_body = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 520px; margin: 0 auto; padding: 40px 20px;">
        <div style="text-align: center; margin-bottom: 32px;">
            <div style="display: inline-block; width: 48px; height: 48px; background: linear-gradient(135deg, #7c3aed, #8b5cf6); border-radius: 12px; line-height: 48px; font-size: 20px; font-weight: bold; color: white;">E</div>
            <h2 style="margin: 16px 0 4px; color: #1a1a2e; font-size: 22px;">Reset Your Password</h2>
            <p style="color: #6b7280; font-size: 14px; margin: 0;">ExpenseFlow AI</p>
        </div>
        <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 32px; text-align: center;">
            <p style="color: #374151; font-size: 14px; line-height: 1.6; margin: 0 0 24px;">
                We received a request to reset the password for your account. Click the button below to choose a new password.
            </p>
            <a href="{reset_url}" style="display: inline-block; background: linear-gradient(135deg, #7c3aed, #8b5cf6); color: white; text-decoration: none; padding: 12px 32px; border-radius: 8px; font-weight: 600; font-size: 14px;">
                Reset Password
            </a>
            <p style="color: #9ca3af; font-size: 12px; margin: 24px 0 0; line-height: 1.5;">
                This link expires in {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes.<br>
                If you did not request a password reset, you can safely ignore this email.
            </p>
        </div>
        <p style="color: #d1d5db; font-size: 11px; text-align: center; margin-top: 24px;">
            &copy; ExpenseFlow AI &mdash; Your Fintech Ledger Workspace
        </p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reset Your Password — ExpenseFlow AI"
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email
    msg.attach(MIMEText(f"Reset your password: {reset_url}", "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(from_email, to_email, msg.as_string())
        logger.info(f"Password reset email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {to_email}: {e}")
        # Fall back to logging the URL even on SMTP failure
        logger.info(f"Fallback reset URL: {reset_url}")
        return False
