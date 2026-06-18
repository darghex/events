from collections.abc import Generator, Iterator
from contextlib import contextmanager

from sqlmodel import Session, create_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


@contextmanager
def transactional(session: Session) -> Iterator[None]:
    try:
        yield
        session.commit()
    except Exception:
        session.rollback()
        raise
