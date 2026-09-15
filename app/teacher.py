"""Кабінет викладача: журнал оцінок (CSV) і сигнали аномалій.

Телеметрія працює на політику, а не на звинувачення (п. 3.4, 6.4): тут лише
показуємо СИРІ сигнали (вставки, перемикання вкладки, час на пункт). Пороги
автоворідингу підбираються за даними пілоту — навмисно НЕ автоматизовано тут.
"""

from __future__ import annotations

import csv
import io

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.service import ServiceError

RESULT_COLS = [
    "group", "full_name", "test_key", "attempt_no", "status",
    "score", "max_score", "percent", "started_at", "finished_at",
]


def _test_or_404(db: Session, test_key: str) -> models.Test:
    test = db.scalar(select(models.Test).where(models.Test.key == test_key))
    if test is None:
        raise ServiceError(404, "тест не знайдено")
    return test


def _attempts(db: Session, test: models.Test) -> list[models.Attempt]:
    return list(
        db.scalars(select(models.Attempt).where(models.Attempt.test_id == test.id))
    )


def _dt(value) -> str:
    return value.isoformat(sep=" ", timespec="seconds") if value else ""


def result_rows(db: Session, test_key: str) -> list[dict]:
    test = _test_or_404(db, test_key)
    rows = []
    for a in _attempts(db, test):
        pct = round(100 * a.score / a.max_score) if a.max_score else 0
        rows.append(
            {
                "group": a.student.group_name,
                "full_name": a.student.full_name,
                "test_key": test.key,
                "attempt_no": a.attempt_no,
                "status": a.status,
                "score": a.score,
                "max_score": a.max_score,
                "percent": pct,
                "started_at": _dt(a.started_at),
                "finished_at": _dt(a.finished_at),
            }
        )
    rows.sort(key=lambda r: (r["group"], r["full_name"], r["attempt_no"]))
    return rows


def results_csv(db: Session, test_key: str) -> str:
    rows = result_rows(db, test_key)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=RESULT_COLS)
    writer.writeheader()
    writer.writerows(rows)
    # BOM, щоб Excel правильно показав кирилицю.
    return "﻿" + buf.getvalue()


def anomalies(db: Session, test_key: str) -> list[dict]:
    test = _test_or_404(db, test_key)
    out = []
    for a in _attempts(db, test):
        events = list(
            db.scalars(select(models.Event).where(models.Event.attempt_id == a.id))
        )
        paste = sum(1 for e in events if e.type == "paste")
        blur = sum(1 for e in events if e.type == "blur")
        first_ms = [
            e.payload["ms"]
            for e in events
            if e.type == "first_input" and isinstance(e.payload, dict) and "ms" in e.payload
        ]
        secs = [
            (q.submitted_at - q.started_at).total_seconds()
            for q in a.questions
            if q.started_at and q.submitted_at
        ]
        flags = []
        if paste:
            flags.append("вставка")
        if blur:
            flags.append("перемикання вкладки")
        out.append(
            {
                "group": a.student.group_name,
                "full_name": a.student.full_name,
                "attempt_no": a.attempt_no,
                "status": a.status,
                "score": a.score,
                "max_score": a.max_score,
                "paste_count": paste,
                "blur_count": blur,
                "min_seconds_per_question": round(min(secs), 1) if secs else None,
                "avg_first_input_ms": round(sum(first_ms) / len(first_ms)) if first_ms else None,
                "flags": flags,
            }
        )
    # Спершу спроби з прапорцями — їх викладач перегляне насамперед.
    out.sort(key=lambda r: (not r["flags"], r["group"], r["full_name"]))
    return out
