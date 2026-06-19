# Fase 4 — Sesiones (EventSession)

**Meta:** Un Organizer programa la agenda de su evento como un conjunto de `EventSession` con ponente asignado. Cada sesión queda dentro del marco temporal del evento, con capacidad opcional acotada por el aforo del evento, y sin solaparse en el tiempo con otras sesiones del mismo ponente (regla **global** entre eventos). El frontend muestra la agenda en el detalle del evento.

## Pre-requisitos de fase anterior

- Fases 1-3 cerradas: modelo `User` (target del FK `speaker_id`), modelo `Event` con `EventStatus` operativo, helper `with transactional(...)`, RBAC owner/admin y máquina de estados activos.

## Variables de entorno requeridas

- Ninguna nueva.

## Decisiones materiales fijadas para esta fase

1. **Ciclo de vida de sesiones:** crear/editar/borrar permitido cuando el evento padre está en `DRAFT` **o** `PUBLISHED`. En `IN_PROGRESS`/`FINISHED`/`CANCELLED` → 409 `EVENT_NOT_MUTABLE` con `details.reason="sessions can only be modified while event is Draft or Published"`. Reutilizamos el código existente en vez de crear uno nuevo.
2. **Speaker = User existente:** el endpoint recibe `speaker_id: int` y valida que el `User` exista; no se crean usuarios inline. Backlog/admin se encarga de provisionar cuentas. UX se cubre con un buscador `GET /api/v1/users?q=...`. Ver [ADR-003](../decisions/003-speaker-as-derived.md).
3. **Regla de no solapamiento — global por speaker:** dos sesiones activas con el mismo `speaker_id` no pueden cruzarse en el tiempo, sin importar el evento. Las sesiones de eventos en estado `CANCELLED` **se ignoran** en el chequeo.
4. **Capacidad del evento bajada:** si un `PATCH /events/{id}` reduce `capacity` por debajo de la capacidad de alguna sesión existente → 409 `EVENT_CAPACITY_BELOW_SESSION` (código nuevo). El bloqueo vive en `EventService.update`.

## Pasos secuenciales (el orden importa)

1. **Modelo `EventSession`** (`app/models/event_session.py`)
   - Tabla `event_sessions` con FKs (event CASCADE, speaker RESTRICT), `CHECK (start_at < end_at)` y `CHECK (capacity IS NULL OR capacity > 0)`.
   - Índices compuestos: `(event_id, start_at)` y `(speaker_id, start_at)` (este último para la query de solapamiento global).

2. **Migración Alembic 0003** — incluye CHECK constraints + 2 índices compuestos.

3. **Schemas Pydantic** (`app/schemas/event_session.py`) — `SessionCreate`, `SessionUpdate`, `SessionRead` (embebe `speaker: { id, email }` para evitar N+1).

4. **Repositorio `EventSessionRepository`** — `get`, `list_by_event`, `max_capacity_for_event`, `find_speaker_overlap` (JOIN con `events` excluyendo CANCELLED), `is_speaker_of_event`, CRUD básico.

5. **Servicio `EventSessionService`** envuelto en `with transactional(...)`:
   - Guards: `_load_mutable_event` (estado DRAFT/PUBLISHED), `_validate_speaker_exists`, `_validate_in_event_range`, `_validate_capacity`, `_validate_no_overlap`.
   - Hidratación: `_enrich_one` y `_enrich_many` agregan el speaker en batch.

6. **Parche `EventService.update`:** si el patch contiene `capacity` y `sessions.max_capacity_for_event(event_id) > new_capacity` → 409 `EVENT_CAPACITY_BELOW_SESSION`.

7. **Catálogo de errores — 4 nuevos:** `SESSION_OUT_OF_RANGE`, `SESSION_OVERLAP`, `SESSION_CAPACITY_EXCEEDS_EVENT`, `EVENT_CAPACITY_BELOW_SESSION`. Ver [`error-catalog.md`](../error-catalog.md).

8. **Endpoints REST** anidados bajo `/api/v1/events/{event_id}/sessions/*` (POST/GET list/detail/PATCH/DELETE). Listado **sin paginación dura** (max defensivo 200).

9. **Endpoint de búsqueda de usuarios** `GET /api/v1/users?q=...&limit=20` (auth requerida, **solo organizer/admin**). Alimenta el `SpeakerPicker`.

