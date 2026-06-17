# Mis Eventos — Backend

FastAPI + SQLModel + PostgreSQL + Alembic. Gestionado con Poetry.

## Requisitos
- Python 3.12
- Poetry 1.8+
- (o solo) Docker + Docker Compose

## Ejecución vía Docker (recomendada)
Desde la raíz del repo:
```bash
cp .env.example .env
make up
```
Endpoint de salud: <http://localhost:8000/health>.
Documentación OpenAPI: <http://localhost:8000/docs>.

## Ejecución local (sin Docker)
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

## Tests
```bash
make test
# o localmente:
poetry run pytest --cov=app
```

## Estructura
```
backend/
├── app/
│   ├── core/        # Configuración (Settings)
│   ├── tests/       # Tests pytest
│   └── main.py      # Entry point FastAPI
├── alembic/         # Migraciones
├── alembic.ini
├── pyproject.toml
└── Dockerfile
```
