"""Тест 1 (первісна та невизначений інтеграл): коректність шаблонів.

Головний запобіжник — test_all_grade_full_on_correct_answers: еталонну відповідь
(вираз первісної) подають назад у grade і вимагають повний бал. Саме це ловить
хибний мінус від символьного порівняння (sp.simplify) на складніших виразах
(корені, tg, exp).
"""

import sympy as sp

import engine
from app.config import SECRET

INTEGRAL1_KEYS = [
    "antideriv_poly_point",
    "antideriv_expand",
    "antideriv_cubic_value",
    "antideriv_reciprocal_sq",
    "antideriv_sqrt",
    "antideriv_linear_power",
    "antideriv_trig_linear",
    "antideriv_exp_linear",
    "antideriv_trig_table",
    "antideriv_find_f",
    "antideriv_find_constant",
    "antideriv_kinematics",
]
NUMBER_KEYS = {"antideriv_cubic_value", "antideriv_find_constant"}


def _build(key, i):
    return engine.build(key, SECRET, f"учень|{i}", "integral1", 1, 0)


def test_has_12_distinct_types():
    assert len(INTEGRAL1_KEYS) == len(set(INTEGRAL1_KEYS)) == 12


def test_all_grade_full_on_correct_answers():
    """Еталон -> повний бал на багатьох варіантах (ловить хибний мінус simplify)."""
    for key in INTEGRAL1_KEYS:
        for i in range(20):
            q = _build(key, i)
            answers = {p.key: str(p.answer) for p in q.parts}
            result = engine.grade(q, answers)
            assert result["score"] == result["max"] == q.max_score, (key, i, result, answers)


def test_wrong_answer_gets_zero():
    """Свідомо хибна відповідь (еталон + 1) -> нуль (немає хибного плюса)."""
    for key in INTEGRAL1_KEYS:
        q = _build(key, 3)
        answers = {p.key: str(sp.sympify(p.answer) + 1) for p in q.parts}
        assert engine.grade(q, answers)["score"] == 0.0, key


def test_statements_use_katex_no_literal_newline():
    for key in INTEGRAL1_KEYS:
        q = _build(key, 1)
        assert "$" in q.statement, key
        assert "\\n" not in q.statement, key  # перенос має бути справжнім \n, не літералом


def test_no_figures():
    """У темі первісної рисунків немає."""
    for key in INTEGRAL1_KEYS:
        assert _build(key, 1).svg is None, key


def test_kinds_as_designed():
    """Числові питання — kind=number; решта — вираз (первісна/функція)."""
    for key in INTEGRAL1_KEYS:
        q = _build(key, 2)
        for p in q.parts:
            if key in NUMBER_KEYS:
                assert p.kind == "number", (key, p.key)
            else:
                assert p.kind == "expr", (key, p.key)


def test_expr_answers_only_use_allowed_symbols():
    """Відповіді-вирази містять лише дозволені змінні (x або t)."""
    allowed = {sp.Symbol("x"), sp.Symbol("t")}
    for key in INTEGRAL1_KEYS:
        if key in NUMBER_KEYS:
            continue
        for i in range(5):
            q = _build(key, i)
            for p in q.parts:
                assert sp.sympify(p.answer).free_symbols <= allowed, (key, p.answer)


def test_number_answers_are_integers():
    for key in NUMBER_KEYS:
        for i in range(20):
            q = _build(key, i)
            for p in q.parts:
                assert sp.sympify(p.answer) == int(p.answer), (key, p.answer)


def test_linear_power_accepts_compact_form():
    """Правило f(kx+b): компактна форма (kx+b)^(n+1)/(k(n+1)) + C теж повний бал
    (не лише розкритий многочлен)."""
    x = sp.Symbol("x")
    for i in range(20):
        q = _build("antideriv_linear_power", i)
        k, b, n, C = (q.params[t] for t in ("k", "b", "n", "C"))
        compact = (k * x + b) ** (n + 1) / (k * (n + 1)) + C
        assert engine.grade(q, {"F": str(compact)})["score"] == 1.0, (i, compact)


def test_points_through_declared_point():
    """Записана первісна справді проходить через оголошену в умові точку M."""
    x = sp.Symbol("x")
    for key in ("antideriv_poly_point", "antideriv_expand", "antideriv_reciprocal_sq",
                "antideriv_sqrt", "antideriv_linear_power", "antideriv_trig_linear",
                "antideriv_exp_linear", "antideriv_trig_table"):
        for i in range(10):
            q = _build(key, i)
            F = sp.sympify(q.parts[0].answer)
            x0 = {
                "antideriv_trig_linear": 0, "antideriv_exp_linear": 0,
            }.get(key, q.params.get("x0"))
            if key == "antideriv_trig_table":
                x0 = 0 if q.params["is_tan"] else sp.pi / 4
            if key in ("antideriv_trig_linear", "antideriv_exp_linear"):
                x0 = 0
            assert sp.simplify(F.subs(x, x0) - q.params["y0"]) == 0, (key, i)
