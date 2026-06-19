# Frontend — Mis Eventos

SPA en React 18 + TypeScript + Vite.

## Stack

- **React** 18 con componentes funcionales y hooks
- **TypeScript** estricto
- **Vite** (build + dev server)
- **React Router** v6 (enrutamiento)
- **Zustand** (estado global · auth store)
- **Axios** (instancia central con interceptores JWT)
- **React Query** / TanStack (cache de server state)
- **Vitest** + **React Testing Library** + **user-event** (tests)

## Setup con Docker (recomendado)

Desde la raíz del repo:

```sh
make up   # backend + frontend en background
open http://localhost:5173
```

El dev server arranca con `--host 0.0.0.0` y proxy a `/api` → `backend:8000` (configurado en `vite.config.ts`).

## Setup local (sin Docker)

Requiere Node `20 LTS`.

```sh
cd frontend
npm install
npm run dev   # http://localhost:5173
```

Si arrancas en local sin docker, configura `VITE_API_BASE_URL=http://localhost:8000/api/v1` en `.env`.

## Tests + cobertura

```sh
make test-front                         # vitest --coverage (gate ≥70%)
# o directo:
docker compose run --rm --no-deps frontend npm run test -- --coverage
# en local:
npm run test -- --coverage
```

Gate de cobertura (en `vite.config.ts`): **lines/branches/functions/statements ≥ 70%**.

Scope de cobertura: `src/{components,hooks,lib,stores}`. Las páginas (`src/pages`) y los wrappers de API (`src/api`) se testean indirectamente vía sus consumidores; al ser composición trivial sobre axios y formularios, se excluyen del scope.

Estado actual: ~**85%** lines / **79%** branches.

## Build de producción

```sh
npm run build       # tsc -b && vite build → dist/
npm run preview     # sirve dist/ localmente para verificar
```

## Variables de entorno

Solo `VITE_*` se exponen al cliente (no secretos).

| Variable | Default | Notas |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` | Base URL para axios |
| `VITE_BACKEND_PROXY` | `http://backend:8000` | Target del proxy `/api` en dev |

## Layout

```
src/
├── api/                       Cliente axios + funciones por dominio
│   ├── client.ts              Instancia con interceptor de refresh
│   ├── errors.ts              extractApiError + mapa UX por código
│   ├── auth.ts
│   ├── events.ts
│   ├── sessions.ts
│   ├── registrations.ts
│   └── users.ts
├── components/
│   ├── ui/                    Reusables (Button, Input, Badge, Pagination, SearchBar)
│   ├── events/                EventoCard, EventoForm, EventTransitionsBar, RegistrationButton
│   ├── sessions/              SpeakerPicker, SessionForm, SessionsAgenda
│   ├── Navbar.tsx
│   ├── RequireAuth.tsx        Wrapper de ruta protegida (sin sesión → /login)
│   └── RequireRole.tsx        Wrapper RBAC (rol no autorizado → /events)
├── hooks/                     React Query hooks por dominio
│   ├── events.ts
│   ├── sessions.ts
│   ├── registrations.ts
│   └── users.ts               useUserSearch con debounce 300ms
├── lib/
│   └── eventTransitions.ts    Matriz espejo de transiciones (UX-only)
├── pages/                     Vistas por ruta
│   ├── LoginPage / RegisterPage / ProfilePage
│   ├── events/                EventsList, EventDetail, MyEvents, EventCreate, EventEdit
│   ├── sessions/              SessionCreate, SessionEdit
│   └── registrations/         MyRegistrationsPage
├── stores/
│   └── auth.ts                Zustand: { user, accessToken, refreshToken, login, logout, setSession }
├── types/                     Tipos compartidos (event, session, registration, user, auth)
├── App.tsx                    Rutas + QueryClientProvider + BrowserRouter
└── main.tsx                   Entry point
```

## Convenciones de integración con el backend

- **Shape de error canónico**: `{ error: { code, message, details } }`. `extractApiError(err)` lo desempaqueta y mapea el `code` a un mensaje UX legible (`src/api/errors.ts`).
- **Auth**: access token en memoria (Zustand). Refresh token en `localStorage` como fallback documentado. Interceptor de Axios renueva el access ante `AUTH_TOKEN_EXPIRED` y reintenta una vez.
- **Cache invalidation**: mutaciones invalidan `["events"]` (sub-árbol jerárquico: list, me, detail, sessions, registrations) y `["me-registrations"]`.
