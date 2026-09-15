"""Спільні фікстури pytest.

Оточення МУСИТЬ бути задане до імпорту app.config (він читає його на імпорті),
тому виставляємо змінні на самому верху модуля, ще до імпортів застосунку.
"""

import os
import tempfile
from pathlib import Path

os.environ.setdefault("TESTUVALKA_SECRET", "test-secret-fixed")
os.environ.setdefault("TESTUVALKA_TEACHER_TOKEN", "teacher-secret")
_tmpdb = Path(tempfile.gettempdir()) / "testuvalka_pytest.db"
os.environ["TESTUVALKA_DATABASE_URL"] = f"sqlite:///{_tmpdb.as_posix()}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine as sa_engine  # noqa: E402
from app.main import app  # noqa: E402
from support import StudentClient  # noqa: E402


@pytest.fixture()
def client():
    """Чиста БД на кожен тест. TestClient як контекст запускає lifespan (init_db
    + сідинг демо-тесту)."""
    Base.metadata.drop_all(sa_engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(sa_engine)


@pytest.fixture()
def student(client):
    """Готовий клієнт студента з демо-даними."""
    return StudentClient(client)
