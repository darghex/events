# Fase 5 — Inscripciones (Regla de Oro)

**Meta:** Un usuario autenticado (incluido el dueño) se inscribe a un evento `Published` sin exceder el aforo bajo concurrencia, gracias a un **lock pesimista** en el servicio. Puede cancelar su inscripción en cualquier momento, y re-inscribirse si todavía hay cupo. El speaker del evento no puede inscribirse como asistente. La cancelación del evento (Fase 3) propaga en cascada transaccional sobre todas las inscripciones activas. El frontend muestra botón de inscripción / cancelación con conteo en vivo y página de historial.

## Pre-requisitos de fase anterior

- Fases 1-4 cerradas: `Event`, `EventSession`, helper `with transactional(...)`, máquina de estados activa.

## Variables de entorno requeridas

- Ninguna nueva.

## Decisiones materiales fijadas para esta fase

1. **Quién se inscribe:** cualquier usuario autenticado (`ATTENDEE`, `ORGANIZER`, `ADMIN`), incluido el dueño del evento. La inscripción es ortogonal al rol.
2. **Cuándo se permite inscripción nueva:** solo si `event.status == PUBLISHED`. Otros estados → 409 `INVALID_REGISTRATION_STATE` (código nuevo).
3. **Cancelación:** permitida siempre que la `Registration` esté `CONFIRMED`, sin importar el estado del evento.
4. **Re-inscripción:** permitida tras cancelar. La fila vieja queda `CANCELLED` y se crea una nueva fila `CONFIRMED`. El unique parcial sobre activas lo habilita naturalmente.
5. **Datos derivados en `EventRead`:** `confirmed_count: int`, `is_full: bool` y `my_registration_status: 'CONFIRMED' | null` (este último `null` cuando no hay sesión autenticada). `EventListItem` añade `confirmed_count` y `is_full` (no `my_registration_status` para no inflar listas).
6. **Test del contrato "Regla de Oro":** SQLite (motor de tests) **no implementa `SELECT ... FOR UPDATE`**. Se cubre con un test **secuencial** que verifica el contrato del servicio. Ver [ADR-004](../decisions/004-sqlite-vs-postgres-locks.md).
7. **Endpoint admin de listar asistentes:** fuera de scope (queda como backlog).

## Pasos secuenciales (el orden importa)

1. **Modelo `Registration`** con FK `user_id` (RESTRICT) y `event_id` (CASCADE), enum `RegistrationStatus`, índice compuesto `(event_id, status)` y **unique parcial sobre activas**: `UNIQUE(user_id, event_id) WHERE status = 'CONFIRMED'`.

2. **Migración Alembic 0004** — incluye el unique parcial portable Postgres/SQLite.

3. **Schemas Pydantic** — `RegistrationRead`, `RegistrationWithEvent` (embebe `EventListItem`).

4. **Actualizar `EventRead` y `EventListItem`** con `confirmed_count`, `is_full` y (solo EventRead) `my_registration_status`.

5. **Repositorio `RegistrationRepository`** con batch lookups (`count_confirmed_for_events`, `active_status_for_user_events`) para evitar N+1.

6. **Repositorio `EventRepository.get_for_update`** con `.with_for_update()` — lock pesimista en Postgres real, no-op en SQLite.

7. **Servicio `RegistrationService`** envuelto en `with transactional()`:
   - `register`: lock → status PUBLISHED → speaker check → duplicado activo → capacidad → INSERT.
   - `cancel_my_registration`: busca activa → marca CANCELLED.
   - `list_mine` con paginación.

8. **Cascada `PUBLISHED → CANCELLED`** en `services/event.py::transition`: reemplaza el `# TODO Fase 5` con `RegistrationRepository.mark_all_active_cancelled_for_event(event.id)` dentro del mismo `with transactional()`.

9. **Hidratación batch en `EventService`** — `hydrate_read`, `hydrate_list_items`. Cero N+1 en listados.

10. **Catálogo de errores (4 nuevos):** `EVENT_FULL`, `DUPLICATE_REGISTRATION`, `SPEAKER_CANNOT_REGISTER`, `INVALID_REGISTRATION_STATE`.

11. **Endpoints REST:**
    - `POST /api/v1/events/{event_id}/registrations` → 201.
    - `DELETE /api/v1/events/{event_id}/registrations/me` → 204.
    - `GET /api/v1/me/registrations` → `Page[RegistrationWithEvent]` con paginación.

