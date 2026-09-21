"""Тест 2 (11 клас): визначений інтеграл і його застосування до обчислення площ.

Повністю за програмою 11 класу: формула Ньютона–Лейбніца
($\\int_a^b f = F(b)-F(a)$), геометричний зміст визначеного інтеграла (площа
криволінійної трапеції), основні властивості (лінійність, адитивність),
знаходження межі за заданим значенням інтеграла, застосування до площ фігур
(під кривою; між параболою й віссю; між параболою й прямою; фігури під віссю,
де площа = |інтеграл|) та фізичне застосування (шлях = інтеграл швидкості).

Тест НЕ елементарний: обчислення інтегралів за Ньютоном–Лейбніцем, а в задачах
на площу — самостійно знайти межі (точки перетину/нулі), правильно вибрати
«верхню мінус нижню» і врахувати знак. Задачі на площу супроводжуються рисунком
із заштрихованою фігурою (генерується на сервері з параметрів).

Відповіді — числа (площі та інтеграли), здебільшого цілі; у класичних задачах на
площу параболи — прості дроби (напр. 9/2, 32/3), як у підручнику.
"""

from __future__ import annotations

import random

import sympy as sp

from engine import Part, Question, template

from app.bank.plotting import coordinate_plane, region_between

_x = sp.Symbol("x")
_t = sp.Symbol("t")

_FRAC_NOTE = "\nВідповідь можна записати дробом (напр. 9/2) або десятковим."


def _signed(v: int) -> str:
    if v == 0:
        return ""
    return f" + {v}" if v > 0 else f" - {abs(v)}"


def _sum_tex(terms: list[tuple[int, str]]) -> str:
    out = ""
    for coef, var in terms:
        if coef == 0:
            continue
        mag = abs(coef)
        body = (("" if mag == 1 else str(mag)) + var) if var else str(mag)
        if not out:
            out = ("-" if coef < 0 else "") + body
        else:
            out += (" - " if coef < 0 else " + ") + body
    return out or "0"


def _int_tex(lo: str, hi: str, integrand: str, var: str = "x") -> str:
    return rf"\int_{{{lo}}}^{{{hi}}} {integrand}\,d{var}"


# =========================================================================
#  ФОРМУЛА НЬЮТОНА–ЛЕЙБНІЦА (обчислення визначеного інтеграла)
# =========================================================================

@template("def_nl_poly")
def _nl_poly(rng: random.Random) -> Question:
    """Визначений інтеграл многочлена за формулою Ньютона–Лейбніца."""
    p = rng.choice([3, 6])            # p/3 ціле
    r = rng.choice([-4, -2, 2, 4])    # r/2 ціле
    q = rng.choice([-3, -2, -1, 1, 2, 3])
    m = rng.choice([-2, -1, 0, 1])
    n = m + rng.choice([2, 3])
    f = p * _x**2 + r * _x + q
    val = sp.integrate(f, (_x, m, n))
    ftex = _sum_tex([(p, "x^2"), (r, "x"), (q, "")])
    return Question(
        key="def_nl_poly",
        statement="Обчисліть визначений інтеграл:\n$$" + _int_tex(str(m), str(n), ftex) + "$$",
        parts=[Part("v", "= ", val, points=1)],
        seconds=120,
        params={"p": p, "r": r, "q": q, "m": m, "n": n},
    )


@template("def_nl_trig")
def _nl_trig(rng: random.Random) -> Question:
    """Визначений інтеграл тригонометричної функції (таблиця + межі з π)."""
    k = rng.choice([2, 3])
    m = rng.choice([1, 2])
    a = k * m
    if rng.random() < 0.5:
        f = a * sp.sin(k * _x)
        hi = sp.pi / k
        hi_tex = rf"\frac{{\pi}}{{{k}}}" if k != 1 else r"\pi"
        head = rf"{a}\sin {k}x"
    else:
        f = a * sp.cos(k * _x)
        hi = sp.pi / (2 * k)
        hi_tex = rf"\frac{{\pi}}{{{2 * k}}}"
        head = rf"{a}\cos {k}x"
    val = sp.integrate(f, (_x, 0, hi))
    return Question(
        key="def_nl_trig",
        statement="Обчисліть визначений інтеграл:\n$$" + _int_tex("0", hi_tex, head) + "$$",
        parts=[Part("v", "= ", val, points=1)],
        seconds=110,
        params={"k": k, "a": a},
    )


