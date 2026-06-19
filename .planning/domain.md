# Dominio y reglas de negocio

## Contexto

**Objetivo:** Aplicación web Full Stack para digitalizar la gestión manual de eventos (inscripciones, horarios, recursos, ponentes y asistentes).

**Entidades clave:** `Event` (con estados y capacidad), `EventSession` (con ponentes y validación de horarios), `User` (autenticación y roles) e `Registration`.

## Entidades

### Usuario (`User`)

Es cualquier persona que interactúa con la plataforma. Control de acceso basado en roles (RBAC) con **3 roles globales**:

- **`ATTENDEE`** (rol por defecto): puede navegar por la lista de eventos, ver detalles, registrarse en eventos con cupo disponible y gestionar su perfil.
- **`ORGANIZER`**: hereda permisos de Attendee. Crea, edita y gestiona **sus propios** eventos y sesiones.
- **`ADMIN`**: control total. Puede modificar cualquier evento y (en backlog post-MVP) gestionar perfiles y asignar roles.

**Ponente (`Speaker`)** — **NO es un rol global**. Es un **atributo derivado por evento**:
- Un usuario es ponente de un evento E si está asignado como `EventSession.speaker_id` de alguna sesión de E.
- Hereda los permisos de Attendee. **Su presencia en una sesión no consume cupo.**
- Un mismo usuario puede ser ponente en el evento A y asistente en el evento B sin fricción.
- Ver [ADR-003: speaker como atributo derivado](decisions/003-speaker-as-derived.md).

### Evento (`Event`)

Unidad principal de valor. Representa un acontecimiento planificado (conferencias, talleres, etc.).

- **Atributos:** título, descripción, ubicación (física o virtual), fecha de inicio/fin, capacidad.
- **Estados:** `Draft → Published → InProgress → Finished` con bifurcación `Cancelled`. Ver [Máquina de estados](#máquina-de-estados-del-evento).
- **Regla de Oro:** límite estricto de capacidad. No se permiten registros si el aforo está al 100%. Ver Fase 5 y [ADR-004](decisions/004-sqlite-vs-postgres-locks.md).

### Sesión (`EventSession`)

Bloque de actividad dentro de un evento (panel, taller, charla).

- **Asignación de Ponente:** cada sesión cuenta con un `speaker_id` (FK a `User`).
- **Validación de horarios:** la sesión cae dentro del marco temporal del evento padre. Dos sesiones con el mismo ponente **no pueden cruzarse en el tiempo a lo largo de todo el catálogo activo** (sesiones de eventos `Cancelled` se ignoran).
- **Capacidad de Sala:** opcional. Si presente, debe ser `≤ event.capacity`.

### Inscripción (`Registration`)

Acto formal y transaccional mediante el cual un usuario asegura su participación en un evento publicado.

- **Control de unicidad:** un usuario solo puede tener **una inscripción activa por evento**. Implementado vía índice UNIQUE parcial: `UNIQUE(user_id, event_id) WHERE status = 'CONFIRMED'`.
- **Estados (MVP):** `CONFIRMED` (cupo asegurado) y `CANCELLED` (el usuario libera su cupo). **Lista de Espera fuera del scope del MVP** (en backlog).
- **Re-inscripción** permitida tras cancelar: la fila vieja queda `CANCELLED`, se crea una nueva `CONFIRMED`.
- **Cascada del evento:** al cancelar un evento `Published`, todas sus inscripciones activas pasan a `CANCELLED` en una sola transacción atómica.

## Matriz de relaciones conceptuales

- Un `User` (Organizer) crea y es dueño de muchos `Event`.
- Un `Event` se compone de una o muchas `EventSession` cronológicas.
- Un `User` (cualquiera) puede ser asignado como ponente vía `EventSession.speaker_id`, sin requerir rol especial.
- Un `User` genera una `Registration` para asistir a un `Event` (las inscripciones se hacen **al evento**, no a sesiones individuales).

## Máquina de estados del evento

Máquina de estados: `Draft → Published → InProgress → Finished` con bifurcación `Cancelled`. Transiciones controladas por rol.

### Matriz de transiciones permitidas

| From → To              | Quién dispara          | Condición                                  |
|------------------------|------------------------|--------------------------------------------|
| Draft → Published      | Organizer (dueño)/Admin| `capacity > 0` y datos básicos completos   |
| Published → InProgress | Organizer (dueño)/Admin| `now >= event.start_at` (disparo manual)   |
| InProgress → Finished  | Organizer (dueño)/Admin| `now >= event.end_at` (disparo manual)     |
| Draft → Cancelled      | Organizer/Admin        | Siempre permitido                          |
| Published → Cancelled  | Organizer/Admin        | Cancela y libera todas las inscripciones (cascada) |
| Finished/Cancelled → * | —                      | Bloqueado (estados terminales)             |

- Endpoint: `POST /api/v1/events/{id}/transition { "to_status": "Published" }`.
- Cualquier transición no listada retorna error `INVALID_TRANSITION`.
- Cron automático para `Published → InProgress → Finished` queda en backlog post-MVP.
- Ver [ADR-002: matriz declarativa](decisions/002-state-machine-matrix.md) para la justificación del diseño.

## Reglas de negocio críticas

### Regla de Oro (Capacidad bajo concurrencia)

- **Invariante:** `count(Registration con status='CONFIRMED') <= event.capacity`.
- **Estrategia:** lock pesimista (`SELECT ... FOR UPDATE`) en el `EventRepository.get_for_update` dentro del servicio de inscripción.
- **Limitación de tests:** SQLite no soporta `FOR UPDATE`, así que el contrato se verifica secuencialmente. Postgres real cubre concurrencia bajo carga. Ver [ADR-004](decisions/004-sqlite-vs-postgres-locks.md).

### No solapamiento de speaker (global)

- **Invariante:** dos sesiones activas con el mismo `speaker_id` no se cruzan en el tiempo, sin importar el evento.
- **Excepción:** sesiones de eventos en estado `CANCELLED` no cuentan.
- **Implementación:** `EventSessionRepository.find_speaker_overlap` con JOIN a `events` y filtro `status != CANCELLED`.

### Speaker no se inscribe como asistente

- Si un usuario es speaker de **cualquier** sesión del evento, no puede generar una `Registration` activa para ese evento (`SPEAKER_CANNOT_REGISTER`, 409).
- Evita doble conteo semántico (speaker no consume cupo + inscrito sí).

### Capacidad sesión/evento

- `session.capacity` es opcional (`NULL` permitido).
- Si presente: `session.capacity <= event.capacity`.
- **Bidireccional:** un `PATCH /events/{id}` que reduzca `capacity` por debajo del aforo de alguna sesión existente → 409 `EVENT_CAPACITY_BELOW_SESSION`.

## Aclaraciones operativas

1. El speaker no se registra ni consume cupo. Su asignación a `EventSession.speaker_id` es la presencia implícita.
2. El capacity counter solo cuenta `Registration` confirmadas → los speakers quedan fuera automáticamente.
3. Validación clave: prohibir que un speaker tenga también `Registration` activa al mismo evento (evita doble conteo semántico — rechaza inscripción).
4. Referenciar el rol Ponente como atributo permite modelar mejor casos donde un user es speaker en un evento y asistente en otro, sin fricción.
5. Capacidad bajo concurrencia: la "Regla de Oro" exige no superar aforo. Estrategia con lock pesimista.
6. Transición de estados: máquina declarada con matriz de transiciones permitidas (quién las dispara y bajo qué condición).
7. Mantener simplicidad — evitar agregar funcionalidades fuera del alcance acordado.
