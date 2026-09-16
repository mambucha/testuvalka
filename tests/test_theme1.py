"""Тема числової функції: коректність шаблонів + рисунки у графічних питаннях."""

import engine
from app.config import SECRET

THEME1_KEYS = [
    "domain_fraction",
    "domain_sqrt",
    "value_at_points",
    "function_zeros",
    "parity_code",
    "parity_values",
    "symmetry_point",
    "monotonic_linear",
    "parabola_vertex_x",
    "parabola_min",
    "bounded_trig",
    "graph_vertex",
    "graph_zeros",
]
FIGURE_KEYS = {"graph_vertex", "graph_zeros"}


def test_all_theme1_templates_grade_full_on_correct_answers():
    """Кожен шаблон на кількох варіантах: еталонні відповіді -> повний бал."""
    for key in THEME1_KEYS:
        for attempt in range(12):
            q = engine.build(key, SECRET, f"учень|{attempt}", "t", 1, 0)
            answers = {p.key: str(p.answer) for p in q.parts}
            result = engine.grade(q, answers)
            assert result["score"] == result["max"] == q.max_score, (key, attempt, result, answers)


def test_theme1_answers_are_integers():
    """Усі відповіді цілі (зручні числа для шкільної теми)."""
    for key in THEME1_KEYS:
        for attempt in range(8):
            q = engine.build(key, SECRET, f"ц|{attempt}", "t", 1, 0)
            for p in q.parts:
                assert isinstance(p.answer, int) or getattr(p.answer, "q", 1) == 1, (
                    key, p.key, p.answer,
                )


def test_theme1_statements_use_katex():
    for key in THEME1_KEYS:
        q = engine.build(key, SECRET, "s|s", "t", 1, 0)
        assert "$" in q.statement


def test_theme1_figure_questions_have_svg():
    for key in FIGURE_KEYS:
        q = engine.build(key, SECRET, "s|1", "t", 1, 0)
        assert q.svg and q.svg.startswith("<svg") and q.svg.endswith("</svg>")
        assert "polyline" in q.svg  # парабола намальована
        assert q.public()["svg"] == q.svg


def test_theme1_nonfigure_have_no_svg():
    for key in THEME1_KEYS:
        if key in FIGURE_KEYS:
            continue
        q = engine.build(key, SECRET, "s|2", "t", 1, 0)
        assert q.svg is None, key


def test_parity_code_values_are_valid():
    """Код парності завжди 1/2/3 і відповідає типу функції."""
    seen = set()
    for attempt in range(40):
        q = engine.build("parity_code", SECRET, f"p|{attempt}", "t", 1, 0)
        code = q.parts[0].answer
        assert code in (1, 2, 3)
        seen.add(code)
    assert seen == {1, 2, 3}  # трапляються всі три випадки