@template("def_nl_sqrt")
def _nl_sqrt(rng: random.Random) -> Question:
    r"""Визначений інтеграл $\int a/\sqrt{x}\,dx$ (табличний), межі — точні квадрати."""
    a = rng.choice([1, 2, 3, 4])
    m = rng.choice([1, 2])
    n = m + rng.choice([1, 2])
    lo, hi = m * m, n * n
    f = sp.Rational(a, 1) / sp.sqrt(_x)
    val = sp.integrate(f, (_x, lo, hi))
    head = rf"\dfrac{{{a}}}{{\sqrt{{x}}}}"
    return Question(
        key="def_nl_sqrt",
        statement="Обчисліть визначений інтеграл:\n$$" + _int_tex(str(lo), str(hi), head) + "$$",
        parts=[Part("v", "= ", val, points=1)],
        seconds=110,
        params={"a": a, "lo": lo, "hi": hi},
    )


@template("def_nl_reciprocal")
def _nl_reciprocal(rng: random.Random) -> Question:
    r"""Визначений інтеграл $\int k/x^2\,dx$ (таблична 1/x² -> -1/x)."""
    m, n, k = rng.choice([
        (1, 2, 2), (1, 2, 4), (1, 2, 6), (2, 3, 6), (2, 3, 12),
        (1, 3, 3), (1, 3, 6), (3, 6, 6),
    ])
    f = sp.Rational(k, 1) / _x**2
    val = sp.integrate(f, (_x, m, n))
    head = rf"\dfrac{{{k}}}{{x^2}}"
    return Question(
        key="def_nl_reciprocal",
        statement="Обчисліть визначений інтеграл:\n$$" + _int_tex(str(m), str(n), head) + "$$",
        parts=[Part("v", "= ", val, points=1)],
        seconds=110,
        params={"m": m, "n": n, "k": k},
    )


@template("def_nl_from_F")
def _nl_from_F(rng: random.Random) -> Question:
    """Пряме застосування формули Ньютона–Лейбніца: дано первісну F, знайти
    визначений інтеграл як F(b) - F(a)."""
    c3 = rng.choice([1, 2])
    c1 = rng.choice([-3, -2, -1, 1, 2, 3])
    c0 = rng.choice([-3, 0, 3])
    a = rng.choice([0, 1])
    b = a + rng.choice([1, 2])
    F = c3 * _x**3 + c1 * _x + c0
    val = F.subs(_x, b) - F.subs(_x, a)
    Ftex = _sum_tex([(c3, "x^3"), (c1, "x"), (c0, "")])
    return Question(
        key="def_nl_from_F",
        statement=(
            rf"Функція $F(x) = {Ftex}$ є первісною для функції $f$."
            + "\nЗа формулою Ньютона–Лейбніца обчисліть $"
            + _int_tex(str(a), str(b), "f(x)") + "$."
        ),
        parts=[Part("v", "= ", val, points=1)],
        seconds=110,
        params={"c3": c3, "c1": c1, "c0": c0, "a": a, "b": b},
    )


# =========================================================================
#  ВЛАСТИВОСТІ  та  ОБЕРНЕНА ЗАДАЧА
# =========================================================================

@template("def_property_linear")
def _property_linear(rng: random.Random) -> Question:
    """Лінійність визначеного інтеграла: за відомими інтегралами f і g знайти
    інтеграл лінійної комбінації (без обчислення самих функцій)."""
    al = rng.choice([2, 3])
    be = rng.choice([2, 3, 4])
    P = rng.choice([-3, -2, 2, 3, 4, 5])
    Q = rng.choice([-3, -2, -1, 1, 2, 3])
    a = rng.choice([0, 1])
    b = a + rng.choice([2, 3])
    val = al * P - be * Q
    lim = f"_{{{a}}}^{{{b}}}"
    return Question(
        key="def_property_linear",
        statement=(
            rf"Відомо, що $\int{lim} f(x)\,dx = {P}$ і $\int{lim} g(x)\,dx = {Q}$."
            + "\nКористуючись властивостями визначеного інтеграла, обчисліть $"
            + rf"\int{lim}\left({al}f(x) - {be}g(x)\right)dx$."
        ),
        parts=[Part("v", "= ", val, points=1)],
        seconds=100,
        params={"al": al, "be": be, "P": P, "Q": Q, "a": a, "b": b},
    )


