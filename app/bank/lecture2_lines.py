"""Лекція 2: рівняння прямої на площині та в просторі.

Теми: загальне рівняння, у відрізках, з кутовим коефіцієнтом, через дві точки,
напрямний вектор (площина й простір), відстань від точки до прямої, скалярний
добуток, паралельність/перпендикулярність. Один шаблон — із рисунком (пряма на
координатній площині, студент зчитує рівняння).

Прийом: спершу задаємо цілу відповідь, потім із неї виводимо умову. Конвенція
запису: проза текстом, математика в $...$ / $$...$$, переноси рядків — \n.
"""

from __future__ import annotations

import random

from engine import Part, Question, template

from app.bank.plotting import coordinate_plane


def _term(coef, var, first=False):
    """Доданок рівняння: 3 -> '+3x' (або '3x' першим), -1 -> '-x'."""
    if coef == 0:
        return ""
    mag = abs(coef)
    body = ("" if mag == 1 else str(mag)) + var
    if first:
        return ("-" if coef < 0 else "") + body
    return (" + " if coef > 0 else " - ") + body


def _line_eq(A, B, C):
    """Рядок 'Ax + By + C = 0' зі знаками, у $...$."""
    s = _term(A, "x", first=True)
    s += _term(B, "y")
    if C:
        s += (f" + {C}" if C > 0 else f" - {abs(C)}")
    return f"${s} = 0$"


# --- загальне рівняння ---------------------------------------------------


@template("general_line_C")
def _general_line_C(rng: random.Random) -> Question:
    """Через точку M0, перпендикулярно нормалі n=(A,B): знайти C у Ax+By+C=0."""
    while True:
        A, B = rng.randint(-5, 5), rng.randint(-5, 5)
        if A and B:
            break
    x0, y0 = rng.randint(-5, 5), rng.randint(-5, 5)
    C = -A * x0 - B * y0
    return Question(
        key="general_line_C",
        statement=(
            f"Пряма проходить через точку $M_0({x0};{y0})$ перпендикулярно "
            f"нормальному вектору $\\vec n = ({A};{B})$.\n"
            f"Її загальне рівняння має вигляд ${_term(A,'x',True)}{_term(B,'y')} + C = 0$. "
            f"Знайдіть $C$."
        ),
        parts=[Part("C", "$C$ =", C, points=1)],
        seconds=90,
        params={"A": A, "B": B, "x0": x0, "y0": y0},
    )


@template("slope_intercept_from_general")
def _slope_intercept_from_general(rng: random.Random) -> Question:
    """Із загального рівняння -> y = kx + b (цілі k, b)."""
    while True:
        k = rng.randint(-4, 4)
        b = rng.randint(-6, 6)
        if k:
            break
    d = rng.choice([1, 1, 2])  # інколи домножуємо, щоб не завжди B=-1
    A, B, C = d * k, -d, d * b
    return Question(
        key="slope_intercept_from_general",
        statement=(
            "Зведіть загальне рівняння прямої до вигляду $y = kx + b$ і знайдіть "
            f"$k$ та $b$:\n{_line_eq(A, B, C)}"
        ),
        parts=[
            Part("k", "$k$ =", k, points=1),
            Part("b", "$b$ =", b, points=1),
        ],
        seconds=100,
        params={"A": A, "B": B, "C": C},
    )


@template("line_intercepts")
def _line_intercepts(rng: random.Random) -> Question:
    """Відрізки прямої на осях: перетин з Ox (a) і з Oy (bb)."""
    while True:
        a = rng.randint(-6, 6)
        bb = rng.randint(-6, 6)
        if a and bb:
            break
    A, B, C = bb, a, -a * bb  # bb*x + a*y - a*bb = 0  ->  x/a + y/bb = 1
    return Question(
        key="line_intercepts",
        statement=(
            "Знайдіть відрізки, які пряма відтинає на осях координат: "
            "абсцису точки перетину з віссю $Ox$ ($a$) та ординату точки "
            f"перетину з віссю $Oy$ ($b$):\n{_line_eq(A, B, C)}"
        ),
        parts=[
            Part("a", "$a$ =", a, points=1),
            Part("b", "$b$ =", bb, points=1),
        ],
        seconds=100,
        params={"A": A, "B": B, "C": C},
    )


