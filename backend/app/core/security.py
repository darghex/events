from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.errors import AuthTokenExpired, Forbidden
from app.db.session import get_session
from app.models.user import User, UserRole

TokenType = Literal["access", "refresh"]

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
_bearer = HTTPBearer(auto_error=False)

settings = get_settings()


# ---------- Passwords ----------
def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ---------- JWT ----------
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _encode(payload: dict) -> str:
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: int, role: UserRole) -> str:
    expire = _now_utc() + timedelta(minutes=settings.ACCESS_TOKEN_TTL_MINUTES)
    return _encode(
        {
            "sub": str(user_id),
            "role": role.value,
            "type": "access",
            "iat": int(_now_utc().timestamp()),
            "exp": int(expire.timestamp()),
        }
    )


def create_refresh_token(user_id: int) -> str:
    expire = _now_utc() + timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS)
    return _encode(
        {
            "sub": str(user_id),
            "type": "refresh",
            "iat": int(_now_utc().timestamp()),
            "exp": int(expire.timestamp()),
        }
    )


def decode_token(token: str, expected_type: TokenType) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise AuthTokenExpired("Token expirado") from exc
    except jwt.PyJWTError as exc:
        raise AuthTokenExpired("Token inválido") from exc
    if payload.get("type") != expected_type:
        raise AuthTokenExpired("Tipo de token incorrecto")
    return payload


# ---------- FastAPI dependencies ----------
def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: Session = Depends(get_session),
) -> User:
    if credentials is None:
        raise AuthTokenExpired("Token no provisto")
    payload = decode_token(credentials.credentials, expected_type="access")
    user_id = int(payload["sub"])
    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise AuthTokenExpired("Usuario inválido o inactivo")
    return user


def require_role(*allowed: UserRole):
    def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise Forbidden(f"Rol requerido: {[r.value for r in allowed]}")
        return user

    return _dep


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email.lower())).first()
