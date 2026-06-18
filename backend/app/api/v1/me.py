from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.security import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.event import EventListItem, Page
from app.schemas.registration import RegistrationWithEvent
from app.services.event import EventService
from app.services.registration import RegistrationService

router = APIRouter()

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


@router.get(
    "/registrations",
    response_model=Page[RegistrationWithEvent],
    summary="Historial de inscripciones del usuario autenticado.",
)
def list_my_registrations(
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    actor: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Page[RegistrationWithEvent]:
    reg_service = RegistrationService(session)
    event_service = EventService(session)
    rows, total = reg_service.list_mine(actor=actor, limit=limit, offset=offset)

    # Hidratar EventListItem (con conteos) en batch para evitar N+1.
    events = [event for _reg, event in rows]
    hydrated_events: dict[int, EventListItem] = {
        item.id: item for item in event_service.hydrate_list_items(events)
    }
    items: list[RegistrationWithEvent] = [
        RegistrationWithEvent(
            id=reg.id,
            user_id=reg.user_id,
            event_id=reg.event_id,
            status=reg.status,
            created_at=reg.created_at,
            updated_at=reg.updated_at,
            event=hydrated_events[event.id],
        )
        for reg, event in rows
    ]
    return Page[RegistrationWithEvent](
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
