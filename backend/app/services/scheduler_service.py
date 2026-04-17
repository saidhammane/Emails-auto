from datetime import datetime
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from pydantic import ValidationError

from app.api.schemas import ScheduleEmailRequest, SendTestEmailRequest
from app.core.config import get_settings
from app.services.bulk_email_service import BulkEmailService
from app.services.email_service import EmailService, EmailServiceError
from app.services.email_log_service import EmailLogService

logger = logging.getLogger("email_dashboard.scheduler")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)


class SchedulerService:
    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler()
        self.email_log_service = EmailLogService()

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started.")

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped.")

    def schedule_single_email(self, payload: ScheduleEmailRequest) -> str:
        normalized_payload = self._validate_single_payload(payload)
        scheduled_for = self._parse_send_at(payload.send_at)

        self.scheduler.add_job(
            self._run_single_email_job,
            trigger="date",
            run_date=scheduled_for,
            args=[normalized_payload.model_dump()],
        )
        self.email_log_service.log_scheduled(
            email=str(normalized_payload.to),
            subject=normalized_payload.subject,
            details=f"Scheduled for {scheduled_for.isoformat()}",
        )

        return scheduled_for.isoformat()

    def schedule_bulk_email(
        self,
        filename: str,
        file_bytes: bytes,
        subject_template: str,
        body_template: str,
        send_at: str,
    ) -> str:
        self._validate_bulk_payload(
            filename=filename,
            file_bytes=file_bytes,
            subject_template=subject_template,
            body_template=body_template,
        )
        scheduled_for = self._parse_send_at(send_at)

        self.scheduler.add_job(
            self._run_bulk_email_job,
            trigger="date",
            run_date=scheduled_for,
            args=[filename, file_bytes, subject_template, body_template],
        )
        self.email_log_service.log_scheduled(
            email="[bulk-job]",
            subject=subject_template.strip(),
            details=(
                f"Bulk email scheduled for {scheduled_for.isoformat()} "
                f"using file {filename.strip()}"
            ),
        )

        return scheduled_for.isoformat()

    def _validate_single_payload(
        self,
        payload: ScheduleEmailRequest,
    ) -> SendTestEmailRequest:
        email_service = EmailService(get_settings())
        email_service.validate_settings()

        subject = payload.subject.strip()
        body = payload.body.strip()

        try:
            return SendTestEmailRequest(
                to=payload.to,
                subject=subject,
                body=body,
            )
        except ValidationError as exc:
            raise EmailServiceError(
                "Invalid email request. Check recipient email, subject, and body.",
                status_code=400,
            ) from exc

    def _validate_bulk_payload(
        self,
        filename: str,
        file_bytes: bytes,
        subject_template: str,
        body_template: str,
    ) -> None:
        if not (filename or "").strip():
            raise EmailServiceError("Uploaded file is required.", status_code=400)

        if not subject_template.strip():
            raise EmailServiceError(
                "subject_template cannot be empty.",
                status_code=400,
            )

        if not body_template.strip():
            raise EmailServiceError(
                "body_template cannot be empty.",
                status_code=400,
            )

        if not file_bytes:
            raise EmailServiceError("Uploaded file is empty.", status_code=400)

        if not filename.lower().endswith((".csv", ".xlsx")):
            raise EmailServiceError(
                "Unsupported file type. Please upload a .csv or .xlsx file.",
                status_code=400,
            )

        email_service = EmailService(get_settings())
        email_service.validate_settings()

    def _parse_send_at(self, send_at: str) -> datetime:
        raw_value = (send_at or "").strip()
        if not raw_value:
            raise EmailServiceError("send_at is required.", status_code=400)

        try:
            scheduled_for = datetime.fromisoformat(raw_value)
        except ValueError as exc:
            raise EmailServiceError(
                "Invalid send_at datetime format. Use ISO 8601 format.",
                status_code=400,
            ) from exc

        now = (
            datetime.now(scheduled_for.tzinfo)
            if scheduled_for.tzinfo is not None
            else datetime.now()
        )
        if scheduled_for <= now:
            raise EmailServiceError(
                "send_at must be in the future.",
                status_code=400,
            )

        return scheduled_for

    def _run_single_email_job(self, payload_data: dict[str, str]) -> None:
        email_service = EmailService(get_settings())

        try:
            payload = SendTestEmailRequest(**payload_data)
            email_service.send_test_email(payload)
            logger.info("Scheduled single email sent to %s.", payload.to)
        except EmailServiceError as exc:
            logger.error(
                "Scheduled single email failed for %s: %s",
                payload_data.get("to", ""),
                exc.message,
            )
        except Exception as exc:
            logger.exception(
                "Unexpected error while sending scheduled single email to %s: %s",
                payload_data.get("to", ""),
                exc,
            )

    def _run_bulk_email_job(
        self,
        filename: str,
        file_bytes: bytes,
        subject_template: str,
        body_template: str,
    ) -> None:
        email_service = EmailService(get_settings())
        bulk_email_service = BulkEmailService(email_service)

        try:
            result = bulk_email_service.send_bulk_email(
                filename=filename,
                file_bytes=file_bytes,
                subject_template=subject_template,
                body_template=body_template,
            )
            logger.info(
                "Scheduled bulk email completed: sent=%s failed=%s skipped=%s.",
                result.sent_count,
                result.failed_count,
                result.skipped_count,
            )
        except EmailServiceError as exc:
            logger.error("Scheduled bulk email failed: %s", exc.message)
        except Exception as exc:
            logger.exception("Unexpected error while sending scheduled bulk email: %s", exc)


scheduler_service = SchedulerService()
