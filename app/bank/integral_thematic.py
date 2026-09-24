"""Тематичне оцінювання (11 клас): ІНТЕГРАЛ — уся тема.

Покриває весь розділ: означення первісної (F'=f), таблиця первісних (степенева,
1/√x, 1/x², sin, cos, eˣ, 1/cos²x), правила (сума, сталий множник, f(kx+b)),
невизначений інтеграл і стала C, формула Ньютона–Лейбніца, властивості
визначеного інтеграла (адитивність, лінійність), обернена задача (знайти межу),
геометричний зміст і площі (криволінійна трапеція, між кривими, фігура під віссю,
де площа = |інтеграл|), фізичне застосування (шлях = інтеграл швидкості).

ГОЛОВНА ВІДМІННІСТЬ від integral1/integral2: задачі КОМПЛЕКСНІ — перевіряється
ШЛЯХ розв'язання, а не лише готова відповідь. Кожне питання має 2–4 поля
(проміжні етапи: первісна -> стала -> значення; межі перетину -> площа; нулі ->
інтеграл -> площа). Бали всередині питання нормуються (points_per_question), тож
3 правильні кроки з 4 дають 0.75 бала.

Скрізь, де доречно, задіяно ПЕРЕНЕСЕННЯ ПОМИЛКИ (carry): якщо студент помилився
на ранньому кроці, наступні звіряються з ЙОГО власним результатом. Це чесно
оцінює розуміння і водночас робить списування дорожчим — треба пред'явити весь
ланцюжок, а не одне число.

Фізичний зміст у класі ще не давали, тому у відповідній задачі формула наведена
прямо в умові.
"""

from __future__ import annotations

import random

import sympy as sp

from engine import Part, Question, template

from app.bank.plotting import coordinate_plane, region_between

_x = sp.Symbol("x")
_t = sp.Symbol("t")

_FRAC_NOTE = "\nДроби можна вводити як 9/2."


def _signed(v: int) -> str:
    if v == 0:
        return ""
    return f" + {v}" if v > 0 else f" - {abs(v)}"


def _sum_tex(terms: list[tuple[int, str]]) -> str:
    """LaTeX многочлена за списком (коефіцієнт, змінна-LaTeX)."""
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


def _sub(expr, var, value):
    """Підстановка у ВЛАСНИЙ вираз студента (для carry).

    Якщо вираз не залежить від змінної (студент увів константу чи сміття), то
    переносити нема чого: повертаємо None, і крок звіряється зі справжнім
    еталоном. Без цієї перевірки однакове «сміття» у двох полях зараховувалося б
    (підстановка в константу дає ту саму константу)."""
    if expr is None or not getattr(expr, "has", lambda _v: False)(var):
        return None
    return expr.subs(var, value)


def _carry_diff(key: str, var, hi, lo):
    """carry для кроку «інтеграл = F(hi) − F(lo)», порахованого з ВЛАСНОЇ
    первісної студента (поле `key`)."""
    def _fn(prev):
        up, down = _sub(prev[key], var, hi), _sub(prev[key], var, lo)
        return None if up is None or down is None else up - down
    return _fn


# Спільне пояснення кроку «первісна зі сталою 0» — щоб умова була однозначна.
_F0 = (
    "Запишіть $F_0(x)$ — первісну, у якій стала дорівнює нулю "
    "(тобто $F(x) = F_0(x) + C$)."
)


# =========================================================================
#  ПЕРВІСНА ТА НЕВИЗНАЧЕНИЙ ІНТЕГРАЛ
# =========================================================================

