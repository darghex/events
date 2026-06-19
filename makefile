COMPOSE ?= docker compose

.PHONY: help up down down-v logs ps sh-back sh-front test test-back test-front build

help:
	@echo "Targets disponibles:"
	@echo "  up         Levanta el stack (db + backend + frontend) en background"
	@echo "  down       Detiene el stack"
	@echo "  down-v     Detiene el stack y elimina volúmenes (DB efímera)"
	@echo "  logs       Sigue los logs de todos los servicios"
	@echo "  ps         Estado de los servicios"
	@echo "  migrate    upgrade de migraciones alembic"
	@echo "  sh-back    Shell dentro del contenedor backend"
	@echo "  sh-front   Shell dentro del contenedor frontend"
	@echo "  test       Corre tests backend + frontend"
	@echo "  test-back  Corre tests backend (pytest)"
	@echo "  test-front Corre tests frontend (vitest)"
	@echo "  build      Reconstruye las imágenes sin levantar nada"

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

down-v:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

migrate:
	$(COMPOSE) exec backend poetry run alembic upgrade head

sh-back:
	$(COMPOSE) exec backend sh

sh-front:
	$(COMPOSE) exec frontend sh

test: test-back test-front

test-back:
	$(COMPOSE) run --rm backend sh -c "poetry install --no-interaction --no-root >/dev/null && poetry run pytest --cov=app --cov-fail-under=80"

test-front:
	$(COMPOSE) run --rm --no-deps frontend npm run test -- --coverage

build:
	$(COMPOSE) build
