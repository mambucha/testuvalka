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
    _migrate()


def _migrate() -> None:
    """Легкі ідемпотентні міграції для колонок, доданих після першого розгортання
    (create_all не змінює наявні таблиці, а на проді БД уже з даними студентів)."""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns("attempt_questions")}
    with engine.begin() as conn:
        if "timeout_reissues" not in cols:
            conn.execute(
                text("ALTER TABLE attempt_questions ADD COLUMN timeout_reissues INTEGER NOT NULL DEFAULT 0")
            )
