import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.api.schemas import EmailLogResponse
from app.db.database import get_db_session
from app.db.models import EmailLog

logger = logging.getLogger("email_dashboard.email_logs")


class EmailLogService:
    def log_sent(self, email: str, subject: str) -> None:
        self._log_status(
            email=email,
            subject=subject,
            status="sent",
        )

    def log_failed(self, email: str, subject: str, error_message: str) -> None:
        self._log_status(
            email=email,
            subject=subject,
            status="failed",
            error_message=error_message,
        )

    def log_scheduled(self, email: str, subject: str, details: str) -> None:
        self._log_status(
            email=email,
            subject=subject,
            status="scheduled",
            error_message=details,
        )

    def list_logs(self) -> list[EmailLogResponse]:
        with get_db_session() as session:
            logs = session.execute(
                select(EmailLog).order_by(EmailLog.timestamp.desc(), EmailLog.id.desc())
            ).scalars().all()
            return [
                EmailLogResponse(
                    id=log.id,
                    email=log.email,
                    subject=log.subject,
                    status=log.status,
                    error_message=log.error_message,
                    timestamp=log.timestamp,
                )
                for log in logs
            ]

    def _log_status(
        self,
        email: str,
        subject: str,
        status: str,
        error_message: str | None = None,
    ) -> None:
        try:
            with get_db_session() as session:
                session.add(
                    EmailLog(
                        email=email,
                        subject=subject,
                        status=status,
                        error_message=error_message,
                    )
                )
        except SQLAlchemyError as exc:
            logger.exception("Failed to persist email log: %s", exc)
