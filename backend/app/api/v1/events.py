from fastapi import APIRouter, Depends, Query, Response, status
from sqlmodel import Session

from app.core.security import get_current_user, get_optional_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.event import (
    EventCreate,
    EventListItem,
    EventRead,
    EventTransitionRequest,
    EventUpdate,
    Page,
)
from app.services.event import EventService

DEFAULT_LIMIT = 20
MAX_LIMIT = 100

router = APIRouter()


def _service(session: Session = Depends(get_session)) -> EventService:
    return EventService(session)


def _paginate(items, total: int, limit: int, offset: int) -> Page[EventListItem]:
    return Page[EventListItem](
        items=[EventListItem.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "",
    response_model=Page[EventListItem],
    summary="Listado público de eventos publicados (paginado + búsqueda por título)",
)
def list_published(
    q: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    service: EventService = Depends(_service),
) -> Page[EventListItem]:
    items, total = service.list_published(q=q, limit=limit, offset=offset)
    return _paginate(items, total, limit, offset)


@router.get(
    "/me",
    response_model=Page[EventListItem],
    summary="Eventos del usuario autenticado (cualquier estado)",
)
def list_mine(
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    actor: User = Depends(get_current_user),
    service: EventService = Depends(_service),
) -> Page[EventListItem]:
    items, total = service.list_mine(actor=actor, limit=limit, offset=offset)
    return _paginate(items, total, limit, offset)


@router.get(
    "/{event_id}",
    response_model=EventRead,
    summary="Detalle de evento (público para Published; owner/admin para Draft)",
)
def get_event(
    event_id: int,
    actor: User | None = Depends(get_optional_user),
    service: EventService = Depends(_service),
) -> EventRead:
    event = service.get(actor=actor, event_id=event_id)
    return EventRead.model_validate(event)


@router.post(
    "",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear evento (organizer o admin). Siempre nace en estado Draft.",
)
def create_event(
    payload: EventCreate,
    actor: User = Depends(get_current_user),
    service: EventService = Depends(_service),
) -> EventRead:
    event = service.create(actor=actor, data=payload)
    return EventRead.model_validate(event)


@router.patch(
    "/{event_id}",
    response_model=EventRead,
    summary="Editar evento (owner o admin). Solo Draft salvo admin.",
)
def update_event(
    event_id: int,
    payload: EventUpdate,
    actor: User = Depends(get_current_user),
    service: EventService = Depends(_service),
) -> EventRead:
    event = service.update(actor=actor, event_id=event_id, patch=payload)
    return EventRead.model_validate(event)


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar evento (owner o admin). Solo Draft.",
)
def delete_event(
    event_id: int,
    actor: User = Depends(get_current_user),
    service: EventService = Depends(_service),
) -> Response:
    service.delete(actor=actor, event_id=event_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{event_id}/transition",
    response_model=EventRead,
    summary="Transicionar el estado del evento según la matriz declarada.",
)
def transition_event(
    event_id: int,
    payload: EventTransitionRequest,
    actor: User = Depends(get_current_user),
    service: EventService = Depends(_service),
) -> EventRead:
    event = service.transition(actor=actor, event_id=event_id, to_status=payload.to_status)
    return EventRead.model_validate(event)
