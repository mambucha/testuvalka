"""Тематичне оцінювання: функції, корені, степінь з раціональним показником.

Складено за зразком контрольної роботи викладача (десять завдань: область
визначення дробу й кореня, читання графіка, обчислення степенів з дробовим
показником, винесення й внесення множника, корінь з кореня, звільнення від
ірраціональності, складена область визначення, дії з дробовими показниками,
ірраціональне рівняння із заміною).

Тут лежать ЛИШЕ ті типи, яких ще не було в банках. Решту завдань тест бере
з готових шаблонів theme2–theme4: перелік у tests.yaml.

Кожне завдання розбите на кроки так, щоб було видно ХІД розв'язання, а не
лише відповідь: окремо проміжний результат, окремо висновок. Через це
переписана чужа відповідь майже завжди не підходить – проміжні числа в
кожного свої, а в задачі з графіком у кожного ще й свій рисунок.
"""

from __future__ import annotations

import math
import random
from fractions import Fraction

import sympy as sp

from app.bank.plotting import coordinate_plane
from engine import Part, Question, template

_x, _y = sp.symbols("x y")

_HINT = ("(Відповідь – число або вираз. Дріб вводьте як 3/2, "
         "степінь як x^(2/3).)")


def _lin(a: int, b: int) -> str:
    head = ("" if a == 1 else "-" if a == -1 else str(a)) + "x"
    if b == 0:
        return head
    return head + (f" + {b}" if b > 0 else f" - {abs(b)}")


def _frac_tex(fr: Fraction) -> str:
    if fr.denominator == 1:
        return str(fr.numerator)
    sign = "-" if fr < 0 else ""
    return rf"{sign}\frac{{{abs(fr.numerator)}}}{{{fr.denominator}}}"


def _pow_tex(var: str, e: int) -> str:
    return var if e == 1 else rf"{var}^{{{e}}}"


def _minus_term(c: int) -> str:
    """Доданок $-cx$ зі справжнім знаком: при від'ємному $c$ виходило «- -2x»."""
    mag = "" if abs(c) == 1 else str(abs(c))
    return (" - " if c > 0 else " + ") + mag + "x"


def _num(value):
    """Число з попереднього кроку; нуль не переносимо (нерухома точка)."""
    if value is None or getattr(value, "free_symbols", set()) or value == 0:
        return None
    return value


# =========================================================================
#  ОБЛАСТЬ ВИЗНАЧЕННЯ
# =========================================================================

@template("tf_domain_pair")
def _domain_pair(rng: random.Random) -> Question:
    """Завдання 1: область визначення дробу і кореня парного степеня.

    Кроки розділено навмисне: окремо точка, де знаменник обертається на нуль,
    окремо межа для кореня, і окремо найменше ЦІЛЕ з області – бо саме на
    округленні дробу вгору найчастіше помиляються.
    """
    a = rng.choice([2, 3, 4, 5])
    b = rng.choice([v for v in range(1, 12) if math.gcd(v, a) == 1])
    c = rng.choice([2, 3, 4, 5])
    # d/c НЕ ціле: інакше «найменше ціле» збігається з межею, крок порожній,
    # а округлення цілого числа дає саме себе – і сміття проходило б.
    d = rng.choice([v for v in range(5, 25) if v % c])
    hole = sp.Rational(b, a)
    edge = sp.Rational(d, c)
    first_int = int(sp.ceiling(edge))
    return Question(
        key="tf_domain_pair",
        statement=(
            "Знайдіть область визначення функцій."
            + "\n" + rf"а) $y = \dfrac{{1}}{{{_lin(a, -b)}}}$"
            + "\n" + rf"б) $y = \sqrt{{{_lin(c, -d)}}}$"
            + "\n1) При якому значенні $x$ функція а) НЕ існує?"
            + "\n2) Яке НАЙМЕНШЕ значення $x$ допустиме для функції б)?"
            + "\n3) Яке найменше ЦІЛЕ число належить області визначення б)?"
            + "\n" + _HINT
        ),
        parts=[
            Part("hole", "1) $x$ =", hole, points=1),
            Part("edge", "2) найменше $x$:", edge, points=1),
            Part("first", "3) найменше ціле:", sp.Integer(first_int), points=1,
                 carry=lambda prev: (
                     None if _num(prev.get("edge")) is None
                     or sp.ceiling(prev["edge"]) == prev["edge"]  # уже ціле
                     else sp.ceiling(prev["edge"])),
                 carry_from=("edge",)),
        ],
        seconds=130,
        params={"a": a, "b": b, "c": c, "d": d},
    )


