"""Лекція 6 (вища математика): похідна – таблиця та ТЕХНІКИ диференціювання.

Обсяг за домовленістю з викладачем:
  * таблиця похідних: степенева, корінь, 1/x, sin, cos, tg, eˣ, aˣ, ln x;
  * правила: сума, сталий множник, ДОБУТОК, ЧАСТКА, СКЛАДЕНА функція
    (ланцюгове правило) з різними зовнішніми функціями;
  * друга похідна.

ЗАСТОСУВАНЬ похідної немає (їх ще не вивчали), і значення похідної в точці
НЕ шукаємо – увесь тест про саму техніку диференціювання.

Чому це стійке до списування:
  * відповідь – ВИРАЗ, а не число: одним числом не поділишся;
  * коефіцієнти в кожного студента свої, тож і похідна своя;
  * задачі багатокрокові (u', v', потім y'), тобто передати треба весь ланцюг.

Грейдинг символьний, тож приймається будь-яка еквівалентна форма: і розкритий
добуток, і нерозкритий, і e^x, і exp(x), і 1/cos²x замість 1+tg²x.
"""

from __future__ import annotations

import random

import sympy as sp

from engine import Part, Question, template

_x = sp.Symbol("x")

# Підказка про ввід – щоб не гадали, як писати експоненту й логарифм.
_INPUT_HINT = "(Позначення для введення: e^x або exp(x), ln(x), sin(x), cos(x), tg(x).)"


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


def _signed(v: int) -> str:
    if v == 0:
        return ""
    return f" + {v}" if v > 0 else f" - {abs(v)}"


def _d(expr):
    """Похідна у зручній для звіряння формі."""
    return sp.simplify(sp.diff(expr, _x))


# =========================================================================
#  ТАБЛИЦЯ ПОХІДНИХ
# =========================================================================

@template("dv_power_root")
def _power_root(rng: random.Random) -> Question:
    r"""Таблиця: степенева, корінь, $1/x$ – сума з трьох доданків."""
    a, n = rng.choice([2, 3, 4]), rng.choice([3, 4, 5])
    b = rng.choice([2, 4, 6])
    c = rng.choice([3, 5, 7])
    f = a * _x**n + b * sp.sqrt(_x) + c / _x
    d1 = sp.diff(a * _x**n, _x)
    dy = sp.diff(f, _x)
    ftex = rf"{a}x^{{{n}}} + {b}\sqrt{{x}} + \dfrac{{{c}}}{{x}}"
    return Question(
        key="dv_power_root",
        statement=(
            rf"Знайдіть похідну функції $y = {ftex}$."
            + "\n1) Спершу продиференціюйте лише перший доданок "
            rf"$\left({a}x^{{{n}}}\right)'$."
            + "\n2) Запишіть похідну всієї функції."
        ),
        parts=[
            Part("d1", rf"$\left({a}x^{{{n}}}\right)'$ =", d1, kind="expr", points=1),
            Part("dy", "$y'$ =", dy, kind="expr", points=1),
        ],
        seconds=110,
        params={"a": a, "n": n, "b": b, "c": c},
    )


@template("dv_trig_table")
def _trig_table(rng: random.Random) -> Question:
    r"""Таблиця тригонометричних: $\sin$, $\cos$, $\operatorname{tg}$."""
    a, b, c = rng.choice([2, 3, 5]), rng.choice([2, 3, 4]), rng.choice([1, 2, 3])
    ctex = "" if c == 1 else str(c)      # "1 tg x" не пишемо
    f = a * sp.sin(_x) + b * sp.cos(_x) + c * sp.tan(_x)
    d1 = sp.diff(a * sp.sin(_x) + b * sp.cos(_x), _x)
    dy = sp.diff(f, _x)
    return Question(
        key="dv_trig_table",
        statement=(
            rf"Знайдіть похідну функції "
            rf"$y = {a}\sin x + {b}\cos x + {ctex}\operatorname{{tg}} x$."
            + "\n1) Продиференціюйте перші два доданки."
            + "\n2) Запишіть похідну всієї функції "
            r"(нагадаємо: $(\operatorname{tg} x)' = \dfrac{1}{\cos^2 x}$)."
        ),
        parts=[
            Part("d1", rf"$\left({a}\sin x + {b}\cos x\right)'$ =", d1,
                 kind="expr", points=1),
            Part("dy", "$y'$ =", dy, kind="expr", points=1),
        ],
        seconds=110,
        params={"a": a, "b": b, "c": c},
    )