# --- відстань ------------------------------------------------------------

_PYTHAG = [(3, 4, 5), (4, 3, 5), (6, 8, 10), (8, 6, 10), (5, 12, 13), (12, 5, 13)]


@template("distance_point_to_line")
def _distance_point_to_line(rng: random.Random) -> Question:
    """Відстань від точки до прямої; (A,B) — піфагорова трійка, тож d ціле."""
    A, B, root = rng.choice(_PYTHAG)
    A *= rng.choice([1, -1])
    B *= rng.choice([1, -1])
    x1, y1 = rng.randint(-4, 4), rng.randint(-4, 4)
    d = rng.randint(1, 4)
    s = rng.choice([1, -1])
    # |A*x1 + B*y1 + C| = d*root  ->  добираємо C
    C = s * d * root - A * x1 - B * y1
    return Question(
        key="distance_point_to_line",
        statement=(
            f"Знайдіть відстань від точки $K({x1};{y1})$ до прямої:\n"
            f"{_line_eq(A, B, C)}"
        ),
        parts=[Part("d", "$d$ =", d, points=1)],
        seconds=120,
        params={"A": A, "B": B, "C": C, "x1": x1, "y1": y1},
    )


@template("point_substitution")
def _point_substitution(rng: random.Random) -> Question:
    """Підстановка точки в ліву частину Ax+By+C (перевірка приналежності)."""
    while True:
        A, B = rng.randint(-5, 5), rng.randint(-5, 5)
        C = rng.randint(-6, 6)
        x0, y0 = rng.randint(-5, 5), rng.randint(-5, 5)
        val = A * x0 + B * y0 + C
        if A and B and val != 0:  # точка НЕ на прямій -> відповідь ненульова
            break
    return Question(
        key="point_substitution",
        statement=(
            f"Щоб перевірити, чи належить точка $M({x0};{y0})$ прямій, підставте "
            f"її координати в ліву частину рівняння. Обчисліть значення "
            f"${_term(A,'x',True)}{_term(B,'y')}"
            + (f" + {C}" if C > 0 else (f" - {abs(C)}" if C else ""))
            + "$:"
        ),
        parts=[Part("v", "значення =", val, points=1)],
        seconds=75,
        params={"A": A, "B": B, "C": C, "x0": x0, "y0": y0},
    )


# --- напрямні вектори ----------------------------------------------------


@template("direction_vector_2pts")
def _direction_vector_2pts(rng: random.Random) -> Question:
    """Напрямний вектор прямої через дві точки на площині: s=(x2-x1, y2-y1)."""
    while True:
        x1, y1 = rng.randint(-6, 6), rng.randint(-6, 6)
        x2, y2 = rng.randint(-6, 6), rng.randint(-6, 6)
        if (x1, y1) != (x2, y2):
            break
    return Question(
        key="direction_vector_2pts",
        statement=(
            f"Пряма проходить через точки $M_1({x1};{y1})$ і $M_2({x2};{y2})$.\n"
            r"Знайдіть координати напрямного вектора $\vec s = M_1M_2 = (m; n)$."
        ),
        parts=[
            Part("m", "$m$ =", x2 - x1, points=1),
            Part("n", "$n$ =", y2 - y1, points=1),
        ],
        seconds=90,
        params={"x1": x1, "y1": y1, "x2": x2, "y2": y2},
    )


