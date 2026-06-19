from sqlalchemy import func, update
from sqlmodel import Session, select

from app.models.event import Event
from app.models.registration import Registration, RegistrationStatus


class RegistrationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_active(self, *, user_id: int, event_id: int) -> Registration | None:
        stmt = (
            select(Registration)
            .where(Registration.user_id == user_id)
            .where(Registration.event_id == event_id)
            .where(Registration.status == RegistrationStatus.CONFIRMED)
        )
        return self.session.exec(stmt).first()

    def count_confirmed(self, event_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Registration)
            .where(Registration.event_id == event_id)
            .where(Registration.status == RegistrationStatus.CONFIRMED)
        )
        return int(self.session.exec(stmt).one())

    def count_confirmed_for_events(self, event_ids: list[int]) -> dict[int, int]:
        """Batch para evitar N+1 en listados públicos / propios."""
        if not event_ids:
            return {}
        stmt = (
            select(Registration.event_id, func.count())
            .where(Registration.event_id.in_(event_ids))  # type: ignore[attr-defined]
            .where(Registration.status == RegistrationStatus.CONFIRMED)
            .group_by(Registration.event_id)
        )
        return {row[0]: int(row[1]) for row in self.session.exec(stmt).all()}

    def active_status_for_user_events(
        self, *, user_id: int, event_ids: list[int]
    ) -> dict[int, RegistrationStatus]:
        """Para hidratar `my_registration_status` en batch."""
        if not event_ids:
            return {}
        stmt = (
            select(Registration.event_id, Registration.status)
            .where(Registration.user_id == user_id)
            .where(Registration.event_id.in_(event_ids))  # type: ignore[attr-defined]
            .where(Registration.status == RegistrationStatus.CONFIRMED)
        )
        return {row[0]: row[1] for row in self.session.exec(stmt).all()}

    def list_for_user(
        self, *, user_id: int, limit: int, offset: int
    ) -> tuple[list[tuple[Registration, Event]], int]:
        base = (
            select(Registration, Event)
            .join(Event, Event.id == Registration.event_id)
            .where(Registration.user_id == user_id)
        )
        count_stmt = (
            select(func.count())
            .select_from(Registration)
            .where(Registration.user_id == user_id)
        )
        total = int(self.session.exec(count_stmt).one())
        rows = self.session.exec(
            base.order_by(Registration.created_at.desc()).limit(limit).offset(offset)  # type: ignore[attr-defined]
        ).all()
        return list(rows), total

    def create(self, *, user_id: int, event_id: int) -> Registration:
        reg = Registration(
            user_id=user_id,
            event_id=event_id,
            status=RegistrationStatus.CONFIRMED,
        )
        self.session.add(reg)
        self.session.flush()
        self.session.refresh(reg)
        return reg

    def mark_cancelled(self, reg: Registration) -> Registration:
        reg.status = RegistrationStatus.CANCELLED
        self.session.add(reg)
        self.session.flush()
        self.session.refresh(reg)
        return reg

    def mark_all_active_cancelled_for_event(self, event_id: int) -> int:
        """Cascada disparada por la transición Published → Cancelled (Fase 3).

        Retorna el número de filas afectadas (para tests).
        """
        stmt = (
            update(Registration)
            .where(Registration.event_id == event_id)
            .where(Registration.status == RegistrationStatus.CONFIRMED)
            .values(status=RegistrationStatus.CANCELLED)
            .execution_options(synchronize_session="fetch")
        )
        result = self.session.exec(stmt)  # type: ignore[arg-type]
        self.session.flush()
        return int(result.rowcount or 0)
