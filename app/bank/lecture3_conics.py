"""Лекція 3: криві другого порядку — коло, еліпс, гіпербола, парабола.

12 різних типів завдань (беруться всі 12, тож у тесті немає повторів типу).
Два завдання з рисунками (коло й еліпс на координатній площині). Числа
підібрані так, щоб відповіді були цілими або простими дробами (піфагорові
трійки для фокусів еліпса/гіперболи).

Конвенція запису: проза текстом, математика в $...$ / $$...$$, переноси \\n.
"""

from __future__ import annotations

import random

from engine import Part, Question, template

from app.bank.plotting import coordinate_plane

# Піфагорові трійки для «красивих» фокусів.
_ELLIPSE = [(5, 3, 4), (5, 4, 3), (10, 6, 8), (10, 8, 6), (13, 5, 12), (13, 12, 5)]  # a>b, c=√(a²-b²)
_HYPER = [(3, 4, 5), (4, 3, 5), (6, 8, 10), (8, 6, 10), (5, 12, 13), (12, 5, 13)]     # c=√(a²+b²)


def _shift(var: str, a: int) -> str:
    """LaTeX для (var - a): 'x - 3', 'x + 3' (при a<0), 'x' (при a=0)."""
    if a == 0:
        return var
    return f"{var} - {a}" if a > 0 else f"{var} + {-a}"


def _signed(coef: int, var: str) -> str:
    """Доданок зі знаком для загального рівняння: '+ 8x', '- 2y', '' при 0."""
    if coef == 0:
        return ""
    return f" + {coef}{var}" if coef > 0 else f" - {-coef}{var}"


# --- коло ----------------------------------------------------------------


@template("circle_from_canonical")
def _circle_from_canonical(rng: random.Random) -> Question:
    a, b = rng.randint(-5, 5), rng.randint(-5, 5)
    R = rng.randint(2, 7)
    return Question(
        key="circle_from_canonical",
        statement=(
            rf"Дано рівняння кола $({_shift('x', a)})^2 + ({_shift('y', b)})^2 = {R*R}$."
            "\nЗнайдіть координати центра $(a; b)$ та радіус $R$."
        ),
        parts=[
            Part("a", "$a$ =", a, points=1),
            Part("b", "$b$ =", b, points=1),
            Part("R", "$R$ =", R, points=1),
        ],
        seconds=45,
        params={"a": a, "b": b, "R": R},
    )


@template("circle_from_general")
def _circle_from_general(rng: random.Random) -> Question:
    """Загальне рівняння -> центр і радіус через виділення повних квадратів."""
    a, b = rng.randint(-4, 4), rng.randint(-4, 4)
    R = rng.randint(2, 6)
    D, E, F = -2 * a, -2 * b, a * a + b * b - R * R
    f_term = "" if F == 0 else (f" + {F}" if F > 0 else f" - {-F}")
    eq = "x^2 + y^2" + _signed(D, "x") + _signed(E, "y") + f_term + " = 0"
    return Question(
        key="circle_from_general",
        statement=(
            "Звівши загальне рівняння до канонічного (виділіть повні квадрати), "
            "знайдіть центр $(a; b)$ і радіус $R$ кола:\n"
            f"$${eq}$$"
        ),
        parts=[
            Part("a", "$a$ =", a, points=1),
            Part("b", "$b$ =", b, points=1),
            Part("R", "$R$ =", R, points=1),
        ],
        seconds=120,
        params={"a": a, "b": b, "R": R},
    )


@template("circle_radius_through_point")
def _circle_radius_through_point(rng: random.Random) -> Question:
    """Радіус кола з центром C, що проходить через точку P (R = |CP|)."""
    a, b = rng.randint(-4, 4), rng.randint(-4, 4)
    dx, dy, R = rng.choice([(3, 4, 5), (4, 3, 5), (6, 8, 10), (0, 5, 5), (5, 0, 5), (0, 3, 3)])
    dx *= rng.choice([1, -1])
    dy *= rng.choice([1, -1])
    px, py = a + dx, b + dy
    return Question(
        key="circle_radius_through_point",
        statement=(
            rf"Коло має центр $C({a}; {b})$ і проходить через точку $M({px}; {py})$."
            "\nЗнайдіть радіус кола $R$ (відстань від центра до точки)."
        ),
        parts=[Part("R", "$R$ =", R, points=1)],
        seconds=70,
        params={"a": a, "b": b, "px": px, "py": py},
    )


