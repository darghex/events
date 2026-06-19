# ADR-005: Scope reducido de Fase 6 — rate-limit y logging JSON al backlog

**Fecha:** Fase 6.
**Estado:** Aceptado.

## Contexto

El spec original de Fase 6 ("Hardening transversal") incluía 7 ítems:

1. Auditar handler global de excepciones.
2. **Logging JSON** + middleware `X-Request-ID`.
3. **Rate-limit `slowapi`** en `/auth/*`.
4. CORS configurado.
5. READMEs (backend, frontend).
6. Cobertura ≥ 80% backend / ≥ 70% frontend (gate).
7. Revisión final de OpenAPI.

Al evaluar el esfuerzo de cada ítem contra el valor entregado pre-entrega, surgió la pregunta: **¿qué es estrictamente necesario para que un evaluador externo pueda hacer la demo del MVP, y qué es "hardening que se ve bien pero no se demuestra en 5 minutos"?**

### Análisis por ítem

| Ítem | ¿Bloquea demo MVP? | Esfuerzo | Valor pre-entrega |
|---|---|---|---|
| 1. Auditar handler global | No (ya existe desde Fase 1) | Bajo | Alto (red de seguridad) |
| 2. **Logging JSON + X-Request-ID** | No | Medio (~1 día) | Bajo (no se ve en demo) |
| 3. **Rate-limit `slowapi`** | No | Alto (Redis para distribuido) | Bajo (no se ve en demo manual) |
| 4. CORS | Sí (frontend → backend desde browser) | Bajo | Alto |
| 5. READMEs | Sí (evaluador externo) | Bajo | Muy alto |
| 6. Coverage gate | No (la suite ya pasa) | Bajo | Alto (protege regresiones) |
| 7. OpenAPI metadata | No (pero profesionaliza `/docs`) | Bajo (~15 min) | Alto |

### Riesgos específicos del rate-limit

- Requiere `slowapi` + storage. Para single-instance, in-memory basta. Para producción distribuida (múltiples replicas detrás de un LB), **necesita Redis** o equivalente.
- Añadir Redis a `docker-compose.yml` introduce un servicio más (otra healthcheck, otro volumen, otra dependencia para `make up`).
- Sin Redis, el rate-limit no protege en producción real → es teatro de seguridad.

### Riesgos específicos del logging JSON

- Añade dependencia (`python-json-logger` o `structlog`).
- Requiere configurar un middleware (`X-Request-ID`) que use `contextvars` para propagar el `request_id` al logger.
- El stdlib `logging` actual ya emite a stderr y el handler global ya formatea errores estructurados. La diferencia entre eso y JSON estructurado es **invisible en la demo manual** y solo importa en infra de observabilidad real (ELK, Datadog, etc.) — que no existe en este MVP.

## Decisión

**Mover al backlog post-MVP:**
- Rate-limit `slowapi`.
- Logging JSON estructurado + middleware `X-Request-ID`.

**Conservar** en Fase 6:
- Auditoría del handler global.
- CORS desde env.
- READMEs (3 archivos).
- Coverage gate (back ≥80%, front ≥70%).
- OpenAPI metadata.

**Mantener** los placeholders `AUTH_RATE_LIMIT` y `LOG_LEVEL` comentados en `.env.example` para señalar la deuda explícita.

Actualizar [`backlog.md`](../backlog.md) con justificación corta para cada ítem movido.

## Consecuencias

**Positivas:**
- **Fase 6 cierra en horas, no días**. El MVP llega más rápido a manos del usuario.
- Demo MVP sigue siendo completa: el evaluador hace todo el flow sin notar la ausencia de rate-limit o logs JSON.
- READMEs y OpenAPI **sí** se notan inmediatamente y elevan la percepción de calidad del entregable.
- Coverage gate protege regresiones en las próximas iteraciones.
- Sin Redis en `docker-compose.yml`: `make up` sigue siendo 3 servicios.

**Negativas:**
- **Brecha de seguridad en producción**: sin rate-limit, los endpoints `/auth/*` son vulnerables a credential stuffing. Mitigación: el MVP es para demo, no producción.
- **Brecha de observabilidad**: sin logging JSON y request-id, debuggear un problema en producción real es más difícil. Mitigación: el MVP no tiene infra de observabilidad montada.
- La deuda queda explícita en el backlog y en el `.env.example`, lo cual sirve para futuros milestones.

**Mitigación:** ambos ítems están en el backlog con la justificación correspondiente y los placeholders en `.env.example` son recordatorios visibles.