@template("tf_domain_combined")
def _domain_combined(rng: random.Random) -> Question:
    """Завдання 8: область визначення суми дробів.

    Головна пастка – СТРОГА нерівність: корінь стоїть у знаменнику, тож
    підкореневий вираз має бути додатним, а не просто невід'ємним.
    """
    a = rng.choice([1, 2, 3])
    b = rng.choice(range(2, 16))
    c = rng.choice([v for v in range(-4, 6) if v != 0])
    edge = sp.Rational(b, a)                       # x < b/a
    last_int = int(sp.ceiling(edge)) - 1
    excluded = sorted({0, c})
    in_range = [v for v in excluded if v < edge]
    good = [v for v in range(-5, 6) if v < edge and v not in excluded]
    return Question(
        key="tf_domain_combined",
        statement=(
            r"Знайдіть область визначення функції"
            + "\n" + rf"$f(x) = \dfrac{{1}}{{\sqrt{{{_lin(-a, b)}}}}} + "
            rf"\dfrac{{1}}{{{_pow_tex('x', 2)}{_minus_term(c)}}}$"
            + "\n1) Яке НАЙБІЛЬШЕ ЦІЛЕ значення $x$ задовольняє умову для "
            "кореня? (увага: корінь у знаменнику)"
            + "\n2) Яке БІЛЬШЕ з двох значень $x$ виключає другий доданок?"
            + "\n3) Скільки цілих чисел від $-5$ до $5$ належать області "
            "визначення всієї функції?"
            + "\n" + _HINT
        ),
        parts=[
            Part("last", "1) найбільше ціле:", sp.Integer(last_int), points=1),
            Part("hole", "2) більше з виколотих:", sp.Integer(max(excluded)),
                 points=1),
            Part("cnt", "3) цілих у області:", sp.Integer(len(good)), points=1),
        ],
        seconds=140,
        params={"a": a, "b": b, "c": c, "excluded": excluded,
                "in_range": in_range},
    )


# =========================================================================
#  ЧИТАННЯ ГРАФІКА
# =========================================================================

@template("tf_graph_properties")
def _graph_properties(rng: random.Random) -> Question:
    """Завдання 2: за графіком встановити $D(f)$, $E(f)$ і проміжки зростання.

    Графік ламаний через вузли з цілими координатами – тоді всі три відповіді
    зчитуються точно, без «на око». Напрямок на сусідніх ланках завжди
    різний, тож кількість проміжків зростання однозначна.

    У кожного студента свій рисунок, тому списати тут нічого.
    """
    seg = rng.choice([3, 4])
    step = rng.choice([2, 3]) if seg == 3 else 2
    x0 = rng.choice([v for v in range(-5, 0) if v + seg * step <= 5])
    xs = [x0 + i * step for i in range(seg + 1)]
    up_first = rng.random() < 0.5
    ys = None
    for _ in range(40):                      # обмежений добір, без зациклення
        deltas = [rng.choice([2, 3, 4]) * (1 if (i % 2 == 0) == up_first else -1)
                  for i in range(seg)]
        run = [0]
        for d in deltas:
            run.append(run[-1] + d)
        if max(run) - min(run) <= 8:
            shift = rng.choice(range(-4 - min(run), 5 - max(run)))
            ys = [v + shift for v in run]
            break
    if ys is None:                           # запасний варіант
        ys = [0, 3, -1, 2][:seg + 1]
    segments = [((ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]),
                 ys[i] - (ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) * xs[i],
                 xs[i], xs[i + 1]) for i in range(seg)]
    rising = sum(1 for i in range(seg) if ys[i + 1] > ys[i])
    return Question(
        key="tf_graph_properties",
        statement=(
            "На рисунку зображено графік функції $y = f(x)$."
            + "\n1) Яке НАЙМЕНШЕ значення входить до області визначення $D(f)$?"
            + "\n2) Яке НАЙБІЛЬШЕ значення набуває функція?"
            + "\n3) На скількох проміжках функція ЗРОСТАЄ?"
            + "\n" + _HINT
        ),
        parts=[
            Part("dmin", "1) найменше з $D(f)$:", sp.Integer(xs[0]), points=1),
            Part("emax", "2) найбільше значення:", sp.Integer(max(ys)), points=1),
            Part("rising", "3) проміжків зростання:", sp.Integer(rising),
                 points=1),
        ],
        seconds=130,
        params={"xs": xs, "ys": ys, "rising": rising},
        svg=coordinate_plane(
            segments=segments,
            points=[(xs[0], ys[0]), (xs[-1], ys[-1])],
        ),
    )


# =========================================================================
#  ПЕРЕТВОРЕННЯ КОРЕНІВ
# =========================================================================

