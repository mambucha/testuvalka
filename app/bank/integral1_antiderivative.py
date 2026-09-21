"""Тест 1 (11 клас): первісна та невизначений інтеграл.

Повністю за програмою 11 класу: означення первісної (F'=f), основна властивість
(усі первісні відрізняються сталою C), таблиця первісних (степенева, 1/x², 1/√x,
sin, cos, eˣ, 1/cos²x, 1/sin²x), правила знаходження первісних (сума, сталий
множник, правило для f(kx+b)), знаходження первісної за заданою точкою (визначення
сталої C), обернений зв'язок «за первісною — функцію», фізичний зміст (первісна
швидкості — закон руху).

Тест НЕ елементарний: майже кожне питання — це інтегрування + визначення сталої C
за точкою, тобто студент має записати саме первісну $F(x)$ (відповідь-вираз,
kind="expr"), а не одну арифметичну дію. Тому активно задіяні екранна клавіатура
і живий математичний прев'ю.

Грейдинг виразів — символьний (engine.equal через sp.simplify), тож будь-яка
алгебраїчно еквівалентна форма запису первісної зараховується. Невизначеність
«+C» усунена скрізь: стала визначається за точкою, або відповідь — число.
"""

from __future__ import annotations

import random

import sympy as sp

from engine import Part, Question, template

_x = sp.Symbol("x")
_t = sp.Symbol("t")


# --- невеликі помічники для LaTeX умови ----------------------------------

def _signed(v: int) -> str:
    """Доданок зі знаком для запису «... ± v» (порожньо, якщо 0)."""
    if v == 0:
        return ""
    return f" + {v}" if v > 0 else f" - {abs(v)}"


def _sum_tex(terms: list[tuple[int, str]]) -> str:
    """LaTeX многочлена за списком (коефіцієнт, змінна-LaTeX). Порожня змінна —
    вільний член. Нульові доданки пропускаються, коефіцієнт ±1 при змінній
    ховається («1x²» -> «x²»)."""
    out = ""
    for coef, var in terms:
        if coef == 0:
            continue
        mag = abs(coef)
        if var:
            body = ("" if mag == 1 else str(mag)) + var
        else:
            body = str(mag)
        if not out:
            out = ("-" if coef < 0 else "") + body
        else:
            out += (" - " if coef < 0 else " + ") + body
    return out or "0"


def _point(x0_tex: str, y0: int) -> str:
    r"""LaTeX точки $M(x_0;\ y_0)$."""
    return rf"M\left({x0_tex};\ {y0}\right)"


_ASK_F = "$F(x) =$"
# спільний «хвіст» умови для задач «знайти первісну через точку»
_TAIL = "\nграфік якої проходить через точку "


# =========================================================================
#  СТЕПЕНЕВА / МНОГОЧЛЕНИ
# =========================================================================

@template("antideriv_poly_point")
def _poly_point(rng: random.Random) -> Question:
    """Первісна квадратного тричлена, визначена за точкою (базова, але повна:
    інтегрування + знаходження сталої C, відповідь-вираз F(x))."""
    a = rng.choice([3, 6])            # a/3 — ціле
    b = rng.choice([-4, -2, 2, 4])    # b/2 — ціле
    c = rng.choice([-3, -2, -1, 1, 2, 3])
    x0 = rng.choice([-2, -1, 1, 2])
    C = rng.choice([-3, -2, -1, 1, 2, 3, 4, 5])
    f = a * _x**2 + b * _x + c
    Fb = sp.integrate(f, _x)
    y0 = int(Fb.subs(_x, x0)) + C
    ans = Fb + C
    ftex = _sum_tex([(a, "x^2"), (b, "x"), (c, "")])
    return Question(
        key="antideriv_poly_point",
        statement=(
            rf"Знайдіть первісну $F$ функції $f(x) = {ftex}$,"
            + _TAIL + f"${_point(str(x0), y0)}$."
        ),
        parts=[Part("F", _ASK_F, ans, kind="expr", points=1)],
        seconds=130,
        params={"a": a, "b": b, "c": c, "x0": x0, "C": C, "y0": y0},
    )


