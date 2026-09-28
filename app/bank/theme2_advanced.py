"""Степенева функція та корінь n-го степеня — КОМПЛЕКСНІ задачі (чинний theme2).

Склад тем той самий, що й у простішому наборі (theme2_powers_roots.py), але
задачі переписані так, щоб КАЛЬКУЛЯТОР НЕ ДОПОМАГАВ:

  * більшість задач — У БУКВАХ: ³√(−8x³) = −2x, √(50a²) = 5a√2, √(x²) при x<0;
  * там, де числа, відповідь — ЗВИЧАЙНИЙ ДРІБ (2/3)³ = 8/27: десятковий дріб
    калькулятора не збігається з еталоном;
  * додано дії з коренями, де потрібне перетворення, а не обчислення:
    зведення подібних (√50+√18−√8) і раціоналізація знаменника.

Формат — як у тематичному оцінюванні з інтеграла: 2–3 поля на задачу
(перевіряється ШЛЯХ), часткові бали нормуються, а перенесення помилки (carry)
звіряє наступні кроки з власним результатом студента.

Баланс збережено: 6 задач на степеневу функцію + 6 на корінь.

ВАЖЛИВО: степеня з РАЦІОНАЛЬНИМ показником (a^(m/n)) тут немає — це наступна
тема. Перетворень графіків елементарними побудовами теж немає.
"""

from __future__ import annotations

import random

import sympy as sp

from engine import Part, Question, template

_x = sp.Symbol("x")
_y = sp.Symbol("y")


def _sub(expr, var, value):
    """Підстановка у ВЛАСНИЙ вираз студента (carry). Якщо вираз не залежить від
    змінної — не переносимо, щоб однакове сміття у двох полях не зараховувалося."""
    if expr is None or not getattr(expr, "has", lambda _v: False)(var):
        return None
    return expr.subs(var, value)


def _root_tex(n: int, inner: str) -> str:
    return rf"\sqrt{{{inner}}}" if n == 2 else rf"\sqrt[{n}]{{{inner}}}"


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


def _pow_tex(base: str, e: int) -> str:
    return base if e == 1 else rf"{base}^{{{e}}}"


# =========================================================================
#  СТЕПЕНЕВА ФУНКЦІЯ
# =========================================================================

@template("pr_power_values")
def _power_values(rng: random.Random) -> Question:
    """Значення степеневої у дробовій точці + друге значення ЧЕРЕЗ ПАРНІСТЬ.

    Відповідь — звичайний дріб, тож десятковий результат калькулятора з еталоном
    не збігається: треба справді піднести дріб до степеня."""
    n = rng.choice([2, 3, 4, 5])
    p = rng.choice([2, 3])
    q = rng.choice([v for v in (3, 4, 5) if v != p])
    base = sp.Rational(p, q)
    v1 = base**n
    v2 = (-base) ** n                      # парність: та сама або протилежна
    kind = "парна" if n % 2 == 0 else "непарна"
    return Question(
        key="pr_power_values",
        statement=(
            rf"Дано степеневу функцію $y = x^{{{n}}}$ (вона {kind})."
            + "\n" + rf"1) Обчисліть $f\left(\dfrac{{{p}}}{{{q}}}\right)$ "
            "(відповідь — звичайний дріб)."
            + "\n" + rf"2) Користуючись парністю (НЕ обчислюючи степінь заново), "
            rf"знайдіть $f\left(-\dfrac{{{p}}}{{{q}}}\right)$."
        ),
        parts=[
            Part("v1", rf"$f\left(\frac{{{p}}}{{{q}}}\right)$ =", v1, points=1),
            Part(
                "v2", rf"$f\left(-\frac{{{p}}}{{{q}}}\right)$ =", v2, points=1,
                # Переносимо крок лише для НЕПАРНОГО n, де парність справді
                # змінює число. При парному n правило дає те саме значення, і
                # перенесення зараховувало б однакове сміття у двох полях.
                carry=lambda prev: None if n % 2 == 0 else -prev["v1"],
                carry_from=("v1",),
            ),
        ],
        seconds=110,
        params={"n": n, "p": p, "q": q},
    )


