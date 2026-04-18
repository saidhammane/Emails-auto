import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape, unescape

from app.api.schemas import SendTestEmailRequest
from app.core.config import Settings
from app.services.email_log_service import EmailLogService

EMAIL_SIGNATURE = """Said HAMMANE
Ing\u00e9nieur Data & Business Intelligence

Tableaux de bord Power BI | Automatisation Excel | Analyse financi\u00e8re

\U0001F4CD Casablanca, Maroc
\u2709 said.hammane1@gmail.com
\U0001F517 linkedin.com/in/said-hammane
\U0001F310 saidhammane.space"""

HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
HTML_BODY_PATTERN = re.compile(r"</?[a-z][\s\S]*?>", re.IGNORECASE)
BODY_CLOSE_TAG_PATTERN = re.compile(r"</body\s*>", re.IGNORECASE)


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
            final_body = self._append_signature(body)
            message = self._build_message(
                recipient=recipient,
                subject=subject,
                body=final_body,
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
        subtype = "html" if self._body_looks_like_html(body) else "plain"
        message.attach(MIMEText(body, subtype, "utf-8"))
        return message

    def _append_signature(self, body: str) -> str:
        normalized_body = body.rstrip()

        if self._signature_already_present(normalized_body):
            return normalized_body

        if self._body_looks_like_html(normalized_body):
            signature_html = escape(EMAIL_SIGNATURE).replace("\n", "<br>")
            signature_block = f"<br><br>--<br>{signature_html}"

            if not normalized_body:
                return f"--<br>{signature_html}"

            if BODY_CLOSE_TAG_PATTERN.search(normalized_body):
                return BODY_CLOSE_TAG_PATTERN.sub(
                    f"{signature_block}</body>",
                    normalized_body,
                    count=1,
                )

            return f"{normalized_body}{signature_block}"

        if not normalized_body:
            return f"--\n{EMAIL_SIGNATURE}"

        return f"{normalized_body}\n\n--\n{EMAIL_SIGNATURE}"

    def _signature_already_present(self, body: str) -> bool:
        normalized_signature = self._normalize_content(EMAIL_SIGNATURE)
        normalized_body = self._normalize_content(body)
        return bool(normalized_signature and normalized_signature in normalized_body)

    def _normalize_content(self, value: str) -> str:
        text_content = unescape(HTML_TAG_PATTERN.sub(" ", value))
        return " ".join(text_content.split()).casefold()

    def _body_looks_like_html(self, body: str) -> bool:
        return bool(HTML_BODY_PATTERN.search(body))

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
