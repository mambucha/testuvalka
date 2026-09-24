"""Поріг виходів із тесту: після N виходів спроба анулюється й учень отримує
ПОВНІСТЮ новий варіант (налаштування restart_after_violations, per-test).

Виходом вважається і перемикання вкладки ("away"), і втрата фокуса вікна
("unfocus" — два вікна поруч). Вставка сюди не рахується.
"""

from sqlalchemy import select

from app import models
from app.db import SessionLocal
from support import StudentClient

RK = "restartcheck"
BANK = ["linear_system_2x2", "quadratic_roots", "derivative_at_point"]


def _make_test(limit=2, max_attempts=3):
    """Окремий тест у БД із порогом виходів (демо-тест його не має)."""
    db = SessionLocal()
    try:
        row = db.scalar(select(models.Test).where(models.Test.key == RK))
        if row is None:
            row = models.Test(key=RK)
            db.add(row)
        row.title = "Перевірка перезапуску"
        row.question_count = 3
        row.bank_keys = list(BANK)
        row.max_attempts = max_attempts
        row.max_reissues = 2
        row.points_per_question = 1
        row.restart_after_violations = limit
        db.commit()
    finally:
        db.close()


def _status(attempt_id):
    db = SessionLocal()
    try:
        return db.get(models.Attempt, attempt_id).status
    finally:
        db.close()


def _attempt_no(attempt_id):
    db = SessionLocal()
    try:
        return db.get(models.Attempt, attempt_id).attempt_no
    finally:
        db.close()


def test_exit_below_limit_only_reissues_and_warns(client):
    _make_test(limit=3)
    s = StudentClient(client)
    s.start(RK)
    s.current_json()
    r = s.event("away", {"ms": 5000}).json()
    assert r["reissued"] is True and r["restart"] is False
    assert r["exits"] == 1 and r["exit_limit"] == 3   # для попередження «1 з 3»
    assert _status(s.attempt_id) == "active"


def test_window_unfocus_also_reissues(client):
    """Втрата фокуса ВІКНА карається так само, як перемикання вкладки."""
    s = StudentClient(client)
    s.start()                       # демо-тест, без порога
    s.current_json()
    r = s.event("unfocus", {"ms": 5000}).json()
    assert r["reissued"] is True and r["restart"] is False


def test_reaching_limit_restarts_attempt(client):
    _make_test(limit=2)
    s = StudentClient(client)
    s.start(RK)
    s.current_json()
    assert s.event("away", {"ms": 5000}).json()["restart"] is False
    s.current_json()                # клієнт перезапитує питання після перевидання
    r = s.event("unfocus", {"ms": 5000}).json()   # інший тип виходу теж рахується
    assert r["restart"] is True and r["exits"] == 2
    assert _status(s.attempt_id) == "restarted"


def test_after_restart_student_gets_fresh_variant(client):
    """Новий старт дає іншу спробу з іншим attempt_no -> інший seed -> інші числа."""
    _make_test(limit=2)
    s = StudentClient(client)
    s.start(RK)
    s.current_json()
    first = s.attempt_id
    s.event("away", {"ms": 5000})
    s.current_json()
    s.event("away", {"ms": 5000})

    s2 = StudentClient(client)
    assert s2.start(RK).status_code == 200
    assert s2.attempt_id != first
    assert _attempt_no(s2.attempt_id) > _attempt_no(first)


def test_restarted_attempt_counts_against_max_attempts(client):
    """ЛАЗІВКА ЗАКРИТА: анульована за виходи спроба рахується як використана,
    тож вихід не можна використати, щоб «перекинути» невдалу спробу."""
    _make_test(limit=2, max_attempts=2)
    for _ in range(2):
        s = StudentClient(client)
        assert s.start(RK).status_code == 200
        s.current_json()
        s.event("away", {"ms": 5000})
        s.current_json()
        s.event("away", {"ms": 5000})
    s3 = StudentClient(client)
    assert s3.start(RK).status_code == 403          # ліміт спроб вичерпано


def test_tests_without_setting_are_unaffected(client):
    """Демо-тест не має порога: скільки б не виходив — лише перевидання."""
    s = StudentClient(client)
    s.start()
    r = None
    for _ in range(4):
        s.current_json()
        r = s.event("away", {"ms": 5000}).json()
        assert r["restart"] is False
    assert r["exit_limit"] is None
    assert _status(s.attempt_id) == "active"


def test_paste_does_not_count_toward_restart(client):
    """Вставка — інше порушення: перевидає питання, але до порога не рахується."""
    _make_test(limit=2)
    s = StudentClient(client)
    s.start(RK)
    for _ in range(3):
        cur = s.current_json()
        r = s.event("paste", {"part": cur["question"]["parts"][0]["key"]}).json()
        assert r["restart"] is False
    assert _status(s.attempt_id) == "active"
