# Fase 1 — Auth & RBAC

**Meta:** Un usuario puede registrarse, loguearse, refrescar su sesión y consultar su perfil. RBAC con 3 roles operativo. El frontend tiene rutas protegidas.

## Variables de entorno requeridas (cierra los placeholders del `.env`)

- `JWT_SECRET` (obligatorio, sin default — falla startup si está vacío).
- `ACCESS_TOKEN_TTL_MINUTES=15`, `REFRESH_TOKEN_TTL_DAYS=7`.
- `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD` (sin defaults).

## Pasos secuenciales (el orden importa)

1. **Modelo `User` y enum de roles**
   - `app/models/user.py`: tabla `users` con columnas `id (PK)`, `email (unique, lowercase, indexed)`, `password_hash`, `role (Enum)`, `is_active (default true)`, `created_at`, `updated_at`.
   - Enum `UserRole`: **`ADMIN`, `ORGANIZER`, `ATTENDEE`** (3 valores; speaker NO es rol, es atributo contextual derivado de `EventSession.speaker_id`). Default DB: `ATTENDEE`.
   - Constraint: `CHECK (email = lower(email))`.

2. **Primera migración Alembic**
   - `alembic revision --autogenerate -m "create users table"`.
   - Conectar `target_metadata` en `alembic/env.py` (reemplazar el `None` de Fase 0).
   - `alembic upgrade head` en el startup del backend o como `make migrate`.

3. **Schemas Pydantic**
   - `UserCreate` (email + password con validator: ≥8, ≥1 mayús, ≥1 dígito).
   - `UserRead` (sin password_hash).
   - `LoginRequest`, `TokenPair { access, refresh, token_type: "bearer" }`, `RefreshRequest`.

4. **Core de seguridad (`app/core/security.py`)**
   - `hash_password(plain) -> str` / `verify_password(plain, hashed) -> bool` con `bcrypt` (cost ≥ 12).
   - `create_access_token(sub, role)` y `create_refresh_token(sub)` con claims `{ sub, role?, type: "access"|"refresh", exp, iat }`.
   - `decode_token(token, expected_type)` → rechaza si `type` no coincide (evita usar refresh como access).
   - Dependencies: `get_current_user` (lee `Authorization: Bearer`), `require_role(*roles)`.

5. **Repositorios y servicios**
   - `UserRepository.get_by_email`, `.create`.
   - `AuthService.register`, `.login`, `.refresh`. Transacciones se abren aquí (no en repo).

6. **Endpoints (`app/api/v1/auth.py`)**
   - `POST /api/v1/auth/register` → 201 `UserRead`. Email duplicado → 409 con `code: USER_ALREADY_EXISTS` (agregar al catálogo).
   - `POST /api/v1/auth/login` (JSON `{ email, password }`) → 200 `TokenPair`. Credenciales malas → 401 `AUTH_INVALID_CREDENTIALS`. Cuenta inactiva → 403 `FORBIDDEN`.
   - `POST /api/v1/auth/refresh` (JSON `{ refresh_token }`) → 200 nuevo `access_token`. Token inválido/expirado → 401 `AUTH_TOKEN_EXPIRED`.
   - `GET /api/v1/auth/me` (protegido) → 200 `UserRead`. Sin token → 401.

7. **Handler global de excepciones**
   - Middleware/exception handler que emite el shape canónico (`{ error: { code, message, details } }`).
   - Mapea `RequestValidationError` → `VALIDATION_ERROR` (422) preservando `details`.
   - Catálogo activo en esta fase: `AUTH_INVALID_CREDENTIALS`, `AUTH_TOKEN_EXPIRED`, `FORBIDDEN`, `NOT_FOUND`, `VALIDATION_ERROR`, `USER_ALREADY_EXISTS` (nuevo, 409).

8. **Seed admin idempotente**
   - Script `app/db/seed.py` ejecutable en startup (o vía `make seed`): si `SEED_ADMIN_EMAIL` no existe → crearlo con rol `ADMIN`. Si existe → no-op.
   - Falla rápido si las env vars `SEED_ADMIN_*` están vacías.

9. **Frontend — auth flow**
   - Dependencias nuevas: `react-router-dom`, `zustand`, `axios`, `@tanstack/react-query`.
   - `src/api/client.ts`: instancia Axios con `baseURL = VITE_API_BASE_URL`. Interceptor de request inyecta `Authorization: Bearer`. Interceptor de response: ante `error.code === "AUTH_TOKEN_EXPIRED"` llama a `/auth/refresh` una sola vez y reintenta; si vuelve a fallar, hace logout.
   - `src/stores/auth.ts` (Zustand): `{ user, accessToken, refreshToken, login(), logout(), setSession() }`. Persistir `refreshToken` en `localStorage` (documentado como fallback hasta cookies httpOnly).
   - Páginas: `LoginPage`, `RegisterPage`, `ProfilePage` (muestra `/auth/me`).
   - Router: `<Routes>` con `<RequireAuth>` HOC/wrapper que redirige a `/login` si no hay sesión.
   - Componentes UI reutilizables en `src/components/ui/`: `Input`, `Button`, `FormField`.

10. **Tests**
    - Backend:
      - Unit: `hash_password/verify_password`, encode/decode JWT (rechazar tipo cruzado), password policy validator.
      - Integration: register→login→/me happy path, login con creds malas, refresh válido e inválido, email duplicado, `require_role` deniega.
    - Frontend (Vitest + RTL):
      - `LoginPage` renderiza form y dispara `login()` en submit.
      - `RequireAuth` redirige a `/login` sin token.

## Definition of Done (verificable)

- [x] `make up` arranca con migración aplicada y admin sembrado (logs lo confirman).
- [x] `POST /api/v1/auth/register` con payload válido → 201; password no aparece en response ni en logs.
- [x] `POST /api/v1/auth/login` correcto → 200 con `access_token` + `refresh_token`; incorrecto → 401 con shape canónico.
- [x] `GET /api/v1/auth/me` con `Authorization: Bearer <access>` → 200 con el usuario; sin token → 401.
- [x] `POST /api/v1/auth/refresh` rota el access; intentar refrescar con un access en lugar de refresh → 401.
- [x] Admin sembrado puede loguearse; `GET /me` reporta `role: "ADMIN"`.
- [x] Frontend: `/login`, `/register`, `/profile` funcionan; `/profile` redirige a `/login` sin sesión; tras login se vuelve a `/profile`.
- [x] Cobertura backend ≥ 80% sobre `app/core/security.py`, `app/services/auth.py`, `app/api/v1/auth.py`.
- [x] `make test` verde (back + front).

## No hacer en Fase 1 (anti-scope-creep)

- No endpoints admin de gestión de usuarios (`PATCH /users/{id}/status|role`) → backlog post-MVP.
- No CRUD de eventos, sesiones, ni inscripciones (Fases 2–5).
- No rate-limit ni logging JSON estructurado (Fase 6 / backlog).
- No cookies httpOnly server-side todavía — refresh en `localStorage` con nota de mejora.
- No blacklist de tokens / logout server-side (post-MVP).

## Salida

Un asistente puede registrarse, loguearse y entrar a una ruta protegida en el front; el admin sembrado se loguea con rol `ADMIN`.
