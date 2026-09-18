"""Тема 2 (степенева функція та корені): коректність шаблонів."""

import engine
from app.config import SECRET

THEME2_KEYS = [
    "root_value",
    "odd_root_negative",
    "root_expression",
    "even_root_modulus",
    "power_value",
    "negative_power_value",
    "root_product",
    "root_quotient",
    "root_simplify",
    "power_of_root",
    "compare_roots_lcm",
    "root_function_domain",
]
EXPR_KEYS = {"root_simplify"}


def test_has_12_distinct_types():
    assert len(THEME2_KEYS) == len(set(THEME2_KEYS)) == 12


def test_all_grade_full_on_correct_answers():
    """Кожен шаблон на багатьох варіантах: еталонні відповіді -> повний бал."""
    for key in THEME2_KEYS:
        for attempt in range(15):
            q = engine.build(key, SECRET, f"учень|{attempt}", "t", 1, 0)
            answers = {p.key: str(p.answer) for p in q.parts}
            result = engine.grade(q, answers)
            assert result["score"] == result["max"] == q.max_score, (key, attempt, result, answers)


def test_statements_use_katex_no_literal_newline():
    for key in THEME2_KEYS:
        q = engine.build(key, SECRET, "s|s", "t", 1, 0)
        assert "$" in q.statement
        assert "\\n" not in q.statement, key


def test_no_graphics_in_this_theme():
    """У темі немає рисунків (графічні перетворення не вивчали)."""
    for key in THEME2_KEYS:
        q = engine.build(key, SECRET, "s|1", "t", 1, 0)
        assert q.svg is None, key


def test_root_simplify_is_expr_and_accepts_forms():
    """Винесення множника: відповідь-вираз, приймаються різні форми запису."""
    q = engine.build("root_simplify", SECRET, "s|1", "t", 1, 0)
    assert q.parts[0].kind == "expr"
    ans = q.parts[0].answer  # k*sqrt(m)
    assert engine.grade(q, {"v": str(ans)})["score"] == 1.0
    # implicit-форма без зірочки: "5sqrt(2)"
    import sympy as sp

    k, m = q.params["k"], q.params["m"]
    assert engine.grade(q, {"v": f"{k}sqrt({m})"})["score"] == 1.0


def test_even_root_modulus_is_nonnegative():
    """Відповідь властивості з модулем завжди додатна (перевірка суті)."""
    for attempt in range(10):
        q = engine.build("even_root_modulus", SECRET, f"m|{attempt}", "t", 1, 0)
        assert q.parts[0].answer > 0


def test_odd_root_negative_answer_is_negative():
    for attempt in range(10):
        q = engine.build("odd_root_negative", SECRET, f"o|{attempt}", "t", 1, 0)
        assert q.parts[0].answer < 0