@template("th_antideriv_poly_point")
def _poly_point(rng: random.Random) -> Question:
    """Повний ланцюжок: первісна многочлена -> стала C за точкою -> значення."""
    a = rng.choice([3, 6])
    b = rng.choice([-4, -2, 2, 4])
    c = rng.choice([-3, -2, -1, 1, 2, 3])
    x0 = rng.choice([-2, -1, 1, 2])
    x1 = rng.choice([v for v in (-2, -1, 1, 2) if v != x0])
    C = rng.choice([-4, -3, -2, -1, 1, 2, 3, 4, 5])
    f = a * _x**2 + b * _x + c
    F0 = sp.integrate(f, _x)                 # стала 0
    y0 = int(F0.subs(_x, x0)) + C
    val = int(F0.subs(_x, x1)) + C
    ftex = _sum_tex([(a, "x^2"), (b, "x"), (c, "")])

    def carry_c(prev):
        s = _sub(prev["F0"], _x, x0)
        return None if s is None else y0 - s

    def carry_v(prev):
        s = _sub(prev["F0"], _x, x1)
        return None if s is None else s + prev["C"]

    return Question(
        key="th_antideriv_poly_point",
        statement=(
            rf"Дано $f(x) = {ftex}$. Графік первісної проходить через точку "
            rf"$M\left({x0};\ {y0}\right)$."
            + "\n" + _F0
            + f"\nДалі знайдіть сталу $C$ і обчисліть $F({x1})$."
        ),
        parts=[
            Part("F0", "$F_0(x)$ =", F0, kind="expr", points=1),
            Part("C", "$C$ =", C, points=1, carry=carry_c, carry_from=("F0",)),
            Part("v", rf"$F({x1})$ =", val, points=1,
                 carry=carry_v, carry_from=("F0", "C")),
        ],
        seconds=125,
        params={"a": a, "b": b, "c": c, "x0": x0, "x1": x1, "C": C, "y0": y0},
    )


@template("th_antideriv_table_sum")
def _table_sum(rng: random.Random) -> Question:
    r"""Сума ДВОХ різних табличних ($a/\sqrt{x}$ і $b/x^2$) + стала за точкою."""
    a = rng.randint(1, 4)
    x0 = rng.choice([1, 4])
    b = rng.choice([2, 4, 6]) if x0 == 1 else rng.choice([4, 8])
    C = rng.choice([-4, -3, -2, -1, 1, 2, 3, 4])
    f = sp.Rational(a, 1) / sp.sqrt(_x) + sp.Rational(b, 1) / _x**2
    F0 = sp.integrate(f, _x)                 # 2a√x - b/x
    y0 = int(F0.subs(_x, x0)) + C
    ftex = rf"\dfrac{{{a}}}{{\sqrt{{x}}}} + \dfrac{{{b}}}{{x^2}}"

    def carry_c(prev):
        s = _sub(prev["F0"], _x, x0)
        return None if s is None else y0 - s

    return Question(
        key="th_antideriv_table_sum",
        statement=(
            rf"Дано $f(x) = {ftex}$ (при $x>0$). Графік первісної проходить через "
            rf"точку $M\left({x0};\ {y0}\right)$."
            + "\n" + _F0
            + "\nДалі знайдіть сталу $C$."
        ),
        parts=[
            Part("F0", "$F_0(x)$ =", F0, kind="expr", points=1),
            Part("C", "$C$ =", C, points=1, carry=carry_c, carry_from=("F0",)),
        ],
        seconds=100,
        params={"a": a, "b": b, "x0": x0, "C": C, "y0": y0},
    )