@template("dv_exp_log")
def _exp_log(rng: random.Random) -> Question:
    r"""Таблиця: $e^x$, $\ln x$, $a^x$ (де $(a^x)' = a^x \ln a$)."""
    a, b = rng.choice([2, 3, 4]), rng.choice([3, 5, 6])
    base = rng.choice([2, 3, 5])
    f = a * sp.exp(_x) + b * sp.log(_x) + base**_x
    d1 = sp.diff(base**_x, _x)
    dy = sp.diff(f, _x)
    return Question(
        key="dv_exp_log",
        statement=(
            rf"Знайдіть похідну функції $y = {a}e^x + {b}\ln x + {base}^x$."
            + "\n1) Спершу знайдіть "
            rf"$\left({base}^x\right)'$ (скористайтеся формулою "
            r"$(a^x)' = a^x \ln a$)."
            + "\n2) Запишіть похідну всієї функції."
            + "\n" + _INPUT_HINT
        ),
        parts=[
            Part("d1", rf"$\left({base}^x\right)'$ =", d1, kind="expr", points=1),
            Part("dy", "$y'$ =", dy, kind="expr", points=1),
        ],
        seconds=120,
        params={"a": a, "b": b, "base": base},
    )


# =========================================================================
#  ПРАВИЛА ДИФЕРЕНЦІЮВАННЯ
# =========================================================================

@template("dv_product")
def _product(rng: random.Random) -> Question:
    r"""Правило добутку: $(uv)' = u'v + uv'$ – три кроки."""
    if rng.random() < 0.5:
        a, b = rng.choice([2, 3]), rng.choice([-3, -1, 1, 3])
        u = a * _x**2 + b
        utex = _sum_tex([(a, "x^2"), (b, "")])
        v, vtex = sp.exp(_x), "e^x"
    else:
        a, b = rng.choice([2, 3, 4]), rng.choice([-2, -1, 1, 2])
        u = a * _x + b
        utex = _sum_tex([(a, "x"), (b, "")])
        v, vtex = sp.sin(_x), r"\sin x"
    du, dv = sp.diff(u, _x), sp.diff(v, _x)
    dy = sp.diff(u * v, _x)
    return Question(
        key="dv_product",
        statement=(
            rf"Знайдіть похідну добутку $y = \left({utex}\right)\cdot {vtex}$."
            + "\nСкористайтеся правилом $(uv)' = u'v + uv'$, де "
            rf"$u = {utex}$, $v = {vtex}$."
            + "\n1) Знайдіть $u'$. 2) Знайдіть $v'$. 3) Запишіть $y'$."
        ),
        parts=[
            Part("du", "$u'$ =", du, kind="expr", points=1),
            Part("dv", "$v'$ =", dv, kind="expr", points=1),
            Part(
                "dy", "$y'$ =", dy, kind="expr", points=1,
                carry=lambda prev: prev["du"] * v + u * prev["dv"],
                carry_from=("du", "dv"),
            ),
        ],
        seconds=150,
        params={"utex": utex, "vtex": vtex, "u": str(u), "v": str(v)},
    )


@template("dv_quotient")
def _quotient(rng: random.Random) -> Question:
    r"""Правило частки: $\left(\frac{u}{v}\right)' = \frac{u'v - uv'}{v^2}$."""
    a = rng.choice([1, 2, 3])
    b = rng.choice([-4, -3, -2, 2, 3, 4])
    u = _x**2 + a
    v = _x + b
    num = sp.expand(sp.diff(u, _x) * v - u * sp.diff(v, _x))
    dy = num / v**2          # чистіший еталон, ніж те, що дає simplify
    return Question(
        key="dv_quotient",
        statement=(
            rf"Знайдіть похідну частки $y = \dfrac{{x^2 + {a}}}{{x{_signed(b)}}}$."
            + "\nЗа правилом $\\left(\\dfrac{u}{v}\\right)' = "
            r"\dfrac{u'v - uv'}{v^2}$."
            + "\n1) Запишіть ЧИСЕЛЬНИК $u'v - uv'$ у розкритому вигляді."
            + "\n2) Запишіть усю похідну $y'$."
        ),
        parts=[
            Part("num", "$u'v - uv'$ =", num, kind="expr", points=1),
            Part(
                "dy", "$y'$ =", dy, kind="expr", points=1,
                carry=lambda prev: prev["num"] / v**2,
                carry_from=("num",),
            ),
        ],
        seconds=160,
        params={"a": a, "b": b},
    )


