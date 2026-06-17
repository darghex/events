import logging

from sqlmodel import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import engine
from app.models.user import User, UserRole
from app.repositories.user import UserRepository

logger = logging.getLogger("app.seed")


def seed_admin() -> User | None:
    """Crea el admin inicial si no existe. Idempotente. Silencioso si faltan envs."""
    settings = get_settings()
    email = settings.SEED_ADMIN_EMAIL
    password = settings.SEED_ADMIN_PASSWORD

    if not email or not password:
        logger.warning("Seed admin omitido: SEED_ADMIN_EMAIL/SEED_ADMIN_PASSWORD vacíos")
        return None

    with Session(engine) as session:
        repo = UserRepository(session)
        existing = repo.get_by_email(email)
        if existing:
            logger.info("Seed admin: ya existe %s", existing.email)
            return existing
        user = repo.create(
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
        )
        session.commit()
        session.refresh(user)
        logger.info("Seed admin creado: %s", user.email)
        return user
