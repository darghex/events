from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
