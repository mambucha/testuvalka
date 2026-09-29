"""Степенева функція та корінь n-го степеня — за підручником Мерзляка (10 клас).

Відповідає типовим вправам §2–§5:
  §2. Степенева функція з НАТУРАЛЬНИМ показником — чи проходить графік через
      точку (2.1–2.2), ПОРІВНЯННЯ значень через монотонність і парність
      (2.3–2.4), найбільше і найменше значення на проміжку (2.7–2.8),
      графічно кількість коренів рівняння (2.9).
  §3. Степенева функція із ЦІЛИМ показником — обчислення виразів зі степенями
      з цілими показниками (2.12), порівняння значень y = x^(-n) (3.3–3.4),
      область визначення і розрив у нулі.
  §4. Означення кореня n-го степеня — чи має зміст запис (4.1), обчислення
      (4.4–4.7), рівняння x^n = a та (x-c)^n = a (4.8–4.9).
  §5. Властивості кореня — винесення множника з-під кореня (5.7–5.8), внесення
      множника під корінь (5.9–5.10), спрощення з урахуванням ЗНАКУ (5.21).

Плюс дві задачі з графіками, як просив викладач.

§6 (степінь з раціональним показником) СВІДОМО не входить — це наступна тема.
Звільнення від ірраціональності теж немає: такого з групою ще не розв'язували.

Задачі багатокрокові (2 поля): часткові бали нормуються, а перенесення помилки
(carry) звіряє другий крок із власним результатом студента. Там, де можливо,
відповідь — звичайний дріб або аргумент, а не число, яке видає калькулятор:
порівняння значень x^19 калькулятор не витягує, а суть — у властивостях.
"""

from __future__ import annotations

import random

import sympy as sp

from engine import Part, Question, template

from app.bank.plotting import coordinate_plane

_x = sp.Symbol("x")


def _root_tex(n: int, inner: str) -> str:
    return rf"\sqrt{{{inner}}}" if n == 2 else rf"\sqrt[{n}]{{{inner}}}"


# =========================================================================
#  §2. СТЕПЕНЕВА ФУНКЦІЯ З НАТУРАЛЬНИМ ПОКАЗНИКОМ
# =========================================================================

@template("mz_find_exponent")
def _find_exponent(rng: random.Random) -> Question:
    r"""Вправи 2.1–2.2: чи проходить графік $y=x^n$ через точку. Тут — обернено:
    за точкою знайти показник, а тоді застосувати парність."""
    a = rng.choice([2, 3])
    n = rng.choice([3, 4, 5]) if a == 2 else rng.choice([3, 4])
    y = a**n
    val = (-a) ** n

    def carry_val(prev):
        k = prev["n"]
        if not getattr(k, "is_Integer", False) or not (1 <= int(k) <= 12):
            return None
        return sp.Integer(-a) ** int(k)

    return Question(
        key="mz_find_exponent",
        statement=(
            r"Графік степеневої функції $y = x^n$ ($n$ — натуральне) проходить "
            rf"через точку $A\left({a};\ {y}\right)$."
            + "\n1) Знайдіть показник $n$."
            + rf" 2) Чи проходить графік через точку $B\left(-{a};\ ?\right)$ — "
            rf"обчисліть $f(-{a})$, користуючись парністю."
        ),
        parts=[
            Part("n", "$n$ =", n, points=1),
            Part("val", rf"$f(-{a})$ =", val, points=1,
                 carry=carry_val, carry_from=("n",)),
        ],
        seconds=110,
        params={"a": a, "n": n, "y": y},
    )


