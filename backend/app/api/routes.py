from fastapi import APIRouter, Depends, File, Form, Response, UploadFile

from app.api.schemas import (
    ApiResponse,
    AnalyticsSummaryResponse,
    BulkEmailResponse,
    DailyAnalyticsResponse,
    EmailLogResponse,
    ErrorInsightResponse,
    ScheduleEmailRequest,
    ScheduleResponse,
    SendTestEmailRequest,
)
from app.core.config import Settings, get_settings
from app.services.analytics_service import AnalyticsService
from app.services.bulk_email_service import BulkEmailService
from app.services.email_service import EmailService, EmailServiceError
from app.services.email_log_service import EmailLogService
from app.services.scheduler_service import SchedulerService, scheduler_service

router = APIRouter()
health_router = APIRouter(tags=["Health"])
email_router = APIRouter(tags=["Email"])
bulk_email_router = APIRouter(tags=["Bulk Email"])
scheduler_router = APIRouter(tags=["Scheduling"])
logs_router = APIRouter(tags=["Logs"])
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_email_service(settings: Settings = Depends(get_settings)) -> EmailService:
    return EmailService(settings)


def get_bulk_email_service(
    email_service: EmailService = Depends(get_email_service),
) -> BulkEmailService:
    return BulkEmailService(email_service)


def get_scheduler_service() -> SchedulerService:
    return scheduler_service


def get_email_log_service() -> EmailLogService:
    return EmailLogService()


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()


def build_api_response(success: bool, message: str) -> ApiResponse:
    return ApiResponse(success=success, message=message)


def build_bulk_email_response(success: bool, message: str) -> BulkEmailResponse:
    return BulkEmailResponse(success=success, message=message)


def build_schedule_response(
    success: bool,
    message: str,
    scheduled_for: str | None = None,
) -> ScheduleResponse:
    return ScheduleResponse(
        success=success,
        message=message,
        scheduled_for=scheduled_for,
    )


@health_router.get("/health", response_model=ApiResponse)
def health_check() -> ApiResponse:
    return build_api_response(True, "API is healthy.")


@email_router.post("/send-test-email", response_model=ApiResponse)
def send_test_email(
    payload: SendTestEmailRequest,
    response: Response,
    email_service: EmailService = Depends(get_email_service),
) -> ApiResponse:
    try:
        email_service.send_test_email(payload)
    except EmailServiceError as exc:
        response.status_code = exc.status_code
        return build_api_response(False, exc.message)

    return build_api_response(True, "Test email sent successfully.")


@bulk_email_router.post("/send-bulk-email", response_model=BulkEmailResponse)
async def send_bulk_email(
    response: Response,
    file: UploadFile | None = File(
        default=None,
        description="CSV or XLSX file containing an email column.",
    ),
    subject_template: str = Form(default=""),
    body_template: str = Form(default=""),
    bulk_email_service: BulkEmailService = Depends(get_bulk_email_service),
) -> BulkEmailResponse:
    if file is None:
        response.status_code = 400
        return build_bulk_email_response(False, "Uploaded file is required.")

    file_bytes = await file.read()

    try:
        return bulk_email_service.send_bulk_email(
            filename=file.filename or "",
            file_bytes=file_bytes,
            subject_template=subject_template,
            body_template=body_template,
        )
    except EmailServiceError as exc:
        response.status_code = exc.status_code
        return build_bulk_email_response(False, exc.message)


@scheduler_router.post("/schedule-email", response_model=ScheduleResponse)
def schedule_email(
    payload: ScheduleEmailRequest,
    response: Response,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
) -> ScheduleResponse:
    try:
        scheduled_for = scheduler_service.schedule_single_email(payload)
    except EmailServiceError as exc:
        response.status_code = exc.status_code
        return build_schedule_response(False, exc.message)

    return build_schedule_response(
        True,
        "Email scheduled successfully.",
        scheduled_for,
    )


@scheduler_router.post("/schedule-bulk-email", response_model=ScheduleResponse)
async def schedule_bulk_email(
    response: Response,
    file: UploadFile | None = File(
        default=None,
        description="CSV or XLSX file containing an email column.",
    ),
    subject_template: str = Form(default=""),
    body_template: str = Form(default=""),
    send_at: str = Form(default=""),
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
) -> ScheduleResponse:
    if file is None:
        response.status_code = 400
        return build_schedule_response(False, "Uploaded file is required.")

    file_bytes = await file.read()

    try:
        scheduled_for = scheduler_service.schedule_bulk_email(
            filename=file.filename or "",
            file_bytes=file_bytes,
            subject_template=subject_template,
            body_template=body_template,
            send_at=send_at,
        )
    except EmailServiceError as exc:
        response.status_code = exc.status_code
        return build_schedule_response(False, exc.message)

    return build_schedule_response(
        True,
        "Bulk email scheduled successfully.",
        scheduled_for,
    )


@logs_router.get("/email-logs", response_model=list[EmailLogResponse])
def get_email_logs(
    email_log_service: EmailLogService = Depends(get_email_log_service),
) -> list[EmailLogResponse]:
    return email_log_service.list_logs()


@analytics_router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsSummaryResponse:
    return analytics_service.get_summary()


@analytics_router.get("/daily", response_model=list[DailyAnalyticsResponse])
def get_analytics_daily(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> list[DailyAnalyticsResponse]:
    return analytics_service.get_daily_activity()


@analytics_router.get("/errors", response_model=list[ErrorInsightResponse])
def get_analytics_errors(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> list[ErrorInsightResponse]:
    return analytics_service.get_error_insights()


router.include_router(health_router)
router.include_router(email_router)
router.include_router(bulk_email_router)
router.include_router(scheduler_router)
router.include_router(logs_router)
router.include_router(analytics_router)