@template("th_antideriv_rules")
def _rules(rng: random.Random) -> Question:
    """Правило для f(kx+b) разом із таблицею: дві різні функції в одній сумі."""
    k = rng.choice([2, 3])
    A = rng.choice([1, 2])
    C = rng.choice([-4, -3, -2, -1, 1, 2, 3, 4])
    if rng.random() < 0.5:
        # a·sin(kx) + m·e^(px)
        p = rng.choice([2, 3])
        M = rng.choice([1, 2])
        a, m = k * A, p * M
        f = a * sp.sin(k * _x) + m * sp.exp(p * _x)
        ftex = rf"{a}\sin {k}x + {m}e^{{{p}x}}"
        branch = "sin_exp"
        hint = "(Експоненту вводьте як e^x або exp(x).)"
    else:
        # a·cos(kx) + d/cos²x
        d = rng.choice([1, 2, 3])
        a = k * A
        f = a * sp.cos(k * _x) + sp.Rational(d, 1) / sp.cos(_x) ** 2
        ftex = rf"{a}\cos {k}x + \dfrac{{{d}}}{{\cos^2 x}}"
        branch = "cos_tan"
        hint = "(Тангенс вводьте як tg(x).)"
    F0 = sp.integrate(f, _x)
    y0 = int(F0.subs(_x, 0)) + C

    def carry_c(prev):
        s = _sub(prev["F0"], _x, 0)
        return None if s is None else y0 - s

    return Question(
        key="th_antideriv_rules",
        statement=(
            rf"Дано $f(x) = {ftex}$. Графік первісної проходить через точку "
            rf"$M\left(0;\ {y0}\right)$."
            + "\n" + _F0
            + "\nДалі знайдіть сталу $C$. " + hint
        ),
        parts=[
            Part("F0", "$F_0(x)$ =", F0, kind="expr", points=1),
            Part("C", "$C$ =", C, points=1, carry=carry_c, carry_from=("F0",)),
        ],
        seconds=115,
        params={"branch": branch, "k": k, "C": C, "y0": y0},
    )


@template("th_antideriv_inverse")
def _inverse(rng: random.Random) -> Question:
    """Означення первісної у зворотний бік: за F знайти f = F', тоді f(x₀)."""
    a = rng.choice([1, 2, 3])
    x0 = rng.choice([1, 4])
    b = rng.choice([2, 4, 6]) if x0 == 1 else rng.choice([4, 8])
    F = a * _x**3 + b * sp.sqrt(_x)
    f = sp.diff(F, _x)                       # 3a x² + (b/2)/√x
    val = f.subs(_x, x0)
    Ftex = _sum_tex([(a, "x^3")]) + rf" + {b}\sqrt{{x}}"
    return Question(
        key="th_antideriv_inverse",
        statement=(
            rf"Функція $F(x) = {Ftex}$ є первісною для функції $f$ (при $x>0$)."
            + "\nКористуючись означенням первісної ($F'(x) = f(x)$), знайдіть "
            rf"$f(x)$, а потім обчисліть $f({x0})$."
        ),
        parts=[
            Part("f", "$f(x)$ =", f, kind="expr", points=1),
            Part(
                "v", rf"$f({x0})$ =", val, points=1,
                carry=lambda prev: _sub(prev["f"], _x, x0),
                carry_from=("f",),
            ),
        ],
        seconds=100,
        params={"a": a, "b": b, "x0": x0},
    )


# =========================================================================
#  ВИЗНАЧЕНИЙ ІНТЕГРАЛ: НЬЮТОН–ЛЕЙБНІЦ І ВЛАСТИВОСТІ
# =========================================================================

@template("th_definite_nl")
def _definite_nl(rng: random.Random) -> Question:
    """Ньютон–Лейбніц по кроках: первісна -> значення на верхній межі -> інтеграл."""
    a = rng.choice([3, 6])
    b = rng.choice([-4, -2, 2, 4])
    c = rng.choice([-3, -2, -1, 1, 2, 3])
    m = rng.choice([-2, -1, 0, 1])
    n = m + rng.choice([2, 3])
    f = a * _x**2 + b * _x + c
    F0 = sp.integrate(f, _x)
    up = F0.subs(_x, n)
    val = sp.integrate(f, (_x, m, n))
    ftex = _sum_tex([(a, "x^2"), (b, "x"), (c, "")])

    return Question(
        key="th_definite_nl",
        statement=(
            "Обчисліть визначений інтеграл за формулою Ньютона–Лейбніца:\n$$"
            + _int_tex(str(m), str(n), rf"\left({ftex}\right)") + "$$"
            + "\n" + _F0
            + f"\nПотім обчисліть $F_0({n})$ і сам інтеграл."
        ),
        parts=[
            Part("F0", "$F_0(x)$ =", F0, kind="expr", points=1),
            Part(
                "up", rf"$F_0({n})$ =", up, points=1,
                carry=lambda prev: _sub(prev["F0"], _x, n),
                carry_from=("F0",),
            ),
            Part("I", "інтеграл =", val, points=1,
                 carry=_carry_diff("F0", _x, n, m), carry_from=("F0",)),
        ],
        seconds=120,
        params={"a": a, "b": b, "c": c, "m": m, "n": n},
    )


