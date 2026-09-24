"""Лекція 5: Функція. Границя функції в точці і на нескінченності. Неперервність.

Покриває весь розділ лекції (яка сама є вижимкою, тож обсяг трохи ширший за неї):
  ФУНКЦІЯ — область визначення, класифікація (парність, період), складена
    функція, обернена функція;
  ГРАНИЦІ — основні теореми й обчислення з розкриттям невизначеностей
    ∞/∞ (порівняння степенів), 0/0 (розкладання на множники), ∞−∞ (сполучений
    вираз), перша (sin x / x) і друга ((1+1/x)^x = e) важливі границі;
  НЕПЕРЕРВНІСТЬ — означення (lim f = f(x₀)), односторонні границі й «стрибок»,
    види розривів (усувний та II роду), читання розриву з ГРАФІКА.

Як і в тематичному оцінюванні з інтеграла, задачі КОМПЛЕКСНІ: перевіряється шлях
(2–3 поля на задачу), часткові бали нормуються, а перенесення помилки (carry)
звіряє наступні кроки з власним результатом студента.

Відповіді з π вводяться як pi (напр. 2*pi/3), з e — як e^k (напр. e^6).
"""

from __future__ import annotations

import random

import sympy as sp

from engine import Part, Question, template

from app.bank.plotting import coordinate_plane

_x = sp.Symbol("x")


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


def _sub(expr, var, value):
    """Підстановка у ВЛАСНИЙ вираз студента (carry). Якщо вираз не залежить від
    змінної (введено константу/сміття) — не переносимо, щоб однакове сміття у
    двох полях не зараховувалося."""
    if expr is None or not getattr(expr, "has", lambda _v: False)(var):
        return None
    return expr.subs(var, value)


def _lim_tex(point: str, body: str) -> str:
    return rf"\lim_{{x \to {point}}} {body}"


# =========================================================================
#  ФУНКЦІЯ
# =========================================================================

@template("lim_domain")
def _domain(rng: random.Random) -> Question:
    r"""Область визначення $\sqrt{x+a}/(x-b)$: ліва межа і виключена точка."""
    a = rng.randint(1, 5)
    b = rng.randint(1, 4)
    return Question(
        key="lim_domain",
        statement=(
            r"Знайдіть область визначення функції"
            + "\n" + rf"$$f(x) = \dfrac{{\sqrt{{x + {a}}}}}{{x - {b}}}$$"
            + "\nУкажіть найменше допустиме значення $x$ і точку, яку потрібно "
            "виключити з області визначення."
        ),
        parts=[
            Part("lo", "найменше $x$ =", -a, points=1),
            Part("ex", "виключити $x$ =", b, points=1),
        ],
        seconds=85,
        params={"a": a, "b": b},
    )


@template("lim_classify")
def _classify(rng: random.Random) -> Question:
    """Класифікація: парність (через f(-x)) і найменший період sin/cos."""
    even = rng.random() < 0.5
    x0 = rng.choice([1, 2])
    if even:
        a, b, c = rng.choice([1, 2, 3]), rng.choice([-3, -2, 2, 3]), rng.choice([-2, 2])
        f = a * _x**4 + b * _x**2 + c
        ftex = _sum_tex([(a, "x^4"), (b, "x^2"), (c, "")])
    else:
        a, b = rng.choice([1, 2]), rng.choice([-4, -3, 3, 4])
        f = a * _x**3 + b * _x
        ftex = _sum_tex([(a, "x^3"), (b, "x")])
    fneg = sp.expand(f.subs(_x, -_x))
    val = fneg.subs(_x, x0)                    # f(-x0)
    k = rng.choice([2, 3, 4])
    m = rng.choice([2, 3, 5])
    period = sp.nsimplify(2 * sp.pi / k)
    trig = rng.choice(["sin", "cos"])
    return Question(
        key="lim_classify",
        statement=(
            rf"Дано функції $f(x) = {ftex}$ та $g(x) = {m}\{trig} {k}x$."
            + "\n1) Знайдіть і спростіть $f(-x)$ (це показує парність)."
            + rf" 2) Обчисліть $f(-{x0})$."
            + "\n3) Укажіть найменший додатний період функції $g$ "
            "(відповідь із $\\pi$ вводьте як pi)."
        ),
        parts=[
            Part("fneg", "$f(-x)$ =", fneg, kind="expr", points=1),
            Part(
                "val", rf"$f(-{x0})$ =", val, points=1,
                carry=lambda prev: _sub(prev["fneg"], _x, x0),
                carry_from=("fneg",),
            ),
            Part("T", "$T$ =", period, points=1),
        ],
        seconds=120,
        params={"even": even, "x0": x0, "k": k},
    )


