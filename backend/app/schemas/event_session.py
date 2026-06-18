from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TITLE_MAX = 200
DESCRIPTION_MAX = 2000


class Speaker(BaseModel):
    id: int
    email: str

    model_config = ConfigDict(from_attributes=True)


class SessionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=TITLE_MAX)
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX)
    speaker_id: int = Field(gt=0)
    start_at: datetime
    end_at: datetime
    capacity: int | None = Field(default=None, gt=0)

    @field_validator("title")
    @classmethod
    def _strip_title(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("no puede estar vacío")
        return stripped

    @model_validator(mode="after")
    def _check_time_range(self) -> "SessionCreate":
        if self.start_at >= self.end_at:
            raise ValueError("start_at debe ser anterior a end_at")
        return self


class SessionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=TITLE_MAX)
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX)
    speaker_id: int | None = Field(default=None, gt=0)
    start_at: datetime | None = None
    end_at: datetime | None = None
    capacity: int | None = Field(default=None, gt=0)

    @field_validator("title")
    @classmethod
    def _strip_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("no puede estar vacío")
        return stripped


class SessionRead(BaseModel):
    id: int
    event_id: int
    speaker_id: int
    title: str
    description: str | None
    start_at: datetime
    end_at: datetime
    capacity: int | None
    created_at: datetime
    updated_at: datetime
    speaker: Speaker

    model_config = ConfigDict(from_attributes=True)
