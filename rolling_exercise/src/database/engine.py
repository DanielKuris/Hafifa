from sqlalchemy import create_engine

from config.settings import settings

engine = create_engine(
    str(settings.DATABASE_URL),
    pool_pre_ping=True,
)
