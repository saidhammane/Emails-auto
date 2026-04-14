from pydantic import BaseModel, EmailStr, Field


class SendTestEmailRequest(BaseModel):
    to: EmailStr
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)


class ApiResponse(BaseModel):
    success: bool
    message: str
