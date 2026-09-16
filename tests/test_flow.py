"""Наскрізний цикл (M1) + модель входу (шар A): вхід за прізвищем+групою, токен
доступу, відсутність витоку еталонів, перенесення помилки.
"""

from fractions import Fraction

from app.service import student_ident
from support import (
    DEV_GROUP,
    DEV_IDENT,
    StudentClient,
    build_question,
    correct_answers,
)


def test_full_cycle_all_correct(student):
    """Проходимо весь тест правильно -> повний бал і finished."""
    assert student.start().status_code == 200

    answered = 0
    while True:
        data = student.current_json()
        if data.get("finished"):
            break
        assert data["ordinal"] == answered
        assert data["total"] == 3
        assert data["seconds_left"] > 0
        r = student.answer(correct_answers(data["question"]["key"]))
        assert r.status_code == 200, r.text
        assert r.json()["ok"] is True
        answered += 1

    assert answered == 3
    final = student.current_json()
    assert final["finished"] is True
    assert final["max_score"] == 9.0  # три задачі по 3 бали
    assert final["score"] == final["max_score"]


def test_empty_answers_score_zero(student):
    """Порожні відповіді -> нуль балів, але цикл доходить до кінця."""
    student.start()
    for _ in range(3):
        cur = student.current_json()
        assert not cur.get("finished")
        parts = {p["key"]: "" for p in cur["question"]["parts"]}
        assert student.answer(parts).status_code == 200

    final = student.current_json()
    assert final["finished"] is True
    assert final["score"] == 0.0
    assert final["max_score"] == 9.0


def test_current_is_deterministic_and_leaks_no_answers(student):
    """Повторний /current дає те саме питання (ті самі числа) і жодних еталонів."""
    student.start()
    r1 = student.current_json()
    r2 = student.current_json()

    assert r1["question"] == r2["question"]  # seconds_left не звіряємо
    assert r1["ordinal"] == r2["ordinal"] == 0

    q = r1["question"]
    assert set(q.keys()) == {"key", "statement", "seconds", "svg", "parts"}
    for p in q["parts"]:
        assert set(p.keys()) == {"key", "label", "kind", "points"}
    assert "answer" not in str(r1).lower()


def test_no_going_back_after_answer(student):
    """Після відповіді /current віддає вже наступне питання, не попереднє."""
    student.start()
    first = student.current_json()
    assert first["ordinal"] == 0
    student.answer(correct_answers(first["question"]["key"]))
    second = student.current_json()
    assert second["ordinal"] == 1
    assert second["question"]["key"] != first["question"]["key"]


def test_start_resumes_active_attempt_with_same_token(student):
    """Повторний вхід тим самим прізвищем+групою повертає ту саму спробу й токен
    (відновлення сесії, а не нова спроба)."""
    r1 = student.start().json()
    r2 = student.start().json()
    assert r1["attempt_id"] == r2["attempt_id"]
    assert r1["token"] == r2["token"]


def test_wrong_token_is_rejected(client):
    """Чужий/порожній токен не дає доступу до спроби (404)."""
    s = StudentClient(client)
    s.start()
    good = s.token
    s.token = "definitely-not-the-token"
    assert s.current().status_code == 404
    s.token = ""
    assert s.current().status_code == 404
    s.token = good
    assert s.current().status_code == 200


def test_start_requires_name_and_group(client):
    r = client.post("/api/attempt/start", json={"test_key": "demo", "full_name": "", "group": ""})
    assert r.status_code == 400


def test_individual_numbers_per_student():
    """Різні студенти -> різні числа в тій самій задачі (п. 3.5): обмін
    відповідями в чаті групи марний."""
    q_a = build_question("quadratic_roots", ident=DEV_IDENT)
    q_b = build_question(
        "quadratic_roots", ident=student_ident("Інший Студент", DEV_GROUP)
    )
    assert q_a.params != q_b.params


def test_carry_gives_partial_credit(student):
    """Перенесення помилки (carry): помилка у визначнику, але x,y узгоджені з нею
    -> 2 з 3 за систему, не 0."""
    student.start()

    target = None
    while True:
        cur = student.current_json()
        if cur.get("finished"):
            break
        q = cur["question"]
        if q["key"] == "linear_system_2x2":
            target = q
            break
        student.answer(correct_answers(q["key"]))

    assert target is not None, "у демо-банку має бути linear_system_2x2"

    built = build_question("linear_system_2x2")
    truth_det = built.parts[0].answer
    a, b, c, d = (built.params[k] for k in ("a", "b", "c", "d"))
    e, f = built.params["e"], built.params["f"]

    wrong_det = truth_det + 1 if truth_det + 1 != 0 else truth_det - 1
    wrong_x = Fraction(e * d - b * f, wrong_det)
    wrong_y = Fraction(a * f - e * c, wrong_det)

    r = student.answer({"det": str(wrong_det), "x": str(wrong_x), "y": str(wrong_y)})
    assert r.status_code == 200, r.text

    while True:
        cur = student.current_json()
        if cur.get("finished"):
            final = cur
            break
        student.answer(correct_answers(cur["question"]["key"]))

    # Дві інші задачі по 3 + система 2 (det=0, x=1, y=1 через carry) = 8.
    assert final["score"] == 8.0


def test_event_logging_returns_204(student):
    student.start()
    r = student.event("paste", {"part": "det", "len": 3})
    assert r.status_code == 204


def test_student_review_after_finish(student):
    """Після завершення студент бачить розбір: бали по питаннях і правильні
    відповіді для помилок. До завершення розбір недоступний (409)."""
    student.start()

    # Під час активної спроби розбір заборонений.
    r = student.client.get(
        f"/api/attempt/{student.attempt_id}/review",
        headers={"X-Attempt-Token": student.token},
    )
    assert r.status_code == 409

    # Проходимо весь тест правильно.
    while True:
        cur = student.current_json()
        if cur.get("finished"):
            break
        student.answer(correct_answers(cur["question"]["key"]))

    r = student.client.get(
        f"/api/attempt/{student.attempt_id}/review",
        headers={"X-Attempt-Token": student.token},
    )
    assert r.status_code == 200
    d = r.json()
    assert len(d["questions"]) == 3
    for q in d["questions"]:
        assert q["verdict"] == "повністю"
        for p in q["parts"]:
            assert p["correct"] is True
            assert {"label", "raw", "expected", "correct"} == set(p)


def test_student_review_requires_token(student):
    student.start()
    while True:
        cur = student.current_json()
        if cur.get("finished"):
            break
        student.answer(correct_answers(cur["question"]["key"]))
    # чужий/порожній токен -> 404
    r = student.client.get(
        f"/api/attempt/{student.attempt_id}/review",
        headers={"X-Attempt-Token": "wrong"},
    )
    assert r.status_code == 404
