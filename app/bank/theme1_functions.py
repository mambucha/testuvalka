"""Тема (шкільна математика): числова функція та її властивості.

Область визначення й значень, нулі, значення в точці, монотонність, парність і
непарність, обмеженість, читання графіка. Обернена функція навмисно не входить.

Багато властивостей за природою не числа (проміжки, класифікація), тож зводимо
їх до числових проміжних результатів: межі проміжків, координати вершини,
значення в точках, а для класифікації (парність, монотонність) вводимо явний
код з поясненням у самій умові. Усі відповіді цілі або прості дроби.

Конвенція запису: проза текстом, математика в $...$ / $$...$$, переноси рядків \\n.
"""

from __future__ import annotations

import random

import sympy as sp

from engine import Part, Question, template

from app.bank.plotting import coordinate_plane

_x = sp.Symbol("x")


def _poly_latex(expr) -> str:
    return sp.latex(expr)


# --- область визначення --------------------------------------------------


@template("domain_fraction")
def _domain_fraction(rng: random.Random) -> Question:
    """D дробу: точки, де знаменник (x-p)(x-q) перетворюється на нуль."""
    while True:
        p, q = rng.randint(-6, 6), rng.randint(-6, 6)
        if p != q:
            break
    lo, hi = min(p, q), max(p, q)
    B, C = -(p + q), p * q  # знаменник x^2 + Bx + C
    r = rng.randint(-6, 6)
    denom = sp.expand((_x - p) * (_x - q))
    return Question(
        key="domain_fraction",
        statement=(
            rf"Задана функція $y = \dfrac{{x {r:+d}}}{{{_poly_latex(denom)}}}$." "\n"
            "Знайдіть точки, які НЕ входять в область визначення (де знаменник "
            "дорівнює нулю). Запишіть меншу і більшу."
        ),
        parts=[
            Part("x1", "менша =", lo, points=1),
            Part("x2", "більша =", hi, points=1),
        ],
        seconds=110,
        params={"p": p, "q": q, "r": r},
    )


@template("domain_sqrt")
def _domain_sqrt(rng: random.Random) -> Question:
    """D кореня парного степеня: y = sqrt(a x + b), a>0 -> x >= -b/a."""
    a = rng.choice([1, 2, 3])
    x0 = rng.randint(-5, 5)
    b = -a * x0  # щоб межа -b/a = x0 була цілою
    return Question(
        key="domain_sqrt",
        statement=(
            rf"Задана функція $y = \sqrt{{{a}x {b:+d}}}$." "\n"
            "Область визначення має вигляд $[x_0; +\\infty)$. Знайдіть ліву межу "
            "$x_0$ (найменше значення $x$)."
        ),
        parts=[Part("x0", "$x_0$ =", x0, points=1)],
        seconds=70,
        params={"a": a, "b": b},
    )


# --- значення й нулі -----------------------------------------------------


@template("value_at_points")
def _value_at_points(rng: random.Random) -> Question:
    """Значення функції в двох точках."""
    b = rng.randint(-6, 6)
    c = rng.randint(-6, 6)
    f = _x**2 + b * _x + c
    a1 = rng.choice([-3, -2, -1, 1, 2, 3])
    a2 = rng.choice([-3, -2, -1, 1, 2, 3])
    while a2 == a1:
        a2 = rng.choice([-3, -2, -1, 1, 2, 3])
    return Question(
        key="value_at_points",
        statement=(
            rf"Задана функція $f(x) = {_poly_latex(f)}$." "\n"
            rf"Обчисліть $f({a1})$ та $f({a2})$."
        ),
        parts=[
            Part("v1", rf"$f({a1})$ =", int(f.subs(_x, a1)), points=1),
            Part("v2", rf"$f({a2})$ =", int(f.subs(_x, a2)), points=1),
        ],
        seconds=70,
        params={"b": b, "c": c, "a1": a1, "a2": a2},
    )