10. **Frontend — tipos + capa de datos:** `types/session.ts`, `types/user.ts`, `api/sessions.ts`, `api/users.ts`, `hooks/sessions.ts` (query-keys jerárquicas `["events", id, "sessions"]`), `hooks/users.ts` (debounce 300ms, min 2 chars).

11. **Frontend — componentes nuevos** (`src/components/sessions/`):
    - **`SpeakerPicker.tsx`** con debounce + fallback message a `/register`.
    - **`SessionForm.tsx`** usa `src/lib/datetime.ts` para conversión `datetime-local` ↔ ISO-8601.
    - **`SessionsAgenda.tsx`** con orden cronológico y acciones contextuales por (rol, estado del evento).

12. **Frontend — integración:** `<SessionsAgenda />` en `EventDetailPage`. Rutas `/events/:id/sessions/new` y `/events/:id/sessions/:sessionId/edit` con `RequireRole`.

13. **Tests backend** (`test_event_sessions_endpoints.py`, `test_users_search.py`):
    - Validators de schema, RBAC, ciclo de vida del evento, todas las validaciones de negocio, solape global y exclusión de CANCELLED, PATCH evento bloqueado, búsqueda de usuarios.

14. **Tests frontend:** `SpeakerPicker.test.tsx`, `SessionForm.test.tsx`, `SessionsAgenda.test.tsx` (render condicional por rol × estado).

## Definition of Done (verificable)

- [x] `make migrate` aplica la migración 0003 sin errores; `\d event_sessions` muestra los `CHECK` y los dos índices compuestos.
- [x] `POST /api/v1/events/{id}/sessions` por owner sobre evento `DRAFT` → 201; sobre `PUBLISHED` → 201; sobre `IN_PROGRESS` → 409 `EVENT_NOT_MUTABLE`.
- [x] `POST` con sesión fuera del marco temporal → 409 `SESSION_OUT_OF_RANGE`; con `capacity > event.capacity` → 409 `SESSION_CAPACITY_EXCEEDS_EVENT`; con speaker inexistente → 404.
- [x] `POST` con solape global del speaker → 409 `SESSION_OVERLAP`; el solape no se gatilla si el evento conflictivo está `CANCELLED`.
- [x] `PATCH` reasignando `speaker_id` a alguien con choque temporal → 409.
- [x] `PATCH /api/v1/events/{id}` bajando `capacity` por debajo de alguna sesión → 409 `EVENT_CAPACITY_BELOW_SESSION`.
- [x] `GET /api/v1/events/{id}/sessions` retorna ordenado por `start_at ASC` y embebe `speaker: {id, email}` en cada item.
- [x] `GET /api/v1/users?q=` por organizer/admin → 200 con resultados; por attendee → 403.
- [x] Frontend: en `/events/:id` aparece la agenda; un organizer dueño en Draft o Published ve "+ Añadir sesión" y acciones por fila; un attendee no.
- [x] `SpeakerPicker` ejecuta la búsqueda con debounce y muestra el mensaje fallback cuando no hay resultados.
- [x] Tras crear/editar/borrar sesión, la agenda se refresca sin reload manual.
- [x] `make test` verde (back + front).

## No hacer en Fase 4 (anti-scope-creep)

- ❌ Múltiples speakers por sesión. El modelo es `speaker_id: int` (1-a-1).
- ❌ Crear usuarios inline desde el formulario de sesión. El `SpeakerPicker` solo asigna.
- ❌ Inscripción **por sesión**. Fase 5 inscribe al **evento**.
- ❌ Detectar solapamientos entre sesiones del mismo evento que no comparten speaker (charlas paralelas son válidas).
- ❌ Exportar agenda a ICS, materiales descargables, recordatorios al speaker, tags/categorías.
- ❌ Reordenamiento drag-and-drop. La agenda se ordena por `start_at`.
- ❌ Cron de transición automática.
- ❌ Soft delete de sesiones.
- ❌ Endpoint público de "speakers más activos" o reportes derivados.

## Salida

Un organizer programa la agenda de su evento. El sistema garantiza que las sesiones encajan dentro del marco del evento, no exceden su aforo y que ningún ponente queda doble-asignado a horarios solapados a lo largo de todo el catálogo de eventos activos. Un visitante anónimo o asistente ve la agenda completa al abrir el detalle del evento publicado. Fase 5 podrá enchufar la "Regla de Oro" sobre el evento sin tocar nada de sesiones.
