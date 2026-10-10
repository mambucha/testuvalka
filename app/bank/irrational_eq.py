"""Ірраціональні рівняння (§7 Мерзляка, 10 клас).

Обсяг за підручником:
  * означення: рівняння зі змінною під знаком кореня;
  * теорема 7.1 – піднесення до НЕПАРНОГО степеня дає рівносильне рівняння,
    сторонніх коренів не буває;
  * теорема 7.2 – піднесення до ПАРНОГО степеня дає рівняння-НАСЛІДОК, тож
    перевірка обов'язкова; поняття стороннього кореня;
  * чому рівняння не має коренів (парний корінь не буває від'ємним, області
    визначення не перетинаються);
  * область допустимих значень;
  * метод заміни змінної.

Головна думка тесту повторює головну думку параграфа: знайти корені
рівняння-наслідку мало, треба ще сказати, які з них СТОРОННІ. Тому в
більшості задач два перші поля це корені наслідку, а третє – висновок про
початкове рівняння.

Чому це стійко до списування. Відповідь тут майже завжди число, тож захист
будується на параметрах: корені в кожного свої, а головне – навмисне
чергується, який саме корінь виявиться стороннім (менший чи більший) і чи
має друге рівняння корені взагалі. Переписане число без розуміння стає
помилкою.
"""

from __future__ import annotations

import random

import sympy as sp

from engine import Part, Question, template

_x = sp.Symbol("x")

_HINT = "(Відповідь – число. Дробові значення вводьте звичайним дробом: 3/2.)"


def _lin(a: int, b: int) -> str:
    """Лінійний вираз ax + b у LaTeX, без зайвих одиниць і плюсів."""
    head = ("" if a == 1 else "-" if a == -1 else str(a)) + "x"
    if b == 0:
        return head
    return head + (f" + {b}" if b > 0 else f" - {abs(b)}")


def _quad(a: int, b: int = 0) -> str:
    """Вираз x^2 + ax + b у LaTeX."""
    out = "x^2"
    if a:
        out += (" + " if a > 0 else " - ") + (f"{abs(a)}x" if abs(a) != 1 else "x")
    if b:
        out += (" + " if b > 0 else " - ") + str(abs(b))
    return out


def _root(n: int, inner: str) -> str:
    return rf"\sqrt{{{inner}}}" if n == 2 else rf"\sqrt[{n}]{{{inner}}}"


def _term(coef: int, body: str) -> str:
    """Доданок зі знаком: « + 3\\sqrt{x}», « - \\sqrt{x}»."""
    sign = " + " if coef > 0 else " - "
    mag = "" if abs(coef) == 1 else str(abs(coef))
    return sign + mag + body


def _num(value):
    if value is None or getattr(value, "free_symbols", set()):
        return None
    return value


def _carry_of(key):
    """Третій крок бере ВЛАСНЕ число студента з указаного поля: якщо він
    помилився в наслідку, але правильно відкинув сторонній корінь, крок
    зараховується.

    Переносимо лише тоді, коли два попередні поля справді РІЗНІ й
    упорядковані. Інакше однакове «сміття» в усіх трьох полях саме себе
    підтверджувало б і приносило бал.
    """
    def _fn(prev):
        lo, hi = _num(prev.get("small")), _num(prev.get("big"))
        if lo is None or hi is None or not lo < hi:
            return None
        return _num(prev.get(key))
    return _fn


# =========================================================================
#  НАЙПРОСТІШІ РІВНЯННЯ: ПАРНИЙ І НЕПАРНИЙ КОРІНЬ
# =========================================================================

