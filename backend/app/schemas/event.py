from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.event import EventStatus

TITLE_MAX = 200
LOCATION_MAX = 200
DESCRIPTION_MAX = 5000


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=TITLE_MAX)
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX)
    location: str = Field(min_length=1, max_length=LOCATION_MAX)
    capacity: int = Field(gt=0)
    start_at: datetime
    end_at: datetime

    @field_validator("title", "location")
    @classmethod
    def _strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("no puede estar vacío")
        return stripped

    @model_validator(mode="after")
    def _check_time_range(self) -> "EventCreate":
        if self.start_at >= self.end_at:
            raise ValueError("start_at debe ser anterior a end_at")
        return self


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=TITLE_MAX)
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX)
    location: str | None = Field(default=None, min_length=1, max_length=LOCATION_MAX)
    capacity: int | None = Field(default=None, gt=0)
    start_at: datetime | None = None
    end_at: datetime | None = None

    @field_validator("title", "location")
    @classmethod
    def _strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("no puede estar vacío")
        return stripped


class EventRead(BaseModel):
    id: int
    title: str
    description: str | None
    location: str
    capacity: int
    start_at: datetime
    end_at: datetime
    status: EventStatus
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventListItem(BaseModel):
    id: int
    title: str
    location: str
    start_at: datetime
    end_at: datetime
    capacity: int
    status: EventStatus
    owner_id: int

    model_config = ConfigDict(from_attributes=True)


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