@template("antideriv_expand")
def _expand(rng: random.Random) -> Question:
    """Спершу тотожне перетворення (розкрити дужки), потім первісна через точку.
    Форми: (x±a)² або (x+p)(x−p)=x²−p²."""
    x0 = rng.choice([-3, 3])          # щоб x₀³/3 було цілим
    C = rng.choice([-4, -3, -2, 2, 3, 4, 5])
    if rng.random() < 0.5:
        a = rng.choice([1, 2, 3])
        s = rng.choice([-1, 1])
        f = (_x + s * a) ** 2
        ftex = rf"\left(x {'+' if s > 0 else '-'} {a}\right)^2"
        kind = "square"
        pp = a * s
    else:
        p = rng.choice([2, 3, 4])
        f = (_x + p) * (_x - p)
        ftex = rf"\left(x + {p}\right)\left(x - {p}\right)"
        kind = "diff"
        pp = p
    fe = sp.expand(f)
    Fb = sp.integrate(fe, _x)
    y0 = int(Fb.subs(_x, x0)) + C
    ans = Fb + C
    return Question(
        key="antideriv_expand",
        statement=(
            r"Спростіть підінтегральний вираз і знайдіть первісну $F$ функції "
            rf"$f(x) = {ftex}$,"
            + _TAIL + f"${_point(str(x0), y0)}$."
        ),
        parts=[Part("F", _ASK_F, ans, kind="expr", points=1)],
        seconds=125,
        params={"kind": kind, "pp": pp, "x0": x0, "C": C, "y0": y0},
    )


@template("antideriv_cubic_value")
def _cubic_value(rng: random.Random) -> Question:
    """Первісна кубічної функції через точку, потім ОБЧИСЛИТИ значення в іншій
    точці (відповідь — число). Задіює табличну x³ -> x⁴/4."""
    a = rng.choice([4, 8])            # a/4 — ціле
    c = rng.choice([-3, -2, -1, 1, 2, 3])
    x0 = rng.choice([-2, -1, 1, 2])
    x1 = rng.choice([xx for xx in (-2, -1, 1, 2) if xx != x0])
    C = rng.choice([-3, -2, -1, 1, 2, 3])
    f = a * _x**3 + c
    Fb = sp.integrate(f, _x)
    y0 = int(Fb.subs(_x, x0)) + C
    val = int(Fb.subs(_x, x1)) + C
    ftex = _sum_tex([(a, "x^3"), (c, "")])
    return Question(
        key="antideriv_cubic_value",
        statement=(
            rf"Первісна $F$ функції $f(x) = {ftex}$ проходить через точку "
            rf"${_point(str(x0), y0)}$."
            + "\nОбчисліть " + rf"$F({x1})$."
        ),
        parts=[Part("v", rf"$F({x1}) =$", val, points=1)],
        seconds=115,
        params={"a": a, "c": c, "x0": x0, "x1": x1, "C": C, "y0": y0},
    )


# =========================================================================
#  ТАБЛИЦЯ ПЕРВІСНИХ (нестепеневі / дробові)
# =========================================================================

@template("antideriv_reciprocal_sq")
def _reciprocal_sq(rng: random.Random) -> Question:
    """Таблична 1/x² -> −1/x. f(x)=k/x²+m, первісна через точку."""
    k = rng.choice([2, 4, 6])         # парне -> k/x₀ ціле для |x₀|∈{1,2}
    m = rng.choice([-3, -2, -1, 1, 2, 3])
    x0 = rng.choice([-2, -1, 1, 2])
    C = rng.choice([-3, -2, -1, 1, 2, 3, 4])
    f = sp.Rational(k, 1) / _x**2 + m
    Fb = sp.integrate(f, _x)          # -k/x + m x
    y0 = int(Fb.subs(_x, x0)) + C
    ans = Fb + C
    ftex = rf"\dfrac{{{k}}}{{x^2}}{_signed(m)}"
    return Question(
        key="antideriv_reciprocal_sq",
        statement=(
            rf"Знайдіть первісну $F$ функції $f(x) = {ftex}$,"
            + _TAIL + f"${_point(str(x0), y0)}$."
        ),
        parts=[Part("F", _ASK_F, ans, kind="expr", points=1)],
        seconds=120,
        params={"k": k, "m": m, "x0": x0, "C": C, "y0": y0},
    )


@template("antideriv_sqrt")
def _sqrt(rng: random.Random) -> Question:
    """Таблична 1/√x -> 2√x. f(x)=k/√x+m, первісна через точку (x₀ — точний
    квадрат)."""
    k = rng.choice([1, 2, 3, 4, 5])
    m = rng.choice([-3, -2, -1, 1, 2, 3])
    x0 = rng.choice([1, 4, 9])
    C = rng.choice([-3, -2, -1, 1, 2, 3, 4])
    f = sp.Rational(k, 1) / sp.sqrt(_x) + m
    Fb = sp.integrate(f, _x)          # 2k√x + m x
    y0 = int(Fb.subs(_x, x0)) + C
    ans = Fb + C
    ftex = rf"\dfrac{{{k}}}{{\sqrt{{x}}}}{_signed(m)}"
    return Question(
        key="antideriv_sqrt",
        statement=(
            rf"Знайдіть первісну $F$ функції $f(x) = {ftex}$ (при $x>0$),"
            + _TAIL + f"${_point(str(x0), y0)}$."
        ),
        parts=[Part("F", _ASK_F, ans, kind="expr", points=1)],
        seconds=120,
        params={"k": k, "m": m, "x0": x0, "C": C, "y0": y0},
    )


