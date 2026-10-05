"""Факторіал у відповіді: приймаємо 5! і factorial(5), але з жорсткою межею.

Навіщо межа. sympy обчислює факторіал ЖАДІБНО вже під час парсингу, тобто до
будь-якої нашої перевірки й до таймауту воркера. `999999999!` – це приблизно
8,5 мільярда цифр, тож одна така відповідь поклала б контейнер по пам'яті.
Через це межа перевіряється СИНТАКСИЧНО, ще до parse_expr – так само, як уже
зроблено для степеневої вежі 9**9**9.

Тести навмисне міряють час: відкидати треба миттєво, а не «через 3 секунди
таймауту».
"""

import time

import pytest
import sympy as sp

import engine


def _p(raw, kind="number"):
    return engine.parse_answer(raw, kind)


# --- що мусить працювати -------------------------------------------------

@pytest.mark.parametrize("raw,want", [
    ("5!", 120),
    ("0!", 1),                       # домовленість 0! = 1 (с. 75 підручника)
    ("1!", 1),
    ("12!", 479001600),
    ("12 !", 479001600),             # пробіл перед знаком
    ("factorial(5)", 120),
    ("factorial( 6 )", 720),
    ("10!/(7!*3!)", 120),            # C(10,3) – як у Мерзляка
    ("20!/16!", 116280),             # A(20,4)
    ("26!/(22!*4!)", 14950),
    ("10! - 9!", 3265920),
    ("3!*2!", 12),
    ("(5!)^2", 14400),
    ("50!", sp.factorial(50)),
])
def test_accepted_factorials(raw, want):
    assert _p(raw) == want


def test_factorial_matches_the_plain_number():
    """Студент може дати і 3628800, і 10! – це те саме."""
    assert engine.equal(_p("10!"), _p("3628800"))
    assert engine.equal(_p("20!/(16!*4!)"), _p("4845"))


def test_factorial_also_allowed_in_expressions():
    """kind=expr користується тим самим простором назв."""
    assert _p("x*3!", "expr") == 6 * sp.Symbol("x")


# --- що мусить відкидатися ----------------------------------------------

@pytest.mark.parametrize("raw", [
    "51!",                  # за межею
    "100!",
    "999999999!",           # ~8,5 млрд цифр – саме через це межа й існує
    "factorial(999999999)",
    "factorial(10**9)",
    "(3+4)!",               # лише ціле число, не вираз
    "x!",
    "factorial(x)",
    "factorial",            # без дужок
    "2**10!",               # розкрилося б у 2**3628800
    "2^10!",
    "2**factorial(10)",
    "1!*2!*3!*4!*5!*6!*7!",  # надто багато факторіалів
])
def test_rejected_factorials(raw):
    with pytest.raises(engine.BadInput):
        _p(raw)


def test_rejection_is_instant():
    """Відкидати треба ДО обчислення – інакше межа не захищає від пам'яті."""
    for raw in ("999999999!", "factorial(999999999)", "2**10!"):
        start = time.perf_counter()
        with pytest.raises(engine.BadInput):
            _p(raw)
        spent = time.perf_counter() - start
        assert spent < 0.05, (raw, spent)


def test_limit_covers_the_whole_bank():
    """Межа мусить перекривати найбільше n, яке трапляється в задачах."""
    assert engine.parse_answer(f"{engine._FACT_LIMIT}!") == sp.factorial(
        engine._FACT_LIMIT)
    assert engine._FACT_LIMIT >= 26, "у банку комбінаторики є n = 26"


def test_old_guards_still_work():
    """Нові перевірки не мають послабити старі."""
    for raw in ("9**9**9", "2**99", "1234567890123"):
        with pytest.raises(engine.BadInput):
            _p(raw)