@template("pr_negative_power")
def _negative_power(rng: random.Random) -> Question:
    """Степенева з цілим ВІД'ЄМНИМ показником: значення-дріб і знак у -a."""
    n = rng.choice([2, 3, 4])
    a = rng.choice([2, 3, 4])
    v1 = sp.Rational(1, a**n)
    v2 = sp.Rational(1, (-a) ** n)
    return Question(
        key="pr_negative_power",
        statement=(
            rf"Дано функцію $y = x^{{-{n}}}$, тобто $y = \dfrac{{1}}{{x^{{{n}}}}}$."
            + "\n" + rf"1) Обчисліть $f({a})$ (звичайним дробом)."
            + rf" 2) Обчисліть $f(-{a})$ — зверніть увагу на знак."
        ),
        parts=[
            Part("v1", rf"$f({a})$ =", v1, points=1),
            Part(
                "v2", rf"$f(-{a})$ =", v2, points=1,
                # Переносимо крок лише для НЕПАРНОГО n, де парність справді
                # змінює число. При парному n правило дає те саме значення, і
                # перенесення зараховувало б однакове сміття у двох полях.
                carry=lambda prev: None if n % 2 == 0 else -prev["v1"],
                carry_from=("v1",),
            ),
        ],
        seconds=110,
        params={"n": n, "a": a},
    )


@template("pr_parity")
def _parity(rng: random.Random) -> Question:
    """Парність СУМИ степеневих: знайти f(-x) як вираз і скористатися ним."""
    even = rng.random() < 0.5
    # Точку добираємо так, щоб значення НЕ було нулем (нуль легко вгадати):
    # напр. для x⁴ - 4x² воно нульове саме при x = 2.
    while True:
        if even:
            a, b = rng.choice([1, 2, 3]), rng.choice([-4, -3, 3, 4])
            f = a * _x**4 + b * _x**2
            ftex = _sum_tex([(a, "x^4"), (b, "x^2")])
        else:
            a, b = rng.choice([1, 2]), rng.choice([-5, -3, 3, 5])
            f = a * _x**5 + b * _x**3
            ftex = _sum_tex([(a, "x^5"), (b, "x^3")])
        fneg = sp.expand(f.subs(_x, -_x))
        ok = [c for c in (1, 2) if fneg.subs(_x, c) != 0]
        if ok:
            x0 = rng.choice(ok)
            val = fneg.subs(_x, x0)
            break
    return Question(
        key="pr_parity",
        statement=(
            rf"Дано функцію $f(x) = {ftex}$."
            + "\n1) Знайдіть і спростіть $f(-x)$ — це показує, парна функція чи "
            "непарна."
            + rf" 2) Користуючись цим, обчисліть $f(-{x0})$."
        ),
        parts=[
            Part("fneg", "$f(-x)$ =", fneg, kind="expr", points=1),
            Part(
                "val", rf"$f(-{x0})$ =", val, points=1,
                carry=lambda prev: _sub(prev["fneg"], _x, x0),
                carry_from=("fneg",),
            ),
        ],
        seconds=110,
        params={"even": even, "x0": x0},
    )


@template("pr_solve_even_power")
def _solve_even_power(rng: random.Random) -> Question:
    r"""Рівняння $(x-c)^{2k} = a$ — ДВА корені."""
    k = rng.choice([1, 2])
    d = rng.choice([2, 3])
    c = rng.choice([-3, -2, -1, 1, 2, 3])
    a = d ** (2 * k)
    return Question(
        key="pr_solve_even_power",
        statement=(
            r"Розв'яжіть рівняння"
            + "\n"
            + rf"$$ \left(x {'+' if c < 0 else '-'} {abs(c)}\right)^{{{2 * k}}} = {a} $$"
            + rf"Показник ПАРНИЙ, тому ${_root_tex(2 * k, str(a))}$ дає два значення "
            r"($\pm$). Запишіть обидва корені."
        ),
        parts=[
            Part("lo", "менший корінь =", c - d, points=1),
            Part("hi", "більший корінь =", c + d, points=1),
        ],
        seconds=120,
        params={"c": c, "d": d, "k": k, "a": a},
    )


@template("pr_solve_odd_power")
def _solve_odd_power(rng: random.Random) -> Question:
    r"""Рівняння $(x-c)^{2k+1} = a$ — ОДИН корінь; $a$ буває від'ємним."""
    n = rng.choice([3, 5])
    d = rng.choice([-3, -2, 2, 3]) if n == 3 else rng.choice([-2, 2])
    c = rng.choice([-3, -2, -1, 1, 2, 3])
    a = d**n                               # непарний степінь зберігає знак
    return Question(
        key="pr_solve_odd_power",
        statement=(
            r"Розв'яжіть рівняння"
            + "\n"
            + rf"$$ \left(x {'+' if c < 0 else '-'} {abs(c)}\right)^{{{n}}} = {a} $$"
            + rf"Показник НЕПАРНИЙ, тому корінь ${_root_tex(n, str(a))}$ існує й "
            "для від'ємного числа, і він один."
            + f"\n1) Чому дорівнює ${_root_tex(n, str(a))}$? 2) Знайдіть $x$."
        ),
        parts=[
            Part("root", f"${_root_tex(n, str(a))}$ =", d, points=1),
            Part(
                "x", "$x$ =", c + d, points=1,
                carry=lambda prev: c + prev["root"],
                carry_from=("root",),
            ),
        ],
        seconds=110,
        params={"n": n, "c": c, "d": d, "a": a},
    )


