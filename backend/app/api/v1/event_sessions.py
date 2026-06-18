from fastapi import APIRouter, Depends, Response, status
from sqlmodel import Session

from app.core.security import get_current_user, get_optional_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.event_session import SessionCreate, SessionRead, SessionUpdate
from app.services.event_session import EventSessionService

router = APIRouter()


def _service(session: Session = Depends(get_session)) -> EventSessionService:
    return EventSessionService(session)


@router.get(
    "",
    response_model=list[SessionRead],
    summary="Agenda de sesiones del evento (pública para Published+; Draft solo owner/admin).",
)
def list_sessions(
    event_id: int,
    actor: User | None = Depends(get_optional_user),
    service: EventSessionService = Depends(_service),
) -> list[SessionRead]:
    return service.list_for_event(actor=actor, event_id=event_id)


@router.get(
    "/{session_id}",
    response_model=SessionRead,
    summary="Detalle de una sesión.",
)
def get_session_detail(
    event_id: int,
    session_id: int,
    actor: User | None = Depends(get_optional_user),
    service: EventSessionService = Depends(_service),
) -> SessionRead:
    return service.get(actor=actor, event_id=event_id, session_id=session_id)


@router.post(
    "",
    response_model=SessionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear sesión (owner del evento o admin). Evento en Draft o Published.",
)
def create_session(
    event_id: int,
    payload: SessionCreate,
    actor: User = Depends(get_current_user),
    service: EventSessionService = Depends(_service),
) -> SessionRead:
    return service.create(actor=actor, event_id=event_id, data=payload)


@router.patch(
    "/{session_id}",
    response_model=SessionRead,
    summary="Editar sesión (owner del evento o admin).",
)
def update_session(
    event_id: int,
    session_id: int,
    payload: SessionUpdate,
    actor: User = Depends(get_current_user),
    service: EventSessionService = Depends(_service),
) -> SessionRead:
    return service.update(
        actor=actor, event_id=event_id, session_id=session_id, patch=payload
    )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar sesión (owner del evento o admin).",
)
def delete_session(
    event_id: int,
    session_id: int,
    actor: User = Depends(get_current_user),
    service: EventSessionService = Depends(_service),
) -> Response:
    service.delete(actor=actor, event_id=event_id, session_id=session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
