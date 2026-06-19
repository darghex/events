# Convenciones de API

## Generales

- **Prefijo:** `/api/v1`.
- **Autenticación:** JWT Bearer (`Authorization: Bearer <access_token>`). Ver Fase 1 para detalles.
- **Paginación offset/limit:**
  ```json
  { "items": [...], "total": 123, "limit": 20, "offset": 0 }
  ```
  `limit` máximo permitido: 100. Por defecto: 20.
- **Timestamps:** ISO-8601 con offset en payloads (ej. `2026-06-16T10:00:00-05:00` o `2026-06-16T15:00:00Z`). **DB almacena en UTC**. Cliente convierte para mostrar.

## Shape de error canónico

Toda respuesta de error (4xx, 5xx) sigue este shape:

```json
{
  "error": {
    "code": "EVENT_FULL",
    "message": "Event capacity reached",
    "details": { "event_id": 42, "capacity": 100 }
  }
}
```

- **`code`**: identificador estable en `SCREAMING_SNAKE_CASE`. El frontend mapea por código, no por `message`.
- **`message`**: texto explicativo (en español, para debugging — el frontend muestra su propio mapa UX).
- **`details`**: objeto con contexto específico del error. Puede ser `{}`.

El handler global (`app/core/exception_handlers.py`) serializa cualquier `DomainError` al shape canónico automáticamente. `RequestValidationError` de Pydantic se mapea a `VALIDATION_ERROR` (422).

Ver [`error-catalog.md`](error-catalog.md) para la tabla completa de códigos.

## Endpoints del MVP

### Auth (`/api/v1/auth`)

| Método | Path | Auth | Notas |
|---|---|---|---|
| POST | `/auth/register` | — | Crea User con rol `ATTENDEE`. |
| POST | `/auth/login` | — | Retorna `{ access_token, refresh_token, token_type: "bearer" }`. |
| POST | `/auth/refresh` | — | Body `{ refresh_token }` → nuevo `access_token`. |
| GET | `/auth/me` | ✅ | Retorna el `UserRead` del actor. |

### Eventos (`/api/v1/events`)

| Método | Path | Auth | RBAC |
|---|---|---|---|
| GET | `/events` | opcional | Pública. Solo `PUBLISHED`. Query `?q=&limit=&offset=`. |
| POST | `/events` | ✅ | Organizer / Admin. Siempre nace en `DRAFT`. |
| GET | `/events/me` | ✅ | Organizer / Admin. Todos los estados del actor. |
| GET | `/events/{id}` | opcional | Pública para `Published+`. Draft solo owner/admin (404 al resto). |
| PATCH | `/events/{id}` | ✅ | Owner o admin. Solo Draft salvo admin (Published → 409 `EVENT_NOT_MUTABLE`). |
| DELETE | `/events/{id}` | ✅ | Owner o admin. Solo Draft (204). |
| POST | `/events/{id}/transition` | ✅ | Owner/admin. Body `{ to_status }`. Ver matriz en [`domain.md`](domain.md#matriz-de-transiciones-permitidas). |

### Sesiones (`/api/v1/events/{event_id}/sessions`)

| Método | Path | Auth | RBAC |
|---|---|---|---|
| GET | `/events/{id}/sessions` | opcional | Igual que GET evento (Draft solo owner/admin). |
| POST | `/events/{id}/sessions` | ✅ | Owner / admin. Evento en `Draft` o `Published`. |
| GET | `/events/{id}/sessions/{sid}` | opcional | Igual que listado. |
| PATCH | `/events/{id}/sessions/{sid}` | ✅ | Owner / admin. |
| DELETE | `/events/{id}/sessions/{sid}` | ✅ | Owner / admin (204). |

### Usuarios (`/api/v1/users`)

| Método | Path | Auth | RBAC |
|---|---|---|---|
| GET | `/users?q=&limit=` | ✅ | Organizer / admin. Búsqueda por email (ILIKE). Alimenta `SpeakerPicker`. |

### Inscripciones (`/api/v1/events/{event_id}/registrations` + `/api/v1/me/registrations`)

| Método | Path | Auth | RBAC |
|---|---|---|---|
| POST | `/events/{id}/registrations` | ✅ | Cualquier autenticado (incluye owner). Evento en `Published`. |
| DELETE | `/events/{id}/registrations/me` | ✅ | El propio usuario (204). |
| GET | `/me/registrations` | ✅ | Historial paginado del actor con eventos embebidos. |

## Datos derivados embebidos

Los endpoints de eventos hidratan campos derivados sin necesidad de queries adicionales por parte del cliente:

**`EventRead` (detalle):**
- `confirmed_count: int` — cuenta de `Registration` activas.
- `is_full: bool` — `confirmed_count >= capacity`.
- `my_registration_status: 'CONFIRMED' | null` — solo si hay sesión autenticada.

**`EventListItem` (lista):**
- `confirmed_count: int`
- `is_full: bool`

(No incluye `my_registration_status` para no inflar listas anónimas. Calcula con `count_confirmed_for_events` + `active_status_for_user_events` en batch para evitar N+1.)

**`SessionRead`:**
- `speaker: { id, email }` — embebido para evitar N+1 en agenda.

## Estado de decisiones (resueltas)

1. ✅ **Matriz de transición de estados** — definida en [`domain.md`](domain.md#matriz-de-transiciones-permitidas).
2. ✅ **Shape de error canónico** — ver arriba.
3. ✅ **TypeScript estricto** — confirmado en `frontend/CLAUDE.md`.
4. ✅ **State manager** — **Zustand** (decidido; menor superficie para este alcance).
5. ✅ **HTTP client** — **Axios** + **React Query (TanStack)** para caché.
6. ✅ **JWT / password policy** — `backend/CLAUDE.md` (Access 15m, Refresh 7d, HS256, bcrypt cost ≥ 12, password mín. 8 + mayúscula + dígito).
7. ✅ **CORS** — `CORS_ORIGINS` CSV en `.env`. `allow_credentials=True`.
8. ✅ **Seed inicial** — `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` en `.env`.
9. ✅ **Timezone I/O** — DB en UTC; API ISO-8601 con offset. Cliente convierte a TZ local.
10. ⏸ **Rate-limit y logging JSON** — backlog post-MVP. Ver [`backlog.md`](backlog.md) y [ADR-005](decisions/005-phase-6-scope-cuts.md).
11. ⏸ **Profile admin** — `PATCH /users/{id}/status|role` en backlog.
