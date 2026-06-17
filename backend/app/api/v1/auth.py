from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.security import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    TokenPair,
    UserCreate,
    UserRead,
)
from app.services.auth import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario (rol ATTENDEE por defecto)",
)
def register(payload: UserCreate, session: Session = Depends(get_session)) -> User:
    return AuthService(session).register(email=payload.email, password=payload.password)


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Login con email + password — emite access + refresh",
)
def login(payload: LoginRequest, session: Session = Depends(get_session)) -> TokenPair:
    access, refresh = AuthService(session).login(
        email=payload.email, password=payload.password
    )
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Renovar access_token usando un refresh_token válido",
)
def refresh(payload: RefreshRequest, session: Session = Depends(get_session)) -> AccessTokenResponse:
    access = AuthService(session).refresh(refresh_token=payload.refresh_token)
    return AccessTokenResponse(access_token=access)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Perfil del usuario autenticado",
)
def me(user: User = Depends(get_current_user)) -> User:
    return user