@template("tf_bring_under_letters")
def _bring_under_letters(rng: random.Random) -> Question:
    """Завдання 5: внести множник під знак кореня.

    Перший крок окремо просить $(kx^m)^n$ – саме там гублять степінь, бо
    підносити треба і коефіцієнт, і змінну.
    """
    n = rng.choice([3, 4])
    k = rng.choice([2, 3])
    m = rng.choice([2, 3])                   # m*n <= 12: більший показник
    e = rng.choice([1, 2])                   # парсер уже не прийме
    p = m * n - e                            # щоб під коренем лишилося x^e * y
    s = rng.choice([1, 2])
    x0 = rng.choice([2, 3])
    y0 = x0 ** (n - e) * s**n
    value = x0 * s
    outer = (("" if k == 1 else str(k)) + _pow_tex("x", m))
    return Question(
        key="tf_bring_under_letters",
        statement=(
            r"Внесіть множник під знак кореня ($x > 0$, $y > 0$):"
            + "\n" + rf"$${outer}\sqrt[{n}]{{\dfrac{{y}}"
            rf"{{{k**n}{_pow_tex('x', p)}}}}}$$"
            + "\n" + rf"1) Чому дорівнює $\left({outer}\right)^{{{n}}}$?"
            + "\n2) Який вираз лишиться ПІД коренем після внесення?"
            + "\n" + rf"3) Обчисліть значення всього виразу при $x = {x0}$, "
            rf"$y = {y0}$."
            + "\n" + _HINT
        ),
        parts=[
            Part("power", "1) =", sp.Integer(k**n) * _x ** (m * n), kind="expr",
                 points=1, positive=True),
            Part("inner", "2) під коренем:", _x**e * _y, kind="expr", points=1,
                 positive=True),
            Part("val", "3) значення:", sp.Integer(value), points=1),
        ],
        seconds=200,
        params={"n": n, "k": k, "m": m, "e": e, "p": p, "x0": x0, "y0": y0},
    )


# Набори (n, m, a, b) для «кореня з кореня». Добираємо так, щоб після
# скорочення лишався СПРАВЖНІЙ корінь (степінь 2..6, не сам x), а числова
# перевірка велася на невеликих числах.
_ROOT_OF_ROOT = []
for _n in (4, 6, 8, 9, 10):
    for _m in (3, 5, 7):
        for _a in (2, 3, 4, 5, 6):
            for _b in range(1, _m):
                if math.gcd(_b, _m) != 1:
                    continue
                _under = _a * _m + _b          # показник під внутрішнім коренем
                _deg = _n * _m                 # степінь спільного кореня
                _g = math.gcd(_deg, _under)
                _d, _e = _deg // _g, _under // _g
                if 2 <= _d <= 8 and 1 <= _e <= 9 and _d != _e:
                    _ROOT_OF_ROOT.append((_n, _m, _a, _b, _under, _deg, _d, _e))


@template("tf_root_of_root")
def _root_of_root(rng: random.Random) -> Question:
    """Завдання 6: корінь з кореня.

    Хід саме той, яким це показують у школі (§5), БЕЗ переходу до раціонального
    показника: внести множник під внутрішній корінь, потім застосувати правило
    кореня з кореня, потім скоротити показники. Через раціональний показник
    задача теж розв'язується, але викладач пояснював її інакше.
    """
    n, m, a, b, under, deg, d, e = rng.choice(_ROOT_OF_ROOT)
    c = 2
    x0 = c**d
    value = c**e
    return Question(
        key="tf_root_of_root",
        statement=(
            r"Спростіть вираз (змінна набуває додатних значень):"
            + "\n" + rf"$$\sqrt[{n}]{{{_pow_tex('x', a)}"
            rf"\sqrt[{m}]{{{_pow_tex('x', b)}}}}}$$"
            + "\n" + rf"1) Внесіть множник ${_pow_tex('x', a)}$ під ВНУТРІШНІЙ "
            rf"корінь. Який показник матиме $x$ під ним?"
            + "\n" + rf"2) За правилом кореня з кореня "
            r"$\sqrt[n]{\sqrt[m]{a}} = \sqrt[nm]{a}$ – корінь якого степеня "
            "вийде?"
            + "\n" + rf"3) Скоротіть показники й обчисліть значення виразу "
            rf"при $x = {x0}$."
            + "\n" + _HINT
        ),
        parts=[
            Part("under", "1) показник під внутрішнім:", sp.Integer(under),
                 points=1),
            Part("deg", "2) степінь спільного кореня:", sp.Integer(deg),
                 points=1),
            Part("val", rf"3) значення при $x = {x0}$:", sp.Integer(value),
                 points=1,
                 carry=lambda prev, _c=c, _d=d: _carry_root_value(prev, _c, _d),
                 carry_from=("under", "deg")),
        ],
        seconds=210,
        params={"n": n, "m": m, "a": a, "b": b, "under": under, "deg": deg,
                "d": d, "e": e, "x0": x0},
    )


