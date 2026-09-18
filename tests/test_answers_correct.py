"""ЗМІСТОВНА перевірка правильності еталонів (не тавтологія «еталон = еталон»).

Для кожного обчислювального шаблону незалежно (через sympy або пряму формулу)
рахуємо правильну відповідь і звіряємо з еталоном, який видає шаблон. Саме брак
такої перевірки колись пропустив бракований root_product (√2·√4 з відповіддю 3).

Тривіальні шаблони (де відповідь просто зчитується з параметрів, напр. центр кола
з канонічного рівняння) тут не дублюються — там нема обчислення, яке могло б
розійтися з умовою.
"""

import sympy as sp

import engine
from app.config import SECRET

N = 120


def _each(key):
    for i in range(N):
        q = engine.build(key, SECRET, f"chk|{i}", "t", 1, 0)
        yield q, q.params, {p.key: p.answer for p in q.parts}


# --- theme2: степенева функція та корені ---------------------------------

def test_theme2_math():
    for q, p, a in _each("root_value"):
        assert a["v"] ** p["n"] == p["a"]
    for q, p, a in _each("odd_root_negative"):
        assert a["v"] ** p["n"] == p["a"] and a["v"] < 0
    for q, p, a in _each("even_root_modulus"):
        assert a["v"] == abs(p["a"]) and a["v"] >= 0
    for q, p, a in _each("power_value"):
        assert p["a"] ** p["n"] == a["v"]
    for q, p, a in _each("negative_power_value"):
        assert sp.Rational(1, p["a"] ** p["n"]) == a["v"]
    for q, p, a in _each("root_product"):
        assert a["v"] * a["v"] == p["a"] * p["b"]
    for q, p, a in _each("root_quotient"):
        assert a["v"] * a["v"] * p["b"] == p["a"]
    for q, p, a in _each("root_simplify"):
        assert sp.simplify(a["v"] ** 2 - p["k"] ** 2 * p["m"]) == 0
    for q, p, a in _each("power_of_root"):
        assert sp.simplify(sp.sqrt(p["a"]) ** p["k"] - a["v"]) == 0
    for q, p, a in _each("compare_roots_lcm"):
        assert sp.ilcm(p["n1"], p["n2"]) == a["v"]
    for q, p, a in _each("root_function_domain"):
        assert p["a"] * a["x0"] + p["b"] == 0
    for q, p, a in _each("root_expression"):
        v = (sp.real_root(p["a1"], p["n1"]) - p["k"] * sp.real_root(p["a2"], p["n2"])
             + sp.real_root(p["a3"], 3))
        assert sp.simplify(v - a["v"]) == 0


# --- lecture1: визначники та СЛАР ----------------------------------------

def test_lecture1_math():
    for q, p, a in _each("det_2x2"):
        assert p["a"] * p["d"] - p["b"] * p["c"] == a["d"]
    for q, p, a in _each("det_3x3_sarrus"):
        assert sp.Matrix(p["m"]).det() == a["d"]
    for q, p, a in _each("det_triangular"):
        assert sp.Matrix(p["m"]).det() == a["d"]
    for q, p, a in _each("linear_system_2x2"):
        M = sp.Matrix([[p["a"], p["b"]], [p["c"], p["d"]]])
        assert M.det() == a["det"]
        sol = M.solve(sp.Matrix([p["e"], p["f"]]))
        assert sol[0] == a["x"] and sol[1] == a["y"]
    for q, p, a in _each("cramer_3x3"):
        A = sp.Matrix(p["A"])
        assert A.det() == a["det"]
        sol = A.solve(sp.Matrix(p["b"]))
        k = int(p["var"][-1]) - 1
        assert sol[k] == a[p["var"]]


# --- lecture3: криві другого порядку -------------------------------------

def test_lecture3_math():
    for q, p, a in _each("ellipse_semi_axes_focus"):
        assert a["a"] > a["b"] and a["a"] ** 2 - a["b"] ** 2 == a["c"] ** 2
    for q, p, a in _each("ellipse_eccentricity"):
        assert a["e"] == sp.Rational(p["c"], p["a"]) and 0 <= a["e"] < 1
    for q, p, a in _each("distance_foci"):
        assert a["d"] == 2 * p["c"]
    for q, p, a in _each("hyperbola_semi_axes_focus"):
        assert a["a"] ** 2 + a["b"] ** 2 == a["c"] ** 2
    for q, p, a in _each("hyperbola_asymptote"):
        assert a["k"] == sp.Rational(p["b"], p["a"])
    for q, p, a in _each("parabola_param_focus"):
        assert a["xf"] == sp.Rational(a["p"], 2) and a["dir"] == -a["xf"]
    for q, p, a in _each("circle_radius_through_point"):
        d2 = (p["px"] - p["a"]) ** 2 + (p["py"] - p["b"]) ** 2
        assert a["R"] ** 2 == d2


# --- theme1: числова функція ---------------------------------------------

def test_theme1_math():
    for q, p, a in _each("function_zeros"):
        for r in (a["lo"], a["hi"]):
            assert r ** 2 + p["b"] * r + p["c"] == 0
    for q, p, a in _each("value_solve"):
        for r in (a["lo"], a["hi"]):
            assert r ** 2 + p["b"] * r + p["c"] == p["m"]
    for q, p, a in _each("parabola_vertex_x"):
        assert sp.Rational(-p["b"], 2 * p["a"]) == a["xv"]
    for q, p, a in _each("domain_fraction"):
        for r in (a["x1"], a["x2"]):
            assert (r - p["p"]) * (r - p["q"]) == 0
    for q, p, a in _each("domain_sqrt"):
        assert p["a"] * a["x0"] + p["b"] == 0
    for q, p, a in _each("zeros_linear"):
        assert p["k"] * a["x0"] + p["b"] == 0
    for q, p, a in _each("symmetry_point"):
        assert abs(a["x"]) == abs(p["p"]) and abs(a["y"]) == abs(p["q"])
