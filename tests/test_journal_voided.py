"""Журнал: анульована спроба — це НЕ оцінка «нуль».

Раніше анульовані (voided) спроби показувалися як 0/12 і 0%, що в журналі
виглядало як двійка. Тепер бал і відсоток для незавершених спроб не показуються
(«—»), а статус подано українською.
"""

from app import models
from app.db import SessionLocal
from support import DEV_FULL_NAME, TEACHER_TOKEN, StudentClient, correct_answers

H = {"X-Teacher-Token": TEACHER_TOKEN}


def _set_status(attempt_id, status):
    db = SessionLocal()
    try:
        db.get(models.Attempt, attempt_id).status = status
        db.commit()
    finally:
        db.close()


def _row(client):
    data = client.get("/api/teacher/anomalies?test_key=demo", headers=H).json()
    return next(a for a in data["attempts"] if a["full_name"] == DEV_FULL_NAME)


def _finish(client):
    s = StudentClient(client)
    s.start()
    while True:
        cur = s.current_json()
        if cur.get("finished"):
            break
        s.answer(correct_answers(cur["question"]["key"], reissue=cur["reissue"]))
    return s


def test_voided_attempt_has_no_grade(client):
    s = StudentClient(client)
    s.start()
    s.current_json()
    _set_status(s.attempt_id, "voided")
    row = _row(client)
    assert row["status"] == "анульовано"
    assert row["score"] is None and row["percent"] is None


def test_active_attempt_has_no_grade(client):
    s = StudentClient(client)
    s.start()
    s.current_json()
    row = _row(client)
    assert row["status"] == "у процесі"
    assert row["score"] is None and row["percent"] is None


def test_finished_attempt_shows_real_grade(client):
    _finish(client)
    row = _row(client)
    assert row["status"] == "завершено"
    assert row["score"] is not None and row["percent"] == 100


def test_csv_leaves_score_empty_for_voided(client):
    s = StudentClient(client)
    s.start()
    s.current_json()
    _set_status(s.attempt_id, "voided")
    body = client.get("/api/teacher/results?test_key=demo", headers=H).text
    line = next(ln for ln in body.splitlines() if DEV_FULL_NAME in ln)
    assert "анульовано" in line
    # бал і відсоток — порожні клітинки, а не нулі
    assert ",0," not in line and not line.rstrip().endswith(",0")