def _carry_root_value(prev, c, d):
    """Значення за ВЛАСНИМИ показниками студента: $x_0^{p_1/p_2}$ при
    $x_0 = c^d$ дає $c^{d p_1 / p_2}$ – переносимо лише коли вийшов цілий
    і розумний показник."""
    p1, p2 = _num(prev.get("under")), _num(prev.get("deg"))
    if p1 is None or p2 is None:
        return None
    power = sp.Rational(d) * p1 / p2
    if not power.is_Integer or not 0 <= power <= 12:
        return None
    return sp.Integer(c) ** int(power)


# =========================================================================
#  ДІЇ З ДРОБОВИМИ ПОКАЗНИКАМИ
# =========================================================================

@template("tf_fraction_actions")
def _fraction_actions(rng: random.Random) -> Question:
    """Завдання 9: виконати дії з дробовими показниками.

    Кожен дріб скорочується окремо (різниця квадратів), і лише потім
    віднімання. Тому два перші поля показують, чи студент узагалі побачив
    розклад, а третє – чи довів дію до кінця.
    """
    k = rng.choice([1, 2, 3, 4, 5])
    c = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    ktex = "" if k == 1 else str(k)
    first = k * (sp.sqrt(_x) + c * sp.sqrt(_y))
    second = k * (sp.sqrt(_x) - c * sp.sqrt(_y))
    return Question(
        key="tf_fraction_actions",
        statement=(
            r"Виконайте дії ($x > 0$, $y > 0$):"
            + "\n" + rf"$$\dfrac{{{ktex}\left(x - {c**2}y\right)}}"
            rf"{{\sqrt{{x}} - {c}\sqrt{{y}}}} - "
            rf"\dfrac{{{ktex}\left(x - {c**2}y\right)}}"
            rf"{{\sqrt{{x}} + {c}\sqrt{{y}}}}$$"
            + "\n1) Скоротіть ПЕРШИЙ дріб."
            + "\n2) Скоротіть ДРУГИЙ дріб."
            + "\n3) Запишіть різницю."
            + "\n" + _HINT
        ),
        parts=[
            Part("first", "1) перший дріб:", sp.expand(first), kind="expr",
                 points=1, positive=True),
            Part("second", "2) другий дріб:", sp.expand(second), kind="expr",
                 points=1, positive=True),
            Part("diff", "3) різниця:", sp.expand(first - second), kind="expr",
                 points=1, positive=True,
                 carry=lambda prev: (
                     None if prev.get("first") is None
                     or prev.get("second") is None
                     or prev["first"] == prev["second"]
                     else prev["first"] - prev["second"]),
                 carry_from=("first", "second")),
        ],
        seconds=210,
        params={"k": k, "c": c},
    )


# =========================================================================
#  ІРРАЦІОНАЛЬНЕ РІВНЯННЯ
# =========================================================================

@template("tf_substitution_quartic")
def _substitution_quartic(rng: random.Random) -> Question:
    """Завдання 10: рівняння із заміною $t = \\sqrt[4]{x+a}$.

    Тут ОБИДВА значення $t$ додатні, тож коренів у рівняння два – на відміну
    від сусідніх задач, де один корінь завжди відкидається. Третій крок
    просить більший, щоб відповідь не збігалася з тим, що студент уже
    написав у другому полі.
    """
    a = rng.choice(range(1, 12))
    t1 = rng.choice([1, 2])
    t2 = rng.choice([v for v in (2, 3, 4) if v > t1])
    b = t1 + t2
    c = t1 * t2
    rhs = rf"{b}\sqrt[4]{{{_lin(1, a)}}} - {c}"
    return Question(
        key="tf_substitution_quartic",
        statement=(
            r"Розв'яжіть рівняння"
            + "\n" + rf"$$\sqrt{{{_lin(1, a)}}} = {rhs}$$"
            + "\n" + rf"Підказка: позначте $t = \sqrt[4]{{{_lin(1, a)}}}$, "
            r"тоді ліва частина дорівнює $t^2$."
            + "\n1) Знайдіть МЕНШИЙ корінь рівняння щодо $t$."
            + "\n2) Знайдіть БІЛЬШИЙ корінь рівняння щодо $t$."
            + "\n3) Знайдіть БІЛЬШИЙ корінь початкового рівняння."
            + "\n" + _HINT
        ),
        parts=[
            Part("t1", "1) менший $t$:", sp.Integer(t1), points=1),
            Part("t2", "2) більший $t$:", sp.Integer(t2), points=1),
            Part("x", "3) більший $x$:", sp.Integer(t2**4 - a), points=1,
                 carry=lambda prev, _a=a: (
                     None if _num(prev.get("t2")) is None
                     or abs(prev["t2"]) > 10
                     else prev["t2"] ** 4 - _a),
                 carry_from=("t2",)),
        ],
        seconds=210,
        params={"a": a, "t1": t1, "t2": t2, "b": b, "c": c},
    )
