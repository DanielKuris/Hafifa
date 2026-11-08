from sqlalchemy.orm import sessionmaker

from database.engine import engine


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)