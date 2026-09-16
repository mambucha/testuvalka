"""Лекція 2: коректність шаблонів + рисунок (SVG) у завданні з графіком."""

import engine
from app.config import SECRET

LECTURE2_KEYS = [
    "general_line_C",
    "slope_intercept_from_general",
    "line_intercepts",
    "distance_point_to_line",
    "point_substitution",
    "direction_vector_2pts",
    "space_direction_vector",
    "dot_product_3d",
    "perpendicular_parallel_slope",
    "line_through_two_points",
    "line_from_graph",
]


def test_all_lecture2_templates_grade_full_on_correct_answers():
    """Кожен шаблон: побудова -> правильні відповіді з еталонів -> повний бал."""
    for key in LECTURE2_KEYS:
        for attempt in range(8):  # кілька варіантів кожного (різні гілки rng)
            q = engine.build(key, SECRET, f"стд|{attempt}", "t", 1, 0)
            answers = {p.key: str(p.answer) for p in q.parts}
            result = engine.grade(q, answers)
            assert result["score"] == result["max"] == q.max_score, (key, result, answers)


def test_lecture2_statements_use_katex_delimiters():
    for key in LECTURE2_KEYS:
        q = engine.build(key, SECRET, "s|s", "t", 1, 0)
        assert "$" in q.statement


def test_line_from_graph_has_valid_svg():
    """Завдання з графіком мусить нести придатний inline-SVG, а public() —
    віддавати його в браузер."""
    q = engine.build("line_from_graph", SECRET, "s|1", "t", 1, 0)
    assert q.svg is not None
    assert q.svg.startswith("<svg") and q.svg.endswith("</svg>")
    assert "viewBox" in q.svg
    # осі + пряма присутні
    assert q.svg.count("<line") >= 3
    pub = q.public()
    assert pub["svg"] == q.svg


def test_non_figure_templates_have_no_svg():
    """Решта завдань — без рисунка (svg None), тож блок рисунка не показується."""
    for key in LECTURE2_KEYS:
        if key == "line_from_graph":
            continue
        q = engine.build(key, SECRET, "s|3", "t", 1, 0)
        assert q.svg is None, key


def test_public_svg_is_none_for_plain_questions():
    """Регрес: у public() є ключ svg, і він None для звичайних задач."""
    q = engine.build("dot_product_3d", SECRET, "s|1", "t", 1, 0)
    pub = q.public()
    assert "svg" in pub and pub["svg"] is None
