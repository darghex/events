# Fase 2 — Eventos (CRUD + búsqueda)

**Meta:** Un Organizer crea, edita y borra eventos en estado `Draft`; cualquiera (auth o no) lista y consulta el detalle de los `Published`. RBAC operativo dueño/admin. Frontend con listado paginado, búsqueda por título, detalle y formulario reutilizable.

## Pre-requisitos de fase anterior

- Fase 1 cerrada: tabla `users`, JWT, dependencies `get_current_user` y `require_role(*roles)` operativas.
- Migraciones aplicadas vía `make migrate` o startup; seed admin disponible.

## Variables de entorno requeridas

- Ninguna nueva. Reutiliza `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `VITE_API_BASE_URL`.
- Constantes de paginación se definen en código (`DEFAULT_LIMIT=20`, `MAX_LIMIT=100`) — no son env vars.

## Pasos secuenciales (el orden importa)

1. **Modelo `Event` y enum de estados**
   - `app/models/event.py`: tabla `events` con columnas:
     - `id (PK)`, `title (str, 1–200, indexed)`, `description (text, ≤5000, nullable)`, `location (str, 1–200)`.
     - `capacity (int, NOT NULL)` con `CHECK (capacity > 0)`.
     - `start_at`, `end_at` (`TIMESTAMP WITH TIME ZONE`, NOT NULL) con `CHECK (start_at < end_at)`.
     - `status (Enum EventStatus, NOT NULL, server_default 'DRAFT', indexed)`.
     - `owner_id (FK users.id, ON DELETE RESTRICT, NOT NULL, indexed)`.
     - `created_at`, `updated_at` (timezone-aware, mismo patrón que `User`).
   - Enum `EventStatus`: `DRAFT, PUBLISHED, IN_PROGRESS, FINISHED, CANCELLED` (los 5 valores se declaran ahora aunque solo `DRAFT` y `PUBLISHED` se usen en Fase 2; el resto los activa Fase 3).
   - Índices compuestos: `(status, start_at)` para listado público; `(owner_id, created_at DESC)` para listado de organizer.

2. **Migración Alembic**
   - `alembic revision --autogenerate -m "create events table"`.
   - Revisar a mano que la migración incluye los `CHECK` constraints y el tipo `Enum` (autogenerate suele perderlos).
   - `alembic upgrade head` aplicado en startup o `make migrate`.

3. **Schemas Pydantic** (`app/schemas/event.py`)
   - `EventCreate`: `title`, `description?`, `location`, `capacity`, `start_at`, `end_at`. **No acepta `status`** (siempre `DRAFT` al crear). Validators: longitudes, `capacity > 0`, `start_at < end_at`.
   - `EventUpdate`: todos los campos opcionales. Tampoco acepta `status` (transiciones = Fase 3).
   - `EventRead`: incluye `id`, `status`, `owner_id`, `created_at`, `updated_at`, conteos derivados los deja en `null`/ausentes (los introduce Fase 5).
   - `EventListItem`: subset ligero (`id`, `title`, `location`, `start_at`, `end_at`, `capacity`, `status`) para listados.
   - `Page[EventListItem]` reutilizable: `{ items, total, limit, offset }`.

4. **Repositorio `EventRepository`** (`app/repositories/event.py`)
   - `get(id) -> Event | None`.
   - `list_published(q: str | None, limit, offset) -> (rows, total)` — filtra `status=PUBLISHED`, ordena `start_at ASC`, aplica `ILIKE %q%` sobre `title` cuando `q` no es vacío.
   - `list_by_owner(owner_id, limit, offset) -> (rows, total)` — todos los estados del dueño, orden `created_at DESC`.
   - `create(data, owner_id)`, `update(id, patch)`, `delete(id)`.
   - Sin lógica de negocio: solo persistencia.

5. **Servicio `EventService`** (`app/services/event.py`)
   - Abre transacciones vía helper `with transactional(session):` (ver [ADR-001](../decisions/001-transactional-helper.md)); orquesta validaciones y RBAC.
   - `create(actor, data)`: requiere `actor.role in {ORGANIZER, ADMIN}`. Setea `owner_id=actor.id`, `status=DRAFT`.
   - `get(actor | None, id)`: si `status=PUBLISHED` → cualquiera. Si `status=DRAFT` y `actor` no es owner ni admin → **404 NOT_FOUND** (no leak de existencia). Resto de estados (`IN_PROGRESS`/`FINISHED`/`CANCELLED`) visibles públicamente.
   - `update(actor, id, patch)`: requiere `actor.id == event.owner_id or actor.role == ADMIN`. Si `event.status != DRAFT` y `actor.role != ADMIN` → `409 EVENT_NOT_MUTABLE`. Admin puede editar en cualquier estado.
   - `delete(actor, id)`: misma RBAC que update. Hard delete. Misma regla `EVENT_NOT_MUTABLE` para no-Draft (sin admin override aquí — `Published+` se cancela vía Fase 3, no se borra).
   - `list_published(q, limit, offset)` y `list_mine(actor, limit, offset)` delegan al repo.

6. **Endpoints** (`app/api/v1/events.py`, prefijo `/api/v1/events`)
   | Método | Path                | Auth      | RBAC                          | Notas |
   |--------|---------------------|-----------|-------------------------------|-------|
   | POST   | `/`                 | Requerida | `organizer` o `admin`         | Crea en `DRAFT`. 201 con `EventRead`. |
   | GET    | `/`                 | Opcional  | Pública                       | Solo `status=PUBLISHED`. Query: `q?`, `limit?`, `offset?`. |
   | GET    | `/me`               | Requerida | `organizer` o `admin`         | Eventos del actor en todos los estados. |
   | GET    | `/{id}`             | Opcional  | Pública para `Published`+     | Draft solo para owner/admin; resto → 404. |
   | PATCH  | `/{id}`             | Requerida | Owner o `admin`               | Solo `DRAFT` salvo admin. Errores: 403/404/409/422. |
   | DELETE | `/{id}`             | Requerida | Owner o `admin`               | Solo `DRAFT`. 204 No Content. |
   - Parámetros de paginación con clamp: `limit ∈ [1, 100]`, `offset ≥ 0`. Valor fuera de rango → 422.
   - Búsqueda: si `q` viene vacío o solo whitespace, se ignora (no se aplica ILIKE).
   - Listado pública responde con shape `{ items: EventListItem[], total, limit, offset }`.

7. **Catálogo de errores — añadir `EVENT_NOT_MUTABLE`**
   - Nuevo código `EVENT_NOT_MUTABLE` (409): "Event can only be edited or deleted while in Draft status." Detalle: `{ event_id, current_status }`.
   - Catálogo activo en esta fase: heredados de Fase 1 + `EVENT_NOT_MUTABLE`.

8. **Frontend — rutas y páginas** (`frontend/src/`)
   - Nuevas páginas:
     - `pages/events/EventsListPage.tsx` (`/events`, público) — listado con búsqueda + paginación.
     - `pages/events/EventDetailPage.tsx` (`/events/:id`, público para Published) — detalle.
     - `pages/events/MyEventsPage.tsx` (`/me/events`, protegida + rol organizer/admin) — eventos propios.
     - `pages/events/EventCreatePage.tsx` (`/events/new`, protegida + rol organizer/admin).
     - `pages/events/EventEditPage.tsx` (`/events/:id/edit`, protegida + rol owner/admin).
   - Router: agregar las rutas; reutilizar `<RequireAuth>` de Fase 1 y crear `<RequireRole roles={["ORGANIZER","ADMIN"]}>` derivado.
   - Header/navbar: link "Mis eventos" visible si rol es organizer/admin.

9. **Frontend — componentes reutilizables** (`src/components/`)
   - `ui/EventoCard.tsx`: muestra `title`, `location`, rango de fechas formateado a TZ local, badge de `status`, capacidad. Click → detalle.
   - `events/EventoForm.tsx`: formulario controlado para crear/editar. Valida client-side `title ≥ 1`, `capacity > 0`, `start_at < end_at`. Convierte `datetime-local` → ISO-8601 con offset antes de enviar (usa `src/lib/datetime.ts`).
   - `ui/SearchBar.tsx`: input con debounce 300ms que actualiza el query param `?q=`.
   - `ui/Pagination.tsx`: prev/next + indicador `página X de Y` calculado desde `{total, limit, offset}`.
   - Reusar `Input`, `Button`, `FormField` de Fase 1.

10. **Frontend — capa de datos**
    - `src/api/events.ts`: funciones `listEvents({q, limit, offset})`, `getEvent(id)`, `listMyEvents(...)`, `createEvent(data)`, `updateEvent(id, patch)`, `deleteEvent(id)`. Usa el cliente Axios de Fase 1 (interceptor de auth ya monta el `Bearer`).
    - `src/hooks/events.ts`: hooks React Query — `useEventsList`, `useEventDetail`, `useMyEvents`, `useCreateEvent`, `useUpdateEvent`, `useDeleteEvent`. Mutaciones invalidan `["events"]` (jerárquico).
    - Mapeo de error `code` → mensaje UX en `src/api/errors.ts`: añadir `EVENT_NOT_MUTABLE`, `FORBIDDEN`, `NOT_FOUND` con mensajes legibles.

11. **Tests**
    - **Backend** (`app/tests/test_events_*.py`):
      - Unit: validators de `EventCreate` (start < end, capacity > 0, title length).
      - Repo: `list_published` aplica ILIKE y orden; paginación clamp.
      - Integration (httpx + DB):
        - Organizer crea evento → 201, `status=DRAFT`, `owner_id` coincide.
        - Attendee intenta crear → 403 `FORBIDDEN`.
        - GET público lista solo Published; un Draft del organizer no aparece.
        - Organizer ve su propio Draft en `/events/me`.
        - GET `/{id}` Draft sin auth → 404; con auth de tercero → 404; con auth del owner → 200.
        - PATCH por no-owner → 403; PATCH de Published por owner → 409 `EVENT_NOT_MUTABLE`; admin sí puede editar Published.
        - DELETE de Draft por owner → 204; DELETE de Published por owner → 409 `EVENT_NOT_MUTABLE`.
        - Search `?q=react` (case-insensitive) devuelve coincidencias; `?q=` vacío no filtra.
        - Paginación: `?limit=2&offset=0` y `?limit=2&offset=2` devuelven items disjuntos; `total` consistente.
    - **Frontend** (Vitest + RTL):
      - `EventoCard` renderiza título, badge de estado y fechas formateadas.
      - `EventoForm` muestra error si `end_at <= start_at` o `capacity ≤ 0` (sin llamar al backend).
      - `EventsListPage` renderiza skeletons mientras carga; tras resolver, muestra cards y paginación.
      - `<RequireRole>` redirige a `/` (o muestra 403 UI) si el rol no aplica.

## Definition of Done (verificable)

- [x] `make migrate` aplica la migración de `events` sin errores; `\d events` muestra constraints `capacity > 0` y `start_at < end_at`.
- [x] `POST /api/v1/events` como organizer → 201 con `status=DRAFT`; payload con `status` enviado → ignorado (no rompe).
- [x] `POST /api/v1/events` como attendee → 403 con shape canónico.
- [x] `GET /api/v1/events` (sin auth) responde shape `{items,total,limit,offset}` con solo Published.
- [x] `GET /api/v1/events?q=foo` aplica ILIKE; `?q=  ` (whitespace) se ignora.
- [x] `GET /api/v1/events?limit=150` → 422 (excede `MAX_LIMIT=100`).
- [x] `GET /api/v1/events/me` requiere auth y devuelve drafts del actor.
- [x] `GET /api/v1/events/{id}` con Draft ajeno → 404 (no 403, para no filtrar existencia).
- [x] `PATCH /api/v1/events/{id}` por no-owner → 403; por owner sobre Published → 409 `EVENT_NOT_MUTABLE`.
- [x] `DELETE /api/v1/events/{id}` solo borra Drafts; sobre Published → 409 `EVENT_NOT_MUTABLE`.
- [x] Frontend: `/events` lista eventos publicados con paginación y búsqueda funcional (debounce visible en devtools).
- [x] Frontend: `/events/new` y `/events/:id/edit` accesibles solo a organizer/admin; attendee es redirigido.
- [x] Frontend: tras crear/editar/borrar, listados se invalidan y refrescan sin reload manual.
- [x] Fechas del formulario se envían como ISO-8601 con offset; se muestran en TZ del cliente.
- [x] `make test` verde (back + front). Cobertura backend ≥ 80% sobre `app/services/event.py`, `app/repositories/event.py`, `app/api/v1/events.py`.

## No hacer en Fase 2 (anti-scope-creep)

- No implementar la máquina de estados ni el endpoint `/transition` — eso es Fase 3 (`EVENT_NOT_MUTABLE` ya bloquea mutaciones fuera de Draft).
- No modelar `EventSession` ni rutas anidadas `/events/{id}/sessions` (Fase 4).
- No modelar `Registration`, conteo de cupo, ni "Regla de Oro" (Fase 5).
- No soft delete, papelera ni auditoría de cambios — `DELETE` solo en Draft, hard.
- No imágenes/uploads, tags, categorías, ni filtros avanzados (rango de fechas, ubicación geográfica).
- No lazy loading de rutas, WebP ni minificación de producción (post-MVP).
- No notificaciones por email al publicar (post-MVP).

## Salida

Un organizer crea un evento en Draft desde el frontend, edita sus datos y lo ve listado en `/me/events`. Un asistente (o visitante sin auth) **aún no puede verlo** hasta que Fase 3 lo publique. La búsqueda y paginación funcionan en la lista pública.