# =========================================================================
#  ПРАВИЛО ДЛЯ f(kx + b)
# =========================================================================

@template("antideriv_linear_power")
def _linear_power(rng: random.Random) -> Question:
    """Правило первісної для f(kx+b): степінь (kx+b)ⁿ. Стала визначається в
    точці, де основа перетворюється на 0."""
    k = rng.choice([2, 3])
    j = rng.choice([-2, -1, 1, 2])
    b = k * j                          # у точці x₀=-j основа kx+b = 0
    n = rng.choice([2, 3])
    x0 = -j
    C = rng.choice([-4, -3, -2, 2, 3, 4, 5])
    f = (k * _x + b) ** n
    # КОМПАКТНА первісна за правилом f(kx+b): (kx+b)^(n+1)/(k(n+1)). НЕ через
    # sp.integrate — той розкриває многочлен і губить сталу (форми різняться на
    # константу), через що точка x₀=-j давала б неціле значення.
    Fb = (k * _x + b) ** (n + 1) / (k * (n + 1))
    y0 = int(Fb.subs(_x, x0)) + C      # основа в x₀ = 0  ->  Fb = 0,  y0 = C
    ans = Fb + C
    ftex = rf"\left({k}x{_signed(b)}\right)^{{{n}}}"
    return Question(
        key="antideriv_linear_power",
        statement=(
            rf"Знайдіть первісну $F$ функції $f(x) = {ftex}$,"
            + _TAIL + f"${_point(str(x0), y0)}$."
            + "\n(Скористайтеся правилом первісної для $f(kx+b)$.)"
        ),
        parts=[Part("F", _ASK_F, ans, kind="expr", points=1)],
        seconds=120,
        params={"k": k, "b": b, "n": n, "x0": x0, "C": C, "y0": y0},
    )


@template("antideriv_trig_linear")
def _trig_linear(rng: random.Random) -> Question:
    """Таблична sin/cos + правило для kx: f(x)=a·cos(kx) або a·sin(kx)."""
    k = rng.choice([2, 3])
    m = rng.choice([1, 2])
    a = k * m                          # a/k = m — ціле
    C = rng.choice([-4, -3, -2, 2, 3, 4, 5])
    is_cos = rng.random() < 0.5
    if is_cos:
        f = a * sp.cos(k * _x)
        Fb = sp.integrate(f, _x)       # m·sin(kx)
        head = rf"{a}\cos {k}x"
    else:
        f = a * sp.sin(k * _x)
        Fb = sp.integrate(f, _x)       # -m·cos(kx)
        head = rf"{a}\sin {k}x"
    y0 = int(Fb.subs(_x, 0)) + C       # cos:0+C ; sin:-m+C
    ans = Fb + C
    return Question(
        key="antideriv_trig_linear",
        statement=(
            rf"Знайдіть первісну $F$ функції $f(x) = {head}$,"
            + _TAIL + f"${_point('0', y0)}$."
        ),
        parts=[Part("F", _ASK_F, ans, kind="expr", points=1)],
        seconds=115,
        params={"k": k, "a": a, "is_cos": is_cos, "C": C, "y0": y0},
    )


@template("antideriv_exp_linear")
def _exp_linear(rng: random.Random) -> Question:
    """Таблична eˣ + правило для kx: f(x)=a·e^{kx}."""
    k = rng.choice([2, 3])
    m = rng.choice([1, 2])
    a = k * m
    C = rng.choice([-4, -3, -2, 2, 3, 4, 5])
    f = a * sp.exp(k * _x)
    Fb = sp.integrate(f, _x)           # m·e^{kx}
    y0 = int(Fb.subs(_x, 0)) + C       # m + C
    ans = Fb + C
    head = rf"{a}e^{{{k}x}}"
    return Question(
        key="antideriv_exp_linear",
        statement=(
            rf"Знайдіть первісну $F$ функції $f(x) = {head}$,"
            + _TAIL + f"${_point('0', y0)}$."
            + "\n(Позначення для введення: e^x або exp(x).)"
        ),
        parts=[Part("F", _ASK_F, ans, kind="expr", points=1)],
        seconds=115,
        params={"k": k, "a": a, "C": C, "y0": y0},
    )


