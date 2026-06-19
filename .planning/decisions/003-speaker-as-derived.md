# ADR-003: Speaker como atributo derivado, no como rol

**Fecha:** Fase 0 (consolidado en Fase 4).
**Estado:** Aceptado.

## Contexto

En la mayoría de plataformas de eventos, "Ponente" (`Speaker`) parece un rol natural: un usuario es speaker, otro es asistente. Sin embargo, en la práctica:

- Un mismo usuario puede ser **ponente en el evento A** y **asistente en el evento B** sin fricción.
- Asignar un rol global "SPEAKER" significaría que pierde la posibilidad de inscribirse a otros eventos, o que necesita lógica especial.
- Hay usuarios que son organizadores en su empresa y, ocasionalmente, ponentes en eventos de terceros.

Alternativas evaluadas:

- **A. Rol global `SPEAKER`** además de `ATTENDEE`/`ORGANIZER`/`ADMIN`. Simple en un nivel, pero introduce ambigüedad: ¿qué hace un SPEAKER que no es organizer ni asistente? ¿Puede inscribirse a otros eventos?
- **B. Atributo derivado por evento** (elegida): un usuario es "speaker de E" si está asignado vía `EventSession.speaker_id` en alguna sesión de E.
- **C. Tabla puente `EventSpeaker`** explícita: mismo efecto que B pero con una tabla N:M extra. Útil si quisiéramos múltiples speakers por sesión (no es MVP).

## Decisión

Sin rol global `SPEAKER`. RBAC global queda con **3 roles**: `ADMIN`, `ORGANIZER`, `ATTENDEE`.

El atributo "speaker" se deriva por evento:

```python
def is_speaker_of_event(self, *, user_id: int, event_id: int) -> bool:
    """True si el user está asignado como speaker en al menos una sesión del evento."""
    stmt = (
        select(EventSession.id)
        .where(EventSession.event_id == event_id)
        .where(EventSession.speaker_id == user_id)
        .limit(1)
    )
    return self.session.exec(stmt).first() is not None
```

Reglas de negocio derivadas:

1. **Cualquier User puede ser asignado a `EventSession.speaker_id`** (sin requerir rol especial). FK con `ON DELETE RESTRICT`.
2. **Speaker no consume cupo**: el counter de `Registration` solo cuenta status `CONFIRMED`. El speaker no tiene fila de registration.
3. **Speaker no puede inscribirse al mismo evento**: si `is_speaker_of_event(actor, event)` → 409 `SPEAKER_CANNOT_REGISTER`. Evita doble conteo semántico (presencia implícita + presencia explícita).
4. **El mismo user puede ser speaker en E1 y asistente en E2** sin restricciones cruzadas.

## Consecuencias

**Positivas:**
- Modelo de roles minimalista (3 valores) — más fácil de razonar y testear.
- Flexibilidad real: refleja cómo funcionan los humanos en eventos.
- **No requiere migración de roles** si un asistente alguna vez es invitado como speaker.
- La regla "speaker no se inscribe" queda en un solo lugar (servicio de Registration) y es testeable con un caso claro.
- "Backlog/admin crea cuenta para el speaker" no requiere endpoint especial: cualquier User registrado vale.

**Negativas:**
- Requiere educación para colaboradores nuevos (no es el patrón "obvio" en booking platforms).
- La derivación requiere una query (`is_speaker_of_event`) en el flow de Registration. Trivial.
- Si en post-MVP queremos "permisos especiales del speaker" (subir slides, ver attendee list de sus sesiones), habrá que derivarlos también — no es problema bloqueante.

**Mitigación:** documentado prominentemente en `domain.md` y en el catálogo de errores con el código `SPEAKER_CANNOT_REGISTER`.