@template("lim_composite")
def _composite(rng: random.Random) -> Question:
    """Складена функція y = f(φ(x)): записати і обчислити в точці."""
    a = rng.choice([-3, -2, -1, 1, 2, 3])
    k = rng.choice([2, 3])
    b = rng.choice([-3, -2, -1, 1, 2, 3])
    x0 = rng.choice([-1, 0, 1, 2])
    inner = k * _x + b
    comp = sp.expand(inner**2 + a)
    val = comp.subs(_x, x0)
    utex = _sum_tex([(k, "x"), (b, "")])
    return Question(
        key="lim_composite",
        statement=(
            rf"Дано $f(u) = u^2{_signed(a)}$ та $u = \varphi(x) = {utex}$."
            + "\nЗапишіть складену функцію $y = f(\\varphi(x))$ у розкритому "
            + rf"вигляді та обчисліть її значення при $x = {x0}$."
        ),
        parts=[
            Part("comp", r"$f(\varphi(x))$ =", comp, kind="expr", points=1),
            Part(
                "val", rf"значення при $x={x0}$ =", val, points=1,
                carry=lambda prev: _sub(prev["comp"], _x, x0),
                carry_from=("comp",),
            ),
        ],
        seconds=110,
        params={"a": a, "k": k, "b": b, "x0": x0},
    )


@template("lim_inverse")
def _inverse(rng: random.Random) -> Question:
    """Обернена функція до лінійної: y = ax + b -> y = (x - b)/a."""
    a = rng.choice([2, 3, 4])
    b = rng.choice([-4, -3, -2, -1, 1, 2, 3, 4])
    t = rng.choice([-2, -1, 1, 2])
    x1 = a * t + b                 # щоб значення обернутої було цілим
    inv = (_x - b) / a
    ftex = _sum_tex([(a, "x"), (b, "")])
    return Question(
        key="lim_inverse",
        statement=(
            rf"Дано функцію $y = {ftex}$."
            + "\nЗнайдіть обернену функцію і запишіть її у вигляді $y = \\varphi(x)$, "
            rf"а потім обчисліть $\varphi({x1})$."
        ),
        parts=[
            Part("inv", r"$\varphi(x)$ =", inv, kind="expr", points=1),
            Part(
                "val", rf"$\varphi({x1})$ =", t, points=1,
                carry=lambda prev: _sub(prev["inv"], _x, x1),
                carry_from=("inv",),
            ),
        ],
        seconds=100,
        params={"a": a, "b": b, "x1": x1, "t": t},
    )


# =========================================================================
#  ОБЧИСЛЕННЯ ГРАНИЦЬ
# =========================================================================

@template("lim_rational_infty")
def _rational_infty(rng: random.Random) -> Question:
    r"""Невизначеність $\infty/\infty$: порівняння степенів чисельника й знаменника."""
    a, d = rng.choice([(2, 6), (3, 4), (5, 2), (4, 6), (3, 9)])
    p, q = rng.choice([-3, -2, 2, 3]), rng.choice([-5, -1, 1, 5])
    r, s = rng.choice([-2, 2, 3]), rng.choice([-4, 1, 7])
    v1 = sp.nsimplify(sp.Rational(a, d))
    top = _sum_tex([(a, "x^2"), (p, "x"), (q, "")])
    bot = _sum_tex([(d, "x^2"), (r, "x"), (s, "")])
    top2 = _sum_tex([(a, "x"), (p, "")])
    return Question(
        key="lim_rational_infty",
        statement=(
            "Обчисліть границі на нескінченності:"
            + "\n" + rf"$$1)\ \ {_lim_tex(r'\infty', rf'\dfrac{{{top}}}{{{bot}}}')}"
            + rf"\qquad 2)\ \ {_lim_tex(r'\infty', rf'\dfrac{{{top2}}}{{{bot}}}')}$$"
            + "\n(Порівняйте найвищі степені чисельника й знаменника.)"
        ),
        parts=[
            Part("l1", "1) =", v1, points=1),
            Part("l2", "2) =", 0, points=1),
        ],
        seconds=95,
        params={"a": a, "d": d},
    )


