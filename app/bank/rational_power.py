"""Степінь з раціональним показником та його властивості (§6 Мерзляка, 10 клас).

Обсяг за підручником:
  * означення $a^{m/n} = \\sqrt[n]{a^m}$ для $a > 0$; $0^{m/n} = 0$ лише для
    додатного показника; для $a < 0$ степінь з дробовим показником НЕ означено,
    хоча корінь непарного степеня з від'ємного числа зміст має;
  * перехід корінь $\\leftrightarrow$ степінь і зведення до одного степеня;
  * властивості: $a^p a^q = a^{p+q}$, $a^p : a^q = a^{p-q}$, $(a^p)^q = a^{pq}$,
    $(ab)^p = a^p b^p$, $(a/b)^p = a^p / b^p$;
  * розкриття дужок і скорочення дробів із дробовими показниками (формули
    скороченого множення працюють так само);
  * степенева функція з раціональним показником та її область визначення.

Ірраціональних рівнянь (§7) тут нема – це наступна тема.

Змінні скрізь $x$ і $y$ (а не $a$, $b$, як у підручнику): парсер приймає лише
ці імена. Основа всюди додатна, і це сказано в кожній умові – інакше дробовий
показник не означений.

Чому це стійке до списування:
  * відповідь переважно ВИРАЗ, а не число: одним числом не поділишся;
  * показники й основи в кожного свої (кілька десятків варіантів на шаблон);
  * задачі багатокрокові, тож передати треба весь ланцюг.

Грейдинг символьний і з `positive=True`: приймаються і $x^{2/3}$, і
$(x^2)^{1/3}$, і $\\sqrt[3]{x^2}$, і нерозкритий добуток.
"""

from __future__ import annotations

import math
import random
from fractions import Fraction

import sympy as sp

from engine import Part, Question, template

_x, _y = sp.symbols("x y")

_HINT = ("(Основа всюди додатна. Степінь вводьте як x^(2/3), "
         "число – звичайним дробом: 2/3.)")

# Межа показника в парсері: далі відповідь просто не приймуть.
_EXP_LIMIT = 12


def _r(num: int, den: int = 1):
    return sp.Rational(num, den)


def _frac_tex(fr: Fraction) -> str:
    """Дріб у LaTeX. У показнику степеня потрібен саме \\frac, а не \\dfrac:
    великий дріб у верхньому індексі виглядає незграбно."""
    if fr.denominator == 1:
        return str(fr.numerator)
    sign = "-" if fr < 0 else ""
    return rf"{sign}\frac{{{abs(fr.numerator)}}}{{{fr.denominator}}}"


def _root_tex(n: int, inner: str) -> str:
    return rf"\sqrt{{{inner}}}" if n == 2 else rf"\sqrt[{n}]{{{inner}}}"


def _coef(v: int) -> str:
    """Коефіцієнт 1 не пишемо."""
    return "" if v == 1 else str(v)


def _num(value):
    """Число з попереднього кроку або None, якщо переносити нічого.

    Нуль теж не переносимо: він нерухома точка і суми, і добутку, тож
    студент, який написав 0 в усі поля, підтверджував би сам себе. Жоден
    еталонний проміжний результат тут нулем не буває.
    """
    if value is None or getattr(value, "free_symbols", set()) or value == 0:
        return None
    return value


def _safe_exp(value):
    """Показник із попереднього кроку, якщо він у межах парсера.

    Без цієї перевірки «сміття» на першому кроці перетворилося б на
    $64^{123456}$ – число на двісті тисяч цифр.
    """
    got = _num(value)
    if got is None or not got.is_rational:
        return None
    return got if abs(got) <= _EXP_LIMIT else None


def _carry_power(key):
    """Крок «запишіть у вигляді $x^r$» від власного показника студента."""
    def _fn(prev):
        r = _safe_exp(prev[key])
        return None if r is None else _x**r
    return _fn


