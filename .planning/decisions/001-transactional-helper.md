# ADR-001: Helper `transactional()` en vez de `with session.begin()`

**Fecha:** Fase 2 (consolidado).
**Estado:** Aceptado.

## Contexto

La convención original del proyecto pedía abrir transacciones en la capa de servicio mediante `with session.begin():`, siguiendo el patrón clásico de SQLAlchemy.

Al intentarlo, los tests fallaron con:

```
sqlalchemy.exc.InvalidRequestError: A transaction is already begun on this Session.
```

**Causa raíz:** SQLAlchemy 2.x usa **autobegin** (la tx se inicia al primer I/O). El dependency `get_current_user` ejecuta `session.get(User, ...)` ANTES de que se invoque el servicio, lo que dispara autobegin. Cuando el servicio luego intenta `session.begin()`, SA 2.x lo rechaza porque ya hay una tx activa.

Alternativas evaluadas:

- **A. Status quo + actualizar doc**: usar `session.commit()` directo, actualizar la convención. 0 código, pierde el "marcador visual" de inicio de tx.
- **B. Helper `transactional()`** (elegida): wrapper propio que hace commit/rollback explícito y mantiene la legibilidad del `with`.
- **C. Unit-of-Work a nivel de dependency**: mover el `with begin()` a `get_session()`. Requiere `autobegin=False` global y refactor cross-cutting. Sobre-arquitectura para MVP.

## Decisión

Helper en `app/db/session.py` (~10 líneas):

```python
@contextmanager
def transactional(session: Session) -> Iterator[None]:
    """Commit al salir limpio, rollback ante excepción. Compatible con autobegin."""
    try:
        yield
        session.commit()
    except Exception:
        session.rollback()
        raise
```

Uso en servicios:

```python
def create(self, *, actor, data):
    if actor.role not in {...}:
        raise Forbidden(...)
    with transactional(self.session):
        event = self.events.create(...)
    self.session.refresh(event)
    return event
```

Aplicado en `services/{auth,event,event_session,registration}.py` y `db/seed.py`.

## Consecuencias

**Positivas:**
- Sintaxis legible: `with transactional(session):` marca claramente el límite atómico.
- Defensa-en-profundidad: rollback explícito antes del re-raise (no depende solo del cleanup de `get_session`).
- Compatible con autobegin de SA 2.x.
- Self-documenting: un junior lee `update()` y ve dónde empieza/termina la transacción.
- **Crítico para Fase 5**: el `SELECT ... FOR UPDATE` y la cascada de cancelación viven visiblemente dentro del bloque atómico.

**Negativas:**
- Una abstracción más en el stack (+7 líneas).
- Diverge de la documentación oficial de SQLAlchemy (que usa `session.begin()` directo).

**Mitigación:** documentar el patrón en `backend/CLAUDE.md` y mantener la decisión registrada aquí.
