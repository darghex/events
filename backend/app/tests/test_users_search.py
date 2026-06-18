"""Tests del endpoint GET /api/v1/users (búsqueda para SpeakerPicker)."""
from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole


def _make_user(session, *, email: str, role: UserRole = UserRole.ATTENDEE) -> User:
    user = User(email=email.lower(), password_hash=hash_password("ValidPass1"), role=role)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id, user.role)}"}


def test_search_users_requires_organizer_or_admin(client, session) -> None:
    attendee = _make_user(session, email="att.search@x.com", role=UserRole.ATTENDEE)
    r = client.get("/api/v1/users?q=foo", headers=_auth(attendee))
    assert r.status_code == 403


def test_search_users_unauthenticated_returns_401(client) -> None:
    r = client.get("/api/v1/users?q=foo")
    assert r.status_code == 401


def test_search_users_by_email_ilike(client, session) -> None:
    organizer = _make_user(session, email="o.search@x.com", role=UserRole.ORGANIZER)
    _make_user(session, email="speaker.alice@x.com")
    _make_user(session, email="speaker.bob@x.com")
    _make_user(session, email="random@x.com")

    r = client.get("/api/v1/users?q=SPEAKER", headers=_auth(organizer))
    assert r.status_code == 200
    emails = {row["email"] for row in r.json()}
    assert "speaker.alice@x.com" in emails
    assert "speaker.bob@x.com" in emails
    assert "random@x.com" not in emails


def test_search_users_admin_also_allowed(client, session) -> None:
    admin = _make_user(session, email="adm.search@x.com", role=UserRole.ADMIN)
    _make_user(session, email="speaker.x@x.com")
    r = client.get("/api/v1/users?q=spe", headers=_auth(admin))
    assert r.status_code == 200


def test_search_users_blank_q_returns_recent(client, session) -> None:
    organizer = _make_user(session, email="o.blank@x.com", role=UserRole.ORGANIZER)
    _make_user(session, email="u1.blank@x.com")
    _make_user(session, email="u2.blank@x.com")

    r = client.get("/api/v1/users?q=%20%20", headers=_auth(organizer))
    assert r.status_code == 200
    assert len(r.json()) >= 3  # incluye al organizer y los dos creados


def test_search_users_limit_clamp_422(client, session) -> None:
    organizer = _make_user(session, email="o.limit@x.com", role=UserRole.ORGANIZER)
    r = client.get("/api/v1/users?limit=200", headers=_auth(organizer))
    assert r.status_code == 422
