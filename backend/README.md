# Backend — Mis Eventos API

API REST en FastAPI con SQLModel, Alembic y PostgreSQL.

## Stack

- **Python** `3.12` (fijo)
- **FastAPI** + **SQLModel** (sobre SQLAlchemy 2.x)
- **PostgreSQL** `16-alpine`
- **Alembic** para migraciones
- **Poetry** para dependencias
- **bcrypt** + `PyJWT` (HS256) para auth
- **pytest** + httpx + pytest-cov para tests

## Setup local (sin Docker)

Requiere `python 3.12` y `poetry` instalados.

```sh
cd backend
poetry install
cp ../.env.example ../.env  # ajusta DATABASE_URL para apuntar a tu Postgres local
poetry run alembic upgrade head
poetry run fastapi dev app/main.py
```

API en `http://localhost:8000`. Swagger en `/docs`.

## Setup con Docker (recomendado)

Desde la raíz del repo:

```sh
make up        # arranca db + backend + frontend
make migrate   # alembic upgrade head dentro del contenedor (opcional, ya corre en entrypoint)
make logs      # seguir logs
```

`entrypoint.sh` ejecuta `alembic upgrade head` automáticamente antes de levantar uvicorn.

## Tests + cobertura

```sh
make test-back              # pytest --cov=app --cov-fail-under=80
# o directo:
docker compose run --rm backend poetry run pytest -v
```

Gate de cobertura: **≥ 80%** (actualmente ~98%).

Tests usan SQLite en memoria con `StaticPool` para velocidad y aislamiento. Producción usa Postgres real.

## Variables de entorno

Todas se leen vía `app/core/config.py` (Pydantic Settings). Ver `.env.example` en la raíz.

| Variable | Default | Notas |
|---|---|---|
| `DATABASE_URL` | — | `postgresql+psycopg2://...` |
| `JWT_SECRET` | — | Mínimo 16 caracteres, no placeholders (`changeme`, `secret`, `todo`) |
| `JWT_ALGORITHM` | `HS256` | |
| `ACCESS_TOKEN_TTL_MINUTES` | `15` | |
| `REFRESH_TOKEN_TTL_DAYS` | `7` | |
| `SEED_ADMIN_EMAIL` | — | Si vacío, no se siembra admin |
| `SEED_ADMIN_PASSWORD` | — | Misma regla |
| `CORS_ORIGINS` | `http://localhost:5173` | CSV |
| `AUTH_RATE_LIMIT` | — | Placeholder · backlog |
| `LOG_LEVEL` | — | Placeholder · backlog |

## Layout

```
app/
├── api/v1/                    Routers FastAPI
│   ├── __init__.py            api_router agrega todos
│   ├── auth.py                /auth/register, /login, /refresh, /me
│   ├── events.py              CRUD eventos + /transition
│   ├── event_sessions.py      CRUD anidado /events/{id}/sessions
│   ├── registrations.py       /events/{id}/registrations + me
│   ├── users.py               GET /users?q= (organizer/admin · alimenta SpeakerPicker)
│   └── me.py                  /me/registrations
├── core/
│   ├── config.py              Settings (Pydantic BaseSettings)
│   ├── errors.py              DomainError + 16 subclases del catálogo
│   ├── exception_handlers.py  Mapea DomainError → shape canónico
│   └── security.py            hash/verify, JWT encode/decode, get_current_user
├── db/
│   ├── session.py             engine + get_session + helper `transactional()`
│   └── seed.py                Seed admin idempotente
├── models/                    SQLModel: User, Event, EventSession, Registration
├── repositories/              Acceso a datos (sin lógica de negocio)
├── schemas/                   Pydantic in/out
├── services/                  Lógica de negocio + transacciones
└── tests/                     pytest (131 tests)
```

## Migraciones

Estado actual:

| Revisión | Contenido |
|---|---|
| `0001_create_users` | Tabla `users` + enum `user_role` |
| `0002_create_events` | Tabla `events` + enum `event_status` + CHECK + índices |
| `0003_create_event_sessions` | Tabla `event_sessions` + CHECK + 2 índices compuestos |
| `0004_create_registrations` | Tabla `registrations` + enum + **unique parcial** sobre `(user_id, event_id) WHERE status='CONFIRMED'` |

## Catálogo de errores

Shape canónico: `{ "error": { "code": "<CODE>", "message": "<texto>", "details": {...} } }`

Códigos activos:

`AUTH_INVALID_CREDENTIALS`, `AUTH_TOKEN_EXPIRED`, `FORBIDDEN`, `NOT_FOUND`, `VALIDATION_ERROR`, `USER_ALREADY_EXISTS`, `EVENT_FULL`, `EVENT_NOT_MUTABLE`, `INVALID_TRANSITION`, `SESSION_OVERLAP`, `SESSION_OUT_OF_RANGE`, `SESSION_CAPACITY_EXCEEDS_EVENT`, `EVENT_CAPACITY_BELOW_SESSION`, `SPEAKER_CANNOT_REGISTER`, `DUPLICATE_REGISTRATION`, `INVALID_REGISTRATION_STATE`.

El handler global (`app/core/exception_handlers.py`) captura `DomainError` y serializa al shape canónico.
