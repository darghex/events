"""Integration tests para CRUD de sesiones (Fase 4).

Estrategia:
- Mismos helpers que `test_events_endpoints.py`.
- Eventos sembrados directamente vía SQLModel para fijar `status` arbitrario.
- Speakers son Users existentes (rol cualquiera).
"""
from datetime import datetime, timedelta, timezone

from app.core.security import create_access_token, hash_password
from app.models.event import Event, EventStatus
from app.models.event_session import EventSession
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
    status: EventStatus = EventStatus.DRAFT,
    start_offset_days: int = 7,
    duration_hours: int = 8,
    capacity: int = 100,
) -> Event:
    start = _now() + timedelta(days=start_offset_days)
    event = Event(
        title="Evento test",
        description=None,
        location="Quito",
        capacity=capacity,
        start_at=start,
        end_at=start + timedelta(hours=duration_hours),
        status=status,
        owner_id=owner_id,
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def _insert_session_row(
    session,
    *,
    event_id: int,
    speaker_id: int,
    start_offset_minutes: int,
    duration_minutes: int,
    capacity: int | None = None,
) -> EventSession:
    """Inserta una sesión directa en DB para escenarios de fixture (sin pasar por el endpoint)."""
    event = session.get(Event, event_id)
    start = event.start_at + timedelta(minutes=start_offset_minutes)
    s = EventSession(
        event_id=event_id,
        speaker_id=speaker_id,
        title="Charla seed",
        description=None,
        start_at=start,
        end_at=start + timedelta(minutes=duration_minutes),
        capacity=capacity,
    )
    session.add(s)
    session.commit()
    session.refresh(s)
    return s


def _session_payload(event: Event, speaker_id: int, **overrides) -> dict:
    """Payload válido por defecto: 1h de duración dentro del rango del evento."""
    start = event.start_at + timedelta(hours=1)
    base = {
        "title": "Charla sobre testing",
        "description": "Cómo testear sin perder la cabeza",
        "speaker_id": speaker_id,
        "start_at": start.isoformat(),
        "end_at": (start + timedelta(hours=1)).isoformat(),
        "capacity": 30,
    }
    base.update(overrides)
    return base


def _post_session(client, event_id: int, payload: dict, *, headers=None):
    return client.post(
        f"/api/v1/events/{event_id}/sessions",
        json=payload,
        headers=headers or {},
    )


# ============================================================
# CREATE — happy path + ciclo de vida del evento
# ============================================================
def test_owner_creates_session_in_draft_event(client, session) -> None:
    owner = _make_user(session, email="o.draft@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp1@x.com")
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)

    r = _post_session(client, ev.id, _session_payload(ev, speaker.id), headers=_auth(owner))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["event_id"] == ev.id
    assert body["speaker"]["id"] == speaker.id
    assert body["speaker"]["email"] == speaker.email
    assert body["capacity"] == 30


def test_owner_creates_session_in_published_event(client, session) -> None:
    owner = _make_user(session, email="o.pub@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp2@x.com")
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.PUBLISHED)

    r = _post_session(client, ev.id, _session_payload(ev, speaker.id), headers=_auth(owner))
    assert r.status_code == 201


def test_owner_cannot_create_session_in_in_progress_event(client, session) -> None:
    owner = _make_user(session, email="o.ip@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp3@x.com")
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.IN_PROGRESS)

    r = _post_session(client, ev.id, _session_payload(ev, speaker.id), headers=_auth(owner))
    assert r.status_code == 409
    body = r.json()
    assert body["error"]["code"] == "EVENT_NOT_MUTABLE"
    assert "sessions can only be modified" in body["error"]["details"]["reason"]


def test_owner_cannot_create_session_in_cancelled_event(client, session) -> None:
    owner = _make_user(session, email="o.cancel@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp4@x.com")
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.CANCELLED)

    r = _post_session(client, ev.id, _session_payload(ev, speaker.id), headers=_auth(owner))
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "EVENT_NOT_MUTABLE"


def test_session_capacity_optional_null_allowed(client, session) -> None:
    owner = _make_user(session, email="o.nocap@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp5@x.com")
    ev = _insert_event(session, owner_id=owner.id)

    payload = _session_payload(ev, speaker.id, capacity=None)
    r = _post_session(client, ev.id, payload, headers=_auth(owner))
    assert r.status_code == 201
    assert r.json()["capacity"] is None


