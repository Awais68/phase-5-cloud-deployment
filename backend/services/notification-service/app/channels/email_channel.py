"""
Email notification channel using SMTP with retry logic.
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Dict, Any, Optional
import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError,
)
import logging

from app.config.settings import get_settings

logger = structlog.get_logger()
std_logger = logging.getLogger(__name__)
settings = get_settings()

# Retryable SMTP exceptions
SMTP_RETRYABLE_EXCEPTIONS = (
    aiosmtplib.SMTPConnectError,
    aiosmtplib.SMTPServerDisconnected,
    aiosmtplib.SMTPResponseException,
    ConnectionError,
    TimeoutError,
    OSError,
)


class EmailChannel:
    """Email notification channel."""

    def __init__(self):
        """Initialize email channel with template engine."""
        self.jinja_env = Environment(
            loader=FileSystemLoader(settings.email_template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(SMTP_RETRYABLE_EXCEPTIONS),
        before_sleep=before_sleep_log(std_logger, logging.WARNING),
        reraise=True,
    )
    async def _send_smtp(self, msg: MIMEMultipart) -> None:
        """
        Internal method to send email via SMTP with retry logic.

        Args:
            msg: Email message to send

        Raises:
            Various SMTP exceptions on failure after all retries
        """
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            start_tls=True,
        )

    async def send(
        self,
        to_email: str,
        subject: str,
        message: str,
        template_name: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send email notification with automatic retry on transient failures.

        Uses exponential backoff: 2s, 4s, 8s between retries.
        Max 3 attempts before giving up.

        Args:
            to_email: Recipient email address
            subject: Email subject
            message: Plain text message (fallback)
            template_name: Optional Jinja2 template name
            template_data: Template context data

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
            msg['To'] = to_email

            # Plain text part
            text_part = MIMEText(message, 'plain')
            msg.attach(text_part)

            # HTML part (if template provided)
            if template_name and template_data:
                try:
                    template = self.jinja_env.get_template(template_name)
                    html_content = template.render(**template_data)
                    html_part = MIMEText(html_content, 'html')
                    msg.attach(html_part)
                except Exception as e:
                    logger.warning(
                        "template_render_failed",
                        template_name=template_name,
                        error=str(e)
                    )

            # Send email with retry logic
            await self._send_smtp(msg)

            logger.info(
                "email_sent",
                to_email=to_email,
                subject=subject
            )

            return True

        except RetryError as e:
            logger.error(
                "email_send_failed_after_retries",
                to_email=to_email,
                attempts=3,
                error=str(e.last_attempt.exception()),
                exc_info=True
            )
            return False

        except Exception as e:
            logger.error(
                "email_send_failed",
                to_email=to_email,
                error=str(e),
                exc_info=True
            )
            return False
