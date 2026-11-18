
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

ROOT_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = ROOT_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Si existe DATABASE_URL, utilizamos PostgreSQL.
# Si no existe, seguimos utilizando SQLite en local.

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Compatibilidad con cadenas antiguas de PostgreSQL.
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgres://",
            "postgresql+psycopg://",
            1
        )
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1
        )

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"sslmode": "require"}
    )

else:
    DATABASE_URL = (
        f"sqlite:///{(STORAGE_DIR / 'quizmaster.db').as_posix()}"
    )

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
