# Fase 3 — Máquina de estados del Evento

**Meta:** Un evento recorre el ciclo `Draft → Published → InProgress → Finished` (más rama `Cancelled` desde Draft/Published) bajo control RBAC. Endpoint dedicado de transición. Frontend muestra acciones contextuales según `(rol, estado)`. Tests cubren cada celda de la matriz (permitidas **y** bloqueadas).

## Pre-requisitos de fase anterior

- Fase 2 cerrada: modelo `Event` con `status: EventStatus` (5 valores ya declarados), RBAC owner/admin operativa en servicios, helper `with transactional(self.session):` disponible, `EVENT_NOT_MUTABLE` ya bloquea mutaciones de payload fuera de `Draft`.

## Variables de entorno requeridas

- Ninguna nueva. Reutiliza las de Fases 1-2.
- "Ahora" se obtiene siempre vía `now_utc()` del módulo compartido `app/core/time.py` (facilita el monkey-patch en tests temporales).

## Pasos secuenciales (el orden importa)

1. **Catálogo de errores — añadir `INVALID_TRANSITION`**
   - Nuevo código `INVALID_TRANSITION` (409): "Event state transition not allowed." Detalle: `{ event_id, from_status, to_status, reason }`. `reason` es opcional (string corto) cuando la transición existe en la matriz pero falla la condición temporal (ej. `now < start_at`).

2. **Schema Pydantic** (`app/schemas/event.py`)
   - `EventTransitionRequest { to_status: EventStatus }`. Validación enum nativa de Pydantic (payload con valor no listado → 422 `VALIDATION_ERROR`).

3. **Matriz de transiciones** (módulo dedicado `app/services/event_state.py` — ver [ADR-002](../decisions/002-state-machine-matrix.md))
   - Tipo `TransitionRule`:
     - `allowed_roles: set[UserRole]` — quién puede disparar.
     - `requires_ownership: bool` — si `True`, el actor debe ser `owner_id` del evento o `ADMIN`.
     - `validator: Callable[[Event, datetime], None]` — levanta `InvalidTransition` con `reason` si la condición temporal/datos no se cumple. Para celdas sin condición usar `_no_op`.
   - `TRANSITIONS: dict[tuple[EventStatus, EventStatus], TransitionRule]`:
     - `(DRAFT, PUBLISHED)` → owner/admin, valida `capacity > 0` y campos básicos no vacíos (defensivo aunque CHECK ya lo cubre).
     - `(DRAFT, CANCELLED)` → owner/admin, sin condición.
     - `(PUBLISHED, IN_PROGRESS)` → owner/admin, **disparo manual**, valida `now >= event.start_at` (sino `reason="event has not started yet"`).
     - `(PUBLISHED, CANCELLED)` → owner/admin, sin condición. Cascada implementada en Fase 5.
     - `(IN_PROGRESS, FINISHED)` → owner/admin, **disparo manual**, valida `now >= event.end_at` (sino `reason="event has not ended yet"`).
   - Cualquier `(from, to)` no listado → `InvalidTransition` con `reason="transition not allowed"`. En particular `FINISHED → *` y `CANCELLED → *` siempre bloqueados (estados terminales).

4. **Servicio** (`app/services/event.py`)
   - Nuevo método `transition(*, actor, event_id, to_status) -> Event` envuelto en `with transactional(self.session):`.
   - Flujo: fetch event (404 si no existe) → buscar `TRANSITIONS[(event.status, to_status)]` (si no existe → `InvalidTransition`) → chequear `actor.role in rule.allowed_roles` → si `rule.requires_ownership and actor.role != ADMIN and event.owner_id != actor.id` → `Forbidden` → ejecutar `rule.validator(event, now_utc())` → mutar `event.status = to_status`.
   - Si `(from, to) == (PUBLISHED, CANCELLED)`: en Fase 5 se enchufa la cascada (`mark_all_active_cancelled_for_event`).
   - El método NO toca otros campos del evento; solo `status`.

5. **Endpoint** (`app/api/v1/events.py`)
   - `POST /api/v1/events/{event_id}/transition` (auth requerida).
   - Body: `EventTransitionRequest`. Response: `EventRead`.
   - Códigos: 200 éxito, 401 sin auth, 403 rol/ownership insuficiente, 404 evento inexistente, 409 `INVALID_TRANSITION`, 422 enum inválido.

6. **Catálogo de errores en código** (`app/core/errors.py`)
   - Añadir clase `InvalidTransition(DomainError)` con `code="INVALID_TRANSITION"`, `status_code=409`, `message="Transición de estado no permitida"`.

