def _register(client, email="user@example.com", password="ValidPass1"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )


def _login(client, email="user@example.com", password="ValidPass1"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def test_register_login_me_happy_path(client) -> None:
    r = _register(client)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == "user@example.com"
    assert body["role"] == "ATTENDEE"
    assert "password" not in body and "password_hash" not in body

    r = _login(client)
    assert r.status_code == 200
    tokens = r.json()
    assert tokens["token_type"] == "bearer"
    access = tokens["access_token"]
    refresh = tokens["refresh_token"]

    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert r.status_code == 200
    assert r.json()["email"] == "user@example.com"

    r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200
    new_access = r.json()["access_token"]
    assert new_access and new_access != access


def test_register_duplicate_email_returns_409(client) -> None:
    _register(client)
    r = _register(client)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "USER_ALREADY_EXISTS"


def test_login_invalid_credentials(client) -> None:
    _register(client)
    r = _login(client, password="WrongPass1")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "AUTH_INVALID_CREDENTIALS"


def test_me_without_token_returns_401(client) -> None:
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "AUTH_TOKEN_EXPIRED"


def test_refresh_with_access_token_is_rejected(client) -> None:
    _register(client)
    tokens = _login(client).json()
    # Intenta refrescar pasando el access_token donde va el refresh
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "AUTH_TOKEN_EXPIRED"


def test_register_password_policy_rejected(client) -> None:
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "weakpass"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