@template("space_direction_vector")
def _space_direction_vector(rng: random.Random) -> Question:
    """Напрямний вектор прямої у просторі через дві точки: s=(x2-x1,y2-y1,z2-z1)."""
    while True:
        p1 = [rng.randint(-6, 6) for _ in range(3)]
        p2 = [rng.randint(-6, 6) for _ in range(3)]
        if p1 != p2:
            break
    m, n, p = p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]
    return Question(
        key="space_direction_vector",
        statement=(
            f"Пряма у просторі проходить через точки "
            f"$M_1({p1[0]};{p1[1]};{p1[2]})$ і $M_2({p2[0]};{p2[1]};{p2[2]})$.\n"
            r"Знайдіть координати напрямного вектора $\vec s = (m; n; p)$."
        ),
        parts=[
            Part("m", "$m$ =", m, points=1),
            Part("n", "$n$ =", n, points=1),
            Part("p", "$p$ =", p, points=1),
        ],
        seconds=120,
        params={"p1": p1, "p2": p2},
    )


@template("dot_product_3d")
def _dot_product_3d(rng: random.Random) -> Question:
    """Скалярний добуток двох векторів у просторі (проміжний крок до кута)."""
    s1 = [rng.randint(-5, 5) for _ in range(3)]
    s2 = [rng.randint(-5, 5) for _ in range(3)]
    val = sum(a * b for a, b in zip(s1, s2))
    return Question(
        key="dot_product_3d",
        statement=(
            f"Дано напрямні вектори двох прямих "
            f"$\\vec s_1 = ({s1[0]};{s1[1]};{s1[2]})$ і "
            f"$\\vec s_2 = ({s2[0]};{s2[1]};{s2[2]})$.\n"
            r"Знайдіть їхній скалярний добуток $\vec s_1 \cdot \vec s_2$."
        ),
        parts=[Part("v", r"$\vec s_1 \cdot \vec s_2$ =", val, points=1)],
        seconds=90,
        params={"s1": s1, "s2": s2},
    )


@template("perpendicular_parallel_slope")
def _perpendicular_parallel_slope(rng: random.Random) -> Question:
    """Кутовий коефіцієнт паралельної (k) або перпендикулярної (-1/k) прямої."""
    import sympy as sp

    while True:
        k1 = rng.randint(-4, 4)
        if k1:
            break
    b1 = rng.randint(-5, 5)
    if rng.random() < 0.5:
        kind = "паралельної"
        ans = k1
    else:
        kind = "перпендикулярної"
        ans = sp.Rational(-1, k1)
    return Question(
        key="perpendicular_parallel_slope",
        statement=(
            f"Дано пряму $y = {k1}x"
            + (f" + {b1}" if b1 > 0 else (f" - {abs(b1)}" if b1 else ""))
            + "$.\n"
            f"Знайдіть кутовий коефіцієнт прямої, {kind} до даної."
        ),
        parts=[Part("k", "$k$ =", ans, points=1)],
        seconds=75,
        params={"k1": k1, "kind": kind},
    )


# --- рисунок -------------------------------------------------------------


@template("line_from_graph")
def _line_from_graph(rng: random.Random) -> Question:
    """РИСУНОК: пряма на координатній площині; студент зчитує y = kx + b."""
    k = rng.choice([-3, -2, -1, 1, 2, 3])
    b = rng.randint(-4, 4)
    # дві цілі опорні точки в межах видимості (|y| <= 5) — позначаємо на графіку
    xs = [x for x in range(-5, 6) if abs(k * x + b) <= 5]
    pts = [(x, k * x + b) for x in (xs[0], xs[-1])]
    svg = coordinate_plane(lines=[(k, b)], points=pts)
    return Question(
        key="line_from_graph",
        statement=(
            "На рисунку зображено пряму (позначено дві точки, через які вона "
            "проходить). Визначте її рівняння у вигляді $y = kx + b$: знайдіть "
            "кутовий коефіцієнт $k$ та вільний член $b$."
        ),
        parts=[
            Part("k", "$k$ =", k, points=1),
            Part("b", "$b$ =", b, points=1),
        ],
        seconds=120,
        params={"k": k, "b": b},
        svg=svg,
    )
