# Fase 0 — Bootstrap del entorno

**Meta:** Stack reproducible: `make up` levanta `db + backend + frontend` y los tres responden a health desde cero.

## Versiones fijadas (single source of truth)

- Python `3.12` · Node `20 LTS` · PostgreSQL `16-alpine`.

## Pasos secuenciales (el orden importa)

1. **Estructura raíz**
   - Archivos raíz: `.env.example`, `docker-compose.yml`, `Makefile`, `.gitignore`.
   - `.gitignore` debe excluir: `.env`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `node_modules/`, `dist/`, `coverage*`.

2. **Backend skeleton (`backend/`)**
   - `poetry init` con Python 3.12. Dependencias mínimas: `fastapi`, `uvicorn[standard]`, `sqlmodel`, `alembic`, `psycopg2-binary`, `pydantic-settings`. Dev: `pytest`, `pytest-cov`, `httpx`, `ruff`.
   - `app/main.py`: app FastAPI con `GET /health` → `{"status": "ok"}`.
   - `app/core/config.py`: `Settings(BaseSettings)` leyendo desde env (al menos `DATABASE_URL`).
   - `alembic init alembic` + configurar `sqlalchemy.url` dinámicamente desde `Settings`. **Sin** modelos ni migraciones todavía (van en Fase 1).
   - `backend/Dockerfile` (multi-stage): base `python:3.12-slim` → instala Poetry → `poetry install --no-root` → expone `8000` → comando `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`.

3. **Frontend skeleton (`frontend/`)**
   - `npm create vite@latest . -- --template react-ts`.
   - Ruta `/` con componente placeholder ("Mis Eventos").
   - `vite.config.ts`: proxy `/api` → `http://backend:8000` para dev en contenedor.
   - `frontend/Dockerfile` (dev): `node:20-alpine` → `npm ci` → comando `npm run dev -- --host 0.0.0.0 --port 5173`.

4. **`docker-compose.yml`** (orquestación)
   | Servicio   | Imagen / build       | Depende de        | Healthcheck                                   | Puerto host |
   |------------|----------------------|-------------------|-----------------------------------------------|-------------|
   | `db`       | `postgres:16-alpine` | —                 | `pg_isready -U $$POSTGRES_USER`               | 5432 (opc.) |
   | `backend`  | `./backend`          | `db (healthy)`    | `curl -f http://localhost:8000/health`        | 8000        |
   | `frontend` | `./frontend`         | `backend`         | `wget -q --spider http://localhost:5173`      | 5173        |
   - Volumen nombrado `pgdata` para `db`.
   - Bind mount `./backend:/app` (hot reload) y `./frontend:/app` + volumen anónimo para `node_modules`.
   - `env_file: .env` en backend y db; el frontend solo recibe `VITE_*` (no exponer secretos al cliente).

5. **`.env.example` (mínimo Fase 0)**
   - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`.
   - `DATABASE_URL=postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}`.
   - `VITE_API_BASE_URL=http://localhost:8000/api/v1`.
   - Placeholders comentados (vacíos) para fases posteriores: `JWT_SECRET=`, `ACCESS_TOKEN_TTL_MINUTES=`, `REFRESH_TOKEN_TTL_DAYS=`, `CORS_ORIGINS=`, `AUTH_RATE_LIMIT=`, `LOG_LEVEL=`, `SEED_ADMIN_EMAIL=`, `SEED_ADMIN_PASSWORD=`.

6. **`Makefile`** (targets mínimos)
   - `up`: `docker compose up --build -d`.
   - `down`: `docker compose down`.
   - `down-v`: `docker compose down -v` (limpia volúmenes).
   - `logs`: `docker compose logs -f`.
   - `ps`: `docker compose ps`.
   - `sh-back` / `sh-front`: `docker compose exec backend|frontend sh`.
   - `test`: `docker compose run --rm backend poetry run pytest`.

## Definition of Done (verificable, sin debate)

- [x] `cp .env.example .env && make up` arranca limpio.
- [x] `curl http://localhost:8000/health` → `{"status":"ok"}`.
- [x] `http://localhost:5173` muestra el placeholder.
- [x] `docker compose ps` reporta los 3 servicios como `healthy`.
- [x] `make down-v && make up` reproduce el estado desde cero sin intervención manual.
- [x] `make test` corre (aunque sea con 0 tests) sin errores de instalación.

## No hacer en Fase 0 (anti-scope-creep)

- No crear modelos ni migraciones (Fase 1).
- No tocar auth, JWT, CORS, rate-limit, logging estructurado (Fase 1 y Fase 6).
- No instalar Zustand, React Query, Axios, React Router (Fase 1).
- No configurar CI ni publicar imágenes (post-MVP).

## Salida

Repo clonable por un tercero que con `cp .env.example .env && make up` tenga los tres servicios sanos.
