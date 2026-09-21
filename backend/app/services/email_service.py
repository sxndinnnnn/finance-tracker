"""
Provider-agnostic email sender. Which provider is used is an env setting
(EMAIL_PROVIDER), not a code branch scattered across the app — swap
providers by adding a class here and pointing the env var at it.
"""
from abc import ABC, abstractmethod

import aiosmtplib
from email.message import EmailMessage

from app.core.config import get_settings

settings = get_settings()


class EmailSender(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> None: ...


class SmtpEmailSender(EmailSender):
    async def send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = settings.email_from_address
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            start_tls=True,
        )


class SendgridEmailSender(EmailSender):
    async def send(self, to: str, subject: str, body: str) -> None:
        # Fill in with the SendGrid SDK/HTTP API when you pick this provider.
        raise NotImplementedError


class ResendEmailSender(EmailSender):
    async def send(self, to: str, subject: str, body: str) -> None:
        # Fill in with the Resend HTTP API when you pick this provider.
        raise NotImplementedError


def get_email_sender() -> EmailSender:
    return {
        "smtp": SmtpEmailSender,
        "sendgrid": SendgridEmailSender,
        "resend": ResendEmailSender,
    }[settings.email_provider]()