@template("dv_chain_power")
def _chain_power(rng: random.Random) -> Question:
    r"""Ланцюгове правило, зовнішня – степенева: $\left(u^n\right)' = n u^{n-1} u'$."""
    a = rng.choice([2, 3, 4])
    b = rng.choice([-3, -1, 1, 3])
    n = rng.choice([3, 4, 5])
    inner = a * _x**2 + b
    itex = _sum_tex([(a, "x^2"), (b, "")])
    du = sp.diff(inner, _x)
    dy = sp.diff(inner**n, _x)
    return Question(
        key="dv_chain_power",
        statement=(
            rf"Знайдіть похідну складеної функції $y = \left({itex}\right)^{{{n}}}$."
            + "\nЗа правилом $\\left(u^n\\right)' = n\\,u^{n-1}\\cdot u'$, де "
            rf"$u = {itex}$."
            + "\n1) Знайдіть похідну ВНУТРІШНЬОЇ функції $u'$."
            + "\n2) Запишіть $y'$."
        ),
        parts=[
            Part("du", "$u'$ =", du, kind="expr", points=1),
            Part(
                "dy", "$y'$ =", dy, kind="expr", points=1,
                carry=lambda prev: n * inner ** (n - 1) * prev["du"],
                carry_from=("du",),
            ),
        ],
        seconds=130,
        params={"a": a, "b": b, "n": n},
    )


@template("dv_product_chain")
def _product_chain(rng: random.Random) -> Question:
    r"""Добуток РАЗОМ із ланцюговим правилом: $y = x\sin kx$."""
    k = rng.choice([2, 3, 4])
    use_sin = rng.random() < 0.5
    v = sp.sin(k * _x) if use_sin else sp.cos(k * _x)
    vtex = rf"\sin {k}x" if use_sin else rf"\cos {k}x"
    dv = sp.diff(v, _x)
    dy = sp.diff(_x * v, _x)
    return Question(
        key="dv_product_chain",
        statement=(
            rf"Знайдіть похідну функції $y = x\,{vtex}$."
            + "\nТут потрібні ОБИДВА правила: добутку і складеної функції."
            + "\n" + rf"1) Спершу знайдіть $\left({vtex}\right)'$."
            + "\n2) Запишіть $y'$."
        ),
        parts=[
            Part("dv", rf"$\left({vtex}\right)'$ =", dv, kind="expr", points=1),
            Part(
                "dy", "$y'$ =", dy, kind="expr", points=1,
                carry=lambda prev: v + _x * prev["dv"],
                carry_from=("dv",),
            ),
        ],
        seconds=150,
        params={"k": k, "use_sin": use_sin},
    )


@template("dv_chain_exp")
def _chain_exp(rng: random.Random) -> Question:
    r"""Ланцюгове правило, зовнішня – показникова: $\left(e^u\right)' = e^u u'$."""
    a = rng.choice([2, 3, 4])
    b = rng.choice([-3, -1, 1, 3])
    inner = a * _x**2 + b
    itex = _sum_tex([(a, "x^2"), (b, "")])
    du = sp.diff(inner, _x)
    dy = sp.diff(sp.exp(inner), _x)
    return Question(
        key="dv_chain_exp",
        statement=(
            rf"Знайдіть похідну функції $y = e^{{{itex}}}$."
            + "\nЗа правилом $\\left(e^u\\right)' = e^u\\cdot u'$."
            + "\n1) Знайдіть $u'$. 2) Запишіть $y'$."
            + "\n" + _INPUT_HINT
        ),
        parts=[
            Part("du", "$u'$ =", du, kind="expr", points=1),
            Part(
                "dy", "$y'$ =", dy, kind="expr", points=1,
                carry=lambda prev: sp.exp(inner) * prev["du"],
                carry_from=("du",),
            ),
        ],
        seconds=120,
        params={"a": a, "b": b},
    )


