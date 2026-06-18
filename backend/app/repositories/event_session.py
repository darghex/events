from sqlalchemy import func
from sqlmodel import Session, select

from app.models.event import Event, EventStatus
from app.models.event_session import EventSession


class EventSessionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, session_id: int) -> EventSession | None:
        return self.session.get(EventSession, session_id)

    def is_speaker_of_event(self, *, user_id: int, event_id: int) -> bool:
        """True si el usuario está asignado como speaker de al menos una sesión del evento."""
        stmt = (
            select(EventSession.id)
            .where(EventSession.event_id == event_id)
            .where(EventSession.speaker_id == user_id)
            .limit(1)
        )
        return self.session.exec(stmt).first() is not None

    def list_by_event(self, event_id: int, *, limit: int = 200) -> list[EventSession]:
        stmt = (
            select(EventSession)
            .where(EventSession.event_id == event_id)
            .order_by(EventSession.start_at.asc())  # type: ignore[attr-defined]
            .limit(limit)
        )
        return list(self.session.exec(stmt).all())

    def max_capacity_for_event(self, event_id: int) -> int | None:
        """Mayor `capacity` entre las sesiones del evento (ignora NULL)."""
        stmt = (
            select(func.max(EventSession.capacity))
            .where(EventSession.event_id == event_id)
            .where(EventSession.capacity.is_not(None))  # type: ignore[attr-defined]
        )
        result = self.session.exec(stmt).first()
        return int(result) if result is not None else None

    def find_speaker_overlap(
        self,
        *,
        speaker_id: int,
        start_at,
        end_at,
        exclude_session_id: int | None = None,
    ) -> EventSession | None:
        """Busca cualquier sesión del mismo `speaker_id` cuyo intervalo se cruce con
        `[start_at, end_at)`. Excluye sesiones de eventos en estado `CANCELLED`."""
        stmt = (
            select(EventSession)
            .join(Event, Event.id == EventSession.event_id)
            .where(EventSession.speaker_id == speaker_id)
            .where(Event.status != EventStatus.CANCELLED)
            .where(EventSession.start_at < end_at)
            .where(EventSession.end_at > start_at)
        )
        if exclude_session_id is not None:
            stmt = stmt.where(EventSession.id != exclude_session_id)
        return self.session.exec(stmt).first()

    def create(self, *, data: dict, event_id: int) -> EventSession:
        payload = {k: v for k, v in data.items() if k != "event_id"}
        session = EventSession(event_id=event_id, **payload)
        self.session.add(session)
        self.session.flush()
        self.session.refresh(session)
        return session

    def update(self, session: EventSession, patch: dict) -> EventSession:
        for field, value in patch.items():
            setattr(session, field, value)
        self.session.add(session)
        self.session.flush()
        self.session.refresh(session)
        return session

    def delete(self, session: EventSession) -> None:
        self.session.delete(session)
        self.session.flush()