@template("function_zeros")
def _function_zeros(rng: random.Random) -> Question:
    """Нулі квадратичної функції з цілими коренями."""
    while True:
        x1, x2 = rng.randint(-6, 6), rng.randint(-6, 6)
        if x1 != x2:
            break
    lo, hi = min(x1, x2), max(x1, x2)
    b, c = -(x1 + x2), x1 * x2
    f = _x**2 + b * _x + c
    return Question(
        key="function_zeros",
        statement=(
            rf"Знайдіть нулі функції $y = {_poly_latex(f)}$ (значення $x$, де "
            "$y = 0$). Запишіть менший і більший."
        ),
        parts=[
            Part("lo", "менший =", lo, points=1),
            Part("hi", "більший =", hi, points=1),
        ],
        seconds=110,
        params={"b": b, "c": c},
    )


# --- парність ------------------------------------------------------------


@template("parity_code")
def _parity_code(rng: random.Random) -> Question:
    """Класифікація парності через код 1/2/3 (пояснення в умові)."""
    kind = rng.choice(["even", "odd", "general"])
    if kind == "even":
        f = rng.choice([1, 2]) * _x**4 + rng.choice([1, 2, 3]) * _x**2 + rng.randint(-4, 4)
        code = 1
    elif kind == "odd":
        f = rng.choice([1, 2]) * _x**3 + rng.choice([1, 2, 3]) * _x
        code = 2
    else:
        f = _x**2 + rng.choice([1, 2, 3]) * _x  # є і парний, і непарний доданок
        code = 3
    return Question(
        key="parity_code",
        statement=(
            rf"Дослідіть функцію $f(x) = {_poly_latex(f)}$ на парність." "\n"
            "Введіть відповідь кодом: 1 — парна, 2 — непарна, "
            "3 — загального вигляду (ні парна, ні непарна)."
        ),
        parts=[Part("code", "код =", code, points=1)],
        seconds=120,
        params={"kind": kind},
    )


@template("parity_values")
def _parity_values(rng: random.Random) -> Question:
    """Обчислювальний крок дослідження парності: f(a) і f(-a)."""
    b = rng.choice([1, 2, 3])
    f = _x**3 - b * _x  # непарна, але тут лише рахуємо значення
    a = rng.choice([2, 3])
    return Question(
        key="parity_values",
        statement=(
            rf"Для дослідження парності функції $f(x) = {_poly_latex(f)}$ "
            rf"обчисліть $f({a})$ та $f(-{a})$."
        ),
        parts=[
            Part("fa", rf"$f({a})$ =", int(f.subs(_x, a)), points=1),
            Part("fna", rf"$f(-{a})$ =", int(f.subs(_x, -a)), points=1),
        ],
        seconds=75,
        params={"b": b, "a": a},
    )


@template("symmetry_point")
def _symmetry_point(rng: random.Random) -> Question:
    """Геометричний зміст парності: симетрія точки відносно Oy або O."""
    p, q = rng.randint(-6, 6), rng.randint(-6, 6)
    if rng.random() < 0.5:
        about, nx, ny = "осі $Oy$", -p, q
    else:
        about, nx, ny = "початку координат", -p, -q
    return Question(
        key="symmetry_point",
        statement=(
            rf"Знайдіть координати точки, симетричної точці $A({p}; {q})$ "
            rf"відносно {about}."
        ),
        parts=[
            Part("x", "$x$ =", nx, points=1),
            Part("y", "$y$ =", ny, points=1),
        ],
        seconds=50,
        params={"p": p, "q": q, "about": about},
    )


# --- монотонність, обмеженість, вершина ----------------------------------


@template("monotonic_linear")
def _monotonic_linear(rng: random.Random) -> Question:
    """Монотонність лінійної функції через код 1/2 (знак кутового коефіцієнта)."""
    k = rng.choice([-4, -3, -2, -1, 1, 2, 3, 4])
    b = rng.randint(-6, 6)
    code = 1 if k > 0 else 2
    return Question(
        key="monotonic_linear",
        statement=(
            rf"Задана функція $y = {k}x {b:+d}$." "\n"
            "Визначте характер монотонності. Введіть: 1 — зростає, 2 — спадає."
        ),
        parts=[Part("code", "код =", code, points=1)],
        seconds=50,
        params={"k": k, "b": b},
    )