7. **Frontend — capa de datos**
   - `src/api/events.ts`: `transitionEvent(id: number, toStatus: EventStatus) → Promise<EventRead>`.
   - `src/hooks/events.ts`: `useTransitionEvent(id)` con `onSuccess` invalidando `[EVENTS_KEY]` (cubre listas y detalle).
   - `src/api/errors.ts`: añadir mensaje UX `INVALID_TRANSITION → "Esta transición no está permitida en el estado actual"`.

8. **Frontend — espejo de la matriz para UX**
   - `src/lib/eventTransitions.ts`: misma matriz que el backend (estructura mínima `{ from, to, label, variant, requiresConfirm }`) — el backend sigue siendo source-of-truth de validación, el cliente solo la usa para **renderizar botones**.
   - Labels: `Publicar` (Draft→Published), `Iniciar` (Published→InProgress), `Finalizar` (InProgress→Finished), `Cancelar` (Draft/Published→Cancelled, requiere confirmación).

9. **Frontend — componente de acciones**
   - `src/components/events/EventTransitionsBar.tsx`: recibe `{event, user}`. Calcula transiciones permitidas desde la matriz cliente filtrando por `(role, ownership, current_status)`. Renderiza un botón por cada una.
   - Estados terminales (`Finished`, `Cancelled`) → no renderiza nada.
   - `Cancelar` muestra `confirm()` antes de mutar.
   - Errores del backend (ej. `INVALID_TRANSITION` por reloj) se muestran inline con `extractApiError`.

10. **Frontend — integración en detalle**
    - `EventDetailPage` renderiza `<EventTransitionsBar />` en el header del detalle, debajo del título.
    - Tras una transición exitosa, React Query refetchea el detalle y el badge muestra el nuevo estado sin reload.

11. **Tests backend** (`app/tests/test_events_transitions.py`)
    - Unit (matriz): celdas permitidas y bloqueadas representativas.
    - Integración: organizer, attendee, admin, ownership, validaciones temporales con monkey-patch de `_now_utc`.

12. **Tests frontend** (`EventTransitionsBar.test.tsx`)
    - Render condicional por (role, status); confirmaciones; estados terminales no renderizan.

## Definition of Done (verificable)

- [x] `POST /api/v1/events/{id}/transition` con body válido y RBAC OK → 200 con `EventRead` reflejando el nuevo `status`.
- [x] `Draft → Published` por organizer dueño funciona; por attendee → 403; por organizer no-dueño → 403; por admin sobre evento ajeno → 200.
- [x] `Published → InProgress` con `now < event.start_at` → 409 `INVALID_TRANSITION` con `details.reason="event has not started yet"`.
- [x] `InProgress → Finished` con `now < event.end_at` → 409 con `details.reason="event has not ended yet"`.
- [x] `Finished → Published` (terminal) → 409 `INVALID_TRANSITION`.
- [x] `Cancelled → Draft` (terminal) → 409 `INVALID_TRANSITION`.
- [x] Body con `to_status` no perteneciente al enum → 422 `VALIDATION_ERROR`.
- [x] El servicio NO mutó campos distintos de `status` (verificable comparando before/after en un test).
- [x] Frontend: en `/events/:id` los botones de transición se renderizan únicamente para `(owner | admin)` y para estados no-terminales.
- [x] Frontend: `Cancelar` pide confirmación antes de disparar la mutación.
- [x] Frontend: tras transicionar, el badge del detalle se actualiza sin reload manual.
- [x] `make test` verde (back + front).

## No hacer en Fase 3 (anti-scope-creep)

- No implementar cron de transición automática `Published → InProgress → Finished`. Backlog post-MVP.
- No implementar la cascada efectiva a `Registration` en `Published → Cancelled` — en Fase 3 solo queda el marcador `# TODO Fase 5`. Fase 5 lo enchufa.
- No exponer `GET /events/{id}/transitions` listando las permitidas — el frontend ya tiene la matriz espejo, añadir el endpoint duplicaría lógica sin ganancia clara.
- No notificaciones por email/push al cambiar de estado (post-MVP).
- No auditoría/historial de transiciones (`event_status_log`).
- No soft-delete ni restauración desde `Cancelled` — los estados terminales son inviolables.
- No tocar la migración 0002 (el enum ya tiene los 5 valores).
- No modelar `EventSession` ni `Registration` (Fases 4 y 5).

## Salida

Un organizer publica su Draft, lo lleva a InProgress al llegar la fecha de inicio, lo cierra como Finished al terminar, o cancela desde Draft/Published. Un Admin hace lo mismo sobre cualquier evento. Los estados terminales no aceptan transiciones. Todo se opera desde la UI con feedback inmediato.