@template("pr_domain_even_root")
def _domain_even_root(rng: random.Random) -> Question:
    r"""Область визначення $\sqrt[2k]{b-ax}$ і значення в точці."""
    n = rng.choice([2, 4])
    a = rng.choice([1, 2])
    b = rng.choice([4, 8, 12, 16])
    bound = sp.Rational(b, a)
    while True:
        t = rng.choice([1, 2])
        inner = t**n
        if (b - inner) % a == 0:
            break
    x0 = (b - inner) // a
    inner_tex = f"{b} - {a}x" if a > 1 else f"{b} - x"
    return Question(
        key="pr_domain_even_root",
        statement=(
            rf"Дано функцію $f(x) = {_root_tex(n, inner_tex)}$."
            + f"\n1) Корінь ПАРНОГО степеня існує лише при невід'ємному "
            "підкореневому виразі. Знайдіть НАЙБІЛЬШЕ допустиме значення $x$."
            + rf" 2) Обчисліть $f({x0})$."
        ),
        parts=[
            Part("bound", "найбільше $x$ =", bound, points=1),
            Part("val", rf"$f({x0})$ =", t, points=1),
        ],
        seconds=120,
        params={"n": n, "a": a, "b": b, "x0": x0, "t": t},
    )


# =========================================================================
#  КОРІНЬ n-го СТЕПЕНЯ ТА ЙОГО ВЛАСТИВОСТІ
# =========================================================================

@template("pr_root_of_power_letters")
def _root_of_power_letters(rng: random.Random) -> Question:
    r"""Корінь НЕПАРНОГО степеня з від'ємного виразу: $\sqrt[3]{-8x^3} = -2x$.

    Калькулятор тут безсилий — відповідь містить букву."""
    n = rng.choice([3, 5])
    c = rng.choice([2, 3]) if n == 3 else 2
    neg = rng.random() < 0.6                # частіше беремо від'ємний варіант
    coef = -(c**n) if neg else c**n
    res = (-c if neg else c) * _x
    x0 = rng.choice([2, 3])       # x=1 звело б підстановку до коефіцієнта
    val = res.subs(_x, x0)
    inner = f"{coef}{_pow_tex('x', n)}" if abs(coef) != 1 else _pow_tex("x", n)
    return Question(
        key="pr_root_of_power_letters",
        statement=(
            rf"Спростіть вираз (для будь-якого $x$):"
            + "\n" + rf"$$ {_root_tex(n, inner)} $$"
            + rf"Показник кореня непарний, тому знак зберігається."
            + f"\nПотім обчисліть значення при $x = {x0}$."
        ),
        parts=[
            Part("simp", "спрощений вираз =", res, kind="expr", points=1),
            Part(
                "val", rf"значення при $x={x0}$ =", val, points=1,
                carry=lambda prev: _sub(prev["simp"], _x, x0),
                carry_from=("simp",),
            ),
        ],
        seconds=120,
        params={"n": n, "c": c, "neg": neg, "x0": x0},
    )


@template("pr_modulus_root")
def _modulus_root(rng: random.Random) -> Question:
    r"""Корінь ПАРНОГО степеня з квадрата: $\sqrt{c^2x^2} = |cx|$, а при $x<0$
    це $-cx$. Перевіряє розуміння модуля, а не обчислення."""
    n = rng.choice([2, 4])
    c = rng.choice([2, 3])
    res = -c * _x                           # бо x < 0  ->  |cx| = -cx
    x0 = rng.choice([-2, -3])     # x=-1 звело б підстановку до коефіцієнта
    val = res.subs(_x, x0)
    inner = f"{c**n}{_pow_tex('x', n)}"
    return Question(
        key="pr_modulus_root",
        statement=(
            rf"Відомо, що $x < 0$. Спростіть вираз:"
            + "\n" + rf"$$ {_root_tex(n, inner)} $$"
            + r"Показник кореня ПАРНИЙ, тому результат невід'ємний: "
            r"${}^{2k}\!\sqrt{a^{2k}} = |a|$. Розкрийте модуль з урахуванням "
            "того, що $x$ від'ємний."
            + f"\nПотім обчисліть значення при $x = {x0}$."
        ),
        parts=[
            Part("simp", "спрощений вираз =", res, kind="expr", points=1),
            Part(
                "val", rf"значення при $x={x0}$ =", val, points=1,
                carry=lambda prev: _sub(prev["simp"], _x, x0),
                carry_from=("simp",),
            ),
        ],
        seconds=120,
        params={"n": n, "c": c, "x0": x0},
    )