@template("mz_compare_power")
def _compare_power(rng: random.Random) -> Question:
    r"""Вправи 2.3–2.4: порівняти значення $f(x)=x^n$ у двох точках.

    Показник великий навмисно — калькулятор тут не поміч, працюють лише
    монотонність і парність. У відповідь пишемо АРГУМЕНТ, при якому значення
    більше."""
    n = rng.choice([19, 21, 24, 30])
    even = n % 2 == 0
    p, q = sorted(rng.sample([2, 3, 4, 5, 6], 2))       # p < q
    # пара 1: два від'ємні аргументи
    if even:
        big1 = -q                                       # більший модуль -> більше
    else:
        big1 = -p                                       # зростаюча -> більший x
    # пара 2: додатний і від'ємний, різні модулі
    s, t = rng.sample([2, 3, 5, 7], 2)
    big2 = (s if s > t else -t) if even else s
    kind = "парна" if even else "непарна"
    return Question(
        key="mz_compare_power",
        statement=(
            rf"Дано функцію $f(x) = x^{{{n}}}$ (показник {'парний' if even else 'непарний'}, "
            rf"тому функція {kind})."
            + "\nПорівняйте значення, НЕ обчислюючи степені — скористайтеся "
            "парністю та зростанням/спаданням."
            + "\n" + rf"1) $f(-{p})$ і $f(-{q})$   2) $f({s})$ і $f(-{t})$"
            + "\nУ кожному пункті запишіть той АРГУМЕНТ, при якому значення "
            "функції більше."
        ),
        parts=[
            Part("b1", "1) більше значення при $x$ =", big1, points=1),
            Part("b2", "2) більше значення при $x$ =", big2, points=1),
        ],
        seconds=140,
        params={"n": n, "p": p, "q": q, "s": s, "t": t},
    )


@template("mz_minmax_power")
def _minmax_power(rng: random.Random) -> Question:
    r"""Вправи 2.7–2.8: найбільше і найменше значення $f(x)=x^n$ на проміжку."""
    n = rng.choice([4, 5, 6, 8]) if rng.random() < 0.5 else rng.choice([3, 5, 7])
    lo, hi = rng.choice([(-2, -1), (-2, 0), (-1, 1), (0, 2), (1, 2), (-2, 2)])
    vals = [sp.Integer(lo) ** n, sp.Integer(hi) ** n]
    if lo <= 0 <= hi:
        vals.append(sp.Integer(0))
    vmin, vmax = min(vals), max(vals)
    return Question(
        key="mz_minmax_power",
        statement=(
            rf"Знайдіть найбільше і найменше значення функції $f(x) = x^{{{n}}}$ "
            rf"на проміжку $[{lo};\ {hi}]$."
            + "\nСпирайтеся на властивості: де функція зростає, а де спадає "
            "(і чи потрапляє в проміжок нуль)."
        ),
        parts=[
            Part("vmin", "найменше значення =", vmin, points=1),
            Part("vmax", "найбільше значення =", vmax, points=1),
        ],
        seconds=130,
        params={"n": n, "lo": lo, "hi": hi},
    )


# =========================================================================
#  §3. СТЕПЕНЕВА ФУНКЦІЯ ІЗ ЦІЛИМ ПОКАЗНИКОМ
# =========================================================================

@template("mz_int_power_expr")
def _int_power_expr(rng: random.Random) -> Question:
    r"""Вправа 2.12: обчислити вираз зі степенями з ЦІЛИМИ показниками.

    Відповідь — звичайний дріб, тож десятковий результат калькулятора з
    еталоном не збігається."""
    a, p = rng.choice([2, 3, 4, 5]), rng.choice([1, 2, 3])
    b, q = rng.choice([2, 3, 6]), rng.choice([1, 2])
    while a**p == b**q:
        b, q = rng.choice([2, 3, 6]), rng.choice([1, 2])
    minus = rng.random() < 0.5
    t1, t2 = sp.Rational(1, a**p), sp.Rational(1, b**q)
    total = t1 - t2 if minus else t1 + t2
    sign = "-" if minus else "+"
    return Question(
        key="mz_int_power_expr",
        statement=(
            r"Обчисліть значення виразу (відповідь — звичайний дріб):"
            + "\n" + rf"$$ {a}^{{-{p}}} {sign} {b}^{{-{q}}} $$"
            + rf"Нагадаємо: $c^{{-m}} = \dfrac{{1}}{{c^m}}$."
            + "\n" + rf"1) Чому дорівнює ${a}^{{-{p}}}$? 2) Обчисліть увесь вираз."
        ),
        parts=[
            Part("t1", rf"${a}^{{-{p}}}$ =", t1, points=1),
            Part(
                "total", "значення виразу =", total, points=1,
                carry=lambda prev: (prev["t1"] - t2) if minus else (prev["t1"] + t2),
                carry_from=("t1",),
            ),
        ],
        seconds=120,
        params={"a": a, "p": p, "b": b, "q": q, "minus": minus},
    )


