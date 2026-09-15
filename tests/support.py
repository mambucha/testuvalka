"""Спільні хелпери для тестів: клієнт студента (керує токеном) і обчислення
правильних відповідей тим самим рушієм, що й сервер.

Оточення задає conftest ДО імпорту застосунку, тож цей модуль можна імпортувати
з тестів безпечно (conftest завантажується pytest-ом першим).
"""

from datetime import datetime

from sqlalchemy import select

import engine
from app import models
from app.config import SECRET
from app.db import SessionLocal
from app.service import student_ident

TEST_KEY = "demo"
FIRST_ATTEMPT_NO = 1  # свіжа БД у фікстурі -> перша спроба студента
DEV_FULL_NAME = "Тест Студент"
DEV_GROUP = "КН-11"
DEV_IDENT = student_ident(DEV_FULL_NAME, DEV_GROUP)
TEACHER_TOKEN = "teacher-secret"  # має збігатися з conftest
PAST = datetime(2000, 1, 1)


class StudentClient:
    """Обгортка навколо TestClient: пам'ятає attempt_id і токен, шле заголовок."""

    def __init__(self, client, full_name=DEV_FULL_NAME, group=DEV_GROUP):
        self.client = client
        self.full_name = full_name
        self.group = group
        self.attempt_id = None
        self.token = None

    def start(self, test_key=TEST_KEY):
        r = self.client.post(
            "/api/attempt/start",
            json={"test_key": test_key, "full_name": self.full_name, "group": self.group},
        )
        if r.status_code == 200:
            self.attempt_id = r.json()["attempt_id"]
            self.token = r.json()["token"]
        return r

    @property
    def _headers(self):
        return {"X-Attempt-Token": self.token or ""}

    def current(self):
        return self.client.get(
            f"/api/attempt/{self.attempt_id}/current", headers=self._headers
        )

    def current_json(self):
        return self.current().json()

    def answer(self, answers):
        return self.client.post(
            f"/api/attempt/{self.attempt_id}/answer",
            json={"answers": answers},
            headers=self._headers,
        )

    def event(self, type_, payload=None):
        return self.client.post(
            f"/api/attempt/{self.attempt_id}/event",
            json={"type": type_, "payload": payload or {}},
            headers=self._headers,
        )


def build_question(question_key, reissue=0, ident=DEV_IDENT, test_key=TEST_KEY):
    return engine.build(question_key, SECRET, ident, test_key, FIRST_ATTEMPT_NO, reissue)


def correct_answers(question_key, reissue=0, ident=DEV_IDENT, test_key=TEST_KEY):
    """Правильні відповіді так, як їх обчислює сервер (той самий seed)."""
    q = build_question(question_key, reissue=reissue, ident=ident, test_key=test_key)
    return {p.key: str(p.answer) for p in q.parts}


# --- прямий доступ до БД для імітації часу (M2) ---


def current_aq(attempt_id):
    db = SessionLocal()
    try:
        return db.scalars(
            select(models.AttemptQuestion)
            .where(
                models.AttemptQuestion.attempt_id == attempt_id,
                models.AttemptQuestion.submitted_at.is_(None),
            )
            .order_by(models.AttemptQuestion.ordinal)
        ).first()
    finally:
        db.close()


def set_current_deadline(attempt_id, when):
    db = SessionLocal()
    try:
        aq = db.scalars(
            select(models.AttemptQuestion)
            .where(
                models.AttemptQuestion.attempt_id == attempt_id,
                models.AttemptQuestion.submitted_at.is_(None),
            )
            .order_by(models.AttemptQuestion.ordinal)
        ).first()
        aq.deadline_at = when
        db.add(aq)
        db.commit()
    finally:
        db.close()


def aq_by_ordinal(attempt_id, ordinal):
    db = SessionLocal()
    try:
        return db.scalars(
            select(models.AttemptQuestion).where(
                models.AttemptQuestion.attempt_id == attempt_id,
                models.AttemptQuestion.ordinal == ordinal,
            )
        ).first()
    finally:
        db.close()
