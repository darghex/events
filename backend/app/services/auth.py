from sqlmodel import Session

from app.core.errors import (
    AuthInvalidCredentials,
    AuthTokenExpired,
    Forbidden,
    UserAlreadyExists,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories.user import UserRepository


class AuthService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)

    def register(self, *, email: str, password: str) -> User:
        if self.users.get_by_email(email):
            raise UserAlreadyExists(details={"email": email.lower()})
        user = self.users.create(
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ATTENDEE,
        )
        self.session.commit()
        self.session.refresh(user)
        return user

    def login(self, *, email: str, password: str) -> tuple[str, str]:
        user = self.users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise AuthInvalidCredentials()
        if not user.is_active:
            raise Forbidden("Cuenta inactiva")
        return (
            create_access_token(user.id, user.role),
            create_refresh_token(user.id),
        )

    def refresh(self, *, refresh_token: str) -> str:
        payload = decode_token(refresh_token, expected_type="refresh")
        user = self.users.get_by_id(int(payload["sub"]))
        if user is None or not user.is_active:
            raise AuthTokenExpired("Usuario inválido o inactivo")
        return create_access_token(user.id, user.role)
