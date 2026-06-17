from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import CheckConstraint, Column, DateTime, func
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    """Roles globales del sistema. SPEAKER NO va aquí: es atributo derivado por evento."""

    ADMIN = "ADMIN"
    ORGANIZER = "ORGANIZER"
    ATTENDEE = "ATTENDEE"


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("email = lower(email)", name="ck_users_email_lowercase"),)

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    password_hash: str = Field(max_length=255)
    role: UserRole = Field(
        sa_column=Column(
            SAEnum(UserRole, name="user_role"),
            nullable=False,
            server_default=UserRole.ATTENDEE.value,
        ),
        default=UserRole.ATTENDEE,
    )
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        ),
    )