@template("lim_zero_over_zero")
def _zero_over_zero(rng: random.Random) -> Question:
    r"""Невизначеність $0/0$: знайти спільний корінь і скоротити множник."""
    r = rng.choice([-2, -1, 1, 2, 3])
    s = rng.choice([v for v in (-3, -1, 2, 4) if v != r])
    q = rng.choice([v for v in (-4, -2, 1, 3) if v not in (r, s)])
    num = sp.expand((_x - r) * (_x - s))
    den = sp.expand((_x - r) * (_x - q))
    val = sp.nsimplify(sp.Rational(r - s, r - q))
    ntex = _sum_tex([(1, "x^2"), (-(r + s), "x"), (r * s, "")])
    dtex = _sum_tex([(1, "x^2"), (-(r + q), "x"), (r * q, "")])
    return Question(
        key="lim_zero_over_zero",
        statement=(
            "Дано границю"
            + "\n" + rf"$$\lim_{{x \to x_0}} \dfrac{{{ntex}}}{{{dtex}}}$$"
            + "\nЧисельник і знаменник мають спільний корінь — саме в цій точці "
            "виникає невизначеність $0/0$."
            + "\n1) Знайдіть цю точку $x_0$. 2) Обчисліть границю (скоротіть "
            "спільний множник)."
        ),
        parts=[
            Part("x0", "$x_0$ =", r, points=1),
            Part("lim", "границя =", val, points=1),
        ],
        seconds=150,
        params={"r": r, "s": s, "q": q},
    )


@template("lim_conjugate")
def _conjugate(rng: random.Random) -> Question:
    r"""Невизначеність $\infty-\infty$: множення на сполучений вираз."""
    a = rng.choice([2, 4, 6, 8])
    val = sp.Rational(a, 2)
    return Question(
        key="lim_conjugate",
        statement=(
            "Обчисліть границю"
            + "\n" + rf"$$\lim_{{x \to \infty}}\left(\sqrt{{x^2 + {a}x}} - x\right)$$"
            + "\n(Помножте і поділіть на сполучений вираз "
            r"$\sqrt{x^2 + " + str(a) + r"x} + x$.)"
        ),
        parts=[Part("lim", "границя =", val, points=1)],
        seconds=125,
        params={"a": a},
    )


@template("lim_first_important")
def _first_important(rng: random.Random) -> Question:
    r"""Перша важлива границя $\lim_{x\to 0}\frac{\sin x}{x} = 1$."""
    a = rng.choice([2, 3, 5, 6])
    b = rng.choice([2, 3, 4])
    v1 = a
    v2 = sp.nsimplify(sp.Rational(a, b))
    return Question(
        key="lim_first_important",
        statement=(
            "Скориставшись першою важливою границею "
            r"$\lim_{x \to 0}\dfrac{\sin x}{x} = 1$, обчисліть:"
            + "\n" + rf"$$1)\ \ \lim_{{x \to 0}} \dfrac{{\sin {a}x}}{{x}}"
            + rf"\qquad 2)\ \ \lim_{{x \to 0}} \dfrac{{\sin {a}x}}{{\operatorname{{tg}} {b}x}}$$"
        ),
        parts=[
            Part("l1", "1) =", v1, points=1),
            Part("l2", "2) =", v2, points=1),
        ],
        seconds=105,
        params={"a": a, "b": b},
    )


@template("lim_second_important")
def _second_important(rng: random.Random) -> Question:
    r"""Друга важлива границя $\lim_{x\to\infty}(1+1/x)^x = e$."""
    a = rng.choice([2, 3])
    b = rng.choice([2, 3])
    return Question(
        key="lim_second_important",
        statement=(
            "Скориставшись другою важливою границею "
            r"$\lim_{x \to \infty}\left(1 + \dfrac{1}{x}\right)^{x} = e$, обчисліть:"
            + "\n" + rf"$$1)\ \ \lim_{{x \to \infty}}\left(1 + \dfrac{{{a}}}{{x}}\right)^{{x}}"
            + rf"\qquad 2)\ \ \lim_{{x \to \infty}}\left(1 + \dfrac{{{a}}}{{x}}\right)^{{{b}x}}$$"
            + "\nВідповідь записуйте у вигляді e^k (напр. e^6)."
        ),
        parts=[
            Part("l1", "1) =", sp.exp(a), points=1),
            Part("l2", "2) =", sp.exp(a * b), points=1),
        ],
        seconds=125,
        params={"a": a, "b": b},
    )


# =========================================================================
#  НЕПЕРЕРВНІСТЬ
# =========================================================================