@template("antideriv_trig_table")
def _trig_table(rng: random.Random) -> Question:
    r"""«Складніші» табличні: 1/cos²x -> tg x, 1/sin²x -> −ctg x."""
    a = rng.choice([1, 2, 3])
    C = rng.choice([-4, -3, -2, 2, 3, 4, 5])
    is_tan = rng.random() < 0.5
    if is_tan:
        f = sp.Rational(a, 1) / sp.cos(_x) ** 2
        Fb = a * sp.tan(_x)
        x0_tex, x0 = "0", sp.Integer(0)
        head = rf"\dfrac{{{a}}}{{\cos^2 x}}"
    else:
        f = sp.Rational(a, 1) / sp.sin(_x) ** 2
        Fb = -a * sp.cot(_x)
        x0_tex, x0 = r"\dfrac{\pi}{4}", sp.pi / 4
        head = rf"\dfrac{{{a}}}{{\sin^2 x}}"
    y0 = int(Fb.subs(_x, x0)) + C
    ans = Fb + C
    return Question(
        key="antideriv_trig_table",
        statement=(
            rf"Знайдіть первісну $F$ функції $f(x) = {head}$,"
            + _TAIL + f"${_point(x0_tex, y0)}$."
        ),
        parts=[Part("F", _ASK_F, ans, kind="expr", points=1)],
        seconds=115,
        params={"a": a, "is_tan": is_tan, "y0": y0, "C": C},
    )


# =========================================================================
#  ОБЕРНЕНИЙ ЗВ'ЯЗОК  та  ВИЗНАЧЕННЯ СТАЛОЇ
# =========================================================================

@template("antideriv_find_f")
def _find_f(rng: random.Random) -> Question:
    """Розуміння означення F'=f: за первісною відновити функцію. Первісна містить
    √x, тож треба впізнати (√x)' = 1/(2√x) — обернене до табличної 1/√x."""
    a = rng.choice([1, 2, 3])
    b = rng.choice([2, 4, 6])
    F = a * _x**3 + b * sp.sqrt(_x)
    f = sp.diff(F, _x)                 # 3a x² + b/(2√x)
    Ftex = _sum_tex([(a, "x^3")]) + rf" + {b}\sqrt{{x}}"
    return Question(
        key="antideriv_find_f",
        statement=(
            rf"Функція $F(x) = {Ftex}$ є первісною для функції $f$ (при $x>0$)."
            + "\nЗнайдіть $f(x)$."
        ),
        parts=[Part("f", "$f(x) =$", f, kind="expr", points=1)],
        seconds=100,
        params={"a": a, "b": b},
    )


@template("antideriv_find_constant")
def _find_constant(rng: random.Random) -> Question:
    r"""Виокремлення суті сталої C: серед первісних тригонометричної функції
    знайти ту, що проходить через точку, і вказати саме C."""
    k = rng.choice([2, 3, 4])
    C = rng.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5])
    is_cos = rng.random() < 0.5
    if is_cos:
        # F = k·sin x + C,  M(π/2; y0):  k·1 + C = y0
        head = rf"{k}\cos x"
        x0_tex = r"\dfrac{\pi}{2}"
        y0 = k + C
    else:
        # F = −k·cos x + C,  M(π; y0):  k + C = y0
        head = rf"{k}\sin x"
        x0_tex = r"\pi"
        y0 = k + C
    return Question(
        key="antideriv_find_constant",
        statement=(
            rf"Первісна функції $f(x) = {head}$ проходить через точку "
            rf"${_point(x0_tex, y0)}$."
            + "\n"
            + r"Знайдіть сталу $C$ у її записі (усі первісні різняться на сталу $C$)."
        ),
        parts=[Part("C", "$C =$", C, points=1)],
        seconds=100,
        params={"k": k, "is_cos": is_cos, "y0": y0, "C": C},
    )


# =========================================================================
#  ФІЗИЧНИЙ ЗМІСТ ПЕРВІСНОЇ
# =========================================================================

@template("antideriv_kinematics")
def _kinematics(rng: random.Random) -> Question:
    """Первісна швидкості — закон руху. s'(t)=v(t), s(t₀)=s₀ визначає сталу."""
    p = rng.choice([2, 4, 6])         # p/2 — ціле
    q = rng.choice([1, 2, 3, 4, 5])
    s0 = rng.choice([0, 2, 5, 8, 10])
    v = p * _t + q
    s = sp.integrate(v, _t) + s0      # (p/2) t² + q t + s0
    vtex = _sum_tex([(p, "t"), (q, "")])
    return Question(
        key="antideriv_kinematics",
        statement=(
            r"Тіло рухається вздовж прямої зі швидкістю "
            rf"$v(t) = {vtex}$ (м/с)."
            + "\n"
            + rf"У момент $t = 0$ його координата $s(0) = {s0}$ (м). "
            + r"Знайдіть закон руху $s(t)$."
        ),
        parts=[Part("s", "$s(t) =$", s, kind="expr", points=1)],
        seconds=125,
        params={"p": p, "q": q, "s0": s0},
    )