@template("mz_compare_int_power")
def _compare_int_power(rng: random.Random) -> Question:
    r"""Вправи 3.3–3.4: порівняти значення $f(x)=x^{-n}$.

    Тут легко помилитися: при $n$ парному функція СПАДАЄ на $(0;+\infty)$, тобто
    більшому аргументу відповідає МЕНШЕ значення."""
    n = rng.choice([19, 20, 24, 40])
    even = n % 2 == 0
    p, q = sorted(rng.sample([2, 3, 4, 5, 6], 2))       # 0 < p < q
    xpow = "x" if n == 1 else f"x^{{{n}}}"
    big1 = p            # спадає на (0;+inf) для будь-якого n -> менший x дає більше
    # пара 2: додатний і від'ємний
    s, t = rng.sample([v for v in (2, 3, 5, 7) if v != p], 2)
    if even:
        big2 = s if s < t else -t        # парна: |менший модуль| -> більше
    else:
        big2 = s                          # непарна: додатне > від'ємного
    return Question(
        key="mz_compare_int_power",
        statement=(
            rf"Дано функцію $f(x) = x^{{-{n}}}$, тобто "
            rf"$f(x) = \dfrac{{1}}{{{xpow}}}$ (показник "
            rf"{'парний' if even else 'непарний'})."
            + "\nПорівняйте значення, спираючись на властивості функції "
            "(вона спадає на проміжку додатних чисел)."
            + "\n" + rf"1) $f({p})$ і $f({q})$   2) $f({s})$ і $f(-{t})$"
            + "\nУ кожному пункті запишіть АРГУМЕНТ, при якому значення більше."
        ),
        parts=[
            Part("b1", "1) більше значення при $x$ =", big1, points=1),
            Part("b2", "2) більше значення при $x$ =", big2, points=1),
        ],
        seconds=140,
        params={"n": n, "p": p, "q": q, "s": s, "t": t},
    )


# =========================================================================
#  §4. ОЗНАЧЕННЯ КОРЕНЯ n-го СТЕПЕНЯ
# =========================================================================

@template("mz_root_sense")
def _root_sense(rng: random.Random) -> Question:
    r"""Вправи 4.1, 4.4: чи має зміст запис $\sqrt[n]{a}$, і обчислення.

    Корінь ПАРНОГО степеня з від'ємного числа не існує; непарного — існує."""
    # трійки (степінь, підкореневе) — частина з від'ємними
    c = rng.choice([2, 3])
    odd_neg = (3, -(c**3))                      # має зміст
    even_neg = (rng.choice([2, 4]), -(c**2))    # НЕ має змісту
    even_pos = (2, c * c)                       # має зміст
    odd_pos = (3, c**3)                         # має зміст
    items = [odd_neg, even_neg, even_pos, odd_pos]
    rng.shuffle(items)
    good = sum(1 for n, a in items if not (n % 2 == 0 and a < 0))
    tex = r",\qquad ".join(_root_tex(n, str(a)) for n, a in items)
    return Question(
        key="mz_root_sense",
        statement=(
            r"Дано чотири записи:"
            + "\n" + rf"$$ {tex} $$"
            + "1) Скільки з них МАЮТЬ ЗМІСТ? (Корінь парного степеня з "
            "від'ємного числа не існує.)"
            + "\n" + rf"2) Обчисліть ${_root_tex(3, str(odd_neg[1]))}$."
        ),
        parts=[
            Part("cnt", "мають зміст (скільки) =", good, points=1),
            Part("val", rf"${_root_tex(3, str(odd_neg[1]))}$ =", -c, points=1),
        ],
        seconds=120,
        params={"c": c, "good": good},
    )


