"""Integration tests para Fase 5 — Inscripciones (Regla de Oro).

Cubre: happy path, duplicado, speaker, full, estado inválido, owner,
cancelación, re-inscripción, cascada del evento, hidratación de EventRead,
historial /me/registrations.
"""
from datetime import datetime, timedelta, timezone

from app.core.security import create_access_token, hash_password
from app.models.event import Event, EventStatus
from app.models.event_session import EventSession
from app.models.registration import Registration, RegistrationStatus
from app.models.user import User, UserRole


# ---------- helpers ----------
def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_user(session, *, email: str, role: UserRole = UserRole.ATTENDEE) -> User:
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
    status: EventStatus = EventStatus.PUBLISHED,
    capacity: int = 10,
) -> Event:
    start = _now() + timedelta(days=7)
    event = Event(
        title="Evento test",
        description=None,
        location="Quito",
        capacity=capacity,
        start_at=start,
        end_at=start + timedelta(hours=2),
        status=status,
        owner_id=owner_id,
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def _insert_session_for(session, *, event_id: int, speaker_id: int) -> EventSession:
    event = session.get(Event, event_id)
    s = EventSession(
        event_id=event_id,
        speaker_id=speaker_id,
        title="Charla",
        description=None,
        start_at=event.start_at,
        end_at=event.start_at + timedelta(hours=1),
        capacity=None,
    )
    session.add(s)
    session.commit()
    session.refresh(s)
    return s


def _post_reg(client, event_id: int, *, headers=None):
    return client.post(
        f"/api/v1/events/{event_id}/registrations",
        headers=headers or {},
    )


# ============================================================
# Happy path
# ============================================================
def test_attendee_registers_to_published_event(client, session) -> None:
    owner = _make_user(session, email="o.happy@x.com", role=UserRole.ORGANIZER)
    attendee = _make_user(session, email="a.happy@x.com")
    ev = _insert_event(session, owner_id=owner.id)

    r = _post_reg(client, ev.id, headers=_auth(attendee))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "CONFIRMED"
    assert body["user_id"] == attendee.id
    assert body["event_id"] == ev.id


def test_owner_can_register_to_own_event(client, session) -> None:
    owner = _make_user(session, email="o.self@x.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id)
    r = _post_reg(client, ev.id, headers=_auth(owner))
    assert r.status_code == 201


def test_unauthenticated_register_returns_401(client, session) -> None:
    owner = _make_user(session, email="o.noauth@x.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id)
    r = _post_reg(client, ev.id)
    assert r.status_code == 401


# ============================================================
# Validaciones de negocio
# ============================================================
def test_duplicate_registration_returns_409(client, session) -> None:
    owner = _make_user(session, email="o.dup@x.com", role=UserRole.ORGANIZER)
    attendee = _make_user(session, email="a.dup@x.com")
    ev = _insert_event(session, owner_id=owner.id)

    r1 = _post_reg(client, ev.id, headers=_auth(attendee))
    assert r1.status_code == 201
    r2 = _post_reg(client, ev.id, headers=_auth(attendee))
    assert r2.status_code == 409
    assert r2.json()["error"]["code"] == "DUPLICATE_REGISTRATION"


def test_speaker_cannot_register(client, session) -> None:
    owner = _make_user(session, email="o.sp@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp.cant@x.com")
    ev = _insert_event(session, owner_id=owner.id)
    _insert_session_for(session, event_id=ev.id, speaker_id=speaker.id)

    r = _post_reg(client, ev.id, headers=_auth(speaker))
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "SPEAKER_CANNOT_REGISTER"


def test_event_full_returns_409(client, session) -> None:
    owner = _make_user(session, email="o.full@x.com", role=UserRole.ORGANIZER)
    a1 = _make_user(session, email="a1.full@x.com")
    a2 = _make_user(session, email="a2.full@x.com")
    ev = _insert_event(session, owner_id=owner.id, capacity=1)

    r1 = _post_reg(client, ev.id, headers=_auth(a1))
    assert r1.status_code == 201
    r2 = _post_reg(client, ev.id, headers=_auth(a2))
    assert r2.status_code == 409
    body = r2.json()
    assert body["error"]["code"] == "EVENT_FULL"
    assert body["error"]["details"]["capacity"] == 1


def test_register_to_draft_returns_invalid_state(client, session) -> None:
    owner = _make_user(session, email="o.draft@x.com", role=UserRole.ORGANIZER)
    attendee = _make_user(session, email="a.draft@x.com")
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)
    r = _post_reg(client, ev.id, headers=_auth(attendee))
    assert r.status_code == 409
    body = r.json()
    assert body["error"]["code"] == "INVALID_REGISTRATION_STATE"
    assert body["error"]["details"]["current_status"] == "DRAFT"


def test_register_to_in_progress_returns_invalid_state(client, session) -> None:
    owner = _make_user(session, email="o.ip@x.com", role=UserRole.ORGANIZER)
    attendee = _make_user(session, email="a.ip@x.com")
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.IN_PROGRESS)
    r = _post_reg(client, ev.id, headers=_auth(attendee))
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "INVALID_REGISTRATION_STATE"


def test_register_missing_event_returns_404(client, session) -> None:
    attendee = _make_user(session, email="a.missing@x.com")
    r = _post_reg(client, 99999, headers=_auth(attendee))
    assert r.status_code == 404


# ============================================================
# Cancelación + re-inscripción
# ============================================================
def test_cancel_my_registration_returns_204(client, session) -> None:
    owner = _make_user(session, email="o.cancel@x.com", role=UserRole.ORGANIZER)
    attendee = _make_user(session, email="a.cancel@x.com")
    ev = _insert_event(session, owner_id=owner.id)
    _post_reg(client, ev.id, headers=_auth(attendee))

    r = client.delete(
        f"/api/v1/events/{ev.id}/registrations/me", headers=_auth(attendee)
    )
    assert r.status_code == 204


def test_cancel_without_active_registration_returns_404(client, session) -> None:
    owner = _make_user(session, email="o.cn@x.com", role=UserRole.ORGANIZER)
    attendee = _make_user(session, email="a.cn@x.com")
    ev = _insert_event(session, owner_id=owner.id)
    r = client.delete(
        f"/api/v1/events/{ev.id}/registrations/me", headers=_auth(attendee)
    )
    assert r.status_code == 404


def test_reregister_after_cancel_creates_new_row(client, session) -> None:
    owner = _make_user(session, email="o.re@x.com", role=UserRole.ORGANIZER)
    attendee = _make_user(session, email="a.re@x.com")
    ev = _insert_event(session, owner_id=owner.id)

    r1 = _post_reg(client, ev.id, headers=_auth(attendee))
    first_id = r1.json()["id"]
    client.delete(f"/api/v1/events/{ev.id}/registrations/me", headers=_auth(attendee))
    r2 = _post_reg(client, ev.id, headers=_auth(attendee))
    assert r2.status_code == 201
    second_id = r2.json()["id"]
    assert second_id != first_id

    # Verificar en DB: una CONFIRMED + una CANCELLED para ese (user, event)
    from sqlmodel import select
    rows = session.exec(
        select(Registration)
        .where(Registration.user_id == attendee.id)
        .where(Registration.event_id == ev.id)
    ).all()
    statuses = sorted(r.status for r in rows)
    assert statuses == [RegistrationStatus.CANCELLED, RegistrationStatus.CONFIRMED]


# ============================================================
# Cascada Fase 3: Published → Cancelled cancela todas las activas
# ============================================================
def test_event_cancellation_cascades_to_registrations(client, session) -> None:
    owner = _make_user(session, email="o.casc@x.com", role=UserRole.ORGANIZER)
    a1 = _make_user(session, email="a1.casc@x.com")
    a2 = _make_user(session, email="a2.casc@x.com")
    a3 = _make_user(session, email="a3.casc@x.com")
    ev = _insert_event(session, owner_id=owner.id, capacity=10)
    for a in (a1, a2, a3):
        _post_reg(client, ev.id, headers=_auth(a))

    # Disparar transición Published → Cancelled
    r = client.post(
        f"/api/v1/events/{ev.id}/transition",
        json={"to_status": "CANCELLED"},
        headers=_auth(owner),
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "CANCELLED"

    # Verificar que TODAS las inscripciones quedaron canceladas
    from sqlmodel import select
    rows = session.exec(
        select(Registration).where(Registration.event_id == ev.id)
    ).all()
    assert len(rows) == 3
    assert all(r.status == RegistrationStatus.CANCELLED for r in rows)


# ============================================================
# Hidratación de EventRead con counts
# ============================================================
def test_event_read_includes_confirmed_count_and_is_full(client, session) -> None:
    owner = _make_user(session, email="o.hyd@x.com", role=UserRole.ORGANIZER)
    a1 = _make_user(session, email="a.hyd1@x.com")
    a2 = _make_user(session, email="a.hyd2@x.com")
    ev = _insert_event(session, owner_id=owner.id, capacity=2)

    _post_reg(client, ev.id, headers=_auth(a1))
    _post_reg(client, ev.id, headers=_auth(a2))

    r = client.get(f"/api/v1/events/{ev.id}")
    assert r.status_code == 200
    body = r.json()
    assert body["confirmed_count"] == 2
    assert body["is_full"] is True


def test_event_read_my_registration_status_with_auth(client, session) -> None:
    owner = _make_user(session, email="o.mystat@x.com", role=UserRole.ORGANIZER)
    attendee = _make_user(session, email="a.mystat@x.com")
    ev = _insert_event(session, owner_id=owner.id)
    _post_reg(client, ev.id, headers=_auth(attendee))

    r = client.get(f"/api/v1/events/{ev.id}", headers=_auth(attendee))
    assert r.json()["my_registration_status"] == "CONFIRMED"


def test_event_read_my_registration_status_null_without_auth(client, session) -> None:
    owner = _make_user(session, email="o.mystat.anon@x.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id)
    r = client.get(f"/api/v1/events/{ev.id}")
    assert r.json()["my_registration_status"] is None


def test_event_list_item_includes_counts(client, session) -> None:
    owner = _make_user(session, email="o.li@x.com", role=UserRole.ORGANIZER)
    a1 = _make_user(session, email="a.li1@x.com")
    ev = _insert_event(session, owner_id=owner.id, capacity=5)
    _post_reg(client, ev.id, headers=_auth(a1))

    r = client.get("/api/v1/events")
    assert r.status_code == 200
    items = r.json()["items"]
    target = next(it for it in items if it["id"] == ev.id)
    assert target["confirmed_count"] == 1
    assert target["is_full"] is False


# ============================================================
# /me/registrations
# ============================================================
def test_my_registrations_returns_history(client, session) -> None:
    owner = _make_user(session, email="o.me@x.com", role=UserRole.ORGANIZER)
    attendee = _make_user(session, email="a.me@x.com")
    ev_a = _insert_event(session, owner_id=owner.id)
    ev_b = _insert_event(session, owner_id=owner.id)
    _post_reg(client, ev_a.id, headers=_auth(attendee))
    _post_reg(client, ev_b.id, headers=_auth(attendee))

    r = client.get("/api/v1/me/registrations", headers=_auth(attendee))
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2
    event_ids = {it["event"]["id"] for it in body["items"]}
    assert event_ids == {ev_a.id, ev_b.id}


def test_my_registrations_requires_auth(client) -> None:
    r = client.get("/api/v1/me/registrations")
    assert r.status_code == 401


def test_my_registrations_includes_cancelled(client, session) -> None:
    owner = _make_user(session, email="o.hist@x.com", role=UserRole.ORGANIZER)
    attendee = _make_user(session, email="a.hist@x.com")
    ev = _insert_event(session, owner_id=owner.id)
    _post_reg(client, ev.id, headers=_auth(attendee))
    client.delete(f"/api/v1/events/{ev.id}/registrations/me", headers=_auth(attendee))

    r = client.get("/api/v1/me/registrations", headers=_auth(attendee))
    assert r.status_code == 200
    items = r.json()["items"]
    assert items[0]["status"] == "CANCELLED"
