# Mis Eventos — Reglas globales

Aplicación web Full Stack para digitalizar la gestión manual de eventos: inscripciones, sesiones, ponentes y asistentes. MVP funcional end-to-end.

## 5 reglas must-know

1. **Idioma:** código, variables, base de datos y endpoints en **inglés**. Comentarios y reglas de dominio en **español**.
2. **Commits:** convención **Semantic** (`feat:`, `fix:`, `chore:`, `test:`, `refactor:`, `docs:`). **NO autocommitear** — los commits los realiza el desarrollador directamente.
3. **Transacciones:** se abren en la capa de **servicios** vía `with transactional(session):` (helper en `app/db/session.py`). Repositorios solo hacen `flush`, nunca `commit`. Ver [ADR-001](.planning/decisions/001-transactional-helper.md).
4. **Shape de error canónico:** toda respuesta de error sigue `{ "error": { "code", "message", "details" } }`. Catálogo en [`.planning/error-catalog.md`](.planning/error-catalog.md).
5. **Timezone I/O:** DB en **UTC**. API recibe/emite **ISO-8601 con offset**. El cliente convierte a TZ local para mostrar.

## Estado de fases

| Fase | Alcance | Detalle | Estado |
|---|---|---|---|
| 0 | Bootstrap entorno (Docker + Alembic + healthchecks) | [`.planning/phases/00-bootstrap.md`](.planning/phases/00-bootstrap.md) | ✅ |
| 1 | Auth & RBAC (JWT, 3 roles, seed admin) | [`.planning/phases/01-auth-rbac.md`](.planning/phases/01-auth-rbac.md) | ✅ |
| 2 | Eventos (CRUD + búsqueda + paginación) | [`.planning/phases/02-events.md`](.planning/phases/02-events.md) | ✅ |
| 3 | Máquina de estados del Evento (matriz declarativa) | [`.planning/phases/03-transitions.md`](.planning/phases/03-transitions.md) | ✅ |
| 4 | Sesiones con solapamiento global del speaker | [`.planning/phases/04-sessions.md`](.planning/phases/04-sessions.md) | ✅ |
| 5 | Inscripciones (Regla de Oro + cascada del evento) | [`.planning/phases/05-registrations.md`](.planning/phases/05-registrations.md) | ✅ |
| 6 | Hardening (CORS, OpenAPI, coverage gates, READMEs) | [`.planning/phases/06-hardening.md`](.planning/phases/06-hardening.md) | ✅ |

## Mapa de la documentación

```
CLAUDE.md                           ← este archivo (índice + must-knows)
.planning/                          ← source-of-truth detallado
├── README.md                       Tabla de contenidos de .planning/
├── domain.md                       Entidades, RBAC, máquina de estados, Regla de Oro
├── api.md                          Convenciones REST + shape de error + endpoints
├── error-catalog.md                Tabla canónica de los 16 códigos de error
├── backlog.md                      Post-MVP explícito (rate-limit, logging JSON, etc.)
├── phases/                         Una fase por archivo (formato denso)
│   ├── 00-bootstrap.md
│   ├── 01-auth-rbac.md
│   ├── 02-events.md
│   ├── 03-transitions.md
│   ├── 04-sessions.md
│   ├── 05-registrations.md
│   └── 06-hardening.md
└── decisions/                      ADRs (Architecture Decision Records)
    ├── 001-transactional-helper.md         Por qué `transactional()` y no `session.begin()`
    ├── 002-state-machine-matrix.md         Matriz declarativa vs if/elif
    ├── 003-speaker-as-derived.md           Speaker como atributo, no rol
    ├── 004-sqlite-vs-postgres-locks.md     Limitación test concurrencia Regla de Oro
    └── 005-phase-6-scope-cuts.md           Rate-limit y logging JSON al backlog

backend/CLAUDE.md                   ← convenciones backend (auto-cargado dentro de backend/)
frontend/CLAUDE.md                  ← convenciones frontend (auto-cargado dentro de frontend/)
```

## Convenciones de API (resumen)

- **Prefijo:** `/api/v1`.
- **Paginación:** offset/limit con shape `{ items, total, limit, offset }`. `limit` máximo: 100.
- **Errores:** ver [`.planning/error-catalog.md`](.planning/error-catalog.md) para los 16 códigos activos.

Detalle completo en [`.planning/api.md`](.planning/api.md).

## Reglas del flujo entre fases

- Cada fase cierra con: **migración aplicada + tests verdes + cobertura no baja + demo manual ok**.
- Si una fase descubre un cambio en otra ya cerrada, se vuelve a tocar esa fase (no se acumula deuda).
- Cobertura: backend ≥ 80%, frontend ≥ 70%. Gate aplicado vía `make test`.

## Para Claude / colaboradores nuevos

Si entras al proyecto sin contexto previo, lee en este orden:

1. **Este archivo** — reglas must-know + estado de fases.
2. **[`.planning/domain.md`](.planning/domain.md)** — qué hace el sistema y por qué.
3. **[`.planning/api.md`](.planning/api.md)** + **[`.planning/error-catalog.md`](.planning/error-catalog.md)** — cómo hablan el cliente y la API.
4. **`.planning/phases/0X-*.md`** — el detalle de la fase en la que vas a trabajar.
5. **`.planning/decisions/00X-*.md`** — el porqué de las decisiones difíciles.

Los archivos en `.planning/` **NO se auto-cargan** en cada conversación — se leen on-demand cuando son relevantes, lo que mantiene el contexto ligero.
