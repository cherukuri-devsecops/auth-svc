from typing import Optional

from pydantic import BaseModel, EmailStr


class GoogleUser(BaseModel):
    google_id: str
    email: EmailStr
    name: str
    picture: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: GoogleUser


class RefreshRequest(BaseModel):
    refresh_token: str


class VerifyTokenRequest(BaseModel):
    token: str


class VerifyTokenResponse(BaseModel):
    valid: bool
    user: Optional[GoogleUser] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
