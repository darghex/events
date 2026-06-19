# Convenciones de Backend - Python 3.12 & FastAPI

## Stack Tecnológico Obligatorio
- **Runtime:** Python 3.12 gestionado con **Poetry**.
- **Framework:** FastAPI con generación automática de OpenAPI/Swagger.
- **ORM:** SQLAlchemy + SQLModel (para validaciones nativas Pydantic). SQLAlchemy 2.x (evitar conflictos Session SQLModel vs modelo de dominio Session).
- **Base de Datos:** PostgreSQL con **Alembic** para el control de migraciones.
- **Testing:** Pruebas unitarias y de integración con **pytest**.


## Arquitectura del Backend
- **Estructura:** Modular o por capas (Rutas -> Servicios -> Repositorios/Modelos).
- **Clean Code:** Usar buenas prácticas como DRY, SOLID.
- **Minimalista:** No hacer lógica compleja, código liviano para la funcionalidad que se desee realizar.
- **Respuestas:** Formatos JSON limpios y manejo centralizado de excepciones con `HTTPException` + handler global que emite el shape de error definido en el root CLAUDE.md.
- **Documentación:** Usar el API doc generado por FastAPI (`/docs` y `/redoc`).
- **RBAC:** Obligatorio (3 roles globales: `admin`, `organizer`, `attendee`). `speaker` **no es rol** — es un atributo derivado por evento (un usuario es speaker de un evento si está asignado en `EventSession.speaker_id`).
- **Estrategia de paginación:** offset/limit (`limit` máx. 100).
- **Migración inicial:** Alembic genera schema desde modelos.
- **Estructura de carpetas sugerida:** `app/{api,core,models,schemas,services,repositories,db,tests}`.
- **Política de transacciones:** Se cierran en la capa de **servicios** mediante el helper `with transactional(session):` (definido en `app/db/session.py`). Internamente hace `commit()` al salir limpio y `rollback()` en excepción — compatible con el autobegin de SQLAlchemy 2.x. Repositorios solo hacen `flush`, nunca `commit`.
- **Manejo de timezone:** UTC en DB; API recibe/emite ISO-8601 con offset; el cliente convierte para mostrar.
- **Renombrado de dominio:** la entidad `Session` se llama `EventSession` para evitar colisión con `sqlmodel.Session`.

## Autenticación y Seguridad
- **JWT:** algoritmo `HS256`; secret en `JWT_SECRET` (env).
  - **Access token:** `ACCESS_TOKEN_TTL_MINUTES=15`.
  - **Refresh token:** `REFRESH_TOKEN_TTL_DAYS=7`.
  - Endpoint `POST /api/v1/auth/refresh` para renovar.
- **Password hashing:** `bcrypt` con cost ≥ 12 (`passlib[bcrypt]`).
- **Password policy:** mínimo 8 caracteres, al menos 1 mayúscula y 1 dígito. Validación en schema Pydantic.
- **CORS:** lista blanca via `CORS_ORIGINS` (CSV en env).
- **Rate limit:** `slowapi` aplicado a `/api/v1/auth/*` — default `5/minute` (`AUTH_RATE_LIMIT` configurable).
- **HTTPS:** terminación en el proxy/edge (no en la app).

## Logging
- **Formato:** JSON estructurado (`structlog` o `logging` con `JsonFormatter`).
- **Request ID:** middleware que inyecta `X-Request-ID` en cada response y lo propaga al logger.
- **Nivel:** `LOG_LEVEL` (default `ERROR`).

## Concurrencia (Regla de Oro)
- Inscripción usa **lock pesimista**: `SELECT ... FOR UPDATE` sobre el `Event` dentro de la transacción del servicio, valida `confirmed_count < capacity` y persiste la `Registration`. Garantiza no exceder aforo bajo concurrencia.

## Seeds / Fixtures
- Seed de usuario admin al arrancar (script idempotente):
  - `SEED_ADMIN_EMAIL` (ej. `admin@mieventos.local`)
  - `SEED_ADMIN_PASSWORD` (requerido en `.env`; sin default)
- Si el usuario ya existe, no sobrescribe.

## Variables de entorno requeridas
`DATABASE_URL`, `JWT_SECRET`, `ACCESS_TOKEN_TTL_MINUTES`, `REFRESH_TOKEN_TTL_DAYS`, `CORS_ORIGINS`, `AUTH_RATE_LIMIT`, `LOG_LEVEL`, `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD`.
                              
## Comandos de Utilidad para Claude
- Instalar dependencias: `poetry install`
- Levantar localmente: `poetry run fastapi dev app/main.py`
- Crear migración: `poetry run alembic revision --autogenerate -m "cambio"`
- Aplicar migración: `poetry run alembic upgrade head`
- Ejecutar tests y cobertura: `poetry run pytest --cov=app`