# ============================================================
# RBAC
# ============================================================
def test_attendee_cannot_create_session(client, session) -> None:
    owner = _make_user(session, email="o.rbac@x.com", role=UserRole.ORGANIZER)
    attendee = _make_user(session, email="att.rbac@x.com", role=UserRole.ATTENDEE)
    speaker = _make_user(session, email="sp6@x.com")
    ev = _insert_event(session, owner_id=owner.id)

    r = _post_session(client, ev.id, _session_payload(ev, speaker.id), headers=_auth(attendee))
    assert r.status_code == 403


def test_organizer_non_owner_cannot_create_session(client, session) -> None:
    owner = _make_user(session, email="o.real@x.com", role=UserRole.ORGANIZER)
    intruder = _make_user(session, email="o.intr@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp7@x.com")
    ev = _insert_event(session, owner_id=owner.id)

    r = _post_session(client, ev.id, _session_payload(ev, speaker.id), headers=_auth(intruder))
    assert r.status_code == 403


def test_admin_can_create_session_on_event_owned_by_another(client, session) -> None:
    owner = _make_user(session, email="o.admincase@x.com", role=UserRole.ORGANIZER)
    admin = _make_user(session, email="adm@x.com", role=UserRole.ADMIN)
    speaker = _make_user(session, email="sp8@x.com")
    ev = _insert_event(session, owner_id=owner.id)

    r = _post_session(client, ev.id, _session_payload(ev, speaker.id), headers=_auth(admin))
    assert r.status_code == 201


def test_unauthenticated_create_returns_401(client, session) -> None:
    owner = _make_user(session, email="o.noauth.s@x.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id)
    r = _post_session(client, ev.id, {"title": "x", "speaker_id": 1, "start_at": "2030-01-01T00:00:00Z", "end_at": "2030-01-01T01:00:00Z"})
    assert r.status_code == 401


# ============================================================
# Validaciones de negocio
# ============================================================
def test_session_before_event_start_returns_out_of_range(client, session) -> None:
    owner = _make_user(session, email="o.before@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp9@x.com")
    ev = _insert_event(session, owner_id=owner.id)

    early_start = ev.start_at - timedelta(hours=1)
    payload = _session_payload(
        ev, speaker.id,
        start_at=early_start.isoformat(),
        end_at=(early_start + timedelta(minutes=30)).isoformat(),
    )
    r = _post_session(client, ev.id, payload, headers=_auth(owner))
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "SESSION_OUT_OF_RANGE"


def test_session_after_event_end_returns_out_of_range(client, session) -> None:
    owner = _make_user(session, email="o.after@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp10@x.com")
    ev = _insert_event(session, owner_id=owner.id)

    late_start = ev.end_at + timedelta(minutes=30)
    payload = _session_payload(
        ev, speaker.id,
        start_at=late_start.isoformat(),
        end_at=(late_start + timedelta(minutes=30)).isoformat(),
    )
    r = _post_session(client, ev.id, payload, headers=_auth(owner))
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "SESSION_OUT_OF_RANGE"


def test_session_capacity_exceeds_event_returns_409(client, session) -> None:
    owner = _make_user(session, email="o.cap@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp11@x.com")
    ev = _insert_event(session, owner_id=owner.id, capacity=50)

    payload = _session_payload(ev, speaker.id, capacity=51)
    r = _post_session(client, ev.id, payload, headers=_auth(owner))
    assert r.status_code == 409
    body = r.json()
    assert body["error"]["code"] == "SESSION_CAPACITY_EXCEEDS_EVENT"
    assert body["error"]["details"]["event_capacity"] == 50
    assert body["error"]["details"]["session_capacity"] == 51


def test_session_with_inverted_times_returns_422(client, session) -> None:
    owner = _make_user(session, email="o.inv@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp12@x.com")
    ev = _insert_event(session, owner_id=owner.id)

    start = ev.start_at + timedelta(hours=2)
    payload = _session_payload(
        ev, speaker.id,
        start_at=start.isoformat(),
        end_at=(start - timedelta(minutes=30)).isoformat(),
    )
    r = _post_session(client, ev.id, payload, headers=_auth(owner))
    assert r.status_code == 422


def test_speaker_not_found_returns_404(client, session) -> None:
    owner = _make_user(session, email="o.nosp@x.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id)

    payload = _session_payload(ev, speaker_id=99999)
    r = _post_session(client, ev.id, payload, headers=_auth(owner))
    assert r.status_code == 404
    body = r.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["details"]["reason"] == "speaker not found"


# ============================================================
# Solapamiento global del speaker
# ============================================================
def test_speaker_overlap_across_events_returns_409(client, session) -> None:
    owner = _make_user(session, email="o.overlap@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp.overlap@x.com")
    # Mismo speaker en dos eventos distintos del mismo organizer.
    ev_a = _insert_event(session, owner_id=owner.id, start_offset_days=5)
    ev_b = _insert_event(session, owner_id=owner.id, start_offset_days=5)
    # Sesión existente en evento A, 10:00-11:00 desde el start del evento.
    _insert_session_row(
        session, event_id=ev_a.id, speaker_id=speaker.id,
        start_offset_minutes=0, duration_minutes=60,
    )
    # Intento en evento B con solape 10:30-11:30 (en términos de offset al start del evento B).
    payload = _session_payload(
        ev_b, speaker.id,
        start_at=(ev_b.start_at + timedelta(minutes=30)).isoformat(),
        end_at=(ev_b.start_at + timedelta(minutes=90)).isoformat(),
    )
    r = _post_session(client, ev_b.id, payload, headers=_auth(owner))
    assert r.status_code == 409
    body = r.json()
    assert body["error"]["code"] == "SESSION_OVERLAP"
    assert body["error"]["details"]["speaker_id"] == speaker.id


def test_speaker_overlap_with_cancelled_event_is_allowed(client, session) -> None:
    owner = _make_user(session, email="o.cancel.ok@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp.cancel.ok@x.com")
    ev_a = _insert_event(session, owner_id=owner.id, status=EventStatus.CANCELLED)
    ev_b = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)
    _insert_session_row(
        session, event_id=ev_a.id, speaker_id=speaker.id,
        start_offset_minutes=0, duration_minutes=60,
    )
    payload = _session_payload(
        ev_b, speaker.id,
        start_at=(ev_b.start_at + timedelta(minutes=30)).isoformat(),
        end_at=(ev_b.start_at + timedelta(minutes=90)).isoformat(),
    )
    r = _post_session(client, ev_b.id, payload, headers=_auth(owner))
    assert r.status_code == 201


# ============================================================
# GET listado / detalle
# ============================================================
def test_list_sessions_of_published_event_is_public(client, session) -> None:
    owner = _make_user(session, email="o.pub.list@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp.list@x.com")
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.PUBLISHED)
    _insert_session_row(
        session, event_id=ev.id, speaker_id=speaker.id,
        start_offset_minutes=60, duration_minutes=60,
    )

    r = client.get(f"/api/v1/events/{ev.id}/sessions")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["speaker"]["email"] == speaker.email


