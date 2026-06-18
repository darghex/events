from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.schemas.event import EventCreate, EventUpdate


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _valid_payload(**overrides) -> dict:
    base = {
        "title": "Conferencia React",
        "description": "Una conferencia de prueba",
        "location": "Quito",
        "capacity": 100,
        "start_at": _now() + timedelta(days=1),
        "end_at": _now() + timedelta(days=1, hours=2),
    }
    base.update(overrides)
    return base


def test_event_create_happy_path() -> None:
    payload = EventCreate(**_valid_payload())
    assert payload.capacity == 100
    assert payload.title == "Conferencia React"


def test_event_create_rejects_non_positive_capacity() -> None:
    with pytest.raises(ValidationError):
        EventCreate(**_valid_payload(capacity=0))
    with pytest.raises(ValidationError):
        EventCreate(**_valid_payload(capacity=-5))


def test_event_create_rejects_start_after_end() -> None:
    with pytest.raises(ValidationError):
        EventCreate(
            **_valid_payload(
                start_at=_now() + timedelta(days=2),
                end_at=_now() + timedelta(days=1),
            )
        )


def test_event_create_rejects_start_equal_end() -> None:
    same = _now() + timedelta(days=1)
    with pytest.raises(ValidationError):
        EventCreate(**_valid_payload(start_at=same, end_at=same))


def test_event_create_strips_title_whitespace() -> None:
    payload = EventCreate(**_valid_payload(title="  ReactConf  "))
    assert payload.title == "ReactConf"


def test_event_create_rejects_whitespace_only_title() -> None:
    with pytest.raises(ValidationError):
        EventCreate(**_valid_payload(title="   "))


def test_event_create_rejects_title_too_long() -> None:
    with pytest.raises(ValidationError):
        EventCreate(**_valid_payload(title="x" * 201))


def test_event_update_all_optional() -> None:
    patch = EventUpdate()
    assert patch.model_dump(exclude_unset=True) == {}


def test_event_update_strips_optional_text() -> None:
    patch = EventUpdate(title="  Nuevo  ")
    assert patch.title == "Nuevo"