def _carry_value(key, base, factor):
    """Крок «обчисліть при $x = base^{factor}$» від власного показника."""
    def _fn(prev):
        r = _safe_exp(prev[key])
        if r is None or abs(r * factor) > 40:
            return None
        return sp.Integer(base) ** (r * factor)
    return _fn


def _carry_subs(key, x0):
    """Крок «обчисліть при $x = x_0$» від власного виразу студента."""
    def _fn(prev):
        got = prev.get(key)
        if got is None or not getattr(got, "has", lambda _v: False)(_x):
            return None
        return sp.nsimplify(got.subs(_x, x0))
    return _fn


def _carry_sum(k1, k2):
    def _fn(prev):
        a, b = prev.get(k1), prev.get(k2)
        return None if a is None or b is None else a + b
    return _fn


# =========================================================================
#  ОЗНАЧЕННЯ: КОРІНЬ <-> СТЕПІНЬ
# =========================================================================

@template("rp_root_to_power")
def _root_to_power(rng: random.Random) -> Question:
    """Корінь у вигляді степеня з дробовим показником (вправи 6.3, 6.4)."""
    c = rng.choice([2, 3, 5, 7])
    n = rng.choice([3, 4, 5, 6])
    m = rng.choice([v for v in range(2, n + 3)
                    if math.gcd(v, n) == 1 and c**v < 10**7])
    r = _r(m, n)
    x0 = c**n
    return Question(
        key="rp_root_to_power",
        statement=(
            rf"Дано вираз ${_root_tex(n, f'x^{{{m}}}')}$, де $x > 0$."
            + "\n1) Запишіть його у вигляді $x^r$. Чому дорівнює показник $r$?"
            + "\n2) Запишіть сам вираз у вигляді степеня."
            + "\n" + rf"3) Обчисліть значення виразу при $x = {x0}$."
            + "\n" + _HINT
        ),
        parts=[
            Part("r", "1) показник $r$ =", r, points=1),
            Part("expr", "2) вираз =", _x**r, kind="expr", points=1,
                 positive=True, carry=_carry_power("r"), carry_from=("r",)),
            Part("val", rf"3) значення при $x = {x0}$:", sp.Integer(c) ** m,
                 points=1, carry=_carry_value("r", c, n), carry_from=("r",)),
        ],
        seconds=120,
        params={"c": c, "n": n, "m": m},
    )


@template("rp_single_power")
def _single_power(rng: random.Random) -> Question:
    """Добуток і частка коренів – до одного степеня (вправа 5.33 + §6).

    Трійки, де показник виходить нульовим, відкидаємо: $x^0 = 1$ вгадується
    без жодних перетворень.
    """
    # Дві форми – з діленням і без: інакше набір показників надто вузький
    # і в кожного сьомого студента відповіді збігаються.
    def _exp(a, b, d, divide):
        return _r(1, a) + _r(1, b) + (-_r(1, d) if divide else _r(1, d))

    good = [(a, b, d, divide)
            for a in (2, 3, 4, 6) for b in (2, 3, 4, 6) for d in (2, 3, 4, 6)
            for divide in (True, False)
            if not _exp(a, b, d, divide).is_integer
            and abs(_exp(a, b, d, divide) * math.lcm(a, b, d)) <= 10]
    a, b, d, divide = rng.choice(good)
    r = _exp(a, b, d, divide)
    lcm = math.lcm(a, b, d)
    # 3^12 = 531441 розпізнати важко, тож трійку беремо лише за малого НСК.
    base = rng.choice([2, 3]) if lcm <= 6 else 2
    x0 = base**lcm
    value = sp.Integer(base) ** (r * lcm)
    return Question(
        key="rp_single_power",
        statement=(
            "Спростіть вираз "
            + (r"$\dfrac{" + _root_tex(a, "x") + r"\cdot " + _root_tex(b, "x")
               + "}{" + _root_tex(d, "x") + "}$" if divide
               else "$" + _root_tex(a, "x") + r"\cdot " + _root_tex(b, "x")
               + r"\cdot " + _root_tex(d, "x") + "$")
            + r", де $x > 0$."
            + "\n1) Чому дорівнює показник $r$, якщо подати вираз як $x^r$?"
            + "\n2) Запишіть сам вираз у вигляді степеня."
            + "\n" + rf"3) Обчисліть його значення при $x = {x0}$."
            + "\n" + _HINT
        ),
        parts=[
            Part("r", "1) показник $r$ =", r, points=1),
            Part("expr", "2) вираз =", _x**r, kind="expr", points=1,
                 positive=True, carry=_carry_power("r"), carry_from=("r",)),
            Part("val", rf"3) значення при $x = {x0}$:", value, points=1,
                 carry=_carry_value("r", base, lcm), carry_from=("r",)),
        ],
        seconds=130,
        params={"a": a, "b": b, "d": d, "base": base, "divide": divide},
    )


