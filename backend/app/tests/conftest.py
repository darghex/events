"""Fixtures de test: usa SQLite en memoria para aislar Postgres de los tests unit/integ.

Truco clave: monkeypatchea `app.db.session.engine` ANTES de crear la app, así
todos los `Depends(get_session)` resuelven contra la SQLite de cada test.
"""
import os

# Variables forzadas para los tests (sobre-escriben lo que haya en .env del host)
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET"] = "test-secret-please-change-1234567890"
os.environ["ACCESS_TOKEN_TTL_MINUTES"] = "15"
os.environ["REFRESH_TOKEN_TTL_DAYS"] = "7"
# Apaga el seed admin: cada test crea sus propios usuarios.
os.environ.pop("SEED_ADMIN_EMAIL", None)
os.environ.pop("SEED_ADMIN_PASSWORD", None)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402
from sqlmodel.pool import StaticPool  # noqa: E402

from app import models  # noqa: F401,E402  -- registra metadata
from app.db import session as db_session  # noqa: E402


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(engine, monkeypatch):
    # Redirige el engine global de la app a la SQLite del test
    monkeypatch.setattr(db_session, "engine", engine)
    from app.main import app  # import perezoso para que tome el engine ya parcheado

    with TestClient(app) as client:
        yield client
