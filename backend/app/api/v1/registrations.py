from fastapi import APIRouter, Depends, Response, status
from sqlmodel import Session

from app.core.security import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.registration import RegistrationRead
from app.services.registration import RegistrationService

router = APIRouter()


def _service(session: Session = Depends(get_session)) -> RegistrationService:
    return RegistrationService(session)


@router.post(
    "",
    response_model=RegistrationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Inscribirse al evento. Requiere evento en Published. Owner permitido.",
)
def register_for_event(
    event_id: int,
    actor: User = Depends(get_current_user),
    service: RegistrationService = Depends(_service),
) -> RegistrationRead:
    reg = service.register(actor=actor, event_id=event_id)
    return RegistrationRead.model_validate(reg)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancelar mi inscripción activa al evento.",
)
def cancel_my_registration(
    event_id: int,
    actor: User = Depends(get_current_user),
    service: RegistrationService = Depends(_service),
) -> Response:
    service.cancel_my_registration(actor=actor, event_id=event_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
