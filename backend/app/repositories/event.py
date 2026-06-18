from sqlalchemy import func
from sqlmodel import Session, select

from app.models.event import Event, EventStatus


class EventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, event_id: int) -> Event | None:
        return self.session.get(Event, event_id)

    def list_published(
        self, *, q: str | None, limit: int, offset: int
    ) -> tuple[list[Event], int]:
        base = select(Event).where(Event.status == EventStatus.PUBLISHED)
        count_base = select(func.count()).select_from(Event).where(
            Event.status == EventStatus.PUBLISHED
        )
        if q:
            pattern = f"%{q}%"
            base = base.where(Event.title.ilike(pattern))  # type: ignore[attr-defined]
            count_base = count_base.where(Event.title.ilike(pattern))  # type: ignore[attr-defined]

        rows = self.session.exec(
            base.order_by(Event.start_at.asc()).limit(limit).offset(offset)  # type: ignore[attr-defined]
        ).all()
        total = self.session.exec(count_base).one()
        return list(rows), int(total)

    def list_by_owner(
        self, *, owner_id: int, limit: int, offset: int
    ) -> tuple[list[Event], int]:
        base = select(Event).where(Event.owner_id == owner_id)
        count_base = select(func.count()).select_from(Event).where(Event.owner_id == owner_id)
        rows = self.session.exec(
            base.order_by(Event.created_at.desc()).limit(limit).offset(offset)  # type: ignore[attr-defined]
        ).all()
        total = self.session.exec(count_base).one()
        return list(rows), int(total)

    def create(self, *, data: dict, owner_id: int) -> Event:
        event = Event(
            **data,
            status=EventStatus.DRAFT,
            owner_id=owner_id,
        )
        self.session.add(event)
        self.session.flush()
        self.session.refresh(event)
        return event

    def update(self, event: Event, patch: dict) -> Event:
        for field, value in patch.items():
            setattr(event, field, value)
        self.session.add(event)
        self.session.flush()
        self.session.refresh(event)
        return event

    def delete(self, event: Event) -> None:
        self.session.delete(event)
        self.session.flush()
