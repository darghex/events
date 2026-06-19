from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.db.seed import seed_admin

settings = get_settings()

API_DESCRIPTION = """\
API REST del MVP de gestión de eventos **Mis Eventos**.

Cubre autenticación con JWT (access + refresh), RBAC con tres roles globales
(`ADMIN`, `ORGANIZER`, `ATTENDEE`), CRUD de eventos con máquina de estados,
agenda de sesiones con regla de no-solapamiento global del ponente, e
inscripciones.

Errores se devuelven con el shape canónico
`{ "error": { "code": "...", "message": "...", "details": {} } }`.
"""


@asynccontextmanager
async def lifespan(_: FastAPI):
    seed_admin()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=API_DESCRIPTION,
    version="0.6.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
