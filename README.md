# Mis Eventos — MVP Full Stack

Aplicación web para digitalizar la gestión manual de eventos: inscripciones, sesiones, ponentes y asistentes. MVP funcional end-to-end con autenticación, RBAC, máquina de estados, agenda de sesiones.

## Quick-start (≤ 3 comandos)

Requisitos: Docker y Docker Compose.

```sh
cp .env.example .env
# Edita .env y rellena al menos: JWT_SECRET, SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD
make up
```

Comprueba que todo arranca:

```sh
curl http://localhost:8000/health   # → {"status": "ok"}
open http://localhost:5173          # frontend
open http://localhost:8000/docs     # Swagger UI de la API
```

## Demo flow MVP

1. **Login del admin sembrado** en `/login` con `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD`.
2. **Registrar un Organizer** en `/register` y darle el rol `ORGANIZER` desde la DB (o usar el admin directo):
   ```sh
   docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB \
     -c "UPDATE users SET role='ORGANIZER' WHERE email='org@example.com';"
   ```
3. **Crear un evento Draft** desde `/events/new` (como organizer).
4. **Publicar el evento** con el botón "Publicar" en el detalle
5. **Añadir una sesión** con un ponente (otro usuario registrado) — el `SpeakerPicker` busca por email.
6. **Registrar un Asistente** en `/register` (rol por defecto `ATTENDEE`).
7. **Inscribirse al evento** desde el detalle público; el conteo (`confirmed_count / capacity`) sube.
8. **Cancelar la inscripción** y verificar que el botón vuelve a "Inscribirme".
9. **Como organizer**, transicionar el evento `Published → Cancelled`; todas las inscripciones activas pasan a `CANCELLED` en cascada transaccional.
10. Verifica el historial en `/me/registrations`.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12 · FastAPI · SQLModel · SQLAlchemy 2.x · Alembic |
| DB | PostgreSQL 16 |
| Frontend | React 18 · TypeScript · Vite · React Router · Zustand · React Query · Axios |
| Tests | pytest + httpx (back) · Vitest + RTL (front) |
| Orquestación | Docker Compose |

## Estructura del repo

```
.
├── backend/                Backend FastAPI
│   ├── app/
│   │   ├── api/v1/         Routers (auth, events, sessions, registrations, users, me)
│   │   ├── core/           Config, errores, security, exception handlers
│   │   ├── db/             Engine, session helper (transactional), seed
│   │   ├── models/         SQLModel: User, Event, EventSession, Registration
│   │   ├── repositories/   Acceso a datos (sin lógica de negocio)
│   │   ├── schemas/        Pydantic in/out
│   │   ├── services/       Lógica de negocio + transacciones
│   │   └── tests/          pytest (131 tests · 98% coverage)
│   ├── alembic/            Migraciones en DB
│   └── README.md           Detalles backend
├── frontend/               Frontend React + Vite
│   ├── src/
│   │   ├── api/            Cliente axios + funciones por dominio
│   │   ├── components/     UI reusable + sesiones + eventos
│   │   ├── hooks/          React Query hooks
│   │   ├── lib/            Matriz espejo de transiciones (UX)
│   │   ├── pages/          Vistas (auth, events, sessions, registrations)
│   │   ├── stores/         Zustand (auth)
│   │   └── types/          Tipos compartidos
│   └── README.md           Detalles frontend
├── docker-compose.yml      Orquestación db + backend + frontend
├── makefile                Atajos (up, down, test, migrate, ...)
└── .env.example            Variables de entorno con placeholders
```

## Comandos make

| Comando | Acción |
|---|---|
| `make up` | Levanta el stack en background |
| `make down` | Detiene el stack (mantiene datos) |
| `make down-v` | Detiene y borra volúmenes (DB fresca) |
| `make migrate` | `alembic upgrade head` en el contenedor backend |
| `make logs` | Sigue logs de los 3 servicios |
| `make ps` | Estado de los servicios |
| `make sh-back` / `sh-front` | Shell dentro del contenedor |
| `make test` | Backend + frontend (con gates de cobertura) |
| `make test-back` | pytest --cov-fail-under=80 |
| `make test-front` | vitest --coverage (≥70%) |
| `make build` | Reconstruye imágenes sin levantar |

Cobertura: backend **98%** · frontend **85.6%** (líneas).

Tests: **131** backend · **50** frontend.