@template("def_find_limit")
def _find_limit(rng: random.Random) -> Question:
    r"""Обернена задача: знайти верхню межу b з рівняння $\int_0^b a x\,dx = S$."""
    a = rng.choice([2, 4, 6])
    b = rng.choice([2, 3, 4])
    S = sp.integrate(a * _x, (_x, 0, b))   # = a b²/2
    return Question(
        key="def_find_limit",
        statement=(
            rf"Знайдіть додатне число $b$, для якого $\int_0^b {a}x\,dx = {S}$."
        ),
        parts=[Part("b", "$b$ = ", b, points=1)],
        seconds=110,
        params={"a": a, "S": int(S), "b": b},
    )


# =========================================================================
#  ЗАСТОСУВАННЯ: ПЛОЩІ ФІГУР  (з рисунком-заштрихуванням)
# =========================================================================

@template("area_trapezoid")
def _area_trapezoid(rng: random.Random) -> Question:
    """Площа криволінійної трапеції: фігура під прямою y=kx+b0 ≥ 0 на [0,n]
    (геометричний зміст визначеного інтеграла)."""
    k = rng.choice([1, 2])
    b0 = rng.choice([0, 1, 2])
    if k == 0 and b0 == 0:
        b0 = 1
    n = 2
    f = k * _x + b0
    val = sp.integrate(f, (_x, 0, n))
    svg = coordinate_plane(
        lines=[(k, b0)],
        regions=[region_between(lambda t: k * t + b0, lambda t: 0.0, 0, n)],
    )
    ftex = _sum_tex([(k, "x"), (b0, "")])
    return Question(
        key="area_trapezoid",
        statement=(
            "Знайдіть площу заштрихованої фігури, обмеженої лініями "
            rf"$y = {ftex}$, $x = 0$, $x = {n}$ та віссю $Ox$."
        ),
        parts=[Part("S", "$S$ = ", val, points=1)],
        seconds=110,
        params={"k": k, "b0": b0, "n": n},
        svg=svg,
    )


@template("area_parabola_axis")
def _area_parabola_axis(rng: random.Random) -> Question:
    """Площа фігури між параболою (гілками вниз) та віссю Ox — знайти нулі
    (межі) і обчислити інтеграл. Класична задача; відповідь — простий дріб."""
    r1, r2 = rng.choice([(-2, 0), (-1, 1), (0, 2), (-2, 1), (-1, 2), (-2, 2)])
    s = r1 + r2          # y = -x² + s x - r1 r2
    c = -r1 * r2
    h = sp.Rational(s, 2)
    K = sp.Rational((r2 - r1) ** 2, 4)
    f = -(_x - r1) * (_x - r2)
    val = sp.integrate(f, (_x, r1, r2))
    svg = coordinate_plane(
        parabolas=[(-1, float(h), float(K))],
        regions=[region_between(lambda tt: -(tt - r1) * (tt - r2), lambda tt: 0.0, r1, r2)],
    )
    ytex = _sum_tex([(-1, "x^2"), (s, "x"), (c, "")])
    return Question(
        key="area_parabola_axis",
        statement=(
            "Знайдіть площу заштрихованої фігури, обмеженої параболою "
            rf"$y = {ytex}$ та віссю $Ox$." + _FRAC_NOTE
        ),
        parts=[Part("S", "$S$ = ", val, points=1)],
        seconds=140,
        params={"r1": r1, "r2": r2},
        svg=svg,
    )


