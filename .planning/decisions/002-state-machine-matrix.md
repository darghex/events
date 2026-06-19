# ADR-002: Matriz declarativa para máquina de estados del evento

**Fecha:** Fase 3.
**Estado:** Aceptado.

## Contexto

La Fase 3 introduce una máquina de estados de 5 nodos (`Draft, Published, InProgress, Finished, Cancelled`) con 5 transiciones válidas. Cada transición tiene:
- **RBAC**: quién puede dispararla (`allowed_roles`).
- **Ownership**: ¿requiere ser owner del evento?
- **Condición temporal**: ej. `now >= event.start_at` para `Published → InProgress`.
- **Side-effects**: ej. cascada a `Registration` en `Published → Cancelled` (Fase 5).

Alternativas evaluadas:

- **A. Cadena de `if/elif`** dentro del servicio: rápido de escribir, mezcla declaración con ejecución. Crece a 50+ líneas. Difícil de testear celda-por-celda.
- **B. Tabla declarativa** (`dict[(from, to), TransitionRule]`) en módulo dedicado: separa "qué" (matriz) de "cómo" (servicio). El servicio solo busca la regla y la ejecuta.
- **C. Librería como `transitions` o `python-statemachine`**: más capacidad (estados anidados, history, guards encadenados), pero overkill para 5 estados.

## Decisión

Tabla declarativa en `app/services/event_state.py`:

```python
@dataclass(frozen=True)
class TransitionRule:
    allowed_roles: frozenset[UserRole]
    requires_ownership: bool
    validator: Callable[[Event, datetime], None]


TRANSITIONS: dict[tuple[EventStatus, EventStatus], TransitionRule] = {
    (DRAFT, PUBLISHED): TransitionRule(
        allowed_roles=_OWNER_OR_ADMIN, requires_ownership=True, validator=_check_publishable
    ),
    (PUBLISHED, IN_PROGRESS): TransitionRule(
        allowed_roles=_OWNER_OR_ADMIN, requires_ownership=True, validator=_check_can_start
    ),
    # ...
}
```

El servicio `EventService.transition` busca `TRANSITIONS[(event.status, to_status)]`. Si no existe → `INVALID_TRANSITION`. Si existe, valida rol/ownership y ejecuta `rule.validator(event, now_utc())`.

## Consecuencias

**Positivas:**
- **Lectura inmediata**: la matriz refleja exactamente la tabla del CLAUDE.md / `domain.md`.
- **Añadir transición = 1 entrada en el dict + 1 validator**. Cero modificación del servicio.
- **Tests granulares**: una prueba por celda (5 permitidas + N bloqueadas) sin condicionales anidados.
- **Validators reutilizables** (`_no_op`, `_check_publishable`, etc.).
- **El frontend tiene matriz espejo** (`src/lib/eventTransitions.ts`) con la misma estructura para renderizar botones contextuales sin duplicar la lógica de backend.

**Negativas:**
- Dos archivos en lugar de uno (`event.py` + `event_state.py`).
- Pequeña indirección al leer el código (el lector salta del servicio a la matriz y al validator).

**Mitigación:** el módulo `event_state.py` es chico (~100 líneas) y self-contained.
