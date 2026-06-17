import pytest

from app.core.errors import AuthTokenExpired
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import UserRole


def test_hash_and_verify_password() -> None:
    hashed = hash_password("Secret123")
    assert hashed != "Secret123"
    assert verify_password("Secret123", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_access_token_roundtrip() -> None:
    token = create_access_token(user_id=1, role=UserRole.ADMIN)
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == "1"
    assert payload["role"] == "ADMIN"
    assert payload["type"] == "access"


def test_refresh_token_cannot_be_used_as_access() -> None:
    refresh = create_refresh_token(user_id=42)
    with pytest.raises(AuthTokenExpired):
        decode_token(refresh, expected_type="access")


def test_access_token_cannot_be_used_as_refresh() -> None:
    access = create_access_token(user_id=42, role=UserRole.ATTENDEE)
    with pytest.raises(AuthTokenExpired):
        decode_token(access, expected_type="refresh")


def test_decode_garbage_token_raises() -> None:
    with pytest.raises(AuthTokenExpired):
        decode_token("not-a-real-token", expected_type="access")