# =========================================================================
#  ОБЧИСЛЕННЯ ЗНАЧЕНЬ
# =========================================================================

@template("rp_numeric_value")
def _numeric_value(rng: random.Random) -> Question:
    """Значення числових степенів з дробовим показником (вправи 6.5, 6.6)."""
    u, q = rng.choice([2, 3, 5]), rng.choice([2, 3, 4])
    p = rng.choice([v for v in (1, 2, 3, 5) if u**v < 10**6 and v % q != 0])
    w, s = rng.choice([2, 3, 5]), rng.choice([2, 3])
    k = rng.choice([v for v in (1, 2, 3) if v % s != 0])
    first = sp.Integer(u) ** p
    second = sp.Rational(1, w**k)
    return Question(
        key="rp_numeric_value",
        statement=(
            "Обчисліть значення виразів."
            + "\n" + rf"1) ${u**q}^{{{_frac_tex(Fraction(p, q))}}}$"
            + "\n" + rf"2) ${w**s}^{{{_frac_tex(Fraction(-k, s))}}}$"
            + "\n3) Чому дорівнює добуток цих двох значень?"
            + "\n" + _HINT
        ),
        parts=[
            Part("first", "1) =", first, points=1),
            Part("second", "2) =", second, points=1),
            Part("prod", "3) добуток =", first * second, points=1,
                 carry=lambda prev: (
                     None if _num(prev.get("first")) is None
                     or _num(prev.get("second")) is None
                     else prev["first"] * prev["second"]),
                 carry_from=("first", "second")),
        ],
        seconds=120,
        params={"u": u, "q": q, "p": p, "w": w, "s": s, "k": k},
    )