@template("mz_solve_power_eq")
def _solve_power_eq(rng: random.Random) -> Question:
    r"""Вправи 4.8–4.9: рівняння $(x-c)^{n} = a$ з ПАРНИМ показником — два корені."""
    k = rng.choice([1, 2])
    d = rng.choice([2, 3])
    c = rng.choice([-3, -2, -1, 1, 2, 3])
    a = d ** (2 * k)
    return Question(
        key="mz_solve_power_eq",
        statement=(
            r"Розв'яжіть рівняння"
            + "\n"
            + rf"$$ \left(x {'+' if c < 0 else '-'} {abs(c)}\right)^{{{2 * k}}} = {a} $$"
            + rf"Показник ПАРНИЙ, тому ${_root_tex(2 * k, str(a))}$ дає два "
            r"значення ($\pm$). Запишіть обидва корені."
        ),
        parts=[
            Part("lo", "менший корінь =", c - d, points=1),
            Part("hi", "більший корінь =", c + d, points=1),
        ],
        seconds=120,
        params={"c": c, "d": d, "k": k, "a": a},
    )


# =========================================================================
#  §5. ВЛАСТИВОСТІ КОРЕНЯ n-го СТЕПЕНЯ
# =========================================================================

@template("mz_factor_out")
def _factor_out(rng: random.Random) -> Question:
    r"""Вправи 5.7–5.8: винести множник з-під знака кореня n-го степеня."""
    n = rng.choice([2, 3])
    c = rng.choice([2, 3]) if n == 3 else rng.choice([2, 3, 4, 5])
    r = rng.choice([2, 3, 5, 6, 7])
    inner = (c**n) * r
    return Question(
        key="mz_factor_out",
        statement=(
            r"Винесіть множник з-під знака кореня (вважайте $x > 0$):"
            + "\n" + rf"$$ {_root_tex(n, f'{inner}x^{{{n}}}')} $$"
            + "1) Запишіть множник, який виноситься ПЕРЕД корінь."
            + "\n2) Яке число лишиться ПІД коренем?"
        ),
        parts=[
            Part("coef", "перед коренем =", c * _x, kind="expr", points=1),
            Part("rad", "під коренем =", r, points=1),
        ],
        seconds=130,
        params={"n": n, "c": c, "r": r, "inner": inner},
    )


@template("mz_bring_under")
def _bring_under(rng: random.Random) -> Question:
    r"""Вправи 5.9–5.10: внести множник ПІД знак кореня: $2\sqrt[3]{3}
    = \sqrt[3]{24}$."""
    n = rng.choice([2, 3])
    c = rng.choice([2, 3]) if n == 3 else rng.choice([2, 3, 4, 5])
    r = rng.choice([2, 3, 5, 6, 7])
    inner = (c**n) * r
    return Question(
        key="mz_bring_under",
        statement=(
            r"Внесіть множник під знак кореня:"
            + "\n" + rf"$$ {c}\,{_root_tex(n, str(r))} $$"
            + rf"Множник треба піднести до {n}-го степеня."
            + "\n" + rf"1) Чому дорівнює ${c}^{{{n}}}$? 2) Яке число стане під коренем?"
        ),
        parts=[
            Part("pw", rf"${c}^{{{n}}}$ =", c**n, points=1),
            Part(
                "inner", "під коренем =", inner, points=1,
                carry=lambda prev: prev["pw"] * r,
                carry_from=("pw",),
            ),
        ],
        seconds=120,
        params={"n": n, "c": c, "r": r, "inner": inner},
    )


