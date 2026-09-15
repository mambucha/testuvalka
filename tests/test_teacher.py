"""Шар D: кабінет викладача — журнал оцінок (CSV) і сигнали аномалій.

Доступ лише за токеном викладача. Аномалії — сирі сигнали (вставки, перемикання
вкладки), не звинувачення; пороги автоворідингу тут навмисно не автоматизовані.
"""

import app.main as main
from support import DEV_FULL_NAME, DEV_GROUP, TEACHER_TOKEN, StudentClient, correct_answers

H = {"X-Teacher-Token": TEACHER_TOKEN}


def _finish_attempt_with_paste(client):
    """Пройти демо-тест до кінця, дорогою залогувавши подію paste."""
    s = StudentClient(client)
    s.start()
    first = True
    while True:
        cur = s.current_json()
        if cur.get("finished"):
            break
        if first:
            s.event("paste", {"part": cur["question"]["parts"][0]["key"]})
            first = False
        s.answer(correct_answers(cur["question"]["key"]))
    return s


def test_results_requires_token(client):
    _finish_attempt_with_paste(client)
    assert client.get("/api/teacher/results?test_key=demo").status_code == 403
    assert client.get(
        "/api/teacher/results?test_key=demo", headers={"X-Teacher-Token": "wrong"}
    ).status_code == 403


def test_results_csv_has_student_row(client):
    _finish_attempt_with_paste(client)
    r = client.get("/api/teacher/results?test_key=demo", headers=H)
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    body = r.text
    assert DEV_GROUP in body
    assert DEV_FULL_NAME in body
    assert "percent" in body  # заголовок
    assert body.startswith("﻿")  # BOM для Excel


def test_results_token_via_query(client):
    _finish_attempt_with_paste(client)
    r = client.get(f"/api/teacher/results?test_key=demo&token={TEACHER_TOKEN}")
    assert r.status_code == 200


def test_anomalies_report_paste_signal(client):
    _finish_attempt_with_paste(client)
    r = client.get("/api/teacher/anomalies?test_key=demo", headers=H)
    assert r.status_code == 200
    data = r.json()
    assert data["test_key"] == "demo"
    row = next(a for a in data["attempts"] if a["full_name"] == DEV_FULL_NAME)
    assert row["paste_count"] >= 1
    assert "вставка" in row["flags"]
    assert row["min_seconds_per_question"] is not None
    assert row["attempt_id"]  # для переходу до розбору
    assert row["finished_at"]  # дата здачі (спроба завершена)


def test_disabled_when_no_token(client, monkeypatch):
    _finish_attempt_with_paste(client)
    monkeypatch.setattr(main, "TEACHER_TOKEN", "")
    r = client.get("/api/teacher/results?test_key=demo", headers=H)
    assert r.status_code == 503


def test_results_xlsx_download(client):
    _finish_attempt_with_paste(client)
    # без токена — заборонено
    assert client.get("/api/teacher/results_xlsx?test_key=demo").status_code == 403
    # з токеном — справжній .xlsx
    r = client.get("/api/teacher/results_xlsx?test_key=demo", headers=H)
    assert r.status_code == 200
    assert "spreadsheetml" in r.headers["content-type"]
    assert r.content[:2] == b"PK"  # xlsx — це zip-архів
    assert len(r.content) > 200


def test_attempt_detail_breakdown(client):
    s = _finish_attempt_with_paste(client)  # усі відповіді правильні
    # без токена — заборонено
    assert client.get(f"/api/teacher/attempt/{s.attempt_id}/detail").status_code == 403
    r = client.get(f"/api/teacher/attempt/{s.attempt_id}/detail", headers=H)
    assert r.status_code == 200
    d = r.json()
    assert d["full_name"] == DEV_FULL_NAME
    assert len(d["questions"]) == 3  # у demo три питання
    for qq in d["questions"]:
        assert qq["parts"]
        for p in qq["parts"]:
            assert {"label", "raw", "expected", "correct", "score", "max"} <= set(p)
    # усе правильно -> усі питання «повністю», кожне поле correct
    assert all(qq["verdict"] == "повністю" for qq in d["questions"])
    assert all(p["correct"] for qq in d["questions"] for p in qq["parts"])


def test_attempt_detail_survives_removed_template(client):
    """Розбір старої спроби з видаленим відтоді шаблоном не має падати."""
    from sqlalchemy import select

    from app import models
    from app.db import SessionLocal

    s = _finish_attempt_with_paste(client)
    db = SessionLocal()
    try:
        aq = db.scalars(
            select(models.AttemptQuestion)
            .where(models.AttemptQuestion.attempt_id == s.attempt_id)
            .order_by(models.AttemptQuestion.ordinal)
        ).first()
        aq.question_key = "gone_template"  # імітуємо видалений шаблон
        db.add(aq)
        db.commit()
    finally:
        db.close()

    r = client.get(f"/api/teacher/attempt/{s.attempt_id}/detail", headers=H)
    assert r.status_code == 200  # не 500
    d = r.json()
    q0 = next(q for q in d["questions"] if q["question_key"] == "gone_template")
    assert q0["parts"]  # показує збережені відповіді
    assert q0["parts"][0]["expected"] == "—"  # еталона немає — і це ок