@template("rp_properties")
def _properties(rng: random.Random) -> Question:
    """Властивості степеня: добуток, частка, степінь степеня (вправи 6.7, 6.8).

    Усі показники в умові – справді дробові: якби вони скоротилися до цілих,
    задача перестала б стосуватися теми.
    """
    b = rng.choice([2, 3, 5, 7, 10])
    # Знаменник 2 неможливий: половина + половина - половина завжди половина,
    # тобто цілого показника з трьох дробових не скласти.
    den = rng.choice([3, 4, 5])
    k1 = rng.choice([1, 2, 3, 4])
    # Лишки мають бути такими, щоб і третій показник не скоротився до цілого.
    pairs = [(ra, rb) for ra in range(1, den) for rb in range(1, den)
             if (ra + rb) % den]
    ra, rb = rng.choice(pairs)
    pn = ra + den * rng.randrange(2, 5)
    qn = rb + den * rng.randrange(1, 4)
    rn = pn + qn - k1 * den          # завжди додатний: pn + qn > 3*den >= k1*den
    p, q, rr = Fraction(pn, den), Fraction(qn, den), Fraction(rn, den)
    # k2 != k1, інакше обидва значення збігаються і одне вгадане число
    # приносить одразу два бали з трьох.
    u, v, k2 = rng.choice([e for e in [
        (Fraction(3, 2), Fraction(4, 3), 2), (Fraction(2, 3), Fraction(3, 2), 1),
        (Fraction(5, 2), Fraction(4, 5), 2), (Fraction(3, 4), Fraction(8, 3), 2),
        (Fraction(4, 3), Fraction(3, 2), 2), (Fraction(5, 3), Fraction(6, 5), 2),
        (Fraction(2, 5), Fraction(5, 2), 1), (Fraction(5, 4), Fraction(8, 5), 2),
        (Fraction(7, 3), Fraction(3, 7), 1), (Fraction(3, 5), Fraction(5, 3), 1),
        (Fraction(5, 2), Fraction(6, 5), 3), (Fraction(9, 2), Fraction(2, 3), 3),
        (Fraction(4, 3), Fraction(9, 4), 3), (Fraction(5, 3), Fraction(9, 5), 3),
        (Fraction(7, 2), Fraction(6, 7), 3),
    ] if e[2] != k1])
    return Question(
        key="rp_properties",
        statement=(
            "Скористайтеся властивостями степеня й обчисліть значення виразів."
            + "\n" + rf"1) ${b}^{{{_frac_tex(p)}}}\cdot {b}^{{{_frac_tex(q)}}} : "
            rf"{b}^{{{_frac_tex(rr)}}}$"
            + "\n" + rf"2) $\left({b}^{{{_frac_tex(u)}}}\right)^{{{_frac_tex(v)}}}$"
            + "\n3) Чому дорівнює добуток цих двох значень?"
            + "\n" + _HINT
        ),
        parts=[
            # Усі три пункти просять ЗНАЧЕННЯ. Коли перший пункт питав показник,
            # а другий – значення, у третьому легко було перемножити показник на
            # значення (3 * 25 замість 125 * 25) – і це була вина умови.
            Part("val1", "1) =", sp.Integer(b) ** k1, points=1),
            Part("val2", "2) =", sp.Integer(b) ** k2, points=1),
            Part("val", "3) добуток =", sp.Integer(b) ** (k1 + k2), points=1,
                 carry=lambda prev: (
                     None if _num(prev.get("val1")) is None
                     or _num(prev.get("val2")) is None
                     else prev["val1"] * prev["val2"]),
                 carry_from=("val1", "val2")),
        ],
        seconds=130,
        # показники зберігаємо рядками, щоб тест міг перевірити їх незалежно
        params={"b": b, "k1": k1, "k2": k2, "den": den,
                "p": str(p), "q": str(q), "r": str(rr),
                "u": str(u), "v": str(v)},
    )


@template("rp_same_base")
def _same_base(rng: random.Random) -> Question:
    """Різні основи – до спільної (вправи 6.11, 6.12)."""
    # Перебираємо явно: цикл добору тут легко зробити нескінченним, а build
    # виконується просто в запиті, без таймауту воркера.
    first = [(p, q, rr) for p in range(1, 7) for q in range(1, 6)
             for rr in range(1, 6)
             if 1 <= p + q - rr <= 8 and p % 4 and q % 3 and rr % 2]
    p, q, rr = rng.choice(first)
    k = p + q - rr
    second = [(s, t) for s in range(2, 8) for t in range(1, 6)
              if 0 <= s - t <= 4 and s % 3 and t % 2]
    s, t = rng.choice(second)
    k2 = s - t
    return Question(
        key="rp_same_base",
        statement=(
            "Зведіть кожен вираз до степеня зі спільною основою."
            + "\n" + rf"1) Чому дорівнює показник $k$, якщо подати "
            rf"$16^{{{_frac_tex(Fraction(p, 4))}}}\cdot "
            rf"8^{{{_frac_tex(Fraction(q, 3))}}} : "
            rf"4^{{{_frac_tex(Fraction(rr, 2))}}}$ у вигляді $2^{{k}}$?"
            + "\n2) Обчисліть значення цього виразу."
            + "\n" + rf"3) Обчисліть значення виразу "
            rf"$27^{{{_frac_tex(Fraction(s, 3))}}} : "
            rf"9^{{{_frac_tex(Fraction(t, 2))}}}$."
            + "\n" + _HINT
        ),
        parts=[
            Part("k", "1) показник двійки =", sp.Integer(k), points=1),
            Part("val", "2) значення першого =", sp.Integer(2) ** k, points=1,
                 carry=lambda prev: (
                     None if _safe_exp(prev.get("k")) is None
                     else sp.Integer(2) ** prev["k"]),
                 carry_from=("k",)),
            Part("val3", "3) значення другого =", sp.Integer(3) ** k2, points=1),
        ],
        seconds=130,
        params={"p": p, "q": q, "r": rr, "s": s, "t": t},
    )


