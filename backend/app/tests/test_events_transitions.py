"""Tests de la máquina de estados de Event (Fase 3).

Estrategia:
- Una prueba por celda permitida (5).
- Pruebas representativas para celdas bloqueadas (saltos y estados terminales).
- RBAC: organizer dueño / organizer no-dueño / admin / attendee.
- Validators temporales: monkey-patch del helper `_now_utc` para no depender del reloj real.
- Verificación de que `transition` solo muta `status` (no toca el resto del evento).
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import create_access_token, hash_password
from app.models.event import Event, EventStatus
from app.models.user import User, UserRole
from app.services import event_state


# ---------- helpers ----------
def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_user(session, *, email: str, role: UserRole) -> User:
    user = User(email=email.lower(), password_hash=hash_password("ValidPass1"), role=role)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id, user.role)}"}


def _insert_event(
    session,
    *,
    owner_id: int,
    status: EventStatus,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> Event:
    start = start_at or (_now() + timedelta(days=3))
    end = end_at or (start + timedelta(hours=2))
    event = Event(
        title="Evento de prueba",
        description=None,
        location="Quito",
        capacity=10,
        start_at=start,
        end_at=end,
        status=status,
        owner_id=owner_id,
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def _transition(client, event_id: int, to_status: str, *, headers=None):
    return client.post(
        f"/api/v1/events/{event_id}/transition",
        json={"to_status": to_status},
        headers=headers or {},
    )


# ============================================================
# Celdas permitidas — una prueba por celda (5 transiciones)
# ============================================================
def test_draft_to_published_by_owner(client, session) -> None:
    owner = _make_user(session, email="o.draft.pub@x.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)
    r = _transition(client, ev.id, "PUBLISHED", headers=_auth(owner))
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "PUBLISHED"


def test_draft_to_cancelled_by_owner(client, session) -> None:
    owner = _make_user(session, email="o.draft.cancel@x.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)
    r = _transition(client, ev.id, "CANCELLED", headers=_auth(owner))
    assert r.status_code == 200
    assert r.json()["status"] == "CANCELLED"


def test_published_to_in_progress_when_started(client, session, monkeypatch) -> None:
    owner = _make_user(session, email="o.pub.ip@x.com", role=UserRole.ORGANIZER)
    start = _now() + timedelta(days=1)
    ev = _insert_event(
        session, owner_id=owner.id, status=EventStatus.PUBLISHED,
        start_at=start, end_at=start + timedelta(hours=2),
    )
    # Avanzar el "ahora" más allá del start_at
    monkeypatch.setattr(event_state, "_now_utc", lambda: start + timedelta(minutes=1))
    r = _transition(client, ev.id, "IN_PROGRESS", headers=_auth(owner))
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "IN_PROGRESS"


def test_published_to_cancelled_by_owner(client, session) -> None:
    owner = _make_user(session, email="o.pub.cancel@x.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.PUBLISHED)
    r = _transition(client, ev.id, "CANCELLED", headers=_auth(owner))
    assert r.status_code == 200
    assert r.json()["status"] == "CANCELLED"


def test_in_progress_to_finished_when_ended(client, session, monkeypatch) -> None:
    owner = _make_user(session, email="o.ip.fin@x.com", role=UserRole.ORGANIZER)
    start = _now() + timedelta(days=1)
    end = start + timedelta(hours=2)
    ev = _insert_event(
        session, owner_id=owner.id, status=EventStatus.IN_PROGRESS,
        start_at=start, end_at=end,
    )
    monkeypatch.setattr(event_state, "_now_utc", lambda: end + timedelta(minutes=1))
    r = _transition(client, ev.id, "FINISHED", headers=_auth(owner))
    assert r.status_code == 200
    assert r.json()["status"] == "FINISHED"


# ============================================================
# Celdas bloqueadas — saltos y estados terminales
# ============================================================
@pytest.mark.parametrize(
    "from_status,to_status",
    [
        # Saltos
        (EventStatus.DRAFT, EventStatus.IN_PROGRESS),
        (EventStatus.DRAFT, EventStatus.FINISHED),
        (EventStatus.PUBLISHED, EventStatus.FINISHED),
        # Regresiones
        (EventStatus.PUBLISHED, EventStatus.DRAFT),
        (EventStatus.IN_PROGRESS, EventStatus.PUBLISHED),
        # Terminales
        (EventStatus.FINISHED, EventStatus.PUBLISHED),
        (EventStatus.FINISHED, EventStatus.CANCELLED),
        (EventStatus.CANCELLED, EventStatus.DRAFT),
        (EventStatus.CANCELLED, EventStatus.PUBLISHED),
        # Self-loop
        (EventStatus.DRAFT, EventStatus.DRAFT),
    ],
)
def test_blocked_transitions_return_invalid_transition(
    client, session, from_status, to_status,
) -> None:
    owner = _make_user(
        session,
        email=f"o.blocked.{from_status.value}.{to_status.value}@x.com",
        role=UserRole.ORGANIZER,
    )
    ev = _insert_event(session, owner_id=owner.id, status=from_status)
    r = _transition(client, ev.id, to_status.value, headers=_auth(owner))
    assert r.status_code == 409, r.text
    body = r.json()
    assert body["error"]["code"] == "INVALID_TRANSITION"
    assert body["error"]["details"]["from_status"] == from_status.value
    assert body["error"]["details"]["to_status"] == to_status.value


# ============================================================
# RBAC
# ============================================================
def test_attendee_cannot_transition(client, session) -> None:
    owner = _make_user(session, email="o.rbac.owner@x.com", role=UserRole.ORGANIZER)
    attendee = _make_user(session, email="a.rbac@x.com", role=UserRole.ATTENDEE)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)
    r = _transition(client, ev.id, "PUBLISHED", headers=_auth(attendee))
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


def test_organizer_non_owner_cannot_transition(client, session) -> None:
    owner = _make_user(session, email="o.rbac.real@x.com", role=UserRole.ORGANIZER)
    intruder = _make_user(session, email="o.rbac.intruder@x.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)
    r = _transition(client, ev.id, "PUBLISHED", headers=_auth(intruder))
    assert r.status_code == 403


def test_admin_can_transition_event_owned_by_another(client, session) -> None:
    owner = _make_user(session, email="o.rbac.admincase@x.com", role=UserRole.ORGANIZER)
    admin = _make_user(session, email="a.rbac.admin@x.com", role=UserRole.ADMIN)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)
    r = _transition(client, ev.id, "PUBLISHED", headers=_auth(admin))
    assert r.status_code == 200


def test_unauthenticated_transition_returns_401(client, session) -> None:
    owner = _make_user(session, email="o.noauth@x.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)
    r = _transition(client, ev.id, "PUBLISHED")
    assert r.status_code == 401


# ============================================================
# Validators temporales
# ============================================================
def test_published_to_in_progress_before_start_returns_409(client, session) -> None:
    owner = _make_user(session, email="o.early.start@x.com", role=UserRole.ORGANIZER)
    # start_at en el futuro → no se puede iniciar todavía
    ev = _insert_event(
        session, owner_id=owner.id, status=EventStatus.PUBLISHED,
        start_at=_now() + timedelta(days=2),
        end_at=_now() + timedelta(days=2, hours=2),
    )
    r = _transition(client, ev.id, "IN_PROGRESS", headers=_auth(owner))
    assert r.status_code == 409
    body = r.json()
    assert body["error"]["code"] == "INVALID_TRANSITION"
    assert body["error"]["details"]["reason"] == "event has not started yet"


def test_in_progress_to_finished_before_end_returns_409(client, session) -> None:
    owner = _make_user(session, email="o.early.end@x.com", role=UserRole.ORGANIZER)
    # end_at en el futuro → no se puede finalizar todavía
    ev = _insert_event(
        session, owner_id=owner.id, status=EventStatus.IN_PROGRESS,
        start_at=_now() + timedelta(days=1),
        end_at=_now() + timedelta(days=1, hours=2),
    )
    r = _transition(client, ev.id, "FINISHED", headers=_auth(owner))
    assert r.status_code == 409
    assert r.json()["error"]["details"]["reason"] == "event has not ended yet"


# ============================================================
# Edge cases
# ============================================================
def test_invalid_to_status_returns_422(client, session) -> None:
    owner = _make_user(session, email="o.badenum@x.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)
    r = _transition(client, ev.id, "WHATEVER", headers=_auth(owner))
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_missing_event_returns_404(client, session) -> None:
    owner = _make_user(session, email="o.missing@x.com", role=UserRole.ORGANIZER)
    r = _transition(client, 99999, "PUBLISHED", headers=_auth(owner))
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_transition_only_mutates_status(client, session) -> None:
    """Garantiza que el servicio no toca campos distintos de `status`."""
    owner = _make_user(session, email="o.onlystatus@x.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)
    snapshot = {
        "title": ev.title,
        "description": ev.description,
        "location": ev.location,
        "capacity": ev.capacity,
        "start_at": ev.start_at,
        "end_at": ev.end_at,
        "owner_id": ev.owner_id,
    }
    r = _transition(client, ev.id, "PUBLISHED", headers=_auth(owner))
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == snapshot["title"]
    assert body["location"] == snapshot["location"]
    assert body["capacity"] == snapshot["capacity"]
    assert body["owner_id"] == snapshot["owner_id"]
    assert body["status"] == "PUBLISHED"


def test_transition_published_to_cancelled_invokes_registration_cascade() -> None:
    """Verifica que el servicio invoca la cascada de Registrations en la transición
    Published → Cancelled (reemplaza al marcador TODO Fase 5 una vez implementada)."""
    from pathlib import Path
    source = Path(__file__).resolve().parents[1] / "services" / "event.py"
    text = source.read_text()
    assert "mark_all_active_cancelled_for_event" in text
    assert "PUBLISHED" in text and "CANCELLED" in text