def test_list_sessions_of_draft_event_returns_404_to_anonymous(client, session) -> None:
    owner = _make_user(session, email="o.draft.list@x.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)
    r = client.get(f"/api/v1/events/{ev.id}/sessions")
    assert r.status_code == 404


def test_get_session_detail_includes_speaker(client, session) -> None:
    owner = _make_user(session, email="o.detail@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp.detail@x.com")
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.PUBLISHED)
    s = _insert_session_row(
        session, event_id=ev.id, speaker_id=speaker.id,
        start_offset_minutes=0, duration_minutes=30,
    )

    r = client.get(f"/api/v1/events/{ev.id}/sessions/{s.id}")
    assert r.status_code == 200
    assert r.json()["speaker"]["email"] == speaker.email


def test_get_session_mismatched_event_returns_404(client, session) -> None:
    owner = _make_user(session, email="o.mismatch@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp.mismatch@x.com")
    ev_a = _insert_event(session, owner_id=owner.id, status=EventStatus.PUBLISHED)
    ev_b = _insert_event(session, owner_id=owner.id, status=EventStatus.PUBLISHED)
    s = _insert_session_row(
        session, event_id=ev_a.id, speaker_id=speaker.id,
        start_offset_minutes=0, duration_minutes=30,
    )
    r = client.get(f"/api/v1/events/{ev_b.id}/sessions/{s.id}")
    assert r.status_code == 404