@template("area_parabola_line")
def _area_parabola_line(rng: random.Random) -> Question:
    """Класична площа між параболою y=x² та прямою: знайти точки перетину
    (межі), інтегрувати «пряма мінус парабола». Відповідь — простий дріб."""
    r1, r2 = rng.choice([(-2, 0), (-1, 1), (0, 2), (-2, 1), (-1, 2), (-2, 2)])
    k = r1 + r2          # пряма y = (r1+r2)x - r1 r2 перетинає y=x² у r1, r2
    m = -r1 * r2
    line = k * _x + m
    val = sp.integrate(line - _x**2, (_x, r1, r2))
    svg = coordinate_plane(
        parabolas=[(1, 0.0, 0.0)],
        lines=[(k, m)],
        regions=[region_between(lambda tt: k * tt + m, lambda tt: tt * tt, r1, r2)],
    )
    ltex = _sum_tex([(k, "x"), (m, "")])
    return Question(
        key="area_parabola_line",
        statement=(
            r"Знайдіть площу заштрихованої фігури, обмеженої параболою $y = x^2$ "
            rf"та прямою $y = {ltex}$." + _FRAC_NOTE
        ),
        parts=[Part("S", "$S$ = ", val, points=1)],
        seconds=150,
        params={"r1": r1, "r2": r2, "k": k, "m": m},
        svg=svg,
    )


@template("area_below_axis")
def _area_below_axis(rng: random.Random) -> Question:
    """Розуміння знаку: на [r1,r2] функція недодатна, тож площа = |визначений
    інтеграл| = -∫. Парабола гілками вгору, що опускається під вісь."""
    c = rng.choice([1, 4])           # точний квадрат -> цілі нулі
    root = int(sp.sqrt(c))
    h = rng.choice([-1, 0, 1])
    r1, r2 = h - root, h + root
    f = (_x - h) ** 2 - c            # нулі r1, r2; між ними f < 0
    integral = sp.integrate(f, (_x, r1, r2))   # від'ємний
    val = -integral                   # площа = |інтеграл|
    svg = coordinate_plane(
        parabolas=[(1, float(h), float(-c))],
        regions=[region_between(lambda tt: 0.0, lambda tt: (tt - h) ** 2 - c, r1, r2)],
    )
    # LaTeX параболи: (x - h)^2 - c, з коректним знаком h
    if h == 0:
        base = "x^2"
    elif h > 0:
        base = rf"(x - {h})^2"
    else:
        base = rf"(x + {abs(h)})^2"
    ytex = base + f" - {c}"
    return Question(
        key="area_below_axis",
        statement=(
            rf"На проміжку $[{r1};\ {r2}]$ графік функції $y = {ytex}$ "
            r"розташований нижче осі $Ox$."
            + "\nЗнайдіть площу заштрихованої фігури, обмеженої цим графіком та "
            r"віссю $Ox$." + _FRAC_NOTE
        ),
        parts=[Part("S", "$S$ = ", val, points=1)],
        seconds=140,
        params={"c": c, "h": h, "r1": r1, "r2": r2},
        svg=svg,
    )


# =========================================================================
#  ФІЗИЧНЕ ЗАСТОСУВАННЯ
# =========================================================================

@template("def_displacement")
def _displacement(rng: random.Random) -> Question:
    """Шлях як визначений інтеграл швидкості: s = ∫_a^b v(t) dt (v ≥ 0)."""
    p = rng.choice([2, 4, 6])
    q = rng.choice([1, 2, 3])
    a = rng.choice([0, 1])
    b = a + rng.choice([2, 3])
    v = p * _t + q
    val = sp.integrate(v, (_t, a, b))
    vtex = _sum_tex([(p, "t"), (q, "")])
    return Question(
        key="def_displacement",
        statement=(
            rf"Тіло рухається вздовж прямої зі швидкістю $v(t) = {vtex}$ (м/с)."
            + f"\nЯкий шлях воно подолало за проміжок часу від $t = {a}$ до $t = {b}$ (с)?"
            + "\n"
            + r"Шлях обчислюється за формулою $s = \int_a^b v(t)\,dt$."
        ),
        parts=[Part("s", "$s$ = ", val, points=1)],
        seconds=120,
        params={"p": p, "q": q, "a": a, "b": b},
    )