# =========================================================================
#  ПЕРЕТВОРЕННЯ ВИРАЗІВ
# =========================================================================

@template("rp_expand_squares")
def _expand_squares(rng: random.Random) -> Question:
    """Формули скороченого множення з дробовими показниками (вправи 6.9, 6.10).

    Показники двох пунктів навмисне різні – інакше другий пункт дублював би
    перший.
    """
    k = rng.choice([2, 3])
    n = rng.choice([v for v in (2, 3, 4) if v != k])
    c = rng.choice([2, 3, 4, 5])
    a1, b1 = rng.choice([1, 2, 3]), rng.choice([1, 2, 3])
    ktex, ntex = _frac_tex(Fraction(1, k)), _frac_tex(Fraction(1, n))
    diff = sp.expand((_x**_r(1, k) + c * _y**_r(1, k))
                     * (_x**_r(1, k) - c * _y**_r(1, k)))
    sq = sp.expand((a1 * _x**_r(1, n) + b1 * _y**_r(1, n)) ** 2)
    return Question(
        key="rp_expand_squares",
        statement=(
            r"Розкрийте дужки ($x > 0$, $y > 0$)."
            + "\n" + rf"1) $\left(x^{{{ktex}}} + {_coef(c)}y^{{{ktex}}}\right)"
            rf"\left(x^{{{ktex}}} - {_coef(c)}y^{{{ktex}}}\right)$"
            + "\n" + rf"2) $\left({_coef(a1)}x^{{{ntex}}} + "
            rf"{_coef(b1)}y^{{{ntex}}}\right)^2$"
            + "\n" + _HINT
        ),
        parts=[
            Part("diff", "1) =", diff, kind="expr", points=1, positive=True),
            Part("sq", "2) =", sq, kind="expr", points=1, positive=True),
        ],
        seconds=120,
        params={"k": k, "n": n, "c": c, "a1": a1, "b1": b1},
    )


@template("rp_cube_identity")
def _cube_identity(rng: random.Random) -> Question:
    """Різниця і сума кубів через неповний квадрат (вправи 6.9.5, 6.10.6)."""
    c = rng.choice([2, 3, 4, 5])
    e = rng.choice([v for v in (2, 3, 4, 5) if v != c])
    w = rng.choice([2, 3, 4, 5, 6])
    x0 = w**3
    return Question(
        key="rp_cube_identity",
        statement=(
            r"Розкрийте дужки ($x > 0$)."
            + "\n" + rf"1) $\left(x^{{\frac{{1}}{{3}}}} - {c}\right)"
            rf"\left(x^{{\frac{{2}}{{3}}}} + {c}x^{{\frac{{1}}{{3}}}} + "
            rf"{c**2}\right)$"
            + "\n" + rf"2) $\left(x^{{\frac{{1}}{{3}}}} + {e}\right)"
            rf"\left(x^{{\frac{{2}}{{3}}}} - {e}x^{{\frac{{1}}{{3}}}} + "
            rf"{e**2}\right)$"
            + "\n" + rf"3) Обчисліть значення ПЕРШОГО виразу при $x = {x0}$."
            + "\n" + _HINT
        ),
        parts=[
            Part("minus", "1) =", _x - c**3, kind="expr", points=1, positive=True),
            Part("plus", "2) =", _x + e**3, kind="expr", points=1, positive=True),
            Part("val", rf"3) при $x = {x0}$:", sp.Integer(x0 - c**3), points=1,
                 carry=_carry_subs("minus", x0), carry_from=("minus",)),
        ],
        seconds=130,
        params={"c": c, "e": e, "w": w},
    )


