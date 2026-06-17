from sqlmodel import Session, select

from app.models.user import User, UserRole


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_email(self, email: str) -> User | None:
        return self.session.exec(select(User).where(User.email == email.lower())).first()

    def get_by_id(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def create(
        self,
        *,
        email: str,
        password_hash: str,
        role: UserRole = UserRole.ATTENDEE,
        is_active: bool = True,
    ) -> User:
        user = User(
            email=email.lower(),
            password_hash=password_hash,
            role=role,
            is_active=is_active,
        )
        self.session.add(user)
        self.session.flush()
        self.session.refresh(user)
        return user
