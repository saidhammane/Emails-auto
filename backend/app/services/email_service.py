import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.api.schemas import SendTestEmailRequest
from app.core.config import Settings


class EmailServiceError(Exception):
    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class EmailService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send_test_email(self, payload: SendTestEmailRequest) -> None:
        self._validate_settings()
        message = self._build_message(payload)

        try:
            if self.settings.smtp_port == 465:
                with smtplib.SMTP_SSL(
                    self.settings.smtp_host,
                    self.settings.smtp_port,
                    timeout=30,
                ) as server:
                    self._login_and_send(server, payload.to, message)
                return

            with smtplib.SMTP(
                self.settings.smtp_host,
                self.settings.smtp_port,
                timeout=30,
            ) as server:
                server.ehlo()
                # Gmail on port 587 expects STARTTLS before login.
                server.starttls()
                server.ehlo()
                self._login_and_send(server, payload.to, message)
        except smtplib.SMTPAuthenticationError as exc:
            raise EmailServiceError(
                "SMTP authentication failed. Check SMTP_USER and SMTP_PASSWORD.",
                status_code=401,
            ) from exc
        except smtplib.SMTPConnectError as exc:
            raise EmailServiceError(
                "Unable to connect to the SMTP server. Check SMTP_HOST and SMTP_PORT.",
                status_code=502,
            ) from exc
        except smtplib.SMTPRecipientsRefused as exc:
            raise EmailServiceError(
                "The recipient address was refused by the SMTP server.",
                status_code=400,
            ) from exc
        except smtplib.SMTPServerDisconnected as exc:
            raise EmailServiceError(
                "The SMTP server disconnected unexpectedly.",
                status_code=502,
            ) from exc
        except smtplib.SMTPException as exc:
            raise EmailServiceError(
                f"SMTP error while sending email: {exc}",
                status_code=502,
            ) from exc
        except (TimeoutError, OSError) as exc:
            raise EmailServiceError(
                "Network error while reaching the SMTP server.",
                status_code=502,
            ) from exc

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

    def _build_message(self, payload: SendTestEmailRequest) -> MIMEMultipart:
        message = MIMEMultipart()
        message["From"] = self.settings.smtp_from or ""
        message["To"] = str(payload.to)
        message["Subject"] = payload.subject
        message.attach(MIMEText(payload.body, "plain"))
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
