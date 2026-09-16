"""Тема (шкільна математика): числова функція та її властивості.

Область визначення й значень, значення в точці, нулі, монотонність (через
абсцису вершини), парність і непарність (через обчислення, без кодів). Обернена
функція, тригонометрія та найбільше/найменше значення сюди не входять.

Класифікаційні властивості зводимо до обчислень: парність досліджується через
f(-x) (вираз) і значення f(a), f(-a); монотонність через абсцису вершини (точку
її зміни). Числові відповіді цілі; парність дає вираз (для нього є екранна
клавіатура). Таймінги підібрані під реальний темп 10-11-класника.

Конвенція запису: проза текстом, математика в $...$ / $$...$$, переноси рядків \\n.
"""

from __future__ import annotations

import random

import sympy as sp

from engine import Part, Question, template

from app.bank.plotting import coordinate_plane

_x = sp.Symbol("x")


def _tex(expr) -> str:
    return sp.latex(expr)


# --- область визначення --------------------------------------------------


@template("domain_fraction")
def _domain_fraction(rng: random.Random) -> Question:
    """Область визначення дробу: точки, де знаменник перетворюється на нуль."""
    while True:
        p, q = rng.randint(-6, 6), rng.randint(-6, 6)
        if p != q:
            break
    lo, hi = min(p, q), max(p, q)
    r = rng.randint(-6, 6)
    denom = sp.expand((_x - p) * (_x - q))
    return Question(
        key="domain_fraction",
        statement=(
            rf"Задана функція $y = \dfrac{{x {r:+d}}}{{{_tex(denom)}}}$." "\n"
            "Знайдіть точки, які не входять в область визначення (де знаменник "
            "дорівнює нулю). Запишіть меншу і більшу."
        ),
        parts=[
            Part("x1", "менша =", lo, points=1),
            Part("x2", "більша =", hi, points=1),
        ],
        seconds=60,
        params={"p": p, "q": q, "r": r},
    )


@template("domain_sqrt")
def _domain_sqrt(rng: random.Random) -> Question:
    """Область визначення кореня: y = sqrt(a x + b), a>0, ліва межа x0 = -b/a."""
    a = rng.choice([1, 2, 3])
    x0 = rng.randint(-5, 5)
    b = -a * x0
    return Question(
        key="domain_sqrt",
        statement=(
            rf"Задана функція $y = \sqrt{{{a}x {b:+d}}}$." "\n"
            "Її область визначення має вигляд $[x_0; +\\infty)$. Знайдіть ліву "
            "межу $x_0$ (найменше допустиме значення $x$)."
        ),
        parts=[Part("x0", "$x_0$ =", x0, points=1)],
        seconds=35,
        params={"a": a, "b": b},
    )


# --- значення й нулі -----------------------------------------------------


@template("value_at_points")
def _value_at_points(rng: random.Random) -> Question:
    """Значення функції у двох точках."""
    b, c = rng.randint(-6, 6), rng.randint(-6, 6)
    f = _x**2 + b * _x + c
    a1 = rng.choice([-3, -2, -1, 1, 2, 3])
    a2 = rng.choice([-3, -2, -1, 1, 2, 3])
    while a2 == a1:
        a2 = rng.choice([-3, -2, -1, 1, 2, 3])
    return Question(
        key="value_at_points",
        statement=(
            rf"Задана функція $f(x) = {_tex(f)}$." "\n"
            rf"Обчисліть $f({a1})$ та $f({a2})$."
        ),
        parts=[
            Part("v1", rf"$f({a1})$ =", int(f.subs(_x, a1)), points=1),
            Part("v2", rf"$f({a2})$ =", int(f.subs(_x, a2)), points=1),
        ],
        seconds=45,
        params={"b": b, "c": c, "a1": a1, "a2": a2},
    )


@template("value_solve")
def _value_solve(rng: random.Random) -> Question:
    """При яких x функція набуває заданого значення m (два цілі розв'язки)."""
    while True:
        x1, x2 = rng.randint(-6, 6), rng.randint(-6, 6)
        if x1 != x2:
            break
    lo, hi = min(x1, x2), max(x1, x2)
    m = rng.randint(-4, 4)
    b = -(x1 + x2)
    c = x1 * x2 + m  # тоді f(x) = m рівносильне (x-x1)(x-x2)=0
    f = _x**2 + b * _x + c
    return Question(
        key="value_solve",
        statement=(
            rf"Задана функція $f(x) = {_tex(f)}$." "\n"
            rf"При яких значеннях $x$ виконується $f(x) = {m}$? Запишіть менший "
            "і більший розв'язок."
        ),
        parts=[
            Part("lo", "менший =", lo, points=1),
            Part("hi", "більший =", hi, points=1),
        ],
        seconds=75,
        params={"b": b, "c": c, "m": m},
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
            rf"Знайдіть нулі функції $y = {_tex(f)}$ (значення $x$, при яких "
            "$y = 0$). Запишіть менший і більший."
        ),
        parts=[
            Part("lo", "менший =", lo, points=1),
            Part("hi", "більший =", hi, points=1),
        ],
        seconds=60,
        params={"b": b, "c": c},
    )