@template("pr_factor_out_letters")
def _factor_out_letters(rng: random.Random) -> Question:
    r"""Винесення множника з-під кореня з буквою: $\sqrt{50a^2} = 5a\sqrt{2}$."""
    c = rng.choice([2, 3, 4, 5])
    r = rng.choice([2, 3, 5, 6, 7])
    inner_num = c * c * r
    res = c * _x * sp.sqrt(r)
    return Question(
        key="pr_factor_out_letters",
        statement=(
            rf"Винесіть множник з-під знака кореня (вважайте $x > 0$):"
            + "\n" + rf"$$ \sqrt{{{inner_num}x^2}} $$"
            + "1) Яке число лишиться під коренем? 2) Запишіть увесь вираз."
        ),
        parts=[
            Part("rad", "під коренем лишиться =", r, points=1),
            Part(
                "res", "результат =", res, kind="expr", points=1,
                carry=lambda prev: c * _x * sp.sqrt(prev["rad"]),
                carry_from=("rad",),
            ),
        ],
        seconds=130,
        params={"c": c, "r": r, "inner": inner_num},
    )


@template("pr_simplify_letters")
def _simplify_letters(rng: random.Random) -> Question:
    r"""Спрощення кореня з буквами: $\sqrt[n]{x^{nk} y^{nm}} = x^k y^m$."""
    n = rng.choice([2, 3, 4])
    k = rng.randint(2, 3)
    m = rng.randint(1, 3)
    res = _x**k * _y**m
    x0, y0 = rng.choice([2, 3]), rng.choice([2, 3])   # y=1 не впливав би
    val = res.subs({_x: x0, _y: y0})
    inner = f"{_pow_tex('x', n * k)} {_pow_tex('y', n * m)}"
    return Question(
        key="pr_simplify_letters",
        statement=(
            rf"Спростіть вираз (вважайте $x>0$, $y>0$):"
            + "\n" + rf"$$ {_root_tex(n, inner)} $$"
            + f"Потім обчисліть значення при $x = {x0}$, $y = {y0}$."
        ),
        parts=[
            Part("simp", "спрощений вираз =", res, kind="expr", points=1),
            Part(
                "val", rf"значення при $x={x0}$, $y={y0}$ =", val, points=1,
                carry=lambda prev: (
                    prev["simp"].subs({_x: x0, _y: y0})
                    if getattr(prev["simp"], "free_symbols", set()) else None
                ),
                carry_from=("simp",),
            ),
        ],
        seconds=130,
        params={"n": n, "k": k, "m": m, "x0": x0, "y0": y0},
    )


@template("pr_collect_radicals")
def _collect_radicals(rng: random.Random) -> Question:
    """Зведення подібних доданків з коренями: винести множник із кожного."""
    r = rng.choice([2, 3, 5, 6, 7])
    c1 = rng.choice([4, 5, 6])
    c2 = rng.choice([2, 3])
    c3 = rng.choice([v for v in (1, 2) if v != c2])   # інакше два доданки зникають
    coef = c1 + c2 - c3
    a1, a2, a3 = c1 * c1 * r, c2 * c2 * r, c3 * c3 * r
    return Question(
        key="pr_collect_radicals",
        statement=(
            r"Спростіть вираз"
            + "\n" + rf"$$ \sqrt{{{a1}}} + \sqrt{{{a2}}} - \sqrt{{{a3}}} $$"
            + "Винесіть множник з-під кожного кореня і зведіть подібні доданки."
            + "\n1) Який підкореневий вираз спільний? 2) Який коефіцієнт вийшов? "
            "3) Запишіть результат."
        ),
        parts=[
            Part("rad", "спільний підкореневий =", r, points=1),
            Part("coef", "коефіцієнт =", coef, points=1),
            Part(
                "res", "результат =", coef * sp.sqrt(r), kind="expr", points=1,
                carry=lambda prev: prev["coef"] * sp.sqrt(prev["rad"]),
                carry_from=("rad", "coef"),
            ),
        ],
        seconds=150,
        params={"r": r, "c1": c1, "c2": c2, "c3": c3},
    )