# --- еліпс ---------------------------------------------------------------


@template("ellipse_semi_axes_focus")
def _ellipse_semi_axes_focus(rng: random.Random) -> Question:
    a, b, c = rng.choice(_ELLIPSE)
    return Question(
        key="ellipse_semi_axes_focus",
        statement=(
            rf"Дано еліпс $\dfrac{{x^2}}{{{a*a}}} + \dfrac{{y^2}}{{{b*b}}} = 1$."
            "\nЗнайдіть велику піввісь $a$, малу піввісь $b$ і фокусну відстань "
            r"$c$ (де $c^2 = a^2 - b^2$)."
        ),
        parts=[
            Part("a", "$a$ =", a, points=1),
            Part("b", "$b$ =", b, points=1),
            Part("c", "$c$ =", c, points=1),
        ],
        seconds=90,
        params={"a": a, "b": b, "c": c},
    )


@template("ellipse_eccentricity")
def _ellipse_eccentricity(rng: random.Random) -> Question:
    import sympy as sp

    a, b, c = rng.choice(_ELLIPSE)
    return Question(
        key="ellipse_eccentricity",
        statement=(
            rf"Дано еліпс $\dfrac{{x^2}}{{{a*a}}} + \dfrac{{y^2}}{{{b*b}}} = 1$."
            "\n"
            r"Знайдіть ексцентриситет $\varepsilon = \dfrac{c}{a}$ "
            r"(де $c^2 = a^2 - b^2$)."
        ),
        parts=[Part("e", r"$\varepsilon$ =", sp.Rational(c, a), points=1)],
        seconds=60,
        params={"a": a, "b": b, "c": c},
    )


@template("distance_foci")
def _distance_foci(rng: random.Random) -> Question:
    a, b, c = rng.choice(_ELLIPSE)
    return Question(
        key="distance_foci",
        statement=(
            rf"Дано еліпс $\dfrac{{x^2}}{{{a*a}}} + \dfrac{{y^2}}{{{b*b}}} = 1$."
            "\nЗнайдіть відстань між його фокусами $F_1F_2 = 2c$."
        ),
        parts=[Part("d", "$2c$ =", 2 * c, points=1)],
        seconds=70,
        params={"a": a, "b": b, "c": c},
    )


# --- гіпербола -----------------------------------------------------------


@template("hyperbola_semi_axes_focus")
def _hyperbola_semi_axes_focus(rng: random.Random) -> Question:
    a, b, c = rng.choice(_HYPER)
    return Question(
        key="hyperbola_semi_axes_focus",
        statement=(
            rf"Дано гіперболу $\dfrac{{x^2}}{{{a*a}}} - \dfrac{{y^2}}{{{b*b}}} = 1$."
            "\nЗнайдіть дійсну піввісь $a$, уявну піввісь $b$ і фокусну відстань "
            r"$c$ (де $c^2 = a^2 + b^2$)."
        ),
        parts=[
            Part("a", "$a$ =", a, points=1),
            Part("b", "$b$ =", b, points=1),
            Part("c", "$c$ =", c, points=1),
        ],
        seconds=90,
        params={"a": a, "b": b, "c": c},
    )


@template("hyperbola_asymptote")
def _hyperbola_asymptote(rng: random.Random) -> Question:
    import sympy as sp

    a, b, c = rng.choice(_HYPER)
    return Question(
        key="hyperbola_asymptote",
        statement=(
            rf"Дано гіперболу $\dfrac{{x^2}}{{{a*a}}} - \dfrac{{y^2}}{{{b*b}}} = 1$."
            "\n"
            r"Її асимптоти мають вигляд $y = \pm k x$. Знайдіть додатний кутовий "
            r"коефіцієнт $k = \dfrac{b}{a}$."
        ),
        parts=[Part("k", "$k$ =", sp.Rational(b, a), points=1)],
        seconds=45,
        params={"a": a, "b": b},
    )


