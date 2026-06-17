import pytest
from pydantic import ValidationError

from app.schemas.auth import UserCreate


def test_password_policy_too_short() -> None:
    with pytest.raises(ValidationError):
        UserCreate(email="user@example.com", password="Ab1")


def test_password_policy_missing_uppercase() -> None:
    with pytest.raises(ValidationError):
        UserCreate(email="user@example.com", password="lowercase1")


def test_password_policy_missing_digit() -> None:
    with pytest.raises(ValidationError):
        UserCreate(email="user@example.com", password="NoDigitsHere")


def test_password_policy_ok_and_email_lowercased() -> None:
    schema = UserCreate(email="User@Example.COM", password="ValidPass1")
    assert schema.email == "user@example.com"
    assert schema.password == "ValidPass1"
