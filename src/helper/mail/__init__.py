import asyncio
import logging
import mimetypes
import os
import smtplib
import time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps
from typing import List, Optional, Union

import aiosmtplib
from tenacity import retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailClient:
    """SMTP email client with connection pooling and retry mechanism."""

    def __init__(
        self,
        host: str,
        port: int = 587,
        username: Optional[str] = None,
        password: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._connection: Optional[smtplib.SMTP] = None
        self._async_connection: Optional[aiosmtplib.SMTP] = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def connect(self):
        """Establish and reuse SMTP connection."""
        if self._connection and self._connection.noop()[0] == 250:
            return  # Reuse existing connection

        try:
            if self.port == 465:
                self._connection = smtplib.SMTP_SSL(self.host, self.port)
            else:
                self._connection = smtplib.SMTP(self.host, self.port)
                self._connection.starttls()

            if self.username and self.password:
                self._connection.login(self.username, self.password)

            logger.info("Connected to SMTP server")
        except Exception as e:
            self._connection = None
            logger.error(f"Connection failed: {e}")
            raise

    def disconnect(self):
        """Close the connection gracefully."""
        if self._connection:
            try:
                self._connection.quit()
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
            finally:
                self._connection = None

    def retry(func):
        """Decorator for retry mechanism with exponential backoff."""

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            attempts = 0
            while attempts <= self.max_retries:
                try:
                    return func(self, *args, **kwargs)
                except (smtplib.SMTPServerDisconnected, smtplib.SMTPSenderRefused) as e:
                    attempts += 1
                    if attempts > self.max_retries:
                        raise
                    delay = self.retry_delay * (2**attempts)
                    logger.warning(
                        f"Retrying in {delay}s (attempt {attempts}) - Error: {e}"
                    )
                    time.sleep(delay)
                    self.connect()
            return False

        return wrapper

    @retry
    def send(
        self,
        to_emails: Union[str, List[str]],
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        attachments: Optional[List[str]] = None,
    ) -> bool:
        """Send email with retry support and connection reuse."""
        if not self._connection:
            self.connect()

        msg = self._build_message(
            to_emails=to_emails,
            subject=subject,
            html_content=html_content,
            from_email=from_email,
            attachments=attachments,
        )

        try:
            self._connection.sendmail(
                from_addr=from_email or self.username,
                to_addrs=to_emails,
                msg=msg.as_string(),
            )
            return True
        except smtplib.SMTPException as e:
            logger.error(f"Email send failed: {e}")
            self.disconnect()  # Force reconnect on next attempt
            raise

    def _build_message(self, to_emails, subject, html_content, from_email, attachments):
        """Construct MIME message with attachments."""
        msg = MIMEMultipart()
        msg["From"] = from_email or self.username
        msg["To"] = ", ".join([to_emails] if isinstance(to_emails, str) else to_emails)
        msg["Subject"] = subject
        msg.attach(MIMEText(html_content, "html"))

        for file_path in attachments or []:
            self._attach_file(msg, file_path)

        return msg

    def _attach_file(self, msg, file_path):
        """Attach a file to the email message."""
        try:
            with open(file_path, "rb") as f:
                main_type, sub_type = self._get_mime_types(file_path)
                part = MIMEBase(main_type, sub_type)
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(file_path)}",
                )
                msg.attach(part)
        except Exception as e:
            logger.error(f"Failed to attach {file_path}: {e}")
            raise

    def _get_mime_types(self, file_path):
        """Get MIME types for attachment."""
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            return "application", "octet-stream"
        return mime_type.split("/", 1)


class AsyncEmailClient(EmailClient):
    """Asynchronous version with aiosmtplib support."""

    async def __aenter__(self):
        await self.async_connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.async_disconnect()

    async def async_connect(self):
        """Establish async SMTP connection."""
        if self._async_connection and await self._async_connection.noop():
            return

        self._async_connection = aiosmtplib.SMTP(
            hostname=self.host,
            port=self.port,
            use_tls=self.port == 465,
            start_tls=self.port != 465,
        )

        try:
            await self._async_connection.connect()
            if self.username and self.password:
                await self._async_connection.login(self.username, self.password)
            logger.info("Connected to SMTP server (async)")
        except Exception as e:
            self._async_connection = None
            logger.error(f"Async connection failed: {e}")
            raise

    async def async_disconnect(self):
        """Close async connection."""
        if self._async_connection:
            try:
                await self._async_connection.quit()
            except Exception as e:
                logger.warning(f"Error closing async connection: {e}")
            finally:
                self._async_connection = None

    @retry
    async def async_send(
        self,
        to_emails: Union[str, List[str]],
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        attachments: Optional[List[str]] = None,
    ) -> bool:
        """Asynchronous send with connection management."""
        if not self._async_connection:
            await self.async_connect()

        msg = self._build_message(
            to_emails=to_emails,
            subject=subject,
            html_content=html_content,
            from_email=from_email,
            attachments=attachments,
        )

        try:
            await self._async_connection.send_message(
                message=msg.as_string(),
                sender=from_email or self.username,
                recipients=to_emails,
            )
            return True
        except aiosmtplib.SMTPException as e:
            logger.error(f"Async email send failed: {e}")
            await self.async_disconnect()
            raise


if __name__ == "__main__":
    with EmailClient(
        host="https://mail.hojangroup.com",
        port=587,
        username="amani@hojangroup.com",
        password="Abcd@1234",
    ) as client:
        print("sending email")
        client.send(
            to_emails="recipient@example.com",
            subject="Test Sync",
            html_content="<h1>Sync Email</h1>",
            # attachments=["file1.pdf"],
        )

    async def async_example():
        async with AsyncEmailClient(
            host="smtp.example.com",
            port=587,
            username="user@example.com",
            password="password",
        ) as async_client:
            await async_client.async_send(
                to_emails="recipient@example.com",
                subject="Test Async",
                html_content="<h1>Async Email</h1>",
                # attachments=["file2.pdf"],
            )

    asyncio.run(async_example())