@template("rp_reduce_fraction")
def _reduce_fraction(rng: random.Random) -> Question:
    """Скорочення дробів із дробовими показниками (вправи 6.13, 6.14)."""
    c = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    d = rng.choice([2, 3, 4, 5])
    w = rng.choice([2, 3, 4, 5, 6])
    x0 = w**3
    second = _x**_r(2, 3) + d * _x**_r(1, 3) + d**2
    return Question(
        key="rp_reduce_fraction",
        statement=(
            r"Скоротіть дроби ($x > 0$)."
            + "\n" + rf"1) $\dfrac{{x - {c**2}}}{{x^{{\frac{{1}}{{2}}}} + {c}}}$"
            + "\n" + rf"2) $\dfrac{{x - {d**3}}}{{x^{{\frac{{1}}{{3}}}} - {d}}}$"
            + "\n" + rf"3) Обчисліть значення ДРУГОГО дробу при $x = {x0}$."
            + "\n" + _HINT
        ),
        parts=[
            Part("first", "1) =", sp.sqrt(_x) - c, kind="expr", points=1,
                 positive=True),
            Part("second", "2) =", second, kind="expr", points=1, positive=True),
            Part("val", rf"3) при $x = {x0}$:",
                 sp.Integer(w**2 + d * w + d**2), points=1,
                 carry=_carry_subs("second", x0), carry_from=("second",)),
        ],
        seconds=130,
        params={"c": c, "d": d, "w": w},
    )


@template("rp_simplify_expr")
def _simplify_expr(rng: random.Random) -> Question:
    """Спрощення виразу з дробовими показниками (задача 1 з теорії §6).

    Другий множник другого добутку навмисне НЕ збігається з другим множником
    першого: інакше вираз згортався б у добуток і задача ставала б іншою.
    """
    a1 = rng.choice([2, 3, 4])
    b1 = rng.choice([1, 2, 3])
    c1 = rng.choice([2, 3, 4])
    d1 = rng.choice([v for v in (2, 3) if v != c1] or [3])
    n = rng.choice([3, 4])
    m = rng.choice([v for v in (3, 5) if v != n])
    px, py = _r(1, n), _r(1, m)
    expr = sp.expand(
        (a1 * _x**px + b1 * _y**py) * (_x**px - c1 * _y**py)
        - (_x**px + d1 * _y**py) * (_x**px - d1 * _y**py)
    )
    xt, yt = _frac_tex(Fraction(1, n)), _frac_tex(Fraction(1, m))
    return Question(
        key="rp_simplify_expr",
        statement=(
            "Спростіть вираз ($x > 0$, $y > 0$):"
            + "\n" + rf"$\left({_coef(a1)}x^{{{xt}}} + {_coef(b1)}y^{{{yt}}}\right)"
            rf"\left(x^{{{xt}}} - {c1}y^{{{yt}}}\right) - "
            rf"\left(x^{{{xt}}} + {d1}y^{{{yt}}}\right)"
            rf"\left(x^{{{xt}}} - {d1}y^{{{yt}}}\right)$"
            + "\n1) Розкрийте дужки й зведіть подібні доданки."
            + "\n" + rf"2) Чому дорівнює коефіцієнт біля "
            rf"$x^{{{_frac_tex(Fraction(2, n))}}}$?"
            + "\n" + _HINT
        ),
        parts=[
            Part("expr", "1) =", expr, kind="expr", points=1, positive=True),
            Part("coef", rf"2) коефіцієнт біля $x^{{{_frac_tex(Fraction(2, n))}}}$:",
                 sp.Integer(a1 - 1), points=1),
        ],
        seconds=140,
        params={"a1": a1, "b1": b1, "c1": c1, "d1": d1, "n": n, "m": m},
    )


