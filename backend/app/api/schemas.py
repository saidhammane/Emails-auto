from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SendTestEmailRequest(BaseModel):
    to: EmailStr
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)


class ApiResponse(BaseModel):
    success: bool
    message: str


class BulkEmailIssue(BaseModel):
    row: int
    email: str
    reason: str


class BulkEmailResponse(ApiResponse):
    total_rows: int = 0
    valid_rows: int = 0
    sent_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    failures: list[BulkEmailIssue] = Field(default_factory=list)
    skipped: list[BulkEmailIssue] = Field(default_factory=list)


class ScheduleEmailRequest(BaseModel):
    to: EmailStr
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    send_at: str = Field(..., min_length=1)


class ScheduleResponse(ApiResponse):
    scheduled_for: str | None = None


class EmailLogResponse(BaseModel):
    id: int
    email: str
    subject: str
    status: str
    error_message: str | None = None
    timestamp: datetime
