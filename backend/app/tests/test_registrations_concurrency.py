"""Test del contrato "Regla de Oro" (Fase 5).

Limitación conocida: la suite usa SQLite con `StaticPool` para velocidad y
aislamiento. SQLite **no** implementa `SELECT ... FOR UPDATE`, por lo que un
test con `threading.Barrier(2)` no reproduce de forma determinista el lock
pesimista que sí protege en Postgres real (vía `.with_for_update()` en
`EventRepository.get_for_update`).

Lo que SÍ podemos verificar end-to-end con SQLite es el **contrato del
servicio** bajo escenarios secuenciales: con `capacity=1`, una segunda
inscripción una vez confirmada la primera retorna 409 `EVENT_FULL`. Esto
demuestra que el chequeo `confirmed_count < capacity` dentro de la misma
transacción funciona.

En producción (Postgres) `.with_for_update()` serializa dos transacciones
concurrentes: la segunda espera a que la primera commitee, lee el conteo
actualizado y rebota con `EVENT_FULL`. El cubrimiento real de concurrencia
queda como prueba de integración contra Postgres en CI (post-MVP).
"""
from datetime import datetime, timedelta, timezone

from sqlmodel import select

from app.core.security import create_access_token, hash_password
from app.models.event import Event, EventStatus
from app.models.registration import Registration, RegistrationStatus
from app.models.user import User, UserRole


def _make_user(session, *, email: str) -> User:
    user = User(
        email=email.lower(),
        password_hash=hash_password("ValidPass1"),
        role=UserRole.ATTENDEE,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _auth_header(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id, user.role)}"}


def _insert_event_capacity_one(session, owner_id: int) -> Event:
    start = datetime.now(timezone.utc) + timedelta(days=3)
    ev = Event(
        title="Lleno",
        description=None,
        location="Quito",
        capacity=1,
        start_at=start,
        end_at=start + timedelta(hours=1),
        status=EventStatus.PUBLISHED,
        owner_id=owner_id,
    )
    session.add(ev)
    session.commit()
    session.refresh(ev)
    return ev


def test_capacity_contract_enforced_sequentially(client, session) -> None:
    """Con capacity=1, la segunda inscripción rebota con EVENT_FULL."""
    organizer = _make_user(session, email="o.seq@x.com")
    a1 = _make_user(session, email="a1.seq@x.com")
    a2 = _make_user(session, email="a2.seq@x.com")
    ev = _insert_event_capacity_one(session, organizer.id)

    r1 = client.post(
        f"/api/v1/events/{ev.id}/registrations", headers=_auth_header(a1)
    )
    assert r1.status_code == 201, r1.text

    r2 = client.post(
        f"/api/v1/events/{ev.id}/registrations", headers=_auth_header(a2)
    )
    assert r2.status_code == 409, r2.text
    body = r2.json()
    assert body["error"]["code"] == "EVENT_FULL"
    assert body["error"]["details"]["capacity"] == 1

    # Solo una fila CONFIRMED en DB.
    confirmed = session.exec(
        select(Registration)
        .where(Registration.event_id == ev.id)
        .where(Registration.status == RegistrationStatus.CONFIRMED)
    ).all()
    assert len(confirmed) == 1
