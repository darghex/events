from datetime import datetime

from sqlmodel import Session

from app.core.errors import (
    EventNotMutable,
    Forbidden,
    NotFound,
    SessionCapacityExceedsEvent,
    SessionOutOfRange,
    SessionOverlap,
    ValidationFailed,
)
from app.db.session import transactional
from app.models.event import Event, EventStatus
from app.models.event_session import EventSession
from app.models.user import User, UserRole
from app.repositories.event import EventRepository
from app.repositories.event_session import EventSessionRepository
from app.repositories.user import UserRepository
from app.schemas.event_session import SessionCreate, SessionUpdate, Speaker, SessionRead

_MUTABLE_EVENT_STATES = {EventStatus.DRAFT, EventStatus.PUBLISHED}


class EventSessionService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.events = EventRepository(session)
        self.sessions = EventSessionRepository(session)
        self.users = UserRepository(session)

    # ---------- queries ----------
    def list_for_event(self, *, actor: User | None, event_id: int) -> list[SessionRead]:
        event = self.events.get(event_id)
        if event is None:
            raise NotFound("Evento no encontrado")
        if event.status == EventStatus.DRAFT and not self._is_owner_or_admin(actor, event):
            raise NotFound("Evento no encontrado")
        sessions = self.sessions.list_by_event(event_id)
        return self._enrich_many(sessions)

    def get(self, *, actor: User | None, event_id: int, session_id: int) -> SessionRead:
        event = self.events.get(event_id)
        if event is None:
            raise NotFound("Evento no encontrado")
        if event.status == EventStatus.DRAFT and not self._is_owner_or_admin(actor, event):
            raise NotFound("Evento no encontrado")
        session = self.sessions.get(session_id)
        if session is None or session.event_id != event_id:
            raise NotFound("Sesión no encontrada")
        return self._enrich_one(session)

    # ---------- mutations ----------
    def create(self, *, actor: User, event_id: int, data: SessionCreate) -> SessionRead:
        with transactional(self.session):
            event = self._load_mutable_event(actor, event_id)
            self._validate_speaker_exists(data.speaker_id)
            self._validate_in_event_range(event, data.start_at, data.end_at)
            self._validate_capacity(event, data.capacity)
            self._validate_no_overlap(
                speaker_id=data.speaker_id,
                start_at=data.start_at,
                end_at=data.end_at,
            )
            payload = data.model_dump()
            created = self.sessions.create(data=payload, event_id=event_id)
        self.session.refresh(created)
        return self._enrich_one(created)

    def update(
        self, *, actor: User, event_id: int, session_id: int, patch: SessionUpdate
    ) -> SessionRead:
        with transactional(self.session):
            event = self._load_mutable_event(actor, event_id)
            session = self.sessions.get(session_id)
            if session is None or session.event_id != event_id:
                raise NotFound("Sesión no encontrada")

            clean = patch.model_dump(exclude_unset=True)
            merged_start = clean.get("start_at", session.start_at)
            merged_end = clean.get("end_at", session.end_at)
            merged_speaker_id = clean.get("speaker_id", session.speaker_id)
            merged_capacity = clean.get("capacity", session.capacity)

            if merged_start >= merged_end:
                raise ValidationFailed(
                    "start_at debe ser anterior a end_at",
                    details={"fields": ["start_at", "end_at"]},
                )

            if "speaker_id" in clean:
                self._validate_speaker_exists(merged_speaker_id)
            self._validate_in_event_range(event, merged_start, merged_end)
            self._validate_capacity(event, merged_capacity)
            self._validate_no_overlap(
                speaker_id=merged_speaker_id,
                start_at=merged_start,
                end_at=merged_end,
                exclude_session_id=session_id,
            )

            updated = self.sessions.update(session, clean)
        self.session.refresh(updated)
        return self._enrich_one(updated)

    def delete(self, *, actor: User, event_id: int, session_id: int) -> None:
        with transactional(self.session):
            event = self._load_mutable_event(actor, event_id)
            session = self.sessions.get(session_id)
            if session is None or session.event_id != event_id:
                raise NotFound("Sesión no encontrada")
            _ = event  # consumido solo por los guards
            self.sessions.delete(session)

    # ---------- guards ----------
    def _load_mutable_event(self, actor: User, event_id: int) -> Event:
        event = self.events.get(event_id)
        if event is None:
            raise NotFound("Evento no encontrado")
        if not self._is_owner_or_admin(actor, event):
            raise Forbidden("No tienes permisos sobre este evento")
        if event.status not in _MUTABLE_EVENT_STATES:
            raise EventNotMutable(
                details={
                    "event_id": event.id,
                    "current_status": event.status.value,
                    "reason": "sessions can only be modified while event is Draft or Published",
                },
            )
        return event

    def _validate_speaker_exists(self, speaker_id: int) -> None:
        speaker = self.users.get_by_id(speaker_id)
        if speaker is None:
            raise NotFound(
                "Ponente no encontrado",
                details={"speaker_id": speaker_id, "reason": "speaker not found"},
            )

    def _validate_in_event_range(
        self, event: Event, start_at: datetime, end_at: datetime
    ) -> None:
        event_start = _as_utc(event.start_at)
        event_end = _as_utc(event.end_at)
        s_start = _as_utc(start_at)
        s_end = _as_utc(end_at)
        if s_start < event_start or s_end > event_end:
            raise SessionOutOfRange(
                details={
                    "event_id": event.id,
                    "event_start": event_start.isoformat(),
                    "event_end": event_end.isoformat(),
                    "session_start": s_start.isoformat(),
                    "session_end": s_end.isoformat(),
                },
            )

    def _validate_capacity(self, event: Event, session_capacity: int | None) -> None:
        if session_capacity is None:
            return
        if session_capacity > event.capacity:
            raise SessionCapacityExceedsEvent(
                details={
                    "event_capacity": event.capacity,
                    "session_capacity": session_capacity,
                },
            )

    def _validate_no_overlap(
        self,
        *,
        speaker_id: int,
        start_at: datetime,
        end_at: datetime,
        exclude_session_id: int | None = None,
    ) -> None:
        conflict = self.sessions.find_speaker_overlap(
            speaker_id=speaker_id,
            start_at=start_at,
            end_at=end_at,
            exclude_session_id=exclude_session_id,
        )
        if conflict is not None:
            raise SessionOverlap(
                details={
                    "speaker_id": speaker_id,
                    "conflicting_session_id": conflict.id,
                    "conflicting_event_id": conflict.event_id,
                },
            )

    # ---------- helpers ----------
    @staticmethod
    def _is_owner_or_admin(actor: User | None, event: Event) -> bool:
        if actor is None:
            return False
        return actor.role == UserRole.ADMIN or actor.id == event.owner_id

    def _enrich_one(self, session: EventSession) -> SessionRead:
        speaker = self.users.get_by_id(session.speaker_id)
        return self._to_read(session, speaker)

    def _enrich_many(self, sessions: list[EventSession]) -> list[SessionRead]:
        speaker_ids = list({s.speaker_id for s in sessions})
        speakers = {u.id: u for u in self.users.get_many(speaker_ids)}
        return [self._to_read(s, speakers.get(s.speaker_id)) for s in sessions]

    @staticmethod
    def _to_read(session: EventSession, speaker: User | None) -> SessionRead:
        # Speaker debería existir siempre (FK ON DELETE RESTRICT); si no, exponemos
        # un placeholder visible para que el bug salga rápido en lugar de un 500 mudo.
        speaker_view = (
            Speaker(id=speaker.id, email=speaker.email)
            if speaker is not None
            else Speaker(id=session.speaker_id, email="<unknown>")
        )
        return SessionRead(
            id=session.id,
            event_id=session.event_id,
            speaker_id=session.speaker_id,
            title=session.title,
            description=session.description,
            start_at=session.start_at,
            end_at=session.end_at,
            capacity=session.capacity,
            created_at=session.created_at,
            updated_at=session.updated_at,
            speaker=speaker_view,
        )


def _as_utc(dt: datetime) -> datetime:
    """Mismo defensivo que en `event_state.py` para tests con SQLite naive."""
    from datetime import timezone

    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