@template("ir_simple_power")
def _simple_power(rng: random.Random) -> Question:
    """Найпростіші рівняння (вправи 7.2, 7.3) і різниця парного/непарного.

    Парний корінь від'ємним не буває, непарний – буває. Третій пункт тому
    і випадковий: інколи там нуль коренів, інколи один.
    """
    n_even = rng.choice([2, 4])
    n_odd = rng.choice([3, 5])
    c = rng.choice([2, 3, 4]) if n_even == 2 else 2
    f = rng.choice([2, 3]) if n_odd == 3 else 2
    a = rng.choice([1, 2, 3, 4])
    d = rng.choice([1, 2, 3, 5])
    x1 = rng.choice([v for v in range(-6, 8) if v])
    x2 = rng.choice([v for v in range(-6, 8) if v])
    b = c**n_even - a * x1           # щоб коренем було саме x1
    e = -(f**n_odd) - d * x2
    # Третє рівняння: корінь парного степеня від'ємним бути не може, а
    # непарного – може. Степінь обираємо випадково, тож відповідь то 0, то 1.
    third_odd = rng.random() < 0.5
    n3 = n_odd if third_odd else n_even
    g = rng.choice([2, 3])
    x3 = rng.choice([v for v in range(-5, 7) if v])
    h = (-(g**n3) - a * x3) if third_odd else (g**n3 - a * x3)
    return Question(
        key="ir_simple_power",
        statement=(
            "Розв'яжіть рівняння."
            + "\n" + rf"1) ${_root(n_even, _lin(a, b))} = {c}$"
            + "\n" + rf"2) ${_root(n_odd, _lin(d, e))} = -{f}$"
            + "\n" + rf"3) Скільки коренів має рівняння "
            rf"${_root(n3, _lin(a, h))} = -{g}$?"
            + "\n" + _HINT
        ),
        parts=[
            Part("x1", "1) $x$ =", sp.Integer(x1), points=1),
            Part("x2", "2) $x$ =", sp.Integer(x2), points=1),
            Part("cnt", "3) коренів:", sp.Integer(1 if third_odd else 0), points=1),
        ],
        seconds=120,
        params={"n_even": n_even, "n_odd": n_odd, "a": a, "b": b, "c": c,
                "d": d, "e": e, "f": f, "x1": x1, "x2": x2,
                "n3": n3, "g": g, "h": h, "third_odd": third_odd},
    )


@template("ir_odd_degree")
def _odd_degree(rng: random.Random) -> Question:
    """Теорема 7.1: непарний степінь дає РІВНОСИЛЬНЕ рівняння (задача 1).

    Сторонніх коренів тут не буває, тож обидва корені наслідку – справжні.
    """
    n = rng.choice([3, 5])
    p = rng.choice([-8, -7, -6, -5, -4, -3, -2, -1])
    q = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
    s = p + q
    m = -p * q                     # > 0, бо p < 0 < q
    return Question(
        key="ir_odd_degree",
        statement=(
            rf"Дано рівняння ${_root(n, _quad(-s))} = {_root(n, str(m))}$."
            + "\n1) Знайдіть МЕНШИЙ корінь."
            + "\n2) Знайдіть БІЛЬШИЙ корінь."
            + "\n" + _HINT
        ),
        parts=[
            Part("small", "1) менший корінь:", sp.Integer(p), points=1),
            Part("big", "2) більший корінь:", sp.Integer(q), points=1),
        ],
        seconds=110,
        params={"n": n, "p": p, "q": q, "s": s, "m": m},
    )


# =========================================================================
#  СТОРОННІ КОРЕНІ
# =========================================================================

@template("ir_even_extraneous")
def _even_extraneous(rng: random.Random) -> Question:
    """Теорема 7.2 і сторонній корінь (задача 3, вправи 7.6, 7.7).

    Знак у правій частині визначає, ЯКИЙ із двох коренів сторонній, і він
    чергується: інакше правильною завжди була б та сама відповідь.
    """
    p = rng.choice([-6, -5, -4, -3, -2, -1])
    q = rng.choice([1, 2, 3, 4, 5, 6])
    a = p + q
    b = -p * q                      # a*x + b = x^2  <=>  x^2 - a*x - b = 0
    minus = rng.random() < 0.5
    rhs = "-x" if minus else "x"
    valid = p if minus else q
    return Question(
        key="ir_even_extraneous",
        statement=(
            rf"Дано рівняння ${_root(2, _lin(a, b))} = {rhs}$."
            + "\n1) Піднесіть обидві частини до квадрата й знайдіть МЕНШИЙ "
            "корінь отриманого рівняння."
            + "\n2) Знайдіть БІЛЬШИЙ корінь отриманого рівняння."
            + "\n3) Який із них є коренем ПОЧАТКОВОГО рівняння?"
            + "\n" + _HINT
        ),
        parts=[
            Part("small", "1) менший корінь наслідку:", sp.Integer(p), points=1),
            Part("big", "2) більший корінь наслідку:", sp.Integer(q), points=1),
            Part("root", "3) корінь початкового:", sp.Integer(valid), points=1,
                 carry=_carry_of("small" if minus else "big"),
                 carry_from=("small", "big")),
        ],
        seconds=140,
        params={"p": p, "q": q, "a": a, "b": b, "minus": minus},
    )