@template("lim_piecewise_jump")
def _piecewise_jump(rng: random.Random) -> Question:
    """Означення неперервності: односторонні границі кусково заданої функції
    і «стрибок». Інколи стрибок = 0, тобто функція неперервна."""
    x0 = rng.choice([-2, -1, 1, 2])
    k1, k2 = rng.choice([1, 2, -1]), rng.choice([1, -1, 2])
    b1 = rng.choice([-2, -1, 0, 1, 2])
    left = k1 * x0 + b1
    # половина випадків — неперервна (стрибок 0)
    if rng.random() < 0.4:
        b2 = left - k2 * x0
    else:
        b2 = left - k2 * x0 + rng.choice([-3, -2, 2, 3])
    right = k2 * x0 + b2
    jump = right - left
    t1 = _sum_tex([(k1, "x"), (b1, "")])
    t2 = _sum_tex([(k2, "x"), (b2, "")])
    return Question(
        key="lim_piecewise_jump",
        statement=(
            "Дано кусково задану функцію"
            + "\n" + rf"$$f(x) = \begin{{cases}} {t1}, & x < {x0} \\ {t2}, & x \ge {x0}"
            + r"\end{cases}$$"
            + "\n" + rf"Дослідіть її на неперервність у точці $x_0 = {x0}$: знайдіть "
            "односторонні границі та стрибок (права мінус ліва)."
            + "\nЯкщо стрибок дорівнює 0 — функція неперервна."
        ),
        parts=[
            Part("L", r"ліва границя =", left, points=1),
            Part("R", r"права границя =", right, points=1),
            Part(
                "J", "стрибок =", jump, points=1,
                carry=lambda prev: prev["R"] - prev["L"],
                carry_from=("L", "R"),
            ),
        ],
        seconds=120,
        params={"x0": x0, "k1": k1, "b1": b1, "k2": k2, "b2": b2},
    )


@template("lim_discontinuity_types")
def _discontinuity_types(rng: random.Random) -> Question:
    """Види розривів: спільний множник дає УСУВНИЙ розрив, «зайвий» корінь
    знаменника — розрив II РОДУ. Плюс границя в усувній точці."""
    p = rng.choice([-2, -1, 1, 2])
    q = rng.choice([v for v in (-3, -1, 2, 3) if v != p])
    s = rng.choice([v for v in (-4, -2, 1, 4) if v not in (p, q)])
    val = sp.nsimplify(sp.Rational(p - s, p - q))
    ntex = _sum_tex([(1, "x^2"), (-(p + s), "x"), (p * s, "")])
    dtex = _sum_tex([(1, "x^2"), (-(p + q), "x"), (p * q, "")])
    return Question(
        key="lim_discontinuity_types",
        statement=(
            "Дано функцію"
            + "\n" + rf"$$f(x) = \dfrac{{{ntex}}}{{{dtex}}}$$"
            + "\nРозкладіть чисельник і знаменник на множники та визначте точки "
            "розриву."
            + "\n1) У якій точці розрив УСУВНИЙ (чисельник і знаменник мають "
            "спільний множник)? 2) У якій точці розрив II РОДУ (границя "
            "нескінченна)? 3) Чому дорівнює границя в точці усувного розриву?"
        ),
        parts=[
            Part("rem", "1) усувний при $x$ =", p, points=1),
            Part("inf", "2) II роду при $x$ =", q, points=1),
            Part("lim", "3) границя =", val, points=1),
        ],
        seconds=165,
        params={"p": p, "q": q, "s": s},
    )


@template("lim_graph_continuity")
def _graph_continuity(rng: random.Random) -> Question:
    """РИСУНОК: кусково-лінійний графік зі «стрибком» — зчитати точку розриву
    й односторонні границі."""
    x0 = rng.choice([-2, -1, 1, 2])
    left = rng.choice([-3, -2, -1, 1, 2, 3])
    right = rng.choice([v for v in (-3, -2, -1, 1, 2, 3) if v != left])
    k1, k2 = rng.choice([-1, 0, 1]), rng.choice([-1, 0, 1])
    b1, b2 = left - k1 * x0, right - k2 * x0
    svg = coordinate_plane(
        segments=[(k1, b1, x0 - 3, x0), (k2, b2, x0, x0 + 3)],
        points=[(x0, left), (x0, right)],
    )
    return Question(
        key="lim_graph_continuity",
        statement=(
            r"На рисунку — графік функції $y = f(x)$, яка має розрив у точці "
            r"$x_0$ (двома точками позначено її односторонні значення)."
            + "\nВизначте за графіком:"
            + r" 1) абсцису $x_0$;"
            + r" 2) ліву границю $\lim\limits_{x \to x_0^-} f(x)$;"
            + r" 3) праву границю $\lim\limits_{x \to x_0^+} f(x)$."
        ),
        parts=[
            Part("x0", "1) $x_0$ =", x0, points=1),
            Part("L", "2) ліва границя =", left, points=1),
            Part("R", "3) права границя =", right, points=1),
        ],
        seconds=100,
        params={"x0": x0, "left": left, "right": right},
        svg=svg,
    )