@template("pr_rationalize")
def _rationalize(rng: random.Random) -> Question:
    """Звільнення від ірраціональності в знаменнику (сполучений вираз)."""
    a, b = rng.choice([(7, 5), (5, 3), (11, 9), (8, 6), (10, 8)])
    k = rng.choice([2, 3])          # k>1: результат не дорівнює сполученому
    c = k * (a - b)
    conj = sp.sqrt(a) + sp.sqrt(b)
    res = k * conj
    return Question(
        key="pr_rationalize",
        statement=(
            r"Звільніться від ірраціональності в знаменнику"
            + "\n" + rf"$$ \dfrac{{{c}}}{{\sqrt{{{a}}} - \sqrt{{{b}}}}} $$"
            + "1) Запишіть сполучений вираз, на який треба помножити чисельник "
            "і знаменник."
            + "\n2) Запишіть спрощений результат."
        ),
        parts=[
            Part("conj", "сполучений вираз =", conj, kind="expr", points=1),
            Part("res", "результат =", res, kind="expr", points=1),
        ],
        seconds=150,
        params={"a": a, "b": b, "k": k, "c": c},
    )


# =========================================================================
#  ЗАПАСНІ ШАБЛОНИ (у банк тесту не входять)
#  Придатні, якщо захочемо зробити пул більшим за кількість питань, щоб
#  сусіди отримували різні задачі.
# =========================================================================

@template("pr_fraction_simplify")
def _fraction_simplify(rng: random.Random) -> Question:
    r"""Спрощення $\frac{x-c^2}{\sqrt{x}-c} = \sqrt{x}+c$ (різниця квадратів)."""
    c = rng.choice([2, 3, 4, 5])
    x0 = rng.choice([v for v in (1, 4, 9, 16, 25, 36) if v != c * c])
    expr = sp.sqrt(_x) + c
    val = int(sp.sqrt(x0)) + c
    return Question(
        key="pr_fraction_simplify",
        statement=(
            rf"Спростіть вираз (при $x \ge 0$, $x \ne {c * c}$)"
            + "\n" + rf"$$ \dfrac{{x - {c * c}}}{{\sqrt{{x}} - {c}}} $$"
            + rf"Підказка: $x - {c * c} = \left(\sqrt{{x}}\right)^2 - {c}^2$ — "
            "різниця квадратів."
            + f"\nПотім обчисліть значення при $x = {x0}$."
        ),
        parts=[
            Part("simp", "спрощений вираз =", expr, kind="expr", points=1),
            Part(
                "val", rf"значення при $x={x0}$ =", val, points=1,
                carry=lambda prev: _sub(prev["simp"], _x, x0),
                carry_from=("simp",),
            ),
        ],
        seconds=140,
        params={"c": c, "x0": x0},
    )


@template("pr_compare_radicals")
def _compare_radicals(rng: random.Random) -> Question:
    """Порівняння чисел виду p√q внесенням множника під корінь."""
    while True:
        p, q = rng.choice([2, 3, 4]), rng.choice([2, 3, 5, 6, 7])
        u, v = rng.choice([2, 3, 4]), rng.choice([2, 3, 5, 6, 7])
        A, B = p * p * q, u * u * v
        if A != B and q != v:
            break
    bigger = p * sp.sqrt(q) if A > B else u * sp.sqrt(v)
    return Question(
        key="pr_compare_radicals",
        statement=(
            rf"Порівняйте числа $ {p}\sqrt{{{q}}} $ і $ {u}\sqrt{{{v}}} $."
            + "\nВнесіть множник під корінь і порівняйте підкореневі вирази."
            + "\n1) Підкореневий у першого? 2) У другого? "
            "3) Запишіть БІЛЬШЕ з двох чисел у початковому вигляді."
        ),
        parts=[
            Part("a1", rf"${p}\sqrt{{{q}}} = \sqrt{{\;?\;}}$", A, points=1),
            Part("a2", rf"${u}\sqrt{{{v}}} = \sqrt{{\;?\;}}$", B, points=1),
            Part("big", "більше число =", bigger, kind="expr", points=1),
        ],
        seconds=140,
        params={"p": p, "q": q, "u": u, "v": v},
    )
