"""Підключення до БД і сесії SQLAlchemy 2.0."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


# check_same_thread=False: FastAPI обслуговує синхронні маршрути у threadpool,
# тож одна сесія може торкнутись різних потоків у межах запиту.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)

# expire_on_commit=False: після commit об'єкти лишаються придатними до читання
# в межах того самого запиту (не тягнемо зайвих SELECT після кожного коміту).
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False, class_=Session
)


def get_db():
    """Залежність FastAPI: одна сесія на запит."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401  — реєстрація моделей у метаданих

    Base.metadata.create_all(engine)
