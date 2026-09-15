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


def test_disabled_when_no_token(client, monkeypatch):
    _finish_attempt_with_paste(client)
    monkeypatch.setattr(main, "TEACHER_TOKEN", "")
    r = client.get("/api/teacher/results?test_key=demo", headers=H)
    assert r.status_code == 503
