# Backlog post-MVP

Ítems explícitamente fuera del alcance del MVP. No bloquean la entrega, pero son los siguientes candidatos cuando el MVP esté validado.

## Seguridad / hardening operativo

- **Rate-limit `slowapi`** en `/api/v1/auth/*` con default `5/minute` (env `AUTH_RATE_LIMIT`). En producción distribuida usar storage Redis. Movido desde Fase 6 para no inflar el alcance del MVP (ver [ADR-005](decisions/005-phase-6-scope-cuts.md)).
- **Logging JSON estructurado** (`python-json-logger`) + middleware `X-Request-ID` que propaga `request_id` a logs y response. Env `LOG_LEVEL`. Movido desde Fase 6 (ver [ADR-005](decisions/005-phase-6-scope-cuts.md)).
- **Logout server-side** (blacklist de tokens via Redis o tabla `revoked_tokens`).
- **Refresh tokens en cookies httpOnly** (hoy fallback en `localStorage`).

## Funcionalidad de producto

- **Profile admin endpoints:**
  - `PATCH /users/{id}/status` — activar / desactivar cuentas.
  - `PATCH /users/{id}/role` — promover/demover roles.
- **Lista de espera** (`Registration.status = Waitlist` + promoción FIFO al cancelar inscripción confirmada). Modela una situación realista de eventos populares.
- **Endpoint admin de listado de inscritos:** `GET /events/{id}/registrations` (organizer/admin).
- **Cron de transición automática** `Published → InProgress → Finished` basada en `now >= start_at / end_at`.
- **Inscripción por sesión** (hoy se inscribe al evento, no a sesiones individuales).
- **Múltiples speakers por sesión** (hoy 1-a-1 vía `speaker_id`).

## Comunicaciones

- **Emails transaccionales:** confirmación de inscripción, recordatorio pre-evento, notificación de cancelación del evento.
- **Notificación al speaker** cuando lo asignan a una sesión.
- **Tickets / códigos QR** para asistencia.
- **Exportar agenda** a ICS / Google Calendar.

## Frontend

- **Optimizaciones de bundle:** lazy loading de rutas (`React.lazy`), WebP para imágenes, code-splitting por feature.
- **Drag-and-drop** para reordenar agenda visual.
- **Mejora de a11y** (audit con axe-core).
- **Internacionalización (i18n)** — hoy mensajes hardcoded en español.

## Testing / infraestructura

- **E2E con Playwright:** flujo MVP completo (login → crear evento → inscribir → cancelar).
- **Test de concurrencia con Postgres real en CI** para "Regla de Oro" (SQLite no soporta `SELECT FOR UPDATE` — ver [ADR-004](decisions/004-sqlite-vs-postgres-locks.md)).
- **CI/CD pipeline** (GitHub Actions: lint + test + build + coverage upload).
- **Imágenes Docker producción multi-stage** optimizadas (hoy las dev sirven para demo).
- **Cobertura del catálogo de errores con test parametrizado** (eliminado del MVP — los códigos se cubren indirectamente via tests de endpoints).
- **Auditoría / historial de cambios** (tablas `event_status_log`, `registration_status_log`).

## Multi-tenancy y escala

- **Soft-delete** con `deleted_at` para auditoría.
- **Búsqueda full-text** en eventos (Postgres `tsvector`).
- **Filtros avanzados** (rango de fechas, ubicación geográfica, categorías).
- **Tags / categorías de evento**.

## Reglas del flujo entre fases

- Cada fase cierra con: **migración aplicada + tests verdes + cobertura no baja + demo manual ok**.
- Si una fase descubre un cambio en otra ya cerrada, se vuelve a tocar esa fase (no se acumula deuda).
- Commits con prefijo `feat:`, `test:`, `refactor:`, etc. para trazabilidad (convención Semantic).
- **NO autocommitear**: los commits los realiza el desarrollador directamente.
