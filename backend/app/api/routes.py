from fastapi import APIRouter, Depends, Response

from app.api.schemas import ApiResponse, SendTestEmailRequest
from app.core.config import Settings, get_settings
from app.services.email_service import EmailService, EmailServiceError

router = APIRouter()
health_router = APIRouter(tags=["Health"])
email_router = APIRouter(tags=["Email"])


def get_email_service(settings: Settings = Depends(get_settings)) -> EmailService:
    return EmailService(settings)


def build_api_response(success: bool, message: str) -> ApiResponse:
    return ApiResponse(success=success, message=message)


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


router.include_router(health_router)
router.include_router(email_router)
