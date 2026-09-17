"""Захист доброчесності: вихід із вкладки (away) та вставка (paste) перевидають
поточне питання з новими числами й повним часом, але НЕ карають балом і не
з'їдають ліміт перевидань за часом."""

from support import PAST, current_aq, set_current_deadline


def _first(student):
    student.start()
    return student.current_json()


def test_away_reissues_with_new_numbers(student):
    c0 = _first(student)
    v0 = c0["question"]["statement"]
    r = student.event("away", {"ms": 5000}).json()
    assert r["reissued"] is True
    c1 = student.current_json()
    assert c1["ordinal"] == c0["ordinal"]            # те саме місце
    assert c1["question"]["key"] == c0["question"]["key"]
    assert c1["question"]["statement"] != v0          # інші числа
    assert c1["reissue"] == 1
    assert c1["seconds_left"] > 0                      # повний час знову


def test_paste_reissues(student):
    c0 = _first(student)
    v0 = c0["question"]["statement"]
    r = student.event("paste", {"part": "x"}).json()
    assert r["reissued"] is True
    c1 = student.current_json()
    assert c1["question"]["statement"] != v0


def test_integrity_reissue_does_not_consume_timeout_limit(student):
    """Багато виходів із вкладки не мають вести до 0 балів: ліміт -> 0 рахує лише
    перевидання ЗА ЧАСОМ, не за доброчесністю."""
    _first(student)
    for _ in range(5):  # 5 виходів поспіль (більше за max_reissues=2)
        assert student.event("away", {"ms": 4000}).json()["reissued"] is True
        student.current_json()
    aq = current_aq(student.attempt_id)
    assert aq.ordinal == 0            # усе ще перше питання, не обнулене
    assert aq.submitted_at is None    # не здане як 0
    assert aq.timeout_reissues == 0   # жодного таймаут-перевидання
    assert aq.reissue == 5            # але числа мінялись 5 разів


def test_timeout_still_zeroes_after_limit_despite_integrity(student):
    """Перевидання за доброчесністю не зменшують «запас» таймаут-перевидань:
    після away питання все одно можна вичерпати саме таймаутами."""
    _first(student)
    student.event("away", {"ms": 4000})   # одне integrity-перевидання
    student.current_json()
    # тепер вичерпуємо саме таймаутами: max_reissues=2 -> 2 перевидання, 3-й = 0
    for _ in range(3):
        set_current_deadline(student.attempt_id, PAST)
        student.current_json()
    aq0 = None
    from support import aq_by_ordinal
    aq0 = aq_by_ordinal(student.attempt_id, 0)
    assert aq0.submitted_at is not None
    assert aq0.score == 0.0
    assert aq0.timeout_reissues == 2   # рівно ліміт


def test_away_not_reissue_before_question_issued(student):
    """Якщо питання ще не видане (не показане), away нічого не перевидає."""
    student.start()  # /current не викликали -> питання не видане
    r = student.event("away", {"ms": 5000}).json()
    assert r["reissued"] is False
