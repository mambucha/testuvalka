"""Тематичне оцінювання «Інтеграл»: коректність комплексних (багатокрокових) задач.

Окрім звичних перевірок тут ГОЛОВНЕ — механіка часткових балів і перенесення
помилки (carry): студент, який помилився на ранньому кроці, але далі розв'язував
правильно ЗІ СВОГО результату, має отримати бали за ці кроки.
"""

import sympy as sp

import engine
from app.config import SECRET

KEYS = [
    "th_antideriv_poly_point",
    "th_antideriv_table_sum",
    "th_antideriv_rules",
    "th_antideriv_inverse",
    "th_definite_nl",
    "th_definite_trig",
    "th_definite_properties",
    "th_definite_find_limit",
    "th_area_trapezoid",
    "th_area_between",
    "th_area_below_axis",
    "th_physics_path",
]
FIGURE_KEYS = {"th_area_trapezoid", "th_area_between", "th_area_below_axis"}
_x, _t = sp.Symbol("x"), sp.Symbol("t")


def _build(key, i):
    return engine.build(key, SECRET, f"учень|{i}", "integral_thematic", 1, 0)


def _ref(q):
    return {p.key: str(p.answer) for p in q.parts}


def test_has_12_distinct_types():
    assert len(KEYS) == len(set(KEYS)) == 12


def test_all_grade_full_on_correct_answers():
    for key in KEYS:
        for i in range(25):
            q = _build(key, i)
            r = engine.grade(q, _ref(q))
            assert r["score"] == r["max"] == q.max_score, (key, i, r, _ref(q))


def test_every_question_is_multistep():
    """Суть цього тесту — перевіряти ШЛЯХ: щонайменше 2 поля в кожній задачі."""
    for key in KEYS:
        q = _build(key, 1)
        assert len(q.parts) >= 2, (key, len(q.parts))


def test_wrong_everything_gets_zero():
    for key in KEYS:
        q = _build(key, 4)
        # свідомо несумісні відповіді: нічого не має зарахуватися через carry
        r = engine.grade(q, {p.key: "123456" for p in q.parts})
        assert r["score"] == 0.0, (key, r)


def test_statements_use_katex_no_literal_newline():
    for key in KEYS:
        q = _build(key, 1)
        assert "$" in q.statement, key
        assert "\\n" not in q.statement, key


def test_figures_only_on_area_tasks():
    for key in KEYS:
        q = _build(key, 3)
        if key in FIGURE_KEYS:
            assert q.svg and "polygon" in q.svg, key
        else:
            assert q.svg is None, key


# --- ГОЛОВНЕ: часткові бали й перенесення помилки --------------------------

def test_carry_wrong_antiderivative_keeps_later_steps():
    """Хибна первісна, але стала й значення обчислені правильно ЗІ СВОЄЇ ->
    втрачається лише перший крок."""
    for i in range(10):
        q = _build("th_antideriv_poly_point", i)
        F0 = q.parts[0].answer
        x0, x1, y0 = q.params["x0"], q.params["x1"], q.params["y0"]
        wrong = sp.expand(F0 + _x)               # типова похибка в первісній
        my_c = y0 - wrong.subs(_x, x0)
        my_v = wrong.subs(_x, x1) + my_c
        r = engine.grade(q, {"F0": str(wrong), "C": str(my_c), "v": str(my_v)})
        assert r["score"] == 2.0 and r["max"] == 3, (i, r)


def test_carry_wrong_bound_keeps_area_step():
    """Хибна межа інтегрування, але площа узгоджена з власними межами."""
    for i in range(10):
        q = _build("th_area_between", i)
        r1, r2, k, m = (q.params[t] for t in ("r1", "r2", "k", "m"))
        G = sp.integrate((k * _x + m) - _x**2, _x)
        bad_lo = r1 - 1
        my_s = G.subs(_x, r2) - G.subs(_x, bad_lo)
        r = engine.grade(q, {"lo": str(bad_lo), "hi": str(r2), "S": str(my_s)})
        assert r["score"] == 2.0 and r["max"] == 3, (i, r)


def test_below_axis_sign_misconception_costs_exactly_one_step():
    """Нулі та інтеграл правильні, але площу записано зі знаком мінус —
    втрачається саме крок «площа = |інтеграл|» (суть задачі)."""
    for i in range(10):
        q = _build("th_area_below_axis", i)
        ans = {p.key: p.answer for p in q.parts}
        r = engine.grade(q, {
            "lo": str(ans["lo"]), "hi": str(ans["hi"]),
            "I": str(ans["I"]), "S": str(ans["I"]),   # забув модуль
        })
        assert r["score"] == 3.0 and r["max"] == 4, (i, r)


def test_below_axis_carry_keeps_modulus_step_for_wrong_negative_integral():
    """Інтеграл порахований неправильно, але ВІД'ЄМНИЙ, і площа = |свій інтеграл|:
    крок з модулем має зараховуватися (втрачено лише сам інтеграл)."""
    for i in range(10):
        q = _build("th_area_below_axis", i)
        ans = {p.key: p.answer for p in q.parts}
        wrong_i = sp.Integer(-7)                 # не еталон, але від'ємний
        r = engine.grade(q, {
            "lo": str(ans["lo"]), "hi": str(ans["hi"]),
            "I": str(wrong_i), "S": str(-wrong_i),
        })
        assert r["score"] == 3.0 and r["max"] == 4, (i, r)


def test_below_axis_integral_negative_area_positive():
    for i in range(15):
        q = _build("th_area_below_axis", i)
        ans = {p.key: p.answer for p in q.parts}
        assert ans["I"] < 0 < ans["S"] and ans["S"] == -ans["I"], (i, ans)


def test_areas_positive():
    for key in ("th_area_trapezoid", "th_area_between", "th_area_below_axis"):
        for i in range(10):
            q = _build(key, i)
            S = next(p.answer for p in q.parts if p.key == "S")
            assert S > 0, (key, i, S)


def test_find_limit_positive_root_satisfies_equation():
    for i in range(15):
        q = _build("th_definite_find_limit", i)
        a, c, S = q.params["a"], q.params["c"], q.params["S"]
        b = next(p.answer for p in q.parts if p.key == "b")
        assert b > 0 and sp.integrate(a * _x + c, (_x, 0, b)) == S, (i, b)


def test_properties_use_additivity_and_linearity():
    for i in range(15):
        q = _build("th_definite_properties", i)
        p = q.params
        ans = {pt.key: pt.answer for pt in q.parts}
        assert ans["I1"] == p["P"] + p["Q"]                       # адитивність
        assert ans["I2"] == p["al"] * ans["I1"] - p["be"] * p["R"]  # лінійність


def test_antiderivatives_really_are_antiderivatives():
    """Незалежна перевірка: похідна F0 дорівнює підінтегральній функції."""
    checks = {
        "th_antideriv_poly_point": lambda p: p["a"] * _x**2 + p["b"] * _x + p["c"],
        "th_antideriv_table_sum": lambda p: (
            sp.Rational(p["a"], 1) / sp.sqrt(_x) + sp.Rational(p["b"], 1) / _x**2
        ),
    }
    for key, f_of in checks.items():
        for i in range(15):
            q = _build(key, i)
            F0 = next(pt.answer for pt in q.parts if pt.key == "F0")
            assert sp.simplify(sp.diff(F0, _x) - f_of(q.params)) == 0, (key, i)
