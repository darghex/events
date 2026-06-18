"""Integration tests para CRUD de eventos.

Usa el `client` y `session` compartiendo el mismo engine SQLite del conftest.
Crea usuarios directo en DB (sirve para asignar roles distintos a ATTENDEE).
"""
from datetime import datetime, timedelta, timezone

from app.core.security import create_access_token, hash_password
from app.models.event import Event, EventStatus
from app.models.user import User, UserRole


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


def _event_payload(**overrides) -> dict:
    start = _now() + timedelta(days=2)
    end = start + timedelta(hours=3)
    base = {
        "title": "Conferencia React",
        "description": "Charlas y workshops",
        "location": "Quito",
        "capacity": 50,
        "start_at": start.isoformat(),
        "end_at": end.isoformat(),
    }
    base.update(overrides)
    return base


def _insert_event(session, *, owner_id: int, status: EventStatus, title: str = "Evento X") -> Event:
    start = _now() + timedelta(days=3)
    event = Event(
        title=title,
        description=None,
        location="Quito",
        capacity=10,
        start_at=start,
        end_at=start + timedelta(hours=2),
        status=status,
        owner_id=owner_id,
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


# ---------- create ----------
def test_organizer_creates_event_in_draft(client, session) -> None:
    organizer = _make_user(session, email="org@example.com", role=UserRole.ORGANIZER)
    r = client.post("/api/v1/events", json=_event_payload(), headers=_auth(organizer))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "DRAFT"
    assert body["owner_id"] == organizer.id
    assert body["title"] == "Conferencia React"


def test_attendee_cannot_create_event(client, session) -> None:
    attendee = _make_user(session, email="ass@example.com", role=UserRole.ATTENDEE)
    r = client.post("/api/v1/events", json=_event_payload(), headers=_auth(attendee))
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


def test_unauthenticated_create_returns_401(client) -> None:
    r = client.post("/api/v1/events", json=_event_payload())
    assert r.status_code == 401


def test_create_event_rejects_invalid_capacity(client, session) -> None:
    organizer = _make_user(session, email="o1@example.com", role=UserRole.ORGANIZER)
    r = client.post("/api/v1/events", json=_event_payload(capacity=0), headers=_auth(organizer))
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_event_rejects_start_after_end(client, session) -> None:
    organizer = _make_user(session, email="o2@example.com", role=UserRole.ORGANIZER)
    start = _now() + timedelta(days=2)
    payload = _event_payload(
        start_at=start.isoformat(), end_at=(start - timedelta(hours=1)).isoformat()
    )
    r = client.post("/api/v1/events", json=payload, headers=_auth(organizer))
    assert r.status_code == 422


# ---------- list public ----------
def test_public_list_hides_drafts(client, session) -> None:
    organizer = _make_user(session, email="o3@example.com", role=UserRole.ORGANIZER)
    _insert_event(session, owner_id=organizer.id, status=EventStatus.DRAFT, title="Draft uno")
    _insert_event(session, owner_id=organizer.id, status=EventStatus.PUBLISHED, title="Pub uno")
    _insert_event(session, owner_id=organizer.id, status=EventStatus.PUBLISHED, title="Pub dos")

    r = client.get("/api/v1/events")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    titles = [it["title"] for it in body["items"]]
    assert "Draft uno" not in titles
    assert set(titles) == {"Pub uno", "Pub dos"}


def test_public_list_pagination_shape(client, session) -> None:
    organizer = _make_user(session, email="o4@example.com", role=UserRole.ORGANIZER)
    for i in range(5):
        _insert_event(session, owner_id=organizer.id, status=EventStatus.PUBLISHED, title=f"P{i}")

    r = client.get("/api/v1/events?limit=2&offset=0")
    assert r.status_code == 200
    body = r.json()
    assert body["limit"] == 2
    assert body["offset"] == 0
    assert body["total"] == 5
    assert len(body["items"]) == 2


def test_public_list_search_case_insensitive(client, session) -> None:
    organizer = _make_user(session, email="o5@example.com", role=UserRole.ORGANIZER)
    _insert_event(session, owner_id=organizer.id, status=EventStatus.PUBLISHED, title="React Summit")
    _insert_event(session, owner_id=organizer.id, status=EventStatus.PUBLISHED, title="Vue Conf")

    r = client.get("/api/v1/events?q=react")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "React Summit"


def test_public_list_ignores_blank_query(client, session) -> None:
    organizer = _make_user(session, email="o6@example.com", role=UserRole.ORGANIZER)
    _insert_event(session, owner_id=organizer.id, status=EventStatus.PUBLISHED)

    r = client.get("/api/v1/events?q=%20%20%20")
    assert r.status_code == 200
    assert r.json()["total"] == 1


def test_public_list_rejects_limit_over_max(client) -> None:
    r = client.get("/api/v1/events?limit=200")
    assert r.status_code == 422


# ---------- list mine ----------
def test_my_events_returns_drafts_of_owner(client, session) -> None:
    org1 = _make_user(session, email="o7@example.com", role=UserRole.ORGANIZER)
    org2 = _make_user(session, email="o8@example.com", role=UserRole.ORGANIZER)
    _insert_event(session, owner_id=org1.id, status=EventStatus.DRAFT, title="Mio Draft")
    _insert_event(session, owner_id=org1.id, status=EventStatus.PUBLISHED, title="Mio Pub")
    _insert_event(session, owner_id=org2.id, status=EventStatus.DRAFT, title="Ajeno")

    r = client.get("/api/v1/events/me", headers=_auth(org1))
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    titles = {it["title"] for it in body["items"]}
    assert titles == {"Mio Draft", "Mio Pub"}


def test_my_events_requires_auth(client) -> None:
    r = client.get("/api/v1/events/me")
    assert r.status_code == 401


# ---------- get detail ----------
def test_get_published_event_public(client, session) -> None:
    org = _make_user(session, email="o9@example.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=org.id, status=EventStatus.PUBLISHED)

    r = client.get(f"/api/v1/events/{ev.id}")
    assert r.status_code == 200
    assert r.json()["id"] == ev.id


def test_get_draft_anonymous_returns_404(client, session) -> None:
    org = _make_user(session, email="o10@example.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=org.id, status=EventStatus.DRAFT)

    r = client.get(f"/api/v1/events/{ev.id}")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_get_draft_third_party_returns_404(client, session) -> None:
    owner = _make_user(session, email="own@example.com", role=UserRole.ORGANIZER)
    third = _make_user(session, email="third@example.com", role=UserRole.ATTENDEE)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)

    r = client.get(f"/api/v1/events/{ev.id}", headers=_auth(third))
    assert r.status_code == 404


def test_get_draft_owner_returns_200(client, session) -> None:
    owner = _make_user(session, email="own2@example.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)

    r = client.get(f"/api/v1/events/{ev.id}", headers=_auth(owner))
    assert r.status_code == 200


def test_get_draft_admin_returns_200(client, session) -> None:
    owner = _make_user(session, email="own3@example.com", role=UserRole.ORGANIZER)
    admin = _make_user(session, email="adm@example.com", role=UserRole.ADMIN)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)

    r = client.get(f"/api/v1/events/{ev.id}", headers=_auth(admin))
    assert r.status_code == 200


def test_get_missing_event_returns_404(client) -> None:
    r = client.get("/api/v1/events/9999")
    assert r.status_code == 404


# ---------- update ----------
def test_patch_event_by_owner_in_draft(client, session) -> None:
    owner = _make_user(session, email="po1@example.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)

    r = client.patch(
        f"/api/v1/events/{ev.id}",
        json={"title": "Nuevo Titulo"},
        headers=_auth(owner),
    )
    assert r.status_code == 200, r.text
    assert r.json()["title"] == "Nuevo Titulo"


def test_patch_event_by_non_owner_returns_403(client, session) -> None:
    owner = _make_user(session, email="po2@example.com", role=UserRole.ORGANIZER)
    intruder = _make_user(session, email="int@example.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)

    r = client.patch(
        f"/api/v1/events/{ev.id}",
        json={"title": "Hack"},
        headers=_auth(intruder),
    )
    assert r.status_code == 403


def test_patch_published_by_owner_returns_409_not_mutable(client, session) -> None:
    owner = _make_user(session, email="po3@example.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.PUBLISHED)

    r = client.patch(
        f"/api/v1/events/{ev.id}",
        json={"title": "Cambio"},
        headers=_auth(owner),
    )
    assert r.status_code == 409
    body = r.json()
    assert body["error"]["code"] == "EVENT_NOT_MUTABLE"
    assert body["error"]["details"]["current_status"] == "PUBLISHED"


def test_admin_can_patch_published_event(client, session) -> None:
    owner = _make_user(session, email="po4@example.com", role=UserRole.ORGANIZER)
    admin = _make_user(session, email="adm2@example.com", role=UserRole.ADMIN)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.PUBLISHED)

    r = client.patch(
        f"/api/v1/events/{ev.id}",
        json={"title": "Editado por admin"},
        headers=_auth(admin),
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Editado por admin"


def test_patch_with_inverted_times_returns_422(client, session) -> None:
    owner = _make_user(session, email="po5@example.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)
    # Solo cambia start_at para que quede después del end_at existente
    bad_start = ev.end_at + timedelta(hours=1)
    r = client.patch(
        f"/api/v1/events/{ev.id}",
        json={"start_at": bad_start.isoformat()},
        headers=_auth(owner),
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


# ---------- delete ----------
def test_delete_draft_by_owner_returns_204(client, session) -> None:
    owner = _make_user(session, email="d1@example.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)

    r = client.delete(f"/api/v1/events/{ev.id}", headers=_auth(owner))
    assert r.status_code == 204

    r2 = client.get(f"/api/v1/events/{ev.id}", headers=_auth(owner))
    assert r2.status_code == 404


def test_delete_published_returns_409_not_mutable(client, session) -> None:
    owner = _make_user(session, email="d2@example.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.PUBLISHED)

    r = client.delete(f"/api/v1/events/{ev.id}", headers=_auth(owner))
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "EVENT_NOT_MUTABLE"


def test_delete_by_non_owner_returns_403(client, session) -> None:
    owner = _make_user(session, email="d3@example.com", role=UserRole.ORGANIZER)
    other = _make_user(session, email="d3b@example.com", role=UserRole.ORGANIZER)
    ev = _insert_event(session, owner_id=owner.id, status=EventStatus.DRAFT)

    r = client.delete(f"/api/v1/events/{ev.id}", headers=_auth(other))
    assert r.status_code == 403


def test_create_event_ignores_status_in_payload(client, session) -> None:
    # status no es campo del schema → Pydantic lo descarta y crea como DRAFT
    organizer = _make_user(session, email="px@example.com", role=UserRole.ORGANIZER)
    payload = _event_payload()
    payload["status"] = "PUBLISHED"
    r = client.post("/api/v1/events", json=payload, headers=_auth(organizer))
    assert r.status_code == 201
    assert r.json()["status"] == "DRAFT"
