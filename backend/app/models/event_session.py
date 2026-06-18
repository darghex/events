from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, func
from sqlmodel import Field, SQLModel


class EventSession(SQLModel, table=True):
    """Bloque de actividad dentro de un Event (panel, taller, charla, etc.)."""

    __tablename__ = "event_sessions"
    __table_args__ = (
        CheckConstraint("start_at < end_at", name="ck_event_sessions_start_before_end"),
        CheckConstraint(
            "capacity IS NULL OR capacity > 0",
            name="ck_event_sessions_capacity_positive_or_null",
        ),
        Index("ix_event_sessions_event_start", "event_id", "start_at"),
        Index("ix_event_sessions_speaker_start", "speaker_id", "start_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    event_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    speaker_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
    )
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    start_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    end_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    capacity: int | None = Field(default=None)
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
