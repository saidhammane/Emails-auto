import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.api.schemas import SendTestEmailRequest
from app.core.config import Settings
from app.services.email_log_service import EmailLogService


class EmailServiceError(Exception):
    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class EmailService:
    def __init__(
        self,
        settings: Settings,
        email_log_service: EmailLogService | None = None,
    ) -> None:
        self.settings = settings
        self.email_log_service = email_log_service or EmailLogService()

    def validate_settings(self) -> None:
        self._validate_settings()

    def send_test_email(self, payload: SendTestEmailRequest) -> None:
        self.send_email(
            recipient=payload.to,
            subject=payload.subject,
            body=payload.body,
        )

    def send_email(self, recipient: str, subject: str, body: str) -> None:
        try:
            self._validate_settings()
            message = self._build_message(
                recipient=recipient,
                subject=subject,
                body=body,
            )

            if self.settings.smtp_port == 465:
                with smtplib.SMTP_SSL(
                    self.settings.smtp_host,
                    self.settings.smtp_port,
                    timeout=30,
                ) as server:
                    self._login_and_send(server, recipient, message)
            else:
                with smtplib.SMTP(
                    self.settings.smtp_host,
                    self.settings.smtp_port,
                    timeout=30,
                ) as server:
                    server.ehlo()
                    # Gmail on port 587 expects STARTTLS before login.
                    server.starttls()
                    server.ehlo()
                    self._login_and_send(server, recipient, message)

            self.log_sent_email(recipient, subject)
        except EmailServiceError as exc:
            self.log_failed_email(recipient, subject, exc.message)
            raise
        except smtplib.SMTPAuthenticationError as exc:
            error_message = (
                "SMTP authentication failed. Check SMTP_USER and SMTP_PASSWORD."
            )
            self.log_failed_email(recipient, subject, error_message)
            raise EmailServiceError(error_message, status_code=401) from exc
        except smtplib.SMTPConnectError as exc:
            error_message = (
                "Unable to connect to the SMTP server. Check SMTP_HOST and SMTP_PORT."
            )
            self.log_failed_email(recipient, subject, error_message)
            raise EmailServiceError(error_message, status_code=502) from exc
        except smtplib.SMTPRecipientsRefused as exc:
            error_message = "The recipient address was refused by the SMTP server."
            self.log_failed_email(recipient, subject, error_message)
            raise EmailServiceError(error_message, status_code=400) from exc
        except smtplib.SMTPServerDisconnected as exc:
            error_message = "The SMTP server disconnected unexpectedly."
            self.log_failed_email(recipient, subject, error_message)
            raise EmailServiceError(error_message, status_code=502) from exc
        except smtplib.SMTPException as exc:
            error_message = f"SMTP error while sending email: {exc}"
            self.log_failed_email(recipient, subject, error_message)
            raise EmailServiceError(error_message, status_code=502) from exc
        except (TimeoutError, OSError) as exc:
            error_message = "Network error while reaching the SMTP server."
            self.log_failed_email(recipient, subject, error_message)
            raise EmailServiceError(error_message, status_code=502) from exc

    def log_sent_email(self, recipient: str, subject: str) -> None:
        self.email_log_service.log_sent(
            email=str(recipient),
            subject=subject,
        )

    def log_failed_email(
        self,
        recipient: str,
        subject: str,
        error_message: str,
    ) -> None:
        self.email_log_service.log_failed(
            email=str(recipient),
            subject=subject,
            error_message=error_message,
        )

    def _validate_settings(self) -> None:
        missing = []

        if not self.settings.smtp_host:
            missing.append("SMTP_HOST")
        if not self.settings.smtp_port:
            missing.append("SMTP_PORT")
        if not self.settings.smtp_user:
            missing.append("SMTP_USER")
        if not self.settings.smtp_password:
            missing.append("SMTP_PASSWORD")
        if not self.settings.smtp_from:
            missing.append("SMTP_FROM")

        if missing:
            raise EmailServiceError(
                f"Missing SMTP environment variables: {', '.join(missing)}.",
                status_code=500,
            )

    def _build_message(
        self,
        recipient: str,
        subject: str,
        body: str,
    ) -> MIMEMultipart:
        message = MIMEMultipart()
        message["From"] = self.settings.smtp_from or ""
        message["To"] = str(recipient)
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))
        return message

    def _login_and_send(
        self,
        server: smtplib.SMTP,
        recipient: str,
        message: MIMEMultipart,
    ) -> None:
        server.login(self.settings.smtp_user, self.settings.smtp_password)
        server.sendmail(
            self.settings.smtp_from,
            str(recipient),
            message.as_string(),
        )
