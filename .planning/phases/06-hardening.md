# Fase 6 — Hardening transversal (pre-entrega)

**Meta:** Endurecer puntos de entrada (CORS), garantizar gate de cobertura, profesionalizar la API (OpenAPI)

## Pre-requisitos de fase anterior

- Fases 1-5 cerradas. MVP funcional end-to-end. Handler global de excepciones ya existe (`app/core/exception_handlers.py`) desde Fase 1 — aquí se audita y completa.

## Variables de entorno requeridas

- Ninguna nueva. Reutiliza `CORS_ORIGINS` (CSV) que ya estaba como placeholder en `.env.example`. `AUTH_RATE_LIMIT` y `LOG_LEVEL` permanecen comentadas como placeholders para los ítems de backlog.

## Decisiones materiales fijadas para esta fase

1. **Scope reducido**: `Rate-limit (slowapi)` y `Logging JSON estructurado + middleware X-Request-ID` se mueven al **Backlog post-MVP**. Ver [ADR-005](../decisions/005-phase-6-scope-cuts.md).
2. **Logging library**: si más adelante se implementa, se prefiere `python-json-logger` sobre el stdlib `logging`.
3. **READMEs**: tres archivos — `README.md` (root), `backend/README.md`, `frontend/README.md`.
4. **Cobertura como gate**: `pytest --cov-fail-under=80` y `vitest --coverage` con thresholds 70%. Si la suite baja del umbral, falla el `make test`.
5. **OpenAPI**: añadir `title`, `description`, `version` a `FastAPI(...)`. Verificar que todos los routers tienen `tags=`.

## Pasos secuenciales (el orden importa)

1. **Auditar handler global de excepciones** — verificar que mapea todos los códigos del catálogo (16 a fin de Fase 5). Confirmar que toda `DomainError` se transforma al shape canónico. La cobertura se verifica indirectamente vía los tests de endpoints de Fases 1-5 (cada error se gatilla al menos una vez).

2. **CORS**
   - `app/core/config.py`: parser de `CORS_ORIGINS` (CSV) → `list[str]`. Default: `["http://localhost:5173"]` cuando la env está vacía.
   - `app/main.py`: añadir `CORSMiddleware` con `allow_origins=settings.cors_origins_list`, `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`.

3. **OpenAPI metadata**
   - `app/main.py`: `FastAPI(title="Mis Eventos API", description=API_DESCRIPTION, version="0.6.0")`.
   - Confirmar que cada router incluye `tags=[...]` con nombres consistentes (`auth`, `events`, `event-sessions`, `registrations`, `users`, `me`).

4. **Coverage gate**
   - **Backend**: `makefile::test-back` → `pytest --cov=app --cov-fail-under=80`.
   - **Frontend**: `vite.config.ts` → `test.coverage.thresholds: { lines: 70, functions: 70, branches: 70, statements: 70 }`, `test.coverage.provider: "v8"`. Scope a `src/{components,hooks,lib,stores}` (api/* y pages/* tienen tests indirectos).
   - +`@vitest/coverage-v8` como devDependency.

8. **Mover rate-limit + logging al backlog** — Reescribir [`backlog.md`](../backlog.md) para incluir ambos con justificación. Conservar `AUTH_RATE_LIMIT` y `LOG_LEVEL` como placeholders en `.env.example`.

## Definition of Done (verificable)

- [x] `make up` levanta los 3 servicios sanos.
- [x] `/docs` muestra los 6 grupos de endpoints (auth, events, event-sessions, registrations, users, me) con `title`/`description`/`version` no-defaults.
- [x] Handler global mapea TODOS los `DomainError` al shape canónico. Cobertura verificada **indirectamente** vía los tests de endpoints de Fases 1-5.
- [x] CORS configurado vía `CORS_ORIGINS` (CSV → `cors_origins_list`) y aplicado por `CORSMiddleware`. Verificación manual desde el frontend en `localhost:5173`; auto-test diferido al backlog.
- [x] `make test-back` falla si la cobertura backend baja de 80% (actualmente ~98%).
- [x] `make test-front` falla si la cobertura frontend baja de 70% (actualmente ~86%).
- [x] `Rate-limit` y `Logging JSON / X-Request-ID` aparecen explícitamente en `backlog.md` con justificación.
- [x] `make test` (back + front) verde con cobertura ≥ 80% / ≥ 70%.

## No hacer en Fase 6 (anti-scope-creep)

- ❌ **Rate-limit `slowapi`** → backlog (no bloquea MVP; producción distribuida prefiere Redis).
- ❌ **Logging JSON + middleware `X-Request-ID`** → backlog (suficiente con stdlib + handler global para MVP).
- ❌ Auth refresh con cookies httpOnly server-side.
- ❌ Logout server-side / blacklist de tokens.
- ❌ Profile admin endpoints (`PATCH /users/{id}/status|role`).
- ❌ Cron de transición automática.
- ❌ E2E tests con Playwright.
- ❌ CI/CD pipeline (GitHub Actions, etc.).
- ❌ Imágenes Docker prod multi-stage optimizadas (las dev sirven para demo).
- ❌ Lista de espera (Waitlist).

## Salida

Repo listo para entregar. Un evaluador clona, copia `.env.example` → `.env`, ejecuta `make up`, y en menos de 5 minutos puede recorrer la demo end-to-end leyendo solo el `README.md`. `/docs` se ve profesional. `make test` corre back+front con gates de cobertura. Rate-limit, logging JSON y X-Request-ID quedan documentados como deuda explícita en el backlog.
