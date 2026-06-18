from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.registration import RegistrationStatus
from app.schemas.event import EventListItem


class RegistrationRead(BaseModel):
    id: int
    user_id: int
    event_id: int
    status: RegistrationStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RegistrationWithEvent(RegistrationRead):
    event: EventListItem