12. **Frontend — tipos + capa de datos:** `types/registration.ts`, `api/registrations.ts`, `hooks/registrations.ts`. Las mutaciones invalidan `["events"]` y `["me-registrations"]`.

13. **Frontend — `RegistrationButton`** con render condicional por prioridad: sin sesión / estado ≠ Published / CONFIRMED / is_full / default → Inscribirme. `confirm()` antes de cancelar.

14. **Frontend — integración detalle:** `<RegistrationButton />` en `EventDetailPage`.

15. **Frontend — página de historial:** `/me/registrations` con `RequireAuth`. Navbar +link "Mis inscripciones".

16. **Tests backend** — happy paths, duplicate, speaker, full, invalid state, owner inscribe, cancel + re-inscripción, cascada del evento, hidratación con/sin auth, contrato Regla de Oro (secuencial).

17. **Tests frontend** — `RegistrationButton.test.tsx`, `MyRegistrationsPage.test.tsx`.

## Definition of Done (verificable)

- [x] `make migrate` aplica `0004_create_registrations` sin errores; `\d registrations` muestra el unique parcial `WHERE status = 'CONFIRMED'`.
- [x] `POST /api/v1/events/{id}/registrations` por attendee en evento Published → 201; `confirmed_count` del evento post = previo + 1.
- [x] Segunda inscripción del mismo user → 409 `DUPLICATE_REGISTRATION`.
- [x] Speaker del evento intenta inscribirse → 409 `SPEAKER_CANNOT_REGISTER`.
- [x] Inscripción en evento `DRAFT` (o cualquier estado no Published) → 409 `INVALID_REGISTRATION_STATE`.
- [x] `capacity=1`, ya hay 1 confirmed → 409 `EVENT_FULL`.
- [x] Owner del evento puede inscribirse a su propio evento Published → 201.
- [x] `DELETE /api/v1/events/{id}/registrations/me` cuando hay activa → 204; row queda `CANCELLED`.
- [x] Re-inscripción tras cancelar → 201 con nueva fila CONFIRMED; la fila vieja queda CANCELLED.
- [x] `POST /api/v1/events/{id}/transition` para `Published → Cancelled` cancela todas las Registrations activas en una sola transacción.
- [x] `EventRead` expone `confirmed_count`, `is_full`, `my_registration_status` (`null` sin auth).
- [x] `EventListItem` expone `confirmed_count` y `is_full`; el listado público no produce N+1.
- [x] **Test del contrato bajo "Regla de Oro"**: con `capacity=1`, segunda inscripción tras la primera confirmada → 409 `EVENT_FULL`. El test con `threading.Barrier(2)` queda diferido a CI con Postgres real.
- [x] Frontend: `/events/:id` muestra `<RegistrationButton />` reactivo a `(auth, status, is_full, my_registration_status)`.
- [x] Frontend: tras inscribirse, el badge del conteo se refresca sin reload; tras cancelar, vuelve a aparecer "Inscribirme".
- [x] Frontend: `/me/registrations` lista historial con event embebido y badge de estado.
- [x] `make test` verde (back + front).

## No hacer en Fase 5 (anti-scope-creep)

- ❌ Lista de espera (Waitlist).
- ❌ Inscripción **por sesión**. Fase 5 inscribe al evento.
- ❌ Endpoint admin de listar inscritos del evento. Backlog.
- ❌ Emails de confirmación / tickets / QR / pagos / asignación de asientos.
- ❌ Cron de cancelación de no-shows o de transición automática.
- ❌ "Soft delete"/restauración de Registrations canceladas — el patrón es crear fila nueva.
- ❌ Auditoría/historial de cambios de status (`registration_status_log`).
- ❌ Permitir inscripción en `IN_PROGRESS` / `FINISHED` / `CANCELLED`.
- ❌ Cambiar el patrón actual de mutaciones (`with transactional()`).

## Salida

Un usuario abre el detalle de un evento Published, ve el conteo y un botón "Inscribirme". Al hacer click, queda confirmado y el botón cambia a "Cancelar mi inscripción". Si la capacidad llega al límite, el botón muestra "Cupo lleno". Al cancelar el evento, las inscripciones se marcan `CANCELLED` en una sola transacción atómica. La página `/me/registrations` lista el historial completo. **El MVP está cerrado end-to-end.**
