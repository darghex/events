"""Matriz declarativa de transiciones de estado para Event.

El servicio (`EventService.transition`) consulta `TRANSITIONS` para validar
RBAC, ownership y condiciones temporales. Cualquier `(from, to)` no listado
está implícitamente bloqueado.
"""
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from app.core.errors import InvalidTransition
from app.core.time import as_utc, now_utc
from app.models.event import Event, EventStatus
from app.models.user import UserRole


def _now_utc() -> datetime:
    return now_utc()


Validator = Callable[[Event, datetime], None]


@dataclass(frozen=True)
class TransitionRule:
    allowed_roles: frozenset[UserRole]
    requires_ownership: bool
    validator: Validator


# ---------- validators ----------
def _no_op(_event: Event, _now: datetime) -> None:
    return None


def _check_publishable(event: Event, _now: datetime) -> None:
    # Defensivo: CHECK en DB ya garantiza capacity > 0, pero protegemos contra
    # mutaciones futuras del modelo.
    if event.capacity <= 0:
        raise InvalidTransition(
            details={
                "event_id": event.id,
                "from_status": event.status.value,
                "to_status": EventStatus.PUBLISHED.value,
                "reason": "capacity must be greater than zero",
            },
        )


def _check_can_start(event: Event, now: datetime) -> None:
    if as_utc(now) < as_utc(event.start_at):
        raise InvalidTransition(
            details={
                "event_id": event.id,
                "from_status": event.status.value,
                "to_status": EventStatus.IN_PROGRESS.value,
                "reason": "event has not started yet",
            },
        )


def _check_can_finish(event: Event, now: datetime) -> None:
    if as_utc(now) < as_utc(event.end_at):
        raise InvalidTransition(
            details={
                "event_id": event.id,
                "from_status": event.status.value,
                "to_status": EventStatus.FINISHED.value,
                "reason": "event has not ended yet",
            },
        )


_OWNER_OR_ADMIN = frozenset({UserRole.ORGANIZER, UserRole.ADMIN})


TRANSITIONS: dict[tuple[EventStatus, EventStatus], TransitionRule] = {
    (EventStatus.DRAFT, EventStatus.PUBLISHED): TransitionRule(
        allowed_roles=_OWNER_OR_ADMIN, requires_ownership=True, validator=_check_publishable
    ),
    (EventStatus.DRAFT, EventStatus.CANCELLED): TransitionRule(
        allowed_roles=_OWNER_OR_ADMIN, requires_ownership=True, validator=_no_op
    ),
    (EventStatus.PUBLISHED, EventStatus.IN_PROGRESS): TransitionRule(
        allowed_roles=_OWNER_OR_ADMIN, requires_ownership=True, validator=_check_can_start
    ),
    (EventStatus.PUBLISHED, EventStatus.CANCELLED): TransitionRule(
        allowed_roles=_OWNER_OR_ADMIN, requires_ownership=True, validator=_no_op
    ),
    (EventStatus.IN_PROGRESS, EventStatus.FINISHED): TransitionRule(
        allowed_roles=_OWNER_OR_ADMIN, requires_ownership=True, validator=_check_can_finish
    ),
}
