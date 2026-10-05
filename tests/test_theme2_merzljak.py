"""Степенева функція та корінь – набір за підручником Мерзляка (§2–§5).

Окрім звичних перевірок тут НЕЗАЛЕЖНО перераховується математика кожної задачі
і закріплено суть кожного типу вправи: порівняння значень має спиратися на
монотонність/парність, корінь парного степеня з від'ємного не існує, тощо.
"""

import re

import sympy as sp

import engine
from app.config import SECRET

# Літеральний "\n" замість переносу; \ne, \nu – валідні команди LaTeX.
_BAD_NEWLINE = re.compile(r"\\n(?![a-zA-Z])")

PARA2 = ["mz_find_exponent", "mz_compare_power", "mz_minmax_power"]
PARA3 = ["mz_int_power_expr", "mz_compare_int_power"]
PARA4 = ["mz_root_sense", "mz_solve_power_eq"]
PARA5 = ["mz_factor_out", "mz_bring_under", "mz_simplify_sign"]
GRAPHS = ["mz_graph_roots_count", "mz_graph_int_power"]
KEYS = PARA2 + PARA3 + PARA4 + PARA5 + GRAPHS
_x = sp.Symbol("x")


def _build(key, i):
    return engine.build(key, SECRET, f"учень|{i}", "theme2", 1, 0)


def _a(q):
    return {p.key: p.answer for p in q.parts}


def test_has_12_types_covering_all_paragraphs():
    assert len(KEYS) == len(set(KEYS)) == 12
    assert len(GRAPHS) == 2, "викладач просив пару задач із графіками"
    for group in (PARA2, PARA3, PARA4, PARA5):
        assert group, "кожен параграф має бути представлений"


def test_all_grade_full_on_correct_answers():
    for key in KEYS:
        for i in range(25):
            q = _build(key, i)
            sub = {p.key: str(p.answer) for p in q.parts}
            r = engine.grade(q, sub)
            assert r["score"] == r["max"] == q.max_score, (key, i, r, sub)


def test_garbage_gets_zero():
    for key in KEYS:
        q = _build(key, 4)
        assert engine.grade(q, {p.key: "123456" for p in q.parts})["score"] == 0.0, key


def test_statements_katex_no_literal_newline():
    for key in KEYS:
        q = _build(key, 1)
        assert "$" in q.statement, key
        assert not _BAD_NEWLINE.search(q.statement), key


def test_every_task_is_multistep():
    for key in KEYS:
        assert len(_build(key, 1).parts) >= 2, key


def test_figures_only_on_graph_tasks():
    for key in KEYS:
        q = _build(key, 3)
        if key in GRAPHS:
            assert q.svg and "polyline" in q.svg, key   # криву намальовано
        else:
            assert q.svg is None, key


def test_no_rational_exponent_topic():
    """§6 (степінь з раціональним показником) – наступна тема, сюди не входить."""
    for key in KEYS:
        for i in range(8):
            s = _build(key, i).statement.replace(" ", "")
            assert "frac{1}{2}}" not in s, (key, "дробовий показник")
            assert "frac{2}{3}}" not in s, (key, "дробовий показник")


def test_timings_calibrated():
    total = 0
    for key in KEYS:
        q = _build(key, 1)
        assert 90 <= q.seconds <= 200, (key, q.seconds)
        total += q.seconds
    assert total <= 1800, total


# --- §2 ---------------------------------------------------------------

def test_find_exponent_math():
    for i in range(30):
        q = _build("mz_find_exponent", i)
        p, a = q.params, _a(q)
        assert p["a"] ** a["n"] == p["y"]
        assert a["val"] == (-p["a"]) ** a["n"]
        assert [k for k in range(1, 13) if p["a"] ** k == p["y"]] == [a["n"]]


def test_compare_power_uses_monotonicity_and_parity():
    """Відповідь має бути тим аргументом, де значення справді більше."""
    for i in range(40):
        q = _build("mz_compare_power", i)
        p, a = q.params, _a(q)
        n = p["n"]
        f = lambda v: sp.Integer(v) ** n          # noqa: E731
        assert f(a["b1"]) == max(f(-p["p"]), f(-p["q"]))
        assert f(a["b2"]) == max(f(p["s"]), f(-p["t"]))
        assert f(-p["p"]) != f(-p["q"]), "значення не мають збігатися"
        assert f(p["s"]) != f(-p["t"])
        assert n >= 19, "показник має бути великим – інакше виручить калькулятор"


