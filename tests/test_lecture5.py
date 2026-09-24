"""Лекція 5 (функція, границі, неперервність): коректність шаблонів.

Окрім звичних перевірок тут НЕЗАЛЕЖНО перераховуються самі границі через
sympy.limit — щоб еталон не був «сам собі доказом».
"""

import sympy as sp

import engine
from app.config import SECRET

KEYS = [
    "lim_domain",
    "lim_classify",
    "lim_composite",
    "lim_inverse",
    "lim_rational_infty",
    "lim_zero_over_zero",
    "lim_conjugate",
    "lim_first_important",
    "lim_second_important",
    "lim_piecewise_jump",
    "lim_discontinuity_types",
    "lim_graph_continuity",
]
FIGURE_KEYS = {"lim_graph_continuity"}
_x = sp.Symbol("x")


def _build(key, i):
    return engine.build(key, SECRET, f"учень|{i}", "lecture5", 1, 0)


def _ans(q):
    return {p.key: p.answer for p in q.parts}


def test_has_12_distinct_types():
    assert len(KEYS) == len(set(KEYS)) == 12


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
        r = engine.grade(q, {p.key: "123456" for p in q.parts})
        assert r["score"] == 0.0, (key, r)


def test_statements_use_katex_no_literal_newline():
    for key in KEYS:
        q = _build(key, 1)
        assert "$" in q.statement, key
        assert "\\n" not in q.statement, key


def test_figure_only_on_graph_task():
    for key in KEYS:
        q = _build(key, 3)
        if key in FIGURE_KEYS:
            assert q.svg and "<line" in q.svg, key   # відрізки кусочного графіка
        else:
            assert q.svg is None, key


def test_mostly_multistep():
    """Перевіряємо ШЛЯХ: щонайменше 10 задач із 12 мають 2+ поля."""
    multi = sum(1 for key in KEYS if len(_build(key, 1).parts) >= 2)
    assert multi >= 10, multi


def test_timings_calibrated():
    total = 0
    for key in KEYS:
        q = _build(key, 1)
        assert 60 <= q.seconds <= 200, (key, q.seconds)
        total += q.seconds
    assert total <= 1800, total


# --- незалежна перевірка самих границь ------------------------------------

def test_limits_match_sympy():
    for i in range(20):
        q = _build("lim_rational_infty", i)
        a, d = q.params["a"], q.params["d"]
        assert _ans(q)["l1"] == sp.Rational(a, d)
        assert _ans(q)["l2"] == 0

        q = _build("lim_zero_over_zero", i)
        r, s, qq = q.params["r"], q.params["s"], q.params["q"]
        num = sp.expand((_x - r) * (_x - s))
        den = sp.expand((_x - r) * (_x - qq))
        assert _ans(q)["x0"] == r
        assert _ans(q)["lim"] == sp.limit(num / den, _x, r)

        q = _build("lim_conjugate", i)
        a = q.params["a"]
        assert _ans(q)["lim"] == sp.limit(sp.sqrt(_x**2 + a * _x) - _x, _x, sp.oo)

        q = _build("lim_first_important", i)
        a, b = q.params["a"], q.params["b"]
        assert _ans(q)["l1"] == sp.limit(sp.sin(a * _x) / _x, _x, 0)
        assert _ans(q)["l2"] == sp.limit(sp.sin(a * _x) / sp.tan(b * _x), _x, 0)

        q = _build("lim_second_important", i)
        a, b = q.params["a"], q.params["b"]
        assert _ans(q)["l1"] == sp.limit((1 + sp.Rational(a, 1) / _x) ** _x, _x, sp.oo)
        assert _ans(q)["l2"] == sp.limit(
            (1 + sp.Rational(a, 1) / _x) ** (b * _x), _x, sp.oo
        )


def test_discontinuity_kinds_are_correct():
    """Усувний — спільний корінь (скінченна границя); II роду — корінь лише
    знаменника (границя нескінченна)."""
    for i in range(20):
        q = _build("lim_discontinuity_types", i)
        p, qq, s = q.params["p"], q.params["q"], q.params["s"]
        f = sp.expand((_x - p) * (_x - s)) / sp.expand((_x - p) * (_x - qq))
        a = _ans(q)
        assert a["rem"] == p and a["inf"] == qq
        assert a["lim"] == sp.limit(f, _x, p)          # скінченна
        assert sp.limit(sp.Abs(f), _x, qq) == sp.oo    # нескінченна
        assert a["lim"].is_finite


def test_piecewise_jump_is_difference_of_one_sided_limits():
    for i in range(20):
        q = _build("lim_piecewise_jump", i)
        p = q.params
        a = _ans(q)
        assert a["L"] == p["k1"] * p["x0"] + p["b1"]
        assert a["R"] == p["k2"] * p["x0"] + p["b2"]
        assert a["J"] == a["R"] - a["L"]


def test_parity_is_genuine():
    """f(-x) справді дорівнює f(-x) (парна -> f, непарна -> -f)."""
    for i in range(20):
        q = _build("lim_classify", i)
        fneg = _ans(q)["fneg"]
        assert sp.simplify(fneg - fneg.subs(_x, -_x) * (1 if q.params["even"] else -1)) == 0


def test_inverse_is_really_inverse():
    """φ(f(x)) = x — тобто знайдена функція справді обернена."""
    for i in range(20):
        q = _build("lim_inverse", i)
        a, b = q.params["a"], q.params["b"]
        inv = _ans(q)["inv"]
        assert sp.simplify(inv.subs(_x, a * _x + b) - _x) == 0


# --- перенесення помилки --------------------------------------------------

def test_carry_wrong_fneg_keeps_value_step():
    for i in range(10):
        q = _build("lim_classify", i)
        fneg = _ans(q)["fneg"]
        x0 = q.params["x0"]
        wrong = sp.expand(fneg + _x)
        r = engine.grade(q, {
            "fneg": str(wrong),
            "val": str(wrong.subs(_x, x0)),
            "T": str(_ans(q)["T"]),
        })
        assert r["score"] == 2.0 and r["max"] == 3, (i, r)


def test_carry_wrong_one_sided_limits_keep_jump():
    for i in range(10):
        q = _build("lim_piecewise_jump", i)
        a = _ans(q)
        badL, badR = a["L"] + 5, a["R"] - 2
        r = engine.grade(q, {"L": str(badL), "R": str(badR), "J": str(badR - badL)})
        assert r["score"] == 1.0 and r["max"] == 3, (i, r)
