from sqlmodel import Session, select

from app.models.user import User, UserRole


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_email(self, email: str) -> User | None:
        return self.session.exec(select(User).where(User.email == email.lower())).first()

    def get_by_id(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def get_many(self, user_ids: list[int]) -> list[User]:
        if not user_ids:
            return []
        rows = self.session.exec(select(User).where(User.id.in_(user_ids))).all()  # type: ignore[attr-defined]
        return list(rows)

    def search_by_email(self, *, q: str | None, limit: int, offset: int) -> list[User]:
        stmt = select(User).where(User.is_active.is_(True))  # type: ignore[attr-defined]
        if q:
            stmt = stmt.where(User.email.ilike(f"%{q.lower()}%"))  # type: ignore[attr-defined]
        stmt = stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)  # type: ignore[attr-defined]
        return list(self.session.exec(stmt).all())

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
