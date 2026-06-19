# Catálogo canónico de códigos de error

Todos los códigos siguen el shape canónico `{ error: { code, message, details } }` definido en [`api.md`](api.md#shape-de-error-canónico).

Cada subclase de `DomainError` en `backend/app/core/errors.py` produce automáticamente este shape vía el handler global. El frontend mapea cada `code` a un mensaje UX legible en `src/api/errors.ts`.

## Tabla de códigos (16 activos)

| Código | HTTP | Caso | Introducido en |
|---|---|---|---|
| `AUTH_INVALID_CREDENTIALS` | 401 | Login con email/password incorrectos | Fase 1 |
| `AUTH_TOKEN_EXPIRED` | 401 | JWT vencido o inválido | Fase 1 |
| `FORBIDDEN` | 403 | Rol/ownership insuficiente para la operación | Fase 1 |
| `NOT_FOUND` | 404 | Recurso inexistente | Fase 1 |
| `VALIDATION_ERROR` | 422 | Payload no cumple el schema | Fase 1 |
| `USER_ALREADY_EXISTS` | 409 | Registro con email ya existente | Fase 1 |
| `EVENT_NOT_MUTABLE` | 409 | Edición/borrado intentado sobre un evento que no está en `Draft` | Fase 2 |
| `INVALID_TRANSITION` | 409 | Transición de estado de evento no permitida | Fase 3 |
| `SESSION_OUT_OF_RANGE` | 409 | Sesión fuera del marco temporal del evento padre | Fase 4 |
| `SESSION_OVERLAP` | 409 | Solapamiento horario del mismo `speaker_id` (global) | Fase 4 |
| `SESSION_CAPACITY_EXCEEDS_EVENT` | 409 | Capacidad de sesión mayor que la del evento padre | Fase 4 |
| `EVENT_CAPACITY_BELOW_SESSION` | 409 | PATCH del evento reduce `capacity` por debajo de alguna sesión existente | Fase 4 |
| `EVENT_FULL` | 409 | Inscripción rechazada por capacidad llena (Regla de Oro) | Fase 5 |
| `DUPLICATE_REGISTRATION` | 409 | Inscripción activa ya existe para `(user, event)` | Fase 5 |
| `SPEAKER_CANNOT_REGISTER` | 409 | Speaker del evento intenta inscribirse como asistente | Fase 5 |
| `INVALID_REGISTRATION_STATE` | 409 | Intento de inscripción en evento que no está `Published` | Fase 5 |

## Códigos planificados (no activos)

| Código | HTTP | Caso | Estado |
|---|---|---|---|
| `AUTH_RATE_LIMIT` | 429 | Demasiados intentos en `/auth/*` | Backlog post-MVP — ver [ADR-005](decisions/005-phase-6-scope-cuts.md) |

## Cómo añadir un código nuevo

1. **Backend** — añadir clase en `app/core/errors.py`:
   ```python
   class MyNewError(DomainError):
       code = "MY_NEW_ERROR"
       status_code = 409
       message = "Mensaje en español para debugging"
   ```
   El handler global lo serializa automáticamente al shape canónico.

2. **Frontend** — añadir entrada en `frontend/src/api/errors.ts::MESSAGES`:
   ```typescript
   MY_NEW_ERROR: 'Mensaje legible para el usuario en español',
   ```

3. **Documentación** — añadir fila a la tabla de arriba con `HTTP`, caso, y fase de introducción.

4. **Lanzar** — desde el servicio que detecte la condición:
   ```python
   raise MyNewError(details={"context_key": value})
   ```

## Convención de `details`

- Siempre incluir el `id` del recurso afectado cuando aplique.
- Incluir información que ayude al cliente a actuar (ej. `event_id`, `current_status`, `reason`).
- Datos legibles para máquinas (snake_case en claves, valores planos sin nesting profundo).
- **No** incluir información sensible (passwords, tokens, datos de otros usuarios).

Ejemplo:
```json
{
  "error": {
    "code": "INVALID_TRANSITION",
    "message": "Transición de estado no permitida",
    "details": {
      "event_id": 42,
      "from_status": "DRAFT",
      "to_status": "IN_PROGRESS",
      "reason": "transition not allowed"
    }
  }
}
```
