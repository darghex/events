from fastapi import APIRouter

from app.api.v1 import auth, event_sessions, events, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(
    event_sessions.router,
    prefix="/events/{event_id}/sessions",
    tags=["event-sessions"],
)
api_router.include_router(users.router, prefix="/users", tags=["users"])