@template("zeros_linear")
def _zeros_linear(rng: random.Random) -> Question:
    """Нуль лінійної функції: x = -b/k (цілий)."""
    k = rng.choice([-3, -2, 2, 3, 4])
    x0 = rng.randint(-5, 5)
    b = -k * x0
    return Question(
        key="zeros_linear",
        statement=(
            rf"Знайдіть нуль функції $y = {k}x {b:+d}$ (значення $x$, при якому "
            "$y = 0$)."
        ),
        parts=[Part("x0", "$x$ =", x0, points=1)],
        seconds=35,
        params={"k": k, "b": b},
    )


@template("range_endpoints")
def _range_endpoints(rng: random.Random) -> Question:
    """Область значень лінійної функції на відрізку: значення на кінцях."""
    k = rng.choice([-3, -2, -1, 1, 2, 3])
    b = rng.randint(-5, 5)
    a1 = rng.randint(-5, 1)
    a2 = a1 + rng.randint(2, 5)
    f = k * _x + b
    return Question(
        key="range_endpoints",
        statement=(
            rf"Функцію $y = {k}x {b:+d}$ розглядають на відрізку $[{a1}; {a2}]$." "\n"
            rf"Обчисліть її значення на кінцях відрізка: $f({a1})$ та $f({a2})$ "
            "(це межі області значень)."
        ),
        parts=[
            Part("fa", rf"$f({a1})$ =", int(f.subs(_x, a1)), points=1),
            Part("fb", rf"$f({a2})$ =", int(f.subs(_x, a2)), points=1),
        ],
        seconds=45,
        params={"k": k, "b": b, "a1": a1, "a2": a2},
    )


# --- парність (через обчислення) ----------------------------------------


@template("parity_compute")
def _parity_compute(rng: random.Random) -> Question:
    """Ключовий крок дослідження парності: знайти вираз f(-x)."""
    kind = rng.choice(["odd", "even", "general"])
    if kind == "odd":
        f = rng.choice([1, 2]) * _x**3 + rng.choice([1, 2, 3]) * _x
    elif kind == "even":
        f = rng.choice([1, 2]) * _x**4 + rng.choice([1, 2, 3]) * _x**2 + rng.randint(1, 4)
    else:
        f = _x**2 + rng.choice([1, 2, 3]) * _x
    fneg = sp.expand(f.subs(_x, -_x))
    return Question(
        key="parity_compute",
        statement=(
            rf"Для дослідження функції $f(x) = {_tex(f)}$ на парність знайдіть "
            r"вираз $f(-x)$ (підставте $-x$ замість $x$ і спростіть)."
        ),
        parts=[Part("fneg", "$f(-x)$ =", fneg, kind="expr", points=1)],
        seconds=55,
        params={"kind": kind},
    )


@template("parity_values")
def _parity_values(rng: random.Random) -> Question:
    """Дослідження парності через значення: f(a) та f(-a)."""
    b = rng.choice([1, 2, 3])
    f = _x**3 - b * _x
    a = rng.choice([2, 3])
    return Question(
        key="parity_values",
        statement=(
            rf"Для функції $f(x) = {_tex(f)}$ обчисліть $f({a})$ та $f(-{a})$ "
            "(порівняння цих значень показує парність)."
        ),
        parts=[
            Part("fa", rf"$f({a})$ =", int(f.subs(_x, a)), points=1),
            Part("fna", rf"$f(-{a})$ =", int(f.subs(_x, -a)), points=1),
        ],
        seconds=50,
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
        seconds=30,
        params={"p": p, "q": q, "about": about},
    )


# --- монотонність через вершину -----------------------------------------


@template("parabola_vertex_x")
def _parabola_vertex_x(rng: random.Random) -> Question:
    """Абсциса вершини параболи: точка, де змінюється монотонність."""
    a = rng.choice([1, 1, 2, -1])
    h = rng.randint(-4, 4)
    b = -2 * a * h
    c = rng.randint(-5, 5)
    f = a * _x**2 + b * _x + c
    return Question(
        key="parabola_vertex_x",
        statement=(
            rf"Знайдіть абсцису вершини параболи $y = {_tex(f)}$ за формулою "
            r"$x_в = -\dfrac{b}{2a}$ (у цій точці змінюється монотонність)."
        ),
        parts=[Part("xv", "$x_в$ =", h, points=1)],
        seconds=40,
        params={"a": a, "b": b, "c": c},
    )


# --- рисунки -------------------------------------------------------------


@template("graph_vertex")
def _graph_vertex(rng: random.Random) -> Question:
    """РИСУНОК: парабола; зчитати координати вершини (x і y)."""
    a = rng.choice([1, -1])
    h = rng.randint(-3, 3)
    k = rng.randint(-4, 1) if a == 1 else rng.randint(-1, 4)
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
        seconds=45,
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
    a = 1.0
    h = (lo + hi) / 2
    k = -((hi - lo) / 2) ** 2
    if abs(k) > 6:
        a, k = 0.5, k / 2
    svg = coordinate_plane(parabolas=[(a, h, k)], points=[(lo, 0), (hi, 0)])
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
        seconds=40,
        params={"x1": lo, "x2": hi},
        svg=svg,
    )
