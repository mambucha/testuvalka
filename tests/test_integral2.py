"""Тест 2 (визначений інтеграл і площі): коректність шаблонів.

Головний запобіжник — test_all_grade_full_on_correct_answers. Незалежну
математичну перевірку (реконструкція інтеграла з параметрів) винесено в
test_answers_correct.py::test_integral2_math.
"""

import sympy as sp

import engine
from app.config import SECRET

INTEGRAL2_KEYS = [
    "def_nl_poly",
    "def_nl_trig",
    "def_nl_sqrt",
    "def_nl_reciprocal",
    "def_nl_from_F",
    "def_property_linear",
    "def_find_limit",
    "area_trapezoid",
    "area_parabola_axis",
    "area_parabola_line",
    "area_below_axis",
    "def_displacement",
]
FIGURE_KEYS = {"area_trapezoid", "area_parabola_axis", "area_parabola_line", "area_below_axis"}


def _build(key, i):
    return engine.build(key, SECRET, f"учень|{i}", "integral2", 1, 0)


def test_has_12_distinct_types():
    assert len(INTEGRAL2_KEYS) == len(set(INTEGRAL2_KEYS)) == 12


def test_all_grade_full_on_correct_answers():
    for key in INTEGRAL2_KEYS:
        for i in range(20):
            q = _build(key, i)
            answers = {p.key: str(p.answer) for p in q.parts}
            result = engine.grade(q, answers)
            assert result["score"] == result["max"] == q.max_score, (key, i, result, answers)


def test_wrong_answer_gets_zero():
    for key in INTEGRAL2_KEYS:
        q = _build(key, 5)
        answers = {p.key: str(sp.sympify(p.answer) + 1) for p in q.parts}
        assert engine.grade(q, answers)["score"] == 0.0, key


def test_statements_use_katex_no_literal_newline():
    for key in INTEGRAL2_KEYS:
        q = _build(key, 1)
        assert "$" in q.statement, key
        assert "\\n" not in q.statement, key


def test_all_answers_are_numbers():
    """Усі відповіді — числа (площі та інтеграли)."""
    for key in INTEGRAL2_KEYS:
        q = _build(key, 2)
        for p in q.parts:
            assert p.kind == "number", (key, p.key)
            assert sp.sympify(p.answer).free_symbols == set(), (key, p.answer)


def test_figures_present_only_on_area_tasks():
    for key in INTEGRAL2_KEYS:
        q = _build(key, 3)
        if key in FIGURE_KEYS:
            assert q.svg and q.svg.startswith("<svg"), key
            assert "polygon" in q.svg, (key, "немає заштрихованої області")
        else:
            assert q.svg is None, key


def test_areas_are_positive():
    """Площа завжди додатна (зокрема для фігури під віссю = |інтеграл|)."""
    for key in ("area_trapezoid", "area_parabola_axis", "area_parabola_line", "area_below_axis"):
        for i in range(15):
            q = _build(key, i)
            assert sp.sympify(q.parts[0].answer) > 0, (key, i)


def test_find_limit_is_positive_root():
    """Відповідь оберненої задачі — саме додатний корінь b."""
    for i in range(15):
        q = _build("def_find_limit", i)
        a, S, b = q.params["a"], q.params["S"], q.parts[0].answer
        assert b > 0 and sp.Rational(a, 1) * b**2 / 2 == S, (i, a, S, b)
