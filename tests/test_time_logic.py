"""M2 — логіка часу: серверні дедлайни, перевидання після обриву, відновлення.

Протермінування імітуємо, зсуваючи deadline_at поточного питання в минуле прямо
в БД. Так перевіряємо саме серверну логіку, не чекаючи реального часу.
"""

from datetime import timedelta

from app import service
from support import (
    PAST,
    aq_by_ordinal,
    correct_answers,
    current_aq,
    set_current_deadline,
)


def test_expiry_reissues_with_new_numbers_and_full_time(student):
    """Вихід за час -> та сама задача з ІНШИМИ числами й повним часом."""
    student.start()
    c0 = student.current_json()
    assert c0["reissue"] == 0
    statement_v0 = c0["question"]["statement"]

    set_current_deadline(student.attempt_id, PAST)
    c1 = student.current_json()

    assert c1["reissue"] == 1
    assert c1["ordinal"] == c0["ordinal"]
    assert c1["question"]["key"] == c0["question"]["key"]
    assert c1["question"]["statement"] != statement_v0
    assert c1["seconds_left"] > 0


def test_late_submit_even_if_correct_is_not_graded(student):
    """Серце захисту (3.3): правильна, але ПІЗНЯ відповідь не оцінюється —
    натомість питання перевидається з новими числами."""
    student.start()
    c0 = student.current_json()
    good = correct_answers(c0["question"]["key"], reissue=0)

    set_current_deadline(student.attempt_id, PAST)
    body = student.answer(good).json()
    assert body["ok"] is False
    assert body["expired"] is True

    aq = current_aq(student.attempt_id)
    assert aq.ordinal == c0["ordinal"]
    assert aq.reissue == 1
    assert aq.submitted_at is None
    assert aq.score is None


def test_reissues_exhausted_then_zero_and_advance(student):
    """Після вичерпання ліміту перевидань пункт -> 0 балів і крок далі."""
    student.start()
    student.current()  # видати q0 (reissue 0)

    for expected in (1, 2):  # max_reissues=2 у демо-тесті
        set_current_deadline(student.attempt_id, PAST)
        c = student.current_json()
        assert c["ordinal"] == 0
        assert c["reissue"] == expected

    set_current_deadline(student.attempt_id, PAST)
    c = student.current_json()
    assert c["ordinal"] == 1  # уже наступне питання

    zeroed = aq_by_ordinal(student.attempt_id, 0)
    assert zeroed.submitted_at is not None
    assert zeroed.score == 0.0


def test_resume_within_time_keeps_same_question_with_less_time(student):
    """Повернення ДО дедлайну: те саме питання, менше часу, без перевидання."""
    student.start()
    c0 = student.current_json()
    statement_v0 = c0["question"]["statement"]

    set_current_deadline(student.attempt_id, service.utcnow() + timedelta(seconds=5))
    c1 = student.current_json()

    assert c1["reissue"] == 0
    assert c1["question"]["statement"] == statement_v0
    assert 0 < c1["seconds_left"] <= 5


def test_full_attempt_with_one_question_zeroed(student):
    """Наскрізь: одне питання повністю протерміноване (0), решта правильні."""
    student.start()
    student.current()  # видати q0

    for _ in range(3):  # видача + 2 перевидання + фінальний вихід -> 0
        set_current_deadline(student.attempt_id, PAST)
        student.current()

    while True:
        cur = student.current_json()
        if cur.get("finished"):
            final = cur
            break
        answers = correct_answers(cur["question"]["key"], reissue=cur["reissue"])
        assert student.answer(answers).status_code == 200

    assert final["max_score"] == 9.0
    assert final["score"] == 6.0  # дві по 3, одна обнулена


def test_answer_in_time_still_grades_normally(student):
    """Регрес: відповідь у межах часу оцінюється як і раніше (expired=False)."""
    student.start()
    c0 = student.current_json()
    r = student.answer(correct_answers(c0["question"]["key"])).json()
    assert r["ok"] is True
    assert r["expired"] is False
    assert r["next"] is True