@template("dv_chain_sqrt")
def _chain_sqrt(rng: random.Random) -> Question:
    r"""Ланцюгове правило, зовнішня – корінь:
    $\left(\sqrt{u}\right)' = \dfrac{u'}{2\sqrt{u}}$."""
    a = rng.choice([3, 5, 7])
    b = rng.choice([1, 2, 4])
    inner = a * _x + b
    itex = _sum_tex([(a, "x"), (b, "")])
    du = sp.diff(inner, _x)
    dy = sp.simplify(sp.diff(sp.sqrt(inner), _x))
    return Question(
        key="dv_chain_sqrt",
        statement=(
            rf"Знайдіть похідну функції $y = \sqrt{{{itex}}}$."
            + "\nЗа правилом $\\left(\\sqrt{u}\\right)' = "
            r"\dfrac{u'}{2\sqrt{u}}$."
            + "\n1) Знайдіть $u'$. 2) Запишіть $y'$."
        ),
        parts=[
            Part("du", "$u'$ =", du, kind="expr", points=1),
            Part(
                "dy", "$y'$ =", dy, kind="expr", points=1,
                carry=lambda prev: prev["du"] / (2 * sp.sqrt(inner)),
                carry_from=("du",),
            ),
        ],
        seconds=130,
        params={"a": a, "b": b},
    )


@template("dv_chain_ln")
def _chain_ln(rng: random.Random) -> Question:
    r"""Ланцюгове правило, зовнішня – логарифм:
    $\left(\ln u\right)' = \dfrac{u'}{u}$."""
    a = rng.choice([2, 3, 5])
    b = rng.choice([-4, -2, 1, 3])
    n = rng.choice([1, 2])
    inner = a * _x**n + b if n == 2 else a * _x + b
    itex = _sum_tex([(a, "x^2" if n == 2 else "x"), (b, "")])
    du = sp.diff(inner, _x)
    dy = sp.simplify(sp.diff(sp.log(inner), _x))
    return Question(
        key="dv_chain_ln",
        statement=(
            rf"Знайдіть похідну функції $y = \ln\left({itex}\right)$."
            + "\nЗа правилом $\\left(\\ln u\\right)' = \\dfrac{u'}{u}$."
            + "\n1) Знайдіть $u'$. 2) Запишіть $y'$."
        ),
        parts=[
            Part("du", "$u'$ =", du, kind="expr", points=1),
            Part(
                "dy", "$y'$ =", dy, kind="expr", points=1,
                carry=lambda prev: prev["du"] / inner,
                carry_from=("du",),
            ),
        ],
        seconds=120,
        params={"a": a, "b": b, "n": n},
    )


# =========================================================================
#  ДРУГА ПОХІДНА
# =========================================================================

@template("dv_second_poly")
def _second_poly(rng: random.Random) -> Question:
    r"""Друга похідна многочлена: $y'' = (y')'$."""
    a = rng.choice([1, 2, 3])
    b = rng.choice([-5, -3, 2, 4])
    c = rng.choice([-4, -2, 3, 6])
    f = a * _x**4 + b * _x**3 + c * _x**2
    d1, d2 = sp.expand(sp.diff(f, _x)), sp.expand(sp.diff(f, _x, 2))
    ftex = _sum_tex([(a, "x^4"), (b, "x^3"), (c, "x^2")])
    return Question(
        key="dv_second_poly",
        statement=(
            rf"Дано функцію $y = {ftex}$."
            + "\nЗнайдіть першу і другу похідні (друга – це похідна від першої)."
        ),
        parts=[
            Part("d1", "$y'$ =", d1, kind="expr", points=1),
            Part(
                "d2", "$y''$ =", d2, kind="expr", points=1,
                carry=lambda prev: sp.diff(prev["d1"], _x),
                carry_from=("d1",),
            ),
        ],
        seconds=130,
        params={"a": a, "b": b, "c": c},
    )


@template("dv_second_trig")
def _second_trig(rng: random.Random) -> Question:
    r"""Друга похідна тригонометричної: $y = a\sin kx \Rightarrow
    y'' = -ak^2\sin kx$."""
    a = rng.choice([2, 3, 4])
    k = rng.choice([2, 3])
    use_sin = rng.random() < 0.5
    f = a * (sp.sin(k * _x) if use_sin else sp.cos(k * _x))
    d1, d2 = sp.diff(f, _x), sp.diff(f, _x, 2)
    ftex = rf"{a}\sin {k}x" if use_sin else rf"{a}\cos {k}x"
    return Question(
        key="dv_second_trig",
        statement=(
            rf"Дано функцію $y = {ftex}$."
            + "\nЗнайдіть першу і другу похідні (не забудьте про множник від "
            "внутрішньої функції на кожному кроці)."
        ),
        parts=[
            Part("d1", "$y'$ =", d1, kind="expr", points=1),
            Part(
                "d2", "$y''$ =", d2, kind="expr", points=1,
                carry=lambda prev: sp.diff(prev["d1"], _x),
                carry_from=("d1",),
            ),
        ],
        seconds=130,
        params={"a": a, "k": k, "use_sin": use_sin},
    )