@template("th_definite_trig")
def _definite_trig(rng: random.Random) -> Question:
    """Визначений інтеграл тригонометричної функції (правило kx + межі з π)."""
    k = rng.choice([2, 3])
    A = rng.choice([1, 2])
    a = k * A
    if rng.random() < 0.5:
        f = a * sp.sin(k * _x)
        hi, hi_tex = sp.pi / k, rf"\frac{{\pi}}{{{k}}}"
        head = rf"{a}\sin {k}x"
    else:
        f = a * sp.cos(k * _x)
        hi, hi_tex = sp.pi / (2 * k), rf"\frac{{\pi}}{{{2 * k}}}"
        head = rf"{a}\cos {k}x"
    F0 = sp.integrate(f, _x)
    val = sp.integrate(f, (_x, 0, hi))
    return Question(
        key="th_definite_trig",
        statement=(
            "Обчисліть визначений інтеграл:\n$$" + _int_tex("0", hi_tex, head) + "$$"
            + "\n" + _F0 + "\nПотім обчисліть інтеграл."
        ),
        parts=[
            Part("F0", "$F_0(x)$ =", F0, kind="expr", points=1),
            Part(
                "I", "інтеграл =", val, points=1,
                carry=_carry_diff("F0", _x, hi, 0),
                carry_from=("F0",),
            ),
        ],
        seconds=105,
        params={"k": k, "a": a},
    )


@template("th_definite_properties")
def _properties(rng: random.Random) -> Question:
    """Властивості БЕЗ обчислення функцій: адитивність за проміжками + лінійність."""
    a = rng.choice([0, 1])
    c = a + rng.choice([1, 2])
    b = c + rng.choice([1, 2])
    P = rng.choice([-4, -3, -2, 2, 3, 4, 5])
    Q = rng.choice([-3, -2, -1, 1, 2, 3])
    R = rng.choice([-3, -2, -1, 1, 2, 3])
    al = rng.choice([2, 3])
    be = rng.choice([2, 3, 4])
    I1 = P + Q                       # адитивність
    I2 = al * I1 - be * R            # лінійність
    return Question(
        key="th_definite_properties",
        statement=(
            rf"Відомо, що $\int_{{{a}}}^{{{c}}} f(x)\,dx = {P}$, "
            rf"$\int_{{{c}}}^{{{b}}} f(x)\,dx = {Q}$ і "
            rf"$\int_{{{a}}}^{{{b}}} g(x)\,dx = {R}$."
            + "\nКористуючись властивостями визначеного інтеграла (не шукаючи самих "
            "функцій), обчисліть:"
            + "\n" + rf"1) $\int_{{{a}}}^{{{b}}} f(x)\,dx$;"
            + "\n" + rf"2) $\int_{{{a}}}^{{{b}}}\left({al}f(x) - {be}g(x)\right)dx$."
        ),
        parts=[
            Part("I1", rf"1) $\int_{{{a}}}^{{{b}}} f\,dx$ =", I1, points=1),
            Part(
                "I2", "2) =", I2, points=1,
                carry=lambda prev: al * prev["I1"] - be * R,
                carry_from=("I1",),
            ),
        ],
        seconds=90,
        params={"a": a, "b": b, "c": c, "P": P, "Q": Q, "R": R, "al": al, "be": be},
    )