def test_minmax_power_math():
    for i in range(40):
        q = _build("mz_minmax_power", i)
        p, a = q.params, _a(q)
        n, lo, hi = p["n"], p["lo"], p["hi"]
        xs = list(range(lo, hi + 1))
        vals = [sp.Integer(v) ** n for v in xs]
        assert a["vmin"] == min(vals) and a["vmax"] == max(vals), (p, a)


# --- §3 ---------------------------------------------------------------

def test_int_power_expr_math():
    for i in range(30):
        q = _build("mz_int_power_expr", i)
        p, a = q.params, _a(q)
        t1 = sp.Rational(1, p["a"] ** p["p"])
        t2 = sp.Rational(1, p["b"] ** p["q"])
        assert a["t1"] == t1
        assert a["total"] == (t1 - t2 if p["minus"] else t1 + t2)
        assert sp.denom(a["total"]) != 1, "відповідь має бути дробом"


def test_compare_int_power_math():
    for i in range(40):
        q = _build("mz_compare_int_power", i)
        p, a = q.params, _a(q)
        n = p["n"]
        f = lambda v: sp.Rational(1, 1) / sp.Integer(v) ** n   # noqa: E731
        assert f(a["b1"]) == max(f(p["p"]), f(p["q"]))
        assert f(a["b2"]) == max(f(p["s"]), f(-p["t"]))
        assert a["b1"] != a["b2"], "відповіді двох пунктів не мають збігатися"


# --- §4 ---------------------------------------------------------------

def test_root_sense_counts_only_valid_records():
    for i in range(40):
        q = _build("mz_root_sense", i)
        a = _a(q)
        # серед чотирьох записів рівно один – парний корінь з від'ємного
        assert a["cnt"] == 3, "три записи мають зміст, один – ні"
        assert a["val"] == -q.params["c"]
        assert a["val"] ** 3 == -(q.params["c"] ** 3)


def test_solve_power_eq_math():
    for i in range(30):
        q = _build("mz_solve_power_eq", i)
        p, a = q.params, _a(q)
        n = 2 * p["k"]
        assert (a["lo"] - p["c"]) ** n == p["a"] == (a["hi"] - p["c"]) ** n
        assert a["lo"] < a["hi"]


# --- §5 ---------------------------------------------------------------

def test_factor_out_math_and_degrees_vary():
    degrees = set()
    for i in range(40):
        q = _build("mz_factor_out", i)
        p, a = q.params, _a(q)
        degrees.add(p["n"])
        assert sp.simplify(a["coef"] ** p["n"] * a["rad"] - p["inner"] * _x ** p["n"]) == 0
    assert degrees == {2, 3}, ("корінь не лише квадратний", degrees)


def test_bring_under_math():
    """Внесення під корінь – дія, обернена до винесення."""
    degrees = set()
    for i in range(40):
        q = _build("mz_bring_under", i)
        p, a = q.params, _a(q)
        degrees.add(p["n"])
        assert a["pw"] == p["c"] ** p["n"]
        assert a["inner"] == p["c"] ** p["n"] * p["r"]
        # c * ⁿ√r  і  ⁿ√(cⁿ·r) – те саме число
        assert sp.simplify(p["c"] * sp.root(p["r"], p["n"])
                           - sp.root(a["inner"], p["n"])) == 0
    assert degrees == {2, 3}


def test_simplify_sign_is_nonnegative():
    for i in range(30):
        q = _build("mz_simplify_sign", i)
        p, a = q.params, _a(q)
        assert sp.simplify(a["simp"] - (-p["c"] * _x)) == 0
        assert a["val"] > 0, "корінь парного степеня невід'ємний"


# --- графіки ------------------------------------------------------------

def test_graph_roots_count_math():
    counts = set()
    for i in range(40):
        q = _build("mz_graph_roots_count", i)
        p, a = q.params, _a(q)
        roots = sp.solve(sp.Eq(_x**2, p["k"] * _x + p["b"]), _x)
        counts.add(a["cnt"])
        assert a["cnt"] == len(set(roots))
        assert a["big"] == max(roots)
    assert counts == {1, 2}, ("має траплятися і дотик (1 корінь)", counts)


def test_graph_int_power_math():
    for i in range(30):
        q = _build("mz_graph_int_power", i)
        p, a = q.params, _a(q)
        assert a["gap"] == 0                       # розрив у нулі
        assert a["val"] == sp.Rational(1, p["x0"] ** p["n"])


# --- перенесення помилки ------------------------------------------------

def test_carry_wrong_power_keeps_second_step():
    for i in range(10):
        q = _build("mz_bring_under", i)
        p, a = q.params, _a(q)
        wrong = a["pw"] + 1
        r = engine.grade(q, {"pw": str(wrong), "inner": str(wrong * p["r"])})
        assert r["score"] == 1.0 and r["max"] == 2, (i, r)
