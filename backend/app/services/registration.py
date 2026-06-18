from sqlmodel import Session

from app.core.errors import (
    DuplicateRegistration,
    EventFull,
    InvalidRegistrationState,
    NotFound,
    SpeakerCannotRegister,
)
from app.db.session import transactional
from app.models.event import EventStatus
from app.models.registration import Registration
from app.models.user import User
from app.repositories.event import EventRepository
from app.repositories.event_session import EventSessionRepository
from app.repositories.registration import RegistrationRepository


class RegistrationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.events = EventRepository(session)
        self.sessions = EventSessionRepository(session)
        self.registrations = RegistrationRepository(session)

    def register(self, *, actor: User, event_id: int) -> Registration:
        with transactional(self.session):
            # Lock pesimista: serializa inscripciones concurrentes sobre el mismo evento.
            event = self.events.get_for_update(event_id)
            if event is None:
                raise NotFound("Evento no encontrado")

            if event.status != EventStatus.PUBLISHED:
                raise InvalidRegistrationState(
                    details={
                        "event_id": event.id,
                        "current_status": event.status.value,
                    },
                )

            if self.sessions.is_speaker_of_event(user_id=actor.id, event_id=event.id):
                raise SpeakerCannotRegister(
                    details={"event_id": event.id, "user_id": actor.id},
                )

            existing = self.registrations.get_active(user_id=actor.id, event_id=event.id)
            if existing is not None:
                raise DuplicateRegistration(
                    details={"event_id": event.id, "registration_id": existing.id},
                )

            confirmed = self.registrations.count_confirmed(event.id)
            if confirmed >= event.capacity:
                raise EventFull(
                    details={"event_id": event.id, "capacity": event.capacity},
                )

            reg = self.registrations.create(user_id=actor.id, event_id=event.id)
        self.session.refresh(reg)
        return reg

    def cancel_my_registration(self, *, actor: User, event_id: int) -> None:
        with transactional(self.session):
            reg = self.registrations.get_active(user_id=actor.id, event_id=event_id)
            if reg is None:
                raise NotFound(
                    "No tienes una inscripción activa para este evento",
                    details={"event_id": event_id, "reason": "no active registration"},
                )
            self.registrations.mark_cancelled(reg)

    def list_mine(
        self, *, actor: User, limit: int, offset: int
    ):
        return self.registrations.list_for_user(
            user_id=actor.id, limit=limit, offset=offset
        )