# --- парабола ------------------------------------------------------------


@template("parabola_param_focus")
def _parabola_param_focus(rng: random.Random) -> Question:
    two_p = rng.choice([4, 8, 12, 16, 20])  # кратне 4 -> p парне -> p/2 ціле
    p = two_p // 2
    fx = p // 2
    return Question(
        key="parabola_param_focus",
        statement=(
            rf"Дано параболу $y^2 = {two_p}x$."
            "\nЗнайдіть її параметр $p$, абсцису фокуса $x_F = \\dfrac{p}{2}$ та "
            r"директрису $x = -\dfrac{p}{2}$ (запишіть праву частину)."
        ),
        parts=[
            Part("p", "$p$ =", p, points=1),
            Part("xf", "$x_F$ =", fx, points=1),
            Part("dir", "директриса $x$ =", -fx, points=1),
        ],
        seconds=75,
        params={"two_p": two_p},
    )


# --- загальне рівняння: центр --------------------------------------------


@template("curve_center_general")
def _curve_center_general(rng: random.Random) -> Question:
    """Зведення загального рівняння (еліпс зі зміщеним центром) до центра."""
    A = rng.choice([1, 4, 9])
    C = rng.choice([1, 4, 9])
    x0, y0 = rng.randint(-4, 4), rng.randint(-4, 4)
    D, E = -2 * A * x0, -2 * C * y0
    # F довільний ненульовий (не впливає на центр)
    F = rng.choice([-3, -1, 1, 3])
    eq = (
        (f"{A}x^2" if A != 1 else "x^2")
        + " + "
        + (f"{C}y^2" if C != 1 else "y^2")
        + _signed(D, "x")
        + _signed(E, "y")
        + (f" + {F}" if F > 0 else f" - {-F}")
        + " = 0"
    )
    return Question(
        key="curve_center_general",
        statement=(
            "Виділивши повні квадрати, знайдіть координати центра $(x_0; y_0)$ "
            "кривої:\n"
            f"$${eq}$$"
        ),
        parts=[
            Part("x0", "$x_0$ =", x0, points=1),
            Part("y0", "$y_0$ =", y0, points=1),
        ],
        seconds=120,
        params={"A": A, "C": C, "x0": x0, "y0": y0},
    )


# --- рисунки -------------------------------------------------------------


@template("circle_from_graph")
def _circle_from_graph(rng: random.Random) -> Question:
    R = rng.randint(2, 4)
    cx = rng.randint(-2, 2)
    cy = rng.randint(-2, 2)
    svg = coordinate_plane(circles=[(cx, cy, R)], points=[(cx, cy)])
    return Question(
        key="circle_from_graph",
        statement=(
            "На рисунку зображено коло (центр позначено точкою). Визначте "
            "координати центра $(a; b)$ та радіус $R$."
        ),
        parts=[
            Part("a", "$a$ =", cx, points=1),
            Part("b", "$b$ =", cy, points=1),
            Part("R", "$R$ =", R, points=1),
        ],
        seconds=55,
        params={"cx": cx, "cy": cy, "R": R},
        svg=svg,
    )


@template("ellipse_from_graph")
def _ellipse_from_graph(rng: random.Random) -> Question:
    while True:
        ra = rng.randint(2, 5)
        rb = rng.randint(2, 5)
        if ra != rb:  # щоб це був еліпс, а не коло
            break
    svg = coordinate_plane(ellipses=[(0, 0, ra, rb)], points=[(0, 0)])
    return Question(
        key="ellipse_from_graph",
        statement=(
            "На рисунку зображено еліпс із центром на початку координат. "
            "Визначте піввісь уздовж осі $Ox$ (це $a$) та піввісь уздовж осі "
            "$Oy$ (це $b$)."
        ),
        parts=[
            Part("a", "$a$ =", ra, points=1),
            Part("b", "$b$ =", rb, points=1),
        ],
        seconds=55,
        params={"ra": ra, "rb": rb},
        svg=svg,
    )