@template("rp_substitution")
def _substitution(rng: random.Random) -> Question:
    """Сума двох дробів, кожен скорочується (задача 2 з теорії §6)."""
    n = rng.choice([2, 3])
    c = rng.choice([2, 3, 4, 5, 6, 7])
    d = rng.choice([v for v in (2, 3, 4, 5, 6, 7) if v != c])
    power_tex = _frac_tex(Fraction(1, n))
    top_tex = "x" if n == 2 else rf"x^{{{_frac_tex(Fraction(2, 3))}}}"
    first, second = _x**_r(1, n) - c, _x**_r(1, n) + d
    return Question(
        key="rp_substitution",
        statement=(
            r"Спростіть вираз ($x > 0$). Підказка: зручно позначити "
            rf"$t = x^{{{power_tex}}}$."
            + "\n" + rf"1) $\dfrac{{{top_tex} - {c**2}}}"
            rf"{{x^{{{power_tex}}} + {c}}}$"
            + "\n" + rf"2) $\dfrac{{{top_tex} - {d**2}}}"
            rf"{{x^{{{power_tex}}} - {d}}}$"
            + "\n3) Чому дорівнює СУМА цих двох дробів?"
            + "\n" + _HINT
        ),
        parts=[
            Part("first", "1) =", first, kind="expr", points=1, positive=True),
            Part("second", "2) =", second, kind="expr", points=1, positive=True),
            Part("total", "3) сума =", sp.expand(first + second), kind="expr",
                 points=1, positive=True,
                 carry=_carry_sum("first", "second"),
                 carry_from=("first", "second")),
        ],
        seconds=140,
        params={"n": n, "c": c, "d": d},
    )


# =========================================================================
#  СТЕПЕНЕВА ФУНКЦІЯ ТА ОЗНАЧЕННЯ
# =========================================================================

@template("rp_domain")
def _domain(rng: random.Random) -> Question:
    """Область визначення функції $y = x^{m/n}$ (теорія §6, с. 35).

    Ключове: нуль належить області визначення лише для ДОДАТНОГО показника.
    """
    n = rng.choice([2, 3, 4, 5])
    m = rng.choice([v for v in range(1, 8) if math.gcd(v, n) == 1])
    negative = rng.random() < 0.5
    r = _r(-m, n) if negative else _r(m, n)
    c1 = rng.choice([2, 3, 5])
    c2 = rng.choice([v for v in (2, 3, 5, 7) if v != c1 and v**n < 10**6])
    v1, v2 = c1**n, c2**n
    # Склад набору теж випадковий: якби він був сталий, перший пункт мав би
    # лише два можливі значення й вгадувався б підкиданням монети.
    pool = [v1, v2]
    pool += rng.sample([-v1, -v2, -1], rng.choice([1, 2]))
    if rng.random() < 0.75:
        pool.append(0)
    if rng.random() < 0.6:
        pool.append(1)
    rng.shuffle(pool)
    cnt = sum(1 for v in pool if v > 0 or (v == 0 and not negative))
    val1 = sp.Rational(1, c1**m) if negative else sp.Integer(c1) ** m
    val2 = sp.Rational(1, c2**m) if negative else sp.Integer(c2) ** m
    nums = ", ".join(str(v) for v in pool)
    return Question(
        key="rp_domain",
        statement=(
            rf"Дано функцію $y = x^{{{_frac_tex(Fraction(int(r.p), int(r.q)))}}}$."
            + "\n" + rf"1) Скільки з чисел ${nums}$ належать її області визначення?"
            + "\n" + rf"2) Обчисліть $y({v1})$."
            + "\n" + rf"3) Обчисліть $y({v2})$."
            + "\n" + _HINT
        ),
        parts=[
            Part("cnt", "1) чисел в області визначення:", sp.Integer(cnt), points=1),
            Part("v1", rf"2) $y({v1})$ =", val1, points=1),
            Part("v2", rf"3) $y({v2})$ =", val2, points=1),
        ],
        seconds=110,
        params={"n": n, "m": m, "negative": negative, "pool": pool,
                "v1": v1, "v2": v2},
    )