# ============================================================
# PATCH / DELETE
# ============================================================
def test_patch_session_changes_title(client, session) -> None:
    owner = _make_user(session, email="o.patch@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp.patch@x.com")
    ev = _insert_event(session, owner_id=owner.id)
    s = _insert_session_row(
        session, event_id=ev.id, speaker_id=speaker.id,
        start_offset_minutes=0, duration_minutes=60,
    )
    r = client.patch(
        f"/api/v1/events/{ev.id}/sessions/{s.id}",
        json={"title": "Nuevo título"},
        headers=_auth(owner),
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Nuevo título"


def test_patch_session_reassign_speaker_with_overlap_returns_409(client, session) -> None:
    owner = _make_user(session, email="o.patch.overlap@x.com", role=UserRole.ORGANIZER)
    speaker_a = _make_user(session, email="sp.pa@x.com")
    speaker_b = _make_user(session, email="sp.pb@x.com")
    ev = _insert_event(session, owner_id=owner.id)
    # speaker_b ya tiene sesión 60-90 minutos después del start.
    _insert_session_row(
        session, event_id=ev.id, speaker_id=speaker_b.id,
        start_offset_minutes=60, duration_minutes=30,
    )
    # speaker_a tiene sesión 60-90 minutos también (mismo horario).
    s = _insert_session_row(
        session, event_id=ev.id, speaker_id=speaker_a.id,
        start_offset_minutes=60, duration_minutes=30,
    )
    # Reasignar la de speaker_a a speaker_b → choque.
    r = client.patch(
        f"/api/v1/events/{ev.id}/sessions/{s.id}",
        json={"speaker_id": speaker_b.id},
        headers=_auth(owner),
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "SESSION_OVERLAP"


def test_patch_session_out_of_range_returns_409(client, session) -> None:
    owner = _make_user(session, email="o.patch.range@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp.patch.range@x.com")
    ev = _insert_event(session, owner_id=owner.id)
    s = _insert_session_row(
        session, event_id=ev.id, speaker_id=speaker.id,
        start_offset_minutes=0, duration_minutes=60,
    )
    bad_start = (ev.end_at + timedelta(hours=1)).isoformat()
    r = client.patch(
        f"/api/v1/events/{ev.id}/sessions/{s.id}",
        json={"start_at": bad_start, "end_at": (ev.end_at + timedelta(hours=2)).isoformat()},
        headers=_auth(owner),
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "SESSION_OUT_OF_RANGE"


def test_delete_session_by_owner_returns_204(client, session) -> None:
    owner = _make_user(session, email="o.del@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp.del@x.com")
    ev = _insert_event(session, owner_id=owner.id)
    s = _insert_session_row(
        session, event_id=ev.id, speaker_id=speaker.id,
        start_offset_minutes=0, duration_minutes=60,
    )
    r = client.delete(f"/api/v1/events/{ev.id}/sessions/{s.id}", headers=_auth(owner))
    assert r.status_code == 204


def test_delete_session_by_non_owner_returns_403(client, session) -> None:
    owner = _make_user(session, email="o.del.real@x.com", role=UserRole.ORGANIZER)
    intruder = _make_user(session, email="o.del.intr@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp.del.x@x.com")
    ev = _insert_event(session, owner_id=owner.id)
    s = _insert_session_row(
        session, event_id=ev.id, speaker_id=speaker.id,
        start_offset_minutes=0, duration_minutes=60,
    )
    r = client.delete(f"/api/v1/events/{ev.id}/sessions/{s.id}", headers=_auth(intruder))
    assert r.status_code == 403


# ============================================================
# Parche EventService.update — capacidad por debajo de una sesión
# ============================================================
def test_patch_event_capacity_below_session_returns_409(client, session) -> None:
    owner = _make_user(session, email="o.evcap@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp.evcap@x.com")
    ev = _insert_event(session, owner_id=owner.id, capacity=100)
    # Sesión con capacidad 80.
    _insert_session_row(
        session, event_id=ev.id, speaker_id=speaker.id,
        start_offset_minutes=0, duration_minutes=60, capacity=80,
    )
    # Intento bajar el evento a 50.
    r = client.patch(
        f"/api/v1/events/{ev.id}",
        json={"capacity": 50},
        headers=_auth(owner),
    )
    assert r.status_code == 409
    body = r.json()
    assert body["error"]["code"] == "EVENT_CAPACITY_BELOW_SESSION"
    assert body["error"]["details"]["new_capacity"] == 50
    assert body["error"]["details"]["max_session_capacity"] == 80


def test_patch_event_capacity_above_max_session_allowed(client, session) -> None:
    owner = _make_user(session, email="o.evcap.ok@x.com", role=UserRole.ORGANIZER)
    speaker = _make_user(session, email="sp.evcap.ok@x.com")
    ev = _insert_event(session, owner_id=owner.id, capacity=100)
    _insert_session_row(
        session, event_id=ev.id, speaker_id=speaker.id,
        start_offset_minutes=0, duration_minutes=60, capacity=80,
    )
    r = client.patch(
        f"/api/v1/events/{ev.id}",
        json={"capacity": 90},
        headers=_auth(owner),
    )
    assert r.status_code == 200
    assert r.json()["capacity"] == 90