@template("th_definite_find_limit")
def _find_limit(rng: random.Random) -> Question:
    """Обернена задача: з рівняння на інтеграл знайти верхню межу (квадратне
    рівняння, брати додатний корінь)."""
    a = rng.choice([2, 4])
    c = rng.choice([1, 3, 5])
    b = rng.choice([2, 3])
    f = a * _x + c
    F0 = sp.integrate(f, _x)                 # (a/2)x² + c x
    S = int(F0.subs(_x, b))
    ftex = _sum_tex([(a, "x"), (c, "")])
    return Question(
        key="th_definite_find_limit",
        statement=(
            rf"Відомо, що $\int_0^b \left({ftex}\right)dx = {S}$, де $b>0$."
            + "\n" + _F0
            + "\nСкладіть рівняння відносно $b$ і знайдіть його додатний корінь."
        ),
        parts=[
            Part("F0", "$F_0(x)$ =", F0, kind="expr", points=1),
            Part("b", "$b$ =", b, points=1),
        ],
        seconds=125,
        params={"a": a, "c": c, "b": b, "S": S},
    )


# =========================================================================
#  ЗАСТОСУВАННЯ: ПЛОЩІ (з рисунком)
# =========================================================================

@template("th_area_trapezoid")
def _area_trapezoid(rng: random.Random) -> Question:
    """Геометричний зміст: площа криволінійної трапеції через первісну."""
    k = rng.choice([1, 2])
    b0 = rng.choice([1, 2])
    n = 2
    f = k * _x + b0
    F0 = sp.integrate(f, _x)
    S = sp.integrate(f, (_x, 0, n))
    svg = coordinate_plane(
        lines=[(k, b0)],
        regions=[region_between(lambda tt: k * tt + b0, lambda tt: 0.0, 0, n)],
    )
    ftex = _sum_tex([(k, "x"), (b0, "")])
    return Question(
        key="th_area_trapezoid",
        statement=(
            "Знайдіть площу заштрихованої фігури, обмеженої лініями "
            rf"$y = {ftex}$, $x = 0$, $x = {n}$ та віссю $Ox$."
            + "\n" + _F0 + f"\nПотім обчисліть площу $S$."
        ),
        parts=[
            Part("F0", "$F_0(x)$ =", F0, kind="expr", points=1),
            Part(
                "S", "$S$ =", S, points=1,
                carry=_carry_diff("F0", _x, n, 0),
                carry_from=("F0",),
            ),
        ],
        seconds=100,
        params={"k": k, "b0": b0, "n": n},
        svg=svg,
    )


@template("th_area_between")
def _area_between(rng: random.Random) -> Question:
    """КОМПЛЕКСНА: спершу знайти межі (точки перетину), тоді площу між кривими."""
    r1, r2 = rng.choice([(-2, 0), (-1, 1), (0, 2), (-2, 1), (-1, 2), (-2, 2)])
    k = r1 + r2
    m = -r1 * r2
    diff = (k * _x + m) - _x**2            # пряма мінус парабола (додатна між r1,r2)
    G = sp.integrate(diff, _x)
    S = sp.integrate(diff, (_x, r1, r2))
    svg = coordinate_plane(
        parabolas=[(1, 0.0, 0.0)],
        lines=[(k, m)],
        regions=[region_between(lambda tt: k * tt + m, lambda tt: tt * tt, r1, r2)],
    )
    ltex = _sum_tex([(k, "x"), (m, "")])
    return Question(
        key="th_area_between",
        statement=(
            r"Знайдіть площу заштрихованої фігури, обмеженої параболою $y = x^2$ "
            rf"та прямою $y = {ltex}$."
            + "\nСпершу знайдіть абсциси точок перетину (межі інтегрування), "
            "потім обчисліть площу." + _FRAC_NOTE
        ),
        parts=[
            Part("lo", "менша абсциса $x_1$ =", r1, points=1),
            Part("hi", "більша абсциса $x_2$ =", r2, points=1),
            Part(
                "S", "$S$ =", S, points=1,
                carry=lambda prev: G.subs(_x, prev["hi"]) - G.subs(_x, prev["lo"]),
                carry_from=("lo", "hi"),
            ),
        ],
        seconds=165,
        params={"r1": r1, "r2": r2, "k": k, "m": m},
        svg=svg,
    )