@template("parabola_vertex_x")
def _parabola_vertex_x(rng: random.Random) -> Question:
    """Абсциса вершини параболи: точка, де змінюється монотонність."""
    a = rng.choice([1, 1, 2, -1])
    h = rng.randint(-4, 4)  # абсциса вершини (ціла)
    b = -2 * a * h
    c = rng.randint(-5, 5)
    f = a * _x**2 + b * _x + c
    return Question(
        key="parabola_vertex_x",
        statement=(
            rf"Знайдіть абсцису вершини параболи $y = {_poly_latex(f)}$ "
            "(точку, у якій змінюється монотонність), за формулою "
            r"$x_в = -\dfrac{b}{2a}$."
        ),
        parts=[Part("xv", "$x_в$ =", h, points=1)],
        seconds=60,
        params={"a": a, "b": b, "c": c},
    )


@template("parabola_min")
def _parabola_min(rng: random.Random) -> Question:
    """Обмеженість: найменше значення параболи вітками вгору (y вершини)."""
    h = rng.randint(-3, 3)
    k = rng.randint(-5, 5)
    b = -2 * h
    c = k + h * h  # з y = (x-h)^2 + k
    f = _x**2 + b * _x + c
    return Question(
        key="parabola_min",
        statement=(
            rf"Функція $y = {_poly_latex(f)}$ обмежена знизу. Знайдіть її "
            "найменше значення (ординату вершини)."
        ),
        parts=[Part("ymin", "$y_{min}$ =", k, points=1)],
        seconds=80,
        params={"b": b, "c": c},
    )


@template("bounded_trig")
def _bounded_trig(rng: random.Random) -> Question:
    """Обмеженість: найбільше і найменше значення y = A*sin(x) + B."""
    A = rng.choice([2, 3, 4, 5])
    B = rng.randint(-4, 4)
    return Question(
        key="bounded_trig",
        statement=(
            rf"Функція $y = {A}\sin(x) {B:+d}$ обмежена. Знайдіть її найбільше "
            "та найменше значення (врахуйте, що $-1 \\le \\sin(x) \\le 1$)."
        ),
        parts=[
            Part("ymax", "найбільше =", B + A, points=1),
            Part("ymin", "найменше =", B - A, points=1),
        ],
        seconds=70,
        params={"A": A, "B": B},
    )


# --- рисунки -------------------------------------------------------------


@template("graph_vertex")
def _graph_vertex(rng: random.Random) -> Question:
    """РИСУНОК: парабола; зчитати координати вершини (x і y)."""
    a = rng.choice([1, -1])
    h = rng.randint(-3, 3)
    k = rng.randint(-4, 4) if a == 1 else rng.randint(-4, 4)
    # тримаємо вершину видимою і вітки в межах
    if a == 1:
        k = rng.randint(-4, 1)
    else:
        k = rng.randint(-1, 4)
    svg = coordinate_plane(parabolas=[(a, h, k)], points=[(h, k)])
    return Question(
        key="graph_vertex",
        statement=(
            "На рисунку зображено параболу. Визначте координати її вершини "
            "(позначено точкою): абсцису $x$ та ординату $y$."
        ),
        parts=[
            Part("x", "$x$ =", h, points=1),
            Part("y", "$y$ =", k, points=1),
        ],
        seconds=100,
        params={"a": a, "h": h, "k": k},
        svg=svg,
    )


@template("graph_zeros")
def _graph_zeros(rng: random.Random) -> Question:
    """РИСУНОК: парабола, що перетинає Ox у двох цілих точках; зчитати нулі."""
    while True:
        x1, x2 = rng.randint(-5, 5), rng.randint(-5, 5)
        if x1 != x2:
            break
    lo, hi = min(x1, x2), max(x1, x2)
    a = sp.Rational(1, 1)
    h = sp.Rational(lo + hi, 2)
    # y = a(x-x1)(x-x2); вершина (h, k); підберемо a так, щоб вітки не тікали
    k = -((hi - lo) / 2) ** 2  # для a=1
    if abs(k) > 6:  # завузька/заширока — стиснемо
        a = sp.Rational(1, 2)
        k = k / 2
    svg = coordinate_plane(
        parabolas=[(float(a), float(h), float(k))],
        points=[(lo, 0), (hi, 0)],
    )
    return Question(
        key="graph_zeros",
        statement=(
            "На рисунку зображено параболу, що перетинає вісь $Ox$ у двох точках "
            "(позначено). Визначте нулі функції: менший і більший."
        ),
        parts=[
            Part("lo", "менший =", lo, points=1),
            Part("hi", "більший =", hi, points=1),
        ],
        seconds=100,
        params={"x1": lo, "x2": hi},
        svg=svg,
    )
