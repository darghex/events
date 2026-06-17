import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole

# Política de password: ≥8 chars, ≥1 mayúscula, ≥1 dígito
PASSWORD_MIN_LENGTH = 8
_UPPER_RE = re.compile(r"[A-Z]")
_DIGIT_RE = re.compile(r"\d")


def _validate_password_policy(value: str) -> str:
    if len(value) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"password debe tener al menos {PASSWORD_MIN_LENGTH} caracteres")
    if not _UPPER_RE.search(value):
        raise ValueError("password debe contener al menos una letra mayúscula")
    if not _DIGIT_RE.search(value):
        raise ValueError("password debe contener al menos un dígito")
    return value


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=128)

    @field_validator("email")
    @classmethod
    def _email_lowercase(cls, value: str) -> str:
        return value.lower()

    @field_validator("password")
    @classmethod
    def _password_policy(cls, value: str) -> str:
        return _validate_password_policy(value)


class UserRead(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def _email_lowercase(cls, value: str) -> str:
        return value.lower()


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
