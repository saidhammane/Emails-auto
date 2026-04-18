from datetime import date

from sqlalchemy import case, func, select

from app.api.schemas import (
    AnalyticsSummaryResponse,
    DailyAnalyticsResponse,
    ErrorInsightResponse,
)
from app.db.database import get_db_session
from app.db.models import EmailLog


class AnalyticsService:
    def get_summary(self) -> AnalyticsSummaryResponse:
        with get_db_session() as session:
            totals = session.execute(
                select(
                    func.sum(case((EmailLog.status == "sent", 1), else_=0)).label(
                        "total_sent"
                    ),
                    func.sum(case((EmailLog.status == "failed", 1), else_=0)).label(
                        "total_failed"
                    ),
                    func.sum(case((EmailLog.status == "scheduled", 1), else_=0)).label(
                        "total_scheduled"
                    ),
                )
            ).one()

        total_sent = int(totals.total_sent or 0)
        total_failed = int(totals.total_failed or 0)
        total_scheduled = int(totals.total_scheduled or 0)
        attempted = total_sent + total_failed

        if attempted == 0:
            success_rate = 0.0
            failure_rate = 0.0
        else:
            success_rate = round((total_sent / attempted) * 100, 1)
            failure_rate = round((total_failed / attempted) * 100, 1)

        return AnalyticsSummaryResponse(
            total_sent=total_sent,
            total_failed=total_failed,
            total_scheduled=total_scheduled,
            success_rate=success_rate,
            failure_rate=failure_rate,
        )

    def get_daily_activity(self) -> list[DailyAnalyticsResponse]:
        log_date = func.date(EmailLog.timestamp)

        with get_db_session() as session:
            rows = session.execute(
                select(
                    log_date.label("date"),
                    func.sum(case((EmailLog.status == "sent", 1), else_=0)).label(
                        "sent_count"
                    ),
                    func.sum(case((EmailLog.status == "failed", 1), else_=0)).label(
                        "failed_count"
                    ),
                )
                .where(EmailLog.status.in_(("sent", "failed")))
                .group_by(log_date)
                .order_by(log_date.desc())
            ).all()

        return [
            DailyAnalyticsResponse(
                date=date.fromisoformat(str(row.date)),
                sent_count=int(row.sent_count or 0),
                failed_count=int(row.failed_count or 0),
            )
            for row in rows
        ]

    def get_error_insights(self) -> list[ErrorInsightResponse]:
        with get_db_session() as session:
            rows = session.execute(
                select(
                    EmailLog.error_message.label("error_message"),
                    func.count(EmailLog.id).label("count"),
                )
                .where(
                    EmailLog.status == "failed",
                    EmailLog.error_message.is_not(None),
                    EmailLog.error_message != "",
                )
                .group_by(EmailLog.error_message)
                .order_by(func.count(EmailLog.id).desc(), EmailLog.error_message.asc())
            ).all()

        return [
            ErrorInsightResponse(
                error_message=str(row.error_message),
                count=int(row.count or 0),
            )
            for row in rows
        ]