@template("rp_meaningful")
def _meaningful(rng: random.Random) -> Question:
    """Коли запис має зміст: $0^r$, від'ємна основа, корінь (теорія §6, с. 34)."""
    c = rng.choice([2, 3, 5, 7])
    n = rng.choice([3, 5])            # непарний: корінь з від'ємного існує
    s = rng.choice([2, 3])
    # Показники мають лишатися ДРОБОВИМИ: 0^1 нічого не перевіряє.
    k = rng.choice([v for v in (2, 3, 4, 5, 7) if v % s != 0])
    m = rng.choice([v for v in (1, 2, 3, 4, 5) if v % s != 0])
    e = rng.choice([v for v in (2, 3, 4, 5) if v != c])
    # Кількість змістовних записів теж має бути різною, інакше «3» вгадується
    # без жодного розбору.
    meaningful = [
        rf"$0^{{{_frac_tex(Fraction(k, s))}}}$",
        rf"${_root_tex(n, f'-{c**n}')}$",
        rf"${c}^{{{_frac_tex(Fraction(-m, s))}}}$",
        rf"${e}^{{{_frac_tex(Fraction(k, s))}}}$",
        rf"${_root_tex(n, f'-{e}')}$",
    ]
    meaningless = [
        rf"$0^{{{_frac_tex(Fraction(-k, s))}}}$",
        rf"$\left(-{c}\right)^{{{_frac_tex(Fraction(1, n))}}}$",
        rf"$\left(-{e}\right)^{{{_frac_tex(Fraction(m, s))}}}$",
        rf"$0^{{{_frac_tex(Fraction(-m, s))}}}$",
        rf"$\left(-{c}\right)^{{{_frac_tex(Fraction(-k, s))}}}$",
    ]
    cnt = rng.choice([2, 3, 4])
    records = ([(t, True) for t in rng.sample(meaningful, cnt)]
               + [(t, False) for t in rng.sample(meaningless, 5 - cnt)])
    rng.shuffle(records)
    listing = "; ".join(t for t, _ in records)
    return Question(
        key="rp_meaningful",
        statement=(
            r"Степінь з дробовим показником означено лише для ДОДАТНОЇ основи, "
            r"а також для нуля – але тільки з додатним показником. "
            r"Корінь непарного степеня з від'ємного числа при цьому зміст має."
            + "\n" + rf"Дано записи: {listing}."
            + "\n1) Скільки з них мають зміст?"
            + "\n" + rf"2) Обчисліть ${_root_tex(n, f'-{c**n}')}$."
            + "\n" + rf"3) Обчисліть ${c**s}^{{{_frac_tex(Fraction(-m, s))}}}$."
            + "\n" + _HINT
        ),
        parts=[
            Part("cnt", "1) записів зі змістом:", sp.Integer(cnt), points=1),
            Part("root", "2) корінь =", sp.Integer(-c), points=1),
            Part("pow", "3) степінь =", sp.Rational(1, c**m), points=1),
        ],
        seconds=120,
        params={"c": c, "n": n, "k": k, "s": s, "m": m},
    )
