from collections.abc import Generator

from sqlalchemy.orm import Session

from database.session import SessionLocal


def get_session() -> Generator[Session]:
    with SessionLocal() as session:
        yield session