@template("mz_simplify_sign")
def _simplify_sign(rng: random.Random) -> Question:
    r"""Вправи 5.21–5.22: спростити $\sqrt[2k]{a^{2k}}$ з урахуванням ЗНАКУ.

    Корінь парного степеня невід'ємний, тому при $x<0$ модуль розкривається
    зі знаком мінус."""
    n = rng.choice([2, 4])
    c = rng.choice([2, 3])
    res = -c * _x                              # бо x < 0
    x0 = rng.choice([-2, -3])
    val = res.subs(_x, x0)
    return Question(
        key="mz_simplify_sign",
        statement=(
            rf"Відомо, що $x < 0$. Спростіть вираз:"
            + "\n" + rf"$$ {_root_tex(n, f'{c**n}x^{{{n}}}')} $$"
            + r"Корінь парного степеня невід'ємний: "
            r"$\sqrt[2k]{a^{2k}} = |a|$. Розкрийте модуль, пам'ятаючи, що $x$ "
            "від'ємний."
            + f"\nПотім обчисліть значення при $x = {x0}$."
        ),
        parts=[
            Part("simp", "спрощений вираз =", res, kind="expr", points=1),
            Part(
                "val", rf"значення при $x={x0}$ =", val, points=1,
                carry=lambda prev: (
                    prev["simp"].subs(_x, x0)
                    if getattr(prev["simp"], "has", lambda _v: False)(_x) else None
                ),
                carry_from=("simp",),
            ),
        ],
        seconds=130,
        params={"n": n, "c": c, "x0": x0},
    )


# =========================================================================
#  ЗАДАЧІ З ГРАФІКАМИ
# =========================================================================

@template("mz_graph_roots_count")
def _graph_roots_count(rng: random.Random) -> Question:
    r"""Вправа 2.9: установити ГРАФІЧНО кількість коренів рівняння $x^n = kx+b$.

    Малюємо обидва графіки; корені — абсциси точок перетину."""
    # добираємо цілі точки перетину, щоб їх було видно на рисунку
    r1, r2 = rng.choice([(-2, 1), (-1, 2), (-2, 2), (0, 2), (-2, 0), (-1, 1),
                         (1, 1), (-1, -1), (2, 2)])   # рівні -> дотик, 1 корінь
    k, b = r1 + r2, -r1 * r2                   # пряма перетинає y=x² у r1 і r2
    cnt = 1 if r1 == r2 else 2
    svg = coordinate_plane(
        curves=[(lambda t: t * t, -2.6, 2.6)],
        lines=[(k, b)],
    )
    line_tex = (f"{k}x" if k not in (0, 1, -1) else ("x" if k == 1 else ("-x" if k == -1 else "")))
    if b:
        line_tex = (line_tex + (f" + {b}" if b > 0 else f" - {abs(b)}")) if line_tex else str(b)
    return Question(
        key="mz_graph_roots_count",
        statement=(
            r"На рисунку зображено графіки функцій $y = x^2$ та "
            rf"$y = {line_tex}$."
            + "\nЗа рисунком установіть, скільки коренів має рівняння "
            rf"$x^2 = {line_tex}$, і запишіть БІЛЬШИЙ із них."
        ),
        parts=[
            Part("cnt", "кількість коренів =", cnt, points=1),
            Part("big", "більший корінь =", max(r1, r2), points=1),
        ],
        seconds=120,
        params={"r1": r1, "r2": r2, "k": k, "b": b},
        svg=svg,
    )


@template("mz_graph_int_power")
def _graph_int_power(rng: random.Random) -> Question:
    r"""§3 з графіком: $y = x^{-n}$ — розрив у нулі й значення в точці."""
    n = rng.choice([1, 2])
    x0 = rng.choice([2, 3]) if n == 2 else rng.choice([2, 3, 4])
    val = sp.Rational(1, x0**n)
    svg = coordinate_plane(
        curves=[(lambda t: (1 / t**n) if t else None, -6.0, 6.0)],
    )
    ytex = rf"y = x^{{-{n}}}"
    xpow = "x" if n == 1 else f"x^{{{n}}}"
    return Question(
        key="mz_graph_int_power",
        statement=(
            rf"На рисунку — графік степеневої функції ${ytex}$, тобто "
            rf"$y = \dfrac{{1}}{{{xpow}}}$."
            + "\n1) При якому значенні $x$ функція НЕ визначена (графік має "
            "розрив)?"
            + rf" 2) Обчисліть $f({x0})$ (звичайним дробом)."
        ),
        parts=[
            Part("gap", "не визначена при $x$ =", 0, points=1),
            Part("val", rf"$f({x0})$ =", val, points=1),
        ],
        seconds=110,
        params={"n": n, "x0": x0},
        svg=svg,
    )
