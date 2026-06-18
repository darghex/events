from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session

from app.core.security import require_role
from app.db.session import get_session
from app.models.user import User, UserRole
from app.repositories.user import UserRepository

router = APIRouter()

USERS_MAX_LIMIT = 50
USERS_DEFAULT_LIMIT = 20


class UserSearchResult(BaseModel):
    id: int
    email: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


@router.get(
    "",
    response_model=list[UserSearchResult],
    summary="Buscar usuarios por email (organizer/admin). Alimenta el SpeakerPicker.",
)
def search_users(
    q: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=USERS_DEFAULT_LIMIT, ge=1, le=USERS_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    _actor: User = Depends(require_role(UserRole.ORGANIZER, UserRole.ADMIN)),
    session: Session = Depends(get_session),
) -> list[UserSearchResult]:
    repo = UserRepository(session)
    normalized = q.strip() if q else None
    rows = repo.search_by_email(q=normalized or None, limit=limit, offset=offset)
    return [UserSearchResult.model_validate(row) for row in rows]
