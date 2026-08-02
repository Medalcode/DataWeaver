from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

try:
    if "sqlite" in settings.DATABASE_URL:
        engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False},
        )
    else:
        engine = create_engine(
            settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=settings.DB_POOL_PRE_PING,
        )
except (ImportError, ModuleNotFoundError):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