@template("ir_radicals_equal")
def _radicals_equal(rng: random.Random) -> Question:
    """Рівність двох коренів: корінь треба перевірити на область визначення.

    Коефіцієнт підібрано так, щоб підкореневий вираз був від'ємним рівно
    в одному з коренів, і цей корінь чергується – то менший, то більший.
    """
    p = rng.choice([-6, -5, -4, -3, -2, -1])
    q = rng.choice([1, 2, 3, 4, 5, 6])
    drop_small = rng.random() < 0.5
    a = rng.choice([q + 1, q + 2, q + 3]) if drop_small else \
        rng.choice([p - 1, p - 2, p - 3])
    b = -p * q                       # > 0
    c = a - (p + q)
    valid = q if drop_small else p
    return Question(
        key="ir_radicals_equal",
        statement=(
            rf"Дано рівняння ${_root(2, _lin(a, b))} = {_root(2, _quad(c))}$."
            + "\n1) Знайдіть МЕНШИЙ корінь рівняння-наслідку."
            + "\n2) Знайдіть БІЛЬШИЙ корінь рівняння-наслідку."
            + "\n3) Який із них є коренем початкового рівняння? "
            "(підкореневий вираз не може бути від'ємним)"
            + "\n" + _HINT
        ),
        parts=[
            Part("small", "1) менший корінь наслідку:", sp.Integer(p), points=1),
            Part("big", "2) більший корінь наслідку:", sp.Integer(q), points=1),
            Part("root", "3) корінь початкового:", sp.Integer(valid), points=1,
                 carry=_carry_of("big" if drop_small else "small"),
                 carry_from=("small", "big")),
        ],
        seconds=140,
        params={"p": p, "q": q, "a": a, "b": b, "c": c, "drop_small": drop_small},
    )