@template("th_area_below_axis")
def _area_below(rng: random.Random) -> Question:
    """КОМПЛЕКСНА + розуміння знаку: нулі -> інтеграл (від'ємний!) -> площа =|I|."""
    c = rng.choice([1, 4])
    root = int(sp.sqrt(c))
    h = rng.choice([-1, 0, 1])
    r1, r2 = h - root, h + root
    f = (_x - h) ** 2 - c
    G = sp.integrate(f, _x)
    I = sp.integrate(f, (_x, r1, r2))       # від'ємний
    S = -I
    svg = coordinate_plane(
        parabolas=[(1, float(h), float(-c))],
        regions=[region_between(lambda tt: 0.0, lambda tt: (tt - h) ** 2 - c, r1, r2)],
    )
    if h == 0:
        base = "x^2"
    elif h > 0:
        base = rf"(x - {h})^2"
    else:
        base = rf"(x + {abs(h)})^2"
    ytex = base + f" - {c}"
    return Question(
        key="th_area_below_axis",
        statement=(
            rf"Дано функцію $y = {ytex}$, графік якої заштриховано між її нулями."
            + "\nЗнайдіть нулі функції, обчисліть визначений інтеграл у цих межах "
            "і визначте площу заштрихованої фігури."
            + "\nЗверніть увагу: на цьому проміжку функція недодатна, тому інтеграл "
            r"і площа — НЕ те саме ($S = |I|$)." + _FRAC_NOTE
        ),
        parts=[
            Part("lo", "менший нуль $x_1$ =", r1, points=1),
            Part("hi", "більший нуль $x_2$ =", r2, points=1),
            Part(
                "I", "інтеграл $I$ =", I, points=1,
                carry=lambda prev: G.subs(_x, prev["hi"]) - G.subs(_x, prev["lo"]),
                carry_from=("lo", "hi"),
            ),
            Part(
                "S", "площа $S$ =", S, points=1,
                # Переносимо крок «площа = |інтеграл|» лише тоді, коли студент
                # справді отримав ВІД'ЄМНИЙ інтеграл (тобто показав розуміння
                # знаку). Інакше модуль нічого не знімає і крок не зараховується.
                carry=lambda prev: (
                    -prev["I"] if getattr(prev["I"], "is_negative", False) else None
                ),
                carry_from=("I",),
            ),
        ],
        seconds=175,
        params={"c": c, "h": h, "r1": r1, "r2": r2},
        svg=svg,
    )


# =========================================================================
#  ФІЗИЧНЕ ЗАСТОСУВАННЯ (формулу наводимо — тему ще не давали)
# =========================================================================

@template("th_physics_path")
def _physics_path(rng: random.Random) -> Question:
    """Шлях як визначений інтеграл швидкості. Формула — в умові."""
    p = rng.choice([2, 4, 6])
    q = rng.choice([1, 2, 3])
    t1 = rng.choice([0, 1])
    t2 = t1 + rng.choice([2, 3])
    v = p * _t + q
    S0 = sp.integrate(v, _t)
    s = sp.integrate(v, (_t, t1, t2))
    vtex = _sum_tex([(p, "t"), (q, "")])
    return Question(
        key="th_physics_path",
        statement=(
            rf"Тіло рухається прямолінійно зі швидкістю $v(t) = {vtex}$ (м/с)."
            + f"\nЗнайдіть шлях, який воно подолало від $t = {t1}$ до $t = {t2}$ (с)."
            + "\nШлях обчислюється за формулою $s = \\int_{t_1}^{t_2} v(t)\\,dt$."
            + "\nСпершу запишіть первісну $S_0(t)$ (зі сталою 0), потім знайдіть шлях."
        ),
        parts=[
            Part("S0", "$S_0(t)$ =", S0, kind="expr", points=1),
            Part(
                "s", "$s$ =", s, points=1,
                carry=_carry_diff("S0", _t, t2, t1),
                carry_from=("S0",),
            ),
        ],
        seconds=95,
        params={"p": p, "q": q, "t1": t1, "t2": t2},
    )
