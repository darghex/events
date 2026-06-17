#!/bin/sh
set -e

echo "[entrypoint] aplicando migraciones..."
alembic upgrade head

echo "[entrypoint] arrancando uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
