from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, func
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class RegistrationStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class Registration(SQLModel, table=True):
    """Inscripción de un usuario a un evento.

    Unicidad: solo una fila CONFIRMED por (user_id, event_id). El índice parcial
    `uq_registrations_active` se crea en la migración (Postgres y SQLite lo soportan).
    Las filas CANCELLED permiten re-inscripción posterior.
    """

    __tablename__ = "registrations"
    __table_args__ = (
        Index("ix_registrations_event_status", "event_id", "status"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
    )
    event_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    status: RegistrationStatus = Field(
        sa_column=Column(
            SAEnum(RegistrationStatus, name="registration_status"),
            nullable=False,
            server_default=RegistrationStatus.CONFIRMED.value,
            index=True,
        ),
        default=RegistrationStatus.CONFIRMED,
    )
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
