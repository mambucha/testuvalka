"""Лекція 3 (криві другого порядку): коректність шаблонів + рисунки."""

import engine
from app.config import SECRET

LECTURE3_KEYS = [
    "circle_from_canonical",
    "circle_from_general",
    "circle_radius_through_point",
    "ellipse_semi_axes_focus",
    "ellipse_eccentricity",
    "distance_foci",
    "hyperbola_semi_axes_focus",
    "hyperbola_asymptote",
    "parabola_param_focus",
    "curve_center_general",
    "circle_from_graph",
    "ellipse_from_graph",
]
FIGURE_KEYS = {"circle_from_graph", "ellipse_from_graph"}


def test_has_12_distinct_types():
    assert len(LECTURE3_KEYS) == len(set(LECTURE3_KEYS)) == 12


def test_all_grade_full_on_correct_answers():
    """Кожен шаблон на кількох варіантах: еталонні відповіді -> повний бал."""
    for key in LECTURE3_KEYS:
        for attempt in range(12):
            q = engine.build(key, SECRET, f"студ|{attempt}", "t", 1, 0)
            answers = {p.key: str(p.answer) for p in q.parts}
            result = engine.grade(q, answers)
            assert result["score"] == result["max"] == q.max_score, (key, attempt, result, answers)


def test_statements_use_katex_and_no_literal_newline():
    """Умови мають математику в $...$, і жодних літеральних '\\n' (raw-помилка)."""
    for key in LECTURE3_KEYS:
        q = engine.build(key, SECRET, "s|s", "t", 1, 0)
        assert "$" in q.statement
        assert "\\n" not in q.statement, key  # має бути справжній перенос, не літерал


def test_figure_questions_have_svg():
    for key in FIGURE_KEYS:
        q = engine.build(key, SECRET, "s|1", "t", 1, 0)
        assert q.svg and q.svg.startswith("<svg") and q.svg.endswith("</svg>")
        assert q.public()["svg"] == q.svg
    # коло малюється <circle>, еліпс <ellipse>
    assert "<circle" in engine.build("circle_from_graph", SECRET, "s|1", "t", 1, 0).svg
    assert "<ellipse" in engine.build("ellipse_from_graph", SECRET, "s|1", "t", 1, 0).svg


def test_nonfigure_have_no_svg():
    for key in LECTURE3_KEYS:
        if key in FIGURE_KEYS:
            continue
        q = engine.build(key, SECRET, "s|2", "t", 1, 0)
        assert q.svg is None, key


def test_eccentricity_accepts_fraction_forms():
    """Ексцентриситет — дріб; приймаються дробова та нескорочена форми."""
    import sympy as sp

    q = engine.build("ellipse_eccentricity", SECRET, "s|1", "t", 1, 0)
    ans = q.parts[0].answer  # sympy Rational, напр 4/5
    assert engine.grade(q, {"e": str(ans)})["score"] == 1.0
    # нескорочена еквівалентна форма (8/10 для 4/5)
    unreduced = f"{ans.p * 2}/{ans.q * 2}"
    assert engine.grade(q, {"e": unreduced})["score"] == 1.0
