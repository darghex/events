from sqlmodel import Session

from app.core.errors import EventNotMutable, Forbidden, NotFound, ValidationFailed
from app.db.session import transactional
from app.models.event import Event, EventStatus
from app.models.user import User, UserRole
from app.repositories.event import EventRepository
from app.schemas.event import EventCreate, EventUpdate


class EventService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.events = EventRepository(session)

    # ---------- queries ----------
    def list_published(
        self, *, q: str | None, limit: int, offset: int
    ) -> tuple[list[Event], int]:
        normalized = q.strip() if q else None
        return self.events.list_published(q=normalized or None, limit=limit, offset=offset)

    def list_mine(
        self, *, actor: User, limit: int, offset: int
    ) -> tuple[list[Event], int]:
        return self.events.list_by_owner(owner_id=actor.id, limit=limit, offset=offset)

    def get(self, *, actor: User | None, event_id: int) -> Event:
        event = self.events.get(event_id)
        if event is None:
            raise NotFound("Evento no encontrado")
        if event.status == EventStatus.DRAFT and not self._is_owner_or_admin(actor, event):
            # No filtrar existencia: el draft solo es visible para owner/admin
            raise NotFound("Evento no encontrado")
        return event

    # ---------- mutations ----------
    def create(self, *, actor: User, data: EventCreate) -> Event:
        if actor.role not in {UserRole.ORGANIZER, UserRole.ADMIN}:
            raise Forbidden("Solo organizadores o admin pueden crear eventos")
        with transactional(self.session):
            event = self.events.create(data=data.model_dump(), owner_id=actor.id)
        self.session.refresh(event)
        return event

    def update(self, *, actor: User, event_id: int, patch: EventUpdate) -> Event:
        with transactional(self.session):
            event = self.events.get(event_id)
            if event is None:
                raise NotFound("Evento no encontrado")
            if not self._is_owner_or_admin(actor, event):
                raise Forbidden("No tienes permisos sobre este evento")
            # Admin puede editar en cualquier estado; el resto solo Draft
            if event.status != EventStatus.DRAFT and actor.role != UserRole.ADMIN:
                raise EventNotMutable(
                    details={"event_id": event.id, "current_status": event.status.value},
                )

            clean_patch = patch.model_dump(exclude_unset=True)
            merged_start = clean_patch.get("start_at", event.start_at)
            merged_end = clean_patch.get("end_at", event.end_at)
            if merged_start >= merged_end:
                raise ValidationFailed(
                    "start_at debe ser anterior a end_at",
                    details={"fields": ["start_at", "end_at"]},
                )

            event = self.events.update(event, clean_patch)
        self.session.refresh(event)
        return event

    def delete(self, *, actor: User, event_id: int) -> None:
        with transactional(self.session):
            event = self.events.get(event_id)
            if event is None:
                raise NotFound("Evento no encontrado")
            if not self._is_owner_or_admin(actor, event):
                raise Forbidden("No tienes permisos sobre este evento")
            if event.status != EventStatus.DRAFT:
                raise EventNotMutable(
                    details={"event_id": event.id, "current_status": event.status.value},
                )
            self.events.delete(event)

    # ---------- helpers ----------
    @staticmethod
    def _is_owner_or_admin(actor: User | None, event: Event) -> bool:
        if actor is None:
            return False
        return actor.role == UserRole.ADMIN or actor.id == event.owner_id
