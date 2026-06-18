from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, func, text
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class EventStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"


class Event(SQLModel, table=True):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("capacity > 0", name="ck_events_capacity_positive"),
        CheckConstraint("start_at < end_at", name="ck_events_start_before_end"),
        Index("ix_events_status_start_at", "status", "start_at"),
        # created_at DESC: optimiza el listado del owner ordenado por más reciente primero
        Index("ix_events_owner_created", "owner_id", text("created_at DESC")),
    )

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    location: str = Field(min_length=1, max_length=200)
    capacity: int
    start_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    end_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    status: EventStatus = Field(
        sa_column=Column(
            SAEnum(EventStatus, name="event_status"),
            nullable=False,
            server_default=EventStatus.DRAFT.value,
        ),
        default=EventStatus.DRAFT,
    )
    owner_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
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
