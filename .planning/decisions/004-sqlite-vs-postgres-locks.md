# ADR-004: SQLite no soporta `SELECT FOR UPDATE` — test de concurrencia diferido

**Fecha:** Fase 5.
**Estado:** Aceptado con deuda explícita.

## Contexto

La Fase 5 implementa la "Regla de Oro": un evento no excede su aforo bajo concurrencia. La estrategia es **lock pesimista** en el servicio de inscripción:

```python
def register(self, *, actor, event_id):
    with transactional(self.session):
        event = self.events.get_for_update(event_id)  # SELECT ... FOR UPDATE
        # ... chequeos
        if count_confirmed(event_id) >= event.capacity:
            raise EventFull(...)
        self.registrations.create(...)
```

El plan inicial era verificar este contrato con un test de concurrencia:

```python
def test_concurrent_registrations_capacity_one(client, session):
    """Capacity=1, 2 inscripciones simultáneas vía threading.Barrier(2)
    → exactamente 1×201 + 1×409 EVENT_FULL."""
```

**Problema:** la suite usa SQLite con `StaticPool` para velocidad y aislamiento. **SQLite no implementa `SELECT FOR UPDATE`** — la cláusula `.with_for_update()` de SQLAlchemy se ignora silenciosamente. El resultado:

- Thread A: `count_confirmed=0`, INSERT (no commit).
- Thread B: `count_confirmed=0` (no ve la inserción pending de A), INSERT.
- Ambos commitean → **2 filas CONFIRMED para `capacity=1`**.

El test falla con `[201, 201]` en lugar de `[201, 409]`.

Alternativas evaluadas:

- **A. Cambiar a Postgres en CI**: refactor del conftest para usar Postgres + testcontainers o servicio externo. Más correcto, pero introduce dependencia infra y aumenta tiempo del CI.
- **B. Configurar SQLite con `BEGIN IMMEDIATE`**: SQLite permite lock por escritura desde el inicio de la tx. Pero con `StaticPool` (1 conexión), no se gana nada — las queries ya se serializan al nivel de conexión, no de tx.
- **C. Test secuencial + documentar deuda** (elegida): verificar el contrato del servicio (`count < capacity` + insert dentro de la misma tx) con un test secuencial. Documentar la limitación explícitamente y diferir el test de concurrencia real a CI con Postgres post-MVP.
- **D. Mock del lock**: instrumentar el servicio con `time.sleep` entre count y insert vía monkey-patch para reproducir la race. Ensucia el código de producción.

## Decisión

**Opción C.** Test secuencial verifica el contrato:

```python
def test_capacity_contract_enforced_sequentially(client, session):
    """Con capacity=1, la segunda inscripción rebota con EVENT_FULL."""
    ev = _insert_event(..., capacity=1)
    r1 = client.post(f"/api/v1/events/{ev.id}/registrations", headers=_auth(a1))
    assert r1.status_code == 201
    r2 = client.post(f"/api/v1/events/{ev.id}/registrations", headers=_auth(a2))
    assert r2.status_code == 409
    assert r2.json()["error"]["code"] == "EVENT_FULL"
```

Esto demuestra que el chequeo dentro del servicio (`confirmed_count < capacity`) funciona y el INSERT bloqueado retorna el error correcto. En Postgres real, `.with_for_update()` provee la garantía adicional bajo concurrencia.

Item de backlog: **"Test de concurrencia para Regla de Oro con Postgres real en CI"** (ver [`backlog.md`](../backlog.md)).

## Consecuencias

**Positivas:**
- **Honesto**: el código de producción no se ensucia para complacer al motor de tests.
- **Suite rápida**: SQLite + StaticPool sigue siendo ideal para iterar (131 tests en ~60s).
- **El contrato del servicio queda cubierto** — el caso secuencial demuestra que la lógica de capacidad funciona.
- La protección bajo concurrencia real (Postgres `FOR UPDATE`) está implementada en código; queda **probada por inspección** y se cubrirá con un test específico cuando se monte el CI con Postgres.

**Negativas:**
- **Brecha en testing**: si alguien modifica `register()` y rompe el lock (ej. quita `.with_for_update()`), los tests de SQLite siguen pasando. Mitigación: comentario explícito en el código + ADR.
- **Demo en SQLite engañosa**: si alguien hiciera demo de concurrencia con SQLite, podría ver el bug. Pero la suite oficial usa Postgres en runtime (docker-compose), donde el lock SÍ funciona.

**Mitigación documental:**
- Docstring extenso en `test_registrations_concurrency.py` explica la limitación.
- Comentario en `EventRepository.get_for_update` describe el comportamiento dual.
- Item explícito en `backlog.md` con la deuda.