@template("ir_quadratic_radicand")
def _quadratic_radicand(rng: random.Random) -> Question:
    """Квадратний тричлен під коренем: сторонніх коренів НЕ з'являється.

    Контраст до сусідніх задач: саме по собі піднесення до квадрата ще не
    означає, що сторонній корінь обов'язково буде.
    """
    b = rng.choice([2, 3, 4, 6, 8, 9, 10, 12])
    sq = b * b
    pairs = [(-d, sq // d) for d in range(1, sq + 1)
             if sq % d == 0 and d <= 30 and sq // d <= 30]
    p, q = rng.choice(pairs)
    a = -(p + q)
    # Друге рівняння: або з від'ємною правою частиною (коренів немає), або
    # з іншою додатною (коренів два). Випадково, щоб третє поле не було стале.
    negative = rng.random() < 0.5
    b2 = rng.choice([v for v in (2, 3, 4, 5, 6, 7, 8) if v != b])
    rhs2 = f"-{b}" if negative else str(b2)
    return Question(
        key="ir_quadratic_radicand",
        statement=(
            rf"Дано рівняння ${_root(2, _quad(a))} = {b}$."
            + "\n1) Знайдіть МЕНШИЙ корінь."
            + "\n2) Знайдіть БІЛЬШИЙ корінь."
            + "\n" + rf"3) Скільки коренів має рівняння "
            rf"${_root(2, _quad(a))} = {rhs2}$?"
            + "\n" + _HINT
        ),
        parts=[
            Part("small", "1) менший корінь:", sp.Integer(p), points=1),
            Part("big", "2) більший корінь:", sp.Integer(q), points=1),
            Part("cnt", "3) коренів у другого:", sp.Integer(0 if negative else 2),
                 points=1),
        ],
        seconds=130,
        params={"a": a, "b": b, "p": p, "q": q, "negative": negative, "b2": b2},
    )


# =========================================================================
#  КОЛИ КОРЕНІВ НЕМАЄ І ЯК ПЕРЕВІРЯТИ
# =========================================================================

@template("ir_no_roots")
def _no_roots(rng: random.Random) -> Question:
    """Чому рівняння не має коренів (вправа 7.1)."""
    a = rng.choice([1, 2, 3, 4, 5, 6])
    c = rng.choice([2, 3, 4, 5])
    n_odd = rng.choice([3, 5])
    k = rng.choice([1, 2, 3])
    empty = [
        rf"${_root(2, _lin(1, -a))} + {c} = 0$",
        rf"${_root(4, _lin(1, -a))} = -{c}$",
        rf"${_root(2, _lin(1, -a))} = -{c}$",
        rf"${_root(2, _lin(1, -a))} + {_root(2, _lin(-1, -c))} = {k}$",
    ]
    solvable = [
        (rf"${_root(2, _lin(1, -a))} = {c}$", a + c * c),
        (rf"${_root(n_odd, _lin(1, -a))} = -{k}$", a - k**n_odd),
        (rf"${_root(4, _lin(1, -a))} = {k}$", a + k**4),
    ]
    n_empty = rng.choice([2, 3])
    chosen = ([(t, None) for t in rng.sample(empty, n_empty)]
              + list(rng.sample(solvable, 4 - n_empty)))
    rng.shuffle(chosen)
    with_root = [(i, v) for i, (t, v) in enumerate(chosen, 1) if v is not None]
    (i1, v1), (i2, v2) = with_root[0], with_root[-1]
    listing = "   ".join(f"{i}) {t}" for i, (t, _) in enumerate(chosen, 1))
    same = i1 == i2
    return Question(
        key="ir_no_roots",
        statement=(
            "Дано чотири рівняння:"
            + "\n" + listing
            + "\n1) Скільки з них НЕ мають коренів?"
            + "\n" + rf"2) Знайдіть корінь рівняння № {i1}."
            + "\n" + (rf"3) Знайдіть корінь рівняння № {i2}." if not same
                      else rf"3) Чому дорівнює підкореневий вираз рівняння "
                           rf"№ {i1} при знайденому $x$?")
            + "\n" + _HINT
        ),
        parts=[
            Part("cnt", "1) без коренів:", sp.Integer(n_empty), points=1),
            Part("r1", rf"2) корінь № {i1}:", sp.Integer(v1), points=1),
            Part("r2", (rf"3) корінь № {i2}:" if not same
                        else "3) підкореневий вираз:"),
                 sp.Integer(v2 if not same else v1 - a), points=1),
        ],
        seconds=140,
        params={"a": a, "c": c, "k": k, "n_empty": n_empty, "same": same},
    )


@template("ir_check_roots")
def _check_roots(rng: random.Random) -> Question:
    """Перевірка коренів і область допустимих значень."""
    p = rng.choice([-6, -5, -4, -3, -2, -1])
    q = rng.choice([v for v in (1, 2, 3, 4, 5, 6) if v != -p])  # a = p+q != 0
    a, b = p + q, -p * q
    # Справжній корінь інколи є серед чисел, інколи ні, тож друге поле не стале.
    show_root = rng.random() < 0.5
    pool = [v for v in range(-7, 8) if v not in (p, q)]
    nums = sorted({p, *rng.sample(pool, 3 if not show_root else 2)}
                  | ({q} if show_root else set()))
    in_domain = sum(1 for v in nums if a * v + b >= 0)
    roots = sum(1 for v in nums if a * v + b >= 0 and sp.sqrt(a * v + b) == v)
    listing = ", ".join(f"${v}$" for v in nums)
    return Question(
        key="ir_check_roots",
        statement=(
            rf"Дано рівняння ${_root(2, _lin(a, b))} = x$ і числа {listing}."
            + "\n1) Для скількох із цих чисел підкореневий вираз НЕвід'ємний?"
            + "\n2) Скільки з них є коренями рівняння?"
            + "\n" + rf"3) Чому дорівнює ліва частина при $x = {p}$?"
            + "\n" + _HINT
        ),
        parts=[
            Part("dom", "1) у області визначення:", sp.Integer(in_domain), points=1),
            Part("cnt", "2) коренів:", sp.Integer(roots), points=1),
            Part("lp", rf"3) при $x = {p}$:", sp.Integer(-p), points=1),
        ],
        seconds=140,
        params={"p": p, "q": q, "a": a, "b": b, "nums": nums,
                "show_root": show_root},
    )


@template("ir_domain")
def _domain(rng: random.Random) -> Question:
    """Область допустимих значень ірраціонального рівняння."""
    a = rng.choice([1, 2])
    c = rng.choice([1, 2])
    low = rng.choice([-6, -5, -4, -3, -2, -1, 1, 2])
    high = rng.choice([3, 4, 5, 6, 7, 8, 9])
    half_lo = a == 2 and rng.random() < 0.5
    half_hi = c == 2 and rng.random() < 0.5
    b = -(a * low + (1 if half_lo else 0))      # a*x + b >= 0  ->  x >= -b/a
    d = c * high + (1 if half_hi else 0)        # d - c*x >= 0  ->  x <= d/c
    lo = sp.Rational(-b, a)
    hi = sp.Rational(d, c)
    count = int(sp.floor(hi)) - int(sp.ceiling(lo)) + 1
    return Question(
        key="ir_domain",
        statement=(
            rf"Дано рівняння ${_root(2, _lin(a, b))} + "
            rf"{_root(2, _lin(-c, d))} = 1$."
            + "\n1) Яке НАЙМЕНШЕ значення $x$ допустиме?"
            + "\n2) Яке НАЙБІЛЬШЕ значення $x$ допустиме?"
            + "\n3) Скільки ЦІЛИХ чисел входить в область допустимих значень?"
            + "\n" + _HINT
        ),
        parts=[
            Part("lo", "1) найменше $x$:", lo, points=1),
            Part("hi", "2) найбільше $x$:", hi, points=1),
            Part("cnt", "3) цілих чисел:", sp.Integer(count), points=1),
        ],
        seconds=130,
        params={"a": a, "b": b, "c": c, "d": d},
    )


# =========================================================================
#  МЕТОД ЗАМІНИ ЗМІННОЇ
# =========================================================================

@template("ir_substitution_sqrt")
def _substitution_sqrt(rng: random.Random) -> Question:
    """Заміна $t = \\sqrt{x}$ (вправи 7.10.2, 7.10.3).

    Від'ємне значення $t$ відкидаємо: арифметичний корінь невід'ємний.
    """
    k = rng.choice([1, 2, 3])
    t2 = rng.choice([2, 3, 4, 5, 6, 7])
    t1 = rng.choice([v for v in (-1, -2, -3, -4, -5) if v != -t2])  # інакше b = 0 і корінь зникає з рівняння
    b = -k * (t1 + t2)
    c = k * t1 * t2
    body = (("" if k == 1 else str(k)) + "x"
            + _term(b, r"\sqrt{x}") + _term(c, ""))
    return Question(
        key="ir_substitution_sqrt",
        statement=(
            rf"Розв'яжіть рівняння ${body} = 0$ заміною $t = \sqrt{{x}}$."
            + "\n1) Знайдіть МЕНШИЙ корінь рівняння щодо $t$."
            + "\n2) Знайдіть БІЛЬШИЙ корінь рівняння щодо $t$."
            + "\n3) Знайдіть корінь початкового рівняння."
            + "\n" + _HINT
        ),
        parts=[
            Part("t1", "1) менший $t$:", sp.Integer(t1), points=1),
            Part("t2", "2) більший $t$:", sp.Integer(t2), points=1),
            Part("x", "3) $x$ =", sp.Integer(t2 * t2), points=1,
                 carry=lambda prev: (None if _num(prev.get("t2")) is None
                                     else prev["t2"] ** 2),
                 carry_from=("t2",)),
        ],
        seconds=150,
        params={"k": k, "t1": t1, "t2": t2, "b": b, "c": c},
    )


@template("ir_substitution_cube")
def _substitution_cube(rng: random.Random) -> Question:
    """Заміна $t = \\sqrt[3]{x}$ (вправа 7.10.1).

    Тут не відкидаємо нічого: кубічний корінь набуває й від'ємних значень,
    тож обидва значення $t$ дають корені.
    """
    k = rng.choice([1, 2])
    t1 = rng.choice([-5, -4, -3, -2, -1])
    t2 = rng.choice([v for v in (1, 2, 3, 4, 5) if v != -t1])  # інакше b = 0 і корінь зникає з рівняння
    b = -k * (t1 + t2)
    c = k * t1 * t2
    head = ("" if k == 1 else str(k)) + r"\sqrt[3]{x^2}"
    body = (head + _term(b, r"\sqrt[3]{x}") + _term(c, ""))
    return Question(
        key="ir_substitution_cube",
        statement=(
            rf"Розв'яжіть рівняння ${body} = 0$ заміною $t = \sqrt[3]{{x}}$."
            + "\n1) Знайдіть МЕНШИЙ корінь рівняння щодо $t$."
            + "\n2) Знайдіть БІЛЬШИЙ корінь рівняння щодо $t$."
            + "\n3) Чому дорівнює СУМА коренів початкового рівняння?"
            + "\n" + _HINT
        ),
        parts=[
            Part("t1", "1) менший $t$:", sp.Integer(t1), points=1),
            Part("t2", "2) більший $t$:", sp.Integer(t2), points=1),
            Part("sum", "3) сума коренів:", sp.Integer(t1**3 + t2**3), points=1,
                 carry=lambda prev: (
                     None if _num(prev.get("t1")) is None
                     or _num(prev.get("t2")) is None
                     else prev["t1"] ** 3 + prev["t2"] ** 3),
                 carry_from=("t1", "t2")),
        ],
        seconds=150,
        params={"k": k, "t1": t1, "t2": t2, "b": b, "c": c},
    )


@template("ir_substitution_shift")
def _substitution_shift(rng: random.Random) -> Question:
    """Заміна $t = \\sqrt{x + a}$ (вправи 7.10.4, 7.11.3)."""
    a = rng.choice([1, 2, 3, 4, 5, 6])
    t1 = rng.choice([-3, -2, -1])
    t2 = rng.choice([v for v in (2, 3, 4, 5) if v != -t1])  # інакше b = 0 і корінь зникає з рівняння
    b = -(t1 + t2)
    c = t1 * t2
    inner = _lin(1, a)
    # Сталі зводимо: «x + 3 - 4*sqrt(x+3) - 5» виглядало б як недороблена
    # робота. Після заміни x = t^2 - a це те саме рівняння t^2 + bt + c = 0.
    const = a + c
    body = "x" + _term(b, rf"\sqrt{{{inner}}}") + (_term(const, "") if const else "")
    return Question(
        key="ir_substitution_shift",
        statement=(
            rf"Розв'яжіть рівняння ${body} = 0$ заміною "
            rf"$t = \sqrt{{{inner}}}$."
            + "\n1) Знайдіть МЕНШИЙ корінь рівняння щодо $t$."
            + "\n2) Знайдіть БІЛЬШИЙ корінь рівняння щодо $t$."
            + "\n3) Знайдіть корінь початкового рівняння."
            + "\n" + _HINT
        ),
        parts=[
            Part("t1", "1) менший $t$:", sp.Integer(t1), points=1),
            Part("t2", "2) більший $t$:", sp.Integer(t2), points=1),
            Part("x", "3) $x$ =", sp.Integer(t2 * t2 - a), points=1,
                 carry=lambda prev, _a=a: (
                     None if _num(prev.get("t2")) is None
                     else prev["t2"] ** 2 - _a),
                 carry_from=("t2",)),
        ],
        seconds=150,
        params={"a": a, "t1": t1, "t2": t2, "b": b, "c": c},
    )


@template("ir_two_radicals")
def _two_radicals(rng: random.Random) -> Question:
    """Сума двох коренів (вправи 7.15, 7.16).

    Ліва частина строго зростає, тож корінь не більше одного – це й дає
    змогу перевірити відповідь без громіздких викладок.
    """
    p = rng.choice([1, 2, 3, 4, 5, 6])
    q = rng.choice([v for v in (1, 2, 3, 4, 5, 6) if v != p])
    x0 = rng.choice([v for v in range(-4, 9) if v])   # нуль не даруємо
    a = p * p - x0
    b = q * q - x0
    lo = max(-a, -b)
    return Question(
        key="ir_two_radicals",
        statement=(
            rf"Дано рівняння ${_root(2, _lin(1, a))} + "
            rf"{_root(2, _lin(1, b))} = {p + q}$."
            + "\n1) Яке НАЙМЕНШЕ значення $x$ допустиме?"
            + "\n2) Знайдіть корінь рівняння."
            + "\n" + rf"3) Чому дорівнює ${_root(2, _lin(1, a))}$ при цьому $x$?"
            + "\n" + _HINT
        ),
        parts=[
            Part("lo", "1) найменше $x$:", sp.Integer(lo), points=1),
            Part("x", "2) корінь:", sp.Integer(x0), points=1),
            Part("val", "3) значення кореня:", sp.Integer(p), points=1,
                 carry=lambda prev, _a=a: (
                     None if _num(prev.get("x")) is None
                     or prev["x"] + _a < 0
                     else sp.sqrt(prev["x"] + _a)),
                 carry_from=("x",)),
        ],
        seconds=140,
        params={"p": p, "q": q, "x0": x0, "a": a, "b": b},
    )
