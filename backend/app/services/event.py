from sqlmodel import Session

from app.core.errors import (
    EventCapacityBelowSession,
    EventNotMutable,
    Forbidden,
    InvalidTransition,
    NotFound,
    ValidationFailed,
)
from app.db.session import transactional
from app.models.event import Event, EventStatus
from app.models.user import User, UserRole
from app.repositories.event import EventRepository
from app.repositories.event_session import EventSessionRepository
from app.repositories.registration import RegistrationRepository
from app.schemas.event import EventCreate, EventListItem, EventRead, EventUpdate
from app.services import event_state


class EventService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.events = EventRepository(session)
        self.sessions_repo = EventSessionRepository(session)
        self.registrations_repo = RegistrationRepository(session)

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

            # Fase 4: si el patch baja capacity, no puede ir por debajo del aforo
            # de alguna sesión ya programada.
            if "capacity" in clean_patch:
                new_capacity = clean_patch["capacity"]
                max_session_capacity = self.sessions_repo.max_capacity_for_event(event.id)
                if (
                    max_session_capacity is not None
                    and new_capacity < max_session_capacity
                ):
                    raise EventCapacityBelowSession(
                        details={
                            "event_id": event.id,
                            "new_capacity": new_capacity,
                            "max_session_capacity": max_session_capacity,
                        },
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

    def transition(self, *, actor: User, event_id: int, to_status: EventStatus) -> Event:
        with transactional(self.session):
            event = self.events.get(event_id)
            if event is None:
                raise NotFound("Evento no encontrado")

            rule = event_state.TRANSITIONS.get((event.status, to_status))
            if rule is None:
                raise InvalidTransition(
                    details={
                        "event_id": event.id,
                        "from_status": event.status.value,
                        "to_status": to_status.value,
                        "reason": "transition not allowed",
                    },
                )

            if actor.role not in rule.allowed_roles:
                raise Forbidden("Rol no autorizado para esta transición")
            if (
                rule.requires_ownership
                and actor.role != UserRole.ADMIN
                and event.owner_id != actor.id
            ):
                raise Forbidden("Solo el dueño o un admin puede transicionar este evento")

            rule.validator(event, event_state._now_utc())

            from_status = event.status
            event.status = to_status
            self.session.add(event)
            self.session.flush()

            # Cascada Fase 5: cancelar el evento Published libera todas las
            # inscripciones activas dentro de la misma transacción atómica.
            if (from_status, to_status) == (
                EventStatus.PUBLISHED,
                EventStatus.CANCELLED,
            ):
                RegistrationRepository(self.session).mark_all_active_cancelled_for_event(
                    event.id
                )
        self.session.refresh(event)
        return event

    # ---------- hidratación con counts (Fase 5) ----------
    def hydrate_read(self, event: Event, *, actor: User | None) -> EventRead:
        confirmed = self.registrations_repo.count_confirmed(event.id)
        my_status = None
        if actor is not None:
            statuses = self.registrations_repo.active_status_for_user_events(
                user_id=actor.id, event_ids=[event.id]
            )
            my_status = statuses.get(event.id)
        return EventRead(
            id=event.id,
            title=event.title,
            description=event.description,
            location=event.location,
            capacity=event.capacity,
            start_at=event.start_at,
            end_at=event.end_at,
            status=event.status,
            owner_id=event.owner_id,
            created_at=event.created_at,
            updated_at=event.updated_at,
            confirmed_count=confirmed,
            is_full=confirmed >= event.capacity,
            my_registration_status=my_status,
        )

    def hydrate_list_items(self, events: list[Event]) -> list[EventListItem]:
        """Listados: solo confirmed_count + is_full (sin my_registration_status para no inflar)."""
        if not events:
            return []
        event_ids = [e.id for e in events]
        counts = self.registrations_repo.count_confirmed_for_events(event_ids)
        items: list[EventListItem] = []
        for e in events:
            c = counts.get(e.id, 0)
            items.append(
                EventListItem(
                    id=e.id,
                    title=e.title,
                    location=e.location,
                    start_at=e.start_at,
                    end_at=e.end_at,
                    capacity=e.capacity,
                    status=e.status,
                    owner_id=e.owner_id,
                    confirmed_count=c,
                    is_full=c >= e.capacity,
                )
            )
        return items

    # ---------- helpers ----------
    @staticmethod
    def _is_owner_or_admin(actor: User | None, event: Event) -> bool:
        if actor is None:
            return False
        return actor.role == UserRole.ADMIN or actor.id == event.owner_id
