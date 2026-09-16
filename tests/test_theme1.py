"""Тема числової функції: коректність шаблонів + рисунки у графічних питаннях."""

import engine
from app.config import SECRET

THEME1_KEYS = [
    "domain_fraction",
    "domain_sqrt",
    "value_at_points",
    "value_solve",
    "function_zeros",
    "zeros_linear",
    "range_endpoints",
    "parity_compute",
    "parity_values",
    "symmetry_point",
    "parabola_vertex_x",
    "graph_vertex",
    "graph_zeros",
]
FIGURE_KEYS = {"graph_vertex", "graph_zeros"}
# parity_compute дає вираз (не число), тож у перевірці цілих його пропускаємо.
EXPR_KEYS = {"parity_compute"}


def test_all_theme1_templates_grade_full_on_correct_answers():
    """Кожен шаблон на кількох варіантах: еталонні відповіді -> повний бал."""
    for key in THEME1_KEYS:
        for attempt in range(12):
            q = engine.build(key, SECRET, f"учень|{attempt}", "t", 1, 0)
            answers = {p.key: str(p.answer) for p in q.parts}
            result = engine.grade(q, answers)
            assert result["score"] == result["max"] == q.max_score, (key, attempt, result, answers)


def test_theme1_numeric_answers_are_integers():
    """Числові відповіді цілі; питання-вираз (parity_compute) пропускаємо."""
    for key in THEME1_KEYS:
        if key in EXPR_KEYS:
            continue
        for attempt in range(8):
            q = engine.build(key, SECRET, f"ц|{attempt}", "t", 1, 0)
            for p in q.parts:
                assert isinstance(p.answer, int) or getattr(p.answer, "q", 1) == 1, (
                    key, p.key, p.answer,
                )


def test_parity_compute_is_expr_and_accepts_equivalent_forms():
    """f(-x): відповідь є виразом, приймаються еквівалентні форми запису."""
    q = None
    for attempt in range(30):
        cand = engine.build("parity_compute", SECRET, f"p|{attempt}", "t", 1, 0)
        if cand.params["kind"] == "odd":
            q = cand
            break
    assert q is not None
    part = q.parts[0]
    assert part.kind == "expr"
    # правильна форма
    assert engine.grade(q, {"fneg": str(part.answer)})["score"] == 1.0
    # еквівалентна форма з ^ замість **
    alt = str(part.answer).replace("**", "^")
    assert engine.grade(q, {"fneg": alt})["score"] == 1.0


def test_theme1_statements_no_em_dash():
    """У жодній умові немає довгих тире (стиль без em dash)."""
    for key in THEME1_KEYS:
        q = engine.build(key, SECRET, "s|s", "t", 1, 0)
        assert "—" not in q.statement, key
        for p in q.parts:
            assert "—" not in p.label, (key, p.key)


def test_theme1_figure_questions_have_svg():
    for key in FIGURE_KEYS:
        q = engine.build(key, SECRET, "s|1", "t", 1, 0)
        assert q.svg and q.svg.startswith("<svg") and q.svg.endswith("</svg>")
        assert "polyline" in q.svg
        assert q.public()["svg"] == q.svg


def test_theme1_nonfigure_have_no_svg():
    for key in THEME1_KEYS:
        if key in FIGURE_KEYS:
            continue
        q = engine.build(key, SECRET, "s|2", "t", 1, 0)
        assert q.svg is None, key
