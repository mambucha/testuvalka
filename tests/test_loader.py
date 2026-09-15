"""Шар B: завантаження тестів із YAML і проходження тесту на БАНКОВОМУ шаблоні.

Цей тест доводить наскрізний сценарій «підвантажити тест»: описали тест у YAML,
завантажили, студент його пройшов, і банковий шаблон коректно оцінено в
підпроцесі (реєстрація банку в дочірньому процесі — див. app/grading.py).
"""

import textwrap

import pytest
from sqlalchemy import select

import app.main as main
from app import models
from app.db import SessionLocal
from app.load_tests import LoadError, load_tests
from support import StudentClient, correct_answers


def _write(tmp_path, text):
    p = tmp_path / "t.yaml"
    p.write_text(textwrap.dedent(text), encoding="utf-8")
    return str(p)


def test_load_and_take_bank_test(client, tmp_path):
    path = _write(
        tmp_path,
        """
        - key: lines_1
          title: Прямі
          question_count: 1
          bank: [line_through_two_points]
          max_attempts: 1
        """,
    )
    created, updated = load_tests(path)
    assert created == 1

    s = StudentClient(client)
    assert s.start("lines_1").status_code == 200
    cur = s.current_json()
    assert cur["question"]["key"] == "line_through_two_points"

    good = correct_answers("line_through_two_points", test_key="lines_1")
    r = s.answer(good).json()
    assert r["ok"] is True
    assert r["finished"] is True
    assert r["score"] == r["max_score"] == 3.0  # k + b + y(x0)


def test_load_is_idempotent_upsert(client, tmp_path):
    path = _write(
        tmp_path,
        """
        - key: lines_1
          title: Прямі
          bank: [line_through_two_points]
        """,
    )
    assert load_tests(path) == (1, 0)
    # Повторно — оновлення, не дублікат.
    assert load_tests(path) == (0, 1)


def test_unknown_template_is_rejected(client, tmp_path):
    path = _write(
        tmp_path,
        """
        - key: bad
          bank: [no_such_template]
        """,
    )
    with pytest.raises(LoadError):
        load_tests(path)


def test_question_count_over_bank_is_rejected(client, tmp_path):
    path = _write(
        tmp_path,
        """
        - key: toomany
          question_count: 5
          bank: [line_through_two_points]
        """,
    )
    with pytest.raises(LoadError):
        load_tests(path)


def test_autoload_loads_yaml_on_startup(client, tmp_path, monkeypatch):
    """Автозавантаження на старті: оновлення тестів = git push -> редеплой."""
    path = _write(
        tmp_path,
        """
        - key: auto1
          title: Авто
          bank: [det_2x2]
        """,
    )
    monkeypatch.setattr(main, "AUTOLOAD", path)
    main._maybe_autoload()
    db = SessionLocal()
    try:
        assert db.scalar(select(models.Test).where(models.Test.key == "auto1")) is not None
    finally:
        db.close()


def test_autoload_missing_or_bad_file_does_not_crash(monkeypatch):
    monkeypatch.setattr(main, "AUTOLOAD", "definitely-missing-file.yaml")
    main._maybe_autoload()  # не кидає — лише лог
