"""Тригонометрія, друга половина §2 Мерзляка (математика, 10 клас).

Обсяг – рівно пункти підручника, яких немає в банку trigonometry.py
(той покриває п.8–12 і п.14 – коло, тотожності, зведення, графіки):
  * п.13 «Формули додавання»: згортання сум у функцію одного кута, точні
    значення некруглих кутів (15°, 75°, 105°), формули подвійного аргументу;
  * п.15 «Рівняння cos x = b» і п.16 «Рівняння sin x = b і tg x = b»:
    аркфункції табличних значень (зокрема від'ємних), корені на проміжку,
    кількість коренів, серії;
  * п.17 «Тригонометричні рівняння, які зводяться до алгебраїчних»:
    квадратне відносно sin/cos і однорідне першого степеня.

ПРО ВИГЛЯД ВІДПОВІДІ. Парсер рушія знає sin, cos, tg і аркфункції, а звіряє
значення, тож «arccos(1/2)» чи переписана в радіанах умова дорівнювали б
еталону. Тому поля, де відповіддю є обчислене число або кут, ВІДМОВЛЯЮТЬ у
прийомі вводу з тригонометричними чи арк-функціями (reject): обчислити – це
і є задача. Корені вводяться виразами з pi: 7pi/6, -pi/3, 2pi/3.

Кути в задачах на формули – у градусах, як у вправах 13.x і 14.5–14.8
підручника; корені рівнянь – у радіанах, як у п.15–17.
"""

import random
import re

import sympy as sp

from app.bank.plotting import unit_circle
from engine import Part, Question, template

_TG = r"\operatorname{tg}"

_HINT_NUM = ("(Відповіді – числа. Корінь позначається sqrt(): наприклад, "
             "sqrt(3)/2 чи (sqrt(6)-sqrt(2))/4.)")
_HINT_ROOTS = ("(Кути вводьте виразами з pi: 7pi/6, -pi/3, 2pi/3. "
               "Аркфункції в відповіді лишати не можна – обчисліть їх.)")

_ARC_RE = re.compile(r"a(sin|cos|tan)|arc", re.IGNORECASE)
_TRIG_RE = re.compile(r"sin|cos|tan|tg|cot|ctg", re.IGNORECASE)


def _no_arc(_value, raw: str):
    """Корінь має бути обчислений: аркфункцію в відповіді не приймаємо."""
    if _ARC_RE.search(raw):
        return "обчисліть значення: аркфункції в відповіді лишати не можна"
    return None


def _plain(_value, raw: str):
    """Відповідь – число: тригонометрії й аркфункцій у вводі бути не має."""
    if _ARC_RE.search(raw):
        return "обчисліть значення: аркфункції в відповіді лишати не можна"
    if _TRIG_RE.search(raw):
        return "доведіть обчислення до числа: sin, cos і tg у відповіді не потрібні"
    return None


def _honest_angle(value, lo, hi, *, forbid=()):
    """Кут зі СВОЄЇ попередньої відповіді: число в (lo; hi), не з заборонених.

    Перенесення помилки не має підтверджувати себе самого (див. _honest у
    probability.py): значення, з якого перерахунок дав би тотожність, і все,
    що не схоже на кут, відкидаємо – тоді звіряння йде з чесним еталоном.
    """
    if value is None:
        return None
    try:
        v = sp.nsimplify(value, [sp.pi])
        f = float(v)
    except (TypeError, ValueError):
        return None
    if not (float(lo) < f < float(hi)):
        return None
    for bad in forbid:
        if v == bad:
            return None
    return v


def _deg(n) -> str:
    return rf"{n}^\circ"


def _kpi(k: int) -> str:
    """k*pi у LaTeX: без одиниці перед pi."""
    return r"\pi" if k == 1 else rf"{k}\pi"


# --------------------------------------------------------------------------
# п.13. Формули додавання
# --------------------------------------------------------------------------

# Цілі градуси, що дають табличний кут у сумі чи різниці. Самі доданки
# НЕтабличні, тож єдиний шлях – згорнути формулою додавання.
_TARGETS = [30, 45, 60, 120, 135, 150]


def _split_angle(rng: random.Random, target: int, diff: bool):
    """target = A − B (diff) або A + B: обидва доданки нетабличні."""
    while True:
        b = rng.randrange(7, 39)
        a = target + b if diff else target - b
        if a <= 0 or a % 15 == 0 or b % 15 == 0 or a == b:
            continue
        return a, b


@template("tq_addition")
def _addition(rng: random.Random) -> Question:
    """Формули додавання (п.13; вправи на кшталт 14.7–14.8 і задача 1 п.13).

    1–2) згорнути суму добутків у функцію одного кута: кути в умові
         нетабличні, тож переписати чи порахувати «в лоб» не вийде;
    3) точне значення sin/cos кута 15°, 75° чи 105° через розклад на
       табличні доданки – відповідь із радикалами.
    """
    # 1) синус суми або різниці
    sin_diff = rng.random() < 0.5
    t1 = rng.choice(_TARGETS)
    a1, b1 = _split_angle(rng, t1, sin_diff)
    sign1 = "-" if sin_diff else "+"
    expr1 = (rf"\sin {_deg(a1)} \cos {_deg(b1)} {sign1} "
             rf"\cos {_deg(a1)} \sin {_deg(b1)}")
    ans1 = sp.sin(sp.rad(t1))

    # 2) косинус різниці або суми – і значення, відмінне від першого
    while True:
        cos_sum = rng.random() < 0.5
        t2 = rng.choice(_TARGETS)
        ans2 = sp.cos(sp.rad(t2))
        if ans2 != ans1:
            break
    a2, b2 = _split_angle(rng, t2, not cos_sum)
    sign2 = "-" if cos_sum else "+"
    expr2 = (rf"\cos {_deg(a2)} \cos {_deg(b2)} {sign2} "
             rf"\sin {_deg(a2)} \sin {_deg(b2)}")

    # 3) точне значення: 15°, 75° або 105°
    t3 = rng.choice([15, 75, 105])
    f3_is_sin = rng.random() < 0.5
    f3name = r"\sin" if f3_is_sin else r"\cos"
    ans3 = sp.sin(sp.rad(t3)) if f3_is_sin else sp.cos(sp.rad(t3))
    split3 = {15: "45^\\circ - 30^\\circ", 75: "45^\\circ + 30^\\circ",
              105: "60^\\circ + 45^\\circ"}[t3]

    return Question(
        key="tq_addition",
        statement=(
            "Застосуйте формули додавання."
            + "\n" + rf"1) Обчисліть ${expr1}$."
            + "\n" + rf"2) Обчисліть ${expr2}$."
            + "\n" + rf"3) Обчисліть ${f3name} {_deg(t3)}$ точно, розклавши "
            rf"кут: ${t3}^\circ = {split3}$."
            + "\n" + _HINT_NUM
        ),
        parts=[
            Part("fold_sin", "1)", ans1, points=1, reject=_plain),
            Part("fold_cos", "2)", ans2, points=1, reject=_plain),
            Part("exact", rf"3) ${f3name} {_deg(t3)}$ =", ans3, points=1,
                 reject=_plain),
        ],
        seconds=220,
        params={"t1": t1, "a1": a1, "b1": b1, "sin_diff": sin_diff,
                "t2": t2, "a2": a2, "b2": b2, "cos_sum": cos_sum,
                "t3": t3, "f3_is_sin": f3_is_sin},
    )


# --------------------------------------------------------------------------
# п.13. Формули подвійного аргументу
# --------------------------------------------------------------------------

# Кути, подвоєння яких дає табличний: градусні й радіанні порівну.
_HALF = [("deg", 15), ("deg", 75), ("deg", 105),
         ("rad", (1, 8)), ("rad", (1, 12)), ("rad", (5, 12))]

_TRIPLES = [(3, 4, 5), (4, 3, 5), (5, 12, 13), (12, 5, 13), (8, 15, 17),
            (15, 8, 17), (7, 24, 25), (20, 21, 29)]


def _half_tex(kind, val):
    if kind == "deg":
        return _deg(val), sp.rad(val)
    num, den = val
    return rf"\dfrac{{{num if num > 1 else ''}\pi}}{{{den}}}", sp.pi * num / den


@template("tq_double")
def _double(rng: random.Random) -> Question:
    """Формули подвійного аргументу (п.13, друга частина).

    1) згорнути $2\\sin\\alpha\\cos\\alpha$ у синус подвійного кута;
    2) згорнути вираз у косинус подвійного кута – кістяк чергується між
       $\\cos^2-\\sin^2$, $1-2\\sin^2$ і $2\\cos^2-1$;
    3) за даним sin або cos знайти $\\cos 2\\alpha$, не шукаючи сам кут, –
       формули $1-2\\sin^2$ і $2\\cos^2-1$ працюють без чверті.
    """
    k1, v1 = rng.choice(_HALF)
    tex1, rad1 = _half_tex(k1, v1)
    ans1 = sp.sin(2 * rad1)

    while True:
        k2, v2 = rng.choice(_HALF)
        if (k2, v2) != (k1, v1):
            break
    tex2, rad2 = _half_tex(k2, v2)
    shape2 = rng.choice(["diff", "one_minus", "two_minus"])
    if shape2 == "diff":
        expr2 = rf"\cos^2 {tex2} - \sin^2 {tex2}"
    elif shape2 == "one_minus":
        expr2 = rf"1 - 2\sin^2 {tex2}"
    else:
        expr2 = rf"2\cos^2 {tex2} - 1"
    ans2 = sp.cos(2 * rad2)

    p, q, h = rng.choice(_TRIPLES)
    given_sin = rng.random() < 0.5
    sign = rng.choice([1, -1])
    given = sp.Rational(sign * p, h)
    if given_sin:
        known = rf"\sin\alpha = {sp.latex(given)}"
        ans3 = 1 - 2 * given**2
    else:
        known = rf"\cos\alpha = {sp.latex(given)}"
        ans3 = 2 * given**2 - 1

    return Question(
        key="tq_double",
        statement=(
            "Застосуйте формули подвійного аргументу."
            + "\n" + rf"1) Обчисліть $2 \sin {tex1} \cos {tex1}$."
            + "\n" + rf"2) Обчисліть ${expr2}$."
            + "\n" + rf"3) Відомо, що ${known}$. Знайдіть $\cos 2\alpha$, "
            "не шукаючи сам кут."
            + "\n" + _HINT_NUM
        ),
        parts=[
            Part("sin2", "1)", ans1, points=1, reject=_plain),
            Part("cos2", "2)", ans2, points=1, reject=_plain),
            Part("from_given", r"3) $\cos 2\alpha$ =", ans3, points=1,
                 reject=_plain),
        ],
        seconds=220,
        params={"half1": (k1, v1), "half2": (k2, v2), "shape2": shape2,
                "p": p, "h": h, "sign": sign, "given_sin": given_sin},
    )


# --------------------------------------------------------------------------
# п.15–16. Аркфункції
# --------------------------------------------------------------------------

_COS_SIN_ARGS = [sp.Rational(1, 2), sp.sqrt(2) / 2, sp.sqrt(3) / 2,
                 sp.Integer(0), sp.Integer(1)]
_TG_ARGS = [sp.sqrt(3) / 3, sp.Integer(1), sp.sqrt(3)]


@template("tq_arc")
def _arc(rng: random.Random) -> Question:
    """Значення аркфункцій (означення в п.15 і п.16).

    Три значення: арккосинус, арксинус, арктангенс. Хоч один аргумент
    від'ємний – там і перевіряється розуміння проміжків: arccos(-b) йде
    через pi - arccos b, а arcsin(-b) і arctg(-b) – просто з мінусом.
    """
    while True:
        b_cos = rng.choice(_COS_SIN_ARGS) * rng.choice([1, -1])
        b_sin = rng.choice(_COS_SIN_ARGS) * rng.choice([1, -1])
        b_tg = rng.choice(_TG_ARGS) * rng.choice([1, -1])
        negatives = sum(1 for b in (b_cos, b_sin, b_tg) if b < 0)
        answers = (sp.acos(b_cos), sp.asin(b_sin), sp.atan(b_tg))
        # хоч один від'ємний аргумент і всі відповіді різні
        if negatives >= 1 and len(set(answers)) == 3:
            break
    a_cos, a_sin, a_tg = answers

    return Question(
        key="tq_arc",
        statement=(
            "Обчисліть (нагадаємо: арккосинус лежить у $[0;\\ \\pi]$, "
            r"арксинус – у $\left[-\frac{\pi}{2};\ \frac{\pi}{2}\right]$, "
            r"арктангенс – у $\left(-\frac{\pi}{2};\ \frac{\pi}{2}\right)$)."
            + "\n" + rf"1) $\arccos\left({sp.latex(b_cos)}\right)$"
            + "\n" + rf"2) $\arcsin\left({sp.latex(b_sin)}\right)$"
            + "\n" + rf"3) $\operatorname{{arctg}}\left({sp.latex(b_tg)}\right)$"
            + "\n" + _HINT_ROOTS
        ),
        parts=[
            Part("acos", "1)", a_cos, kind="expr", points=1, reject=_no_arc),
            Part("asin", "2)", a_sin, kind="expr", points=1, reject=_no_arc),
            Part("atg", "3)", a_tg, kind="expr", points=1, reject=_no_arc),
        ],
        seconds=200,
        params={"b_cos": str(b_cos), "b_sin": str(b_sin), "b_tg": str(b_tg)},
    )


# --------------------------------------------------------------------------
# п.15. Рівняння cos x = b – ІНТЕРАКТИВНЕ КОЛО
# --------------------------------------------------------------------------

_COS_B = [sp.Rational(1, 2), -sp.Rational(1, 2), sp.sqrt(2) / 2,
          -sp.sqrt(2) / 2, sp.sqrt(3) / 2, -sp.sqrt(3) / 2]

# Проміжок третього пункту -> його єдиний корінь як функція від alpha.
# На кожному з цих проміжків рівняння cos x = b (0 < alpha < pi) має рівно
# один корінь – це перевіряє test_eq_cos_unique_root_on_interval.
_COS_INTERVALS = [
    (r"[-\pi;\ 0]", lambda a: -a),
    (r"[2\pi;\ 3\pi]", lambda a: 2 * sp.pi + a),
    (r"[-2\pi;\ -\pi]", lambda a: a - 2 * sp.pi),
]


@template("tq_eq_cos")
def _eq_cos(rng: random.Random) -> Question:
    """Рівняння cos x = b на інтерактивному колі (п.15).

    Два корені на $[0; 2\\pi)$ – це дві точки кола з однаковою абсцисою.
    Менший корінь можна клацнути прямо на колі (клац вписує кут у перше
    поле – так само, як у tr_circle_locate). Третій пункт – корінь на
    іншому періоді: перевіряє, що студент володіє серією $\\pm\\alpha +
    2\\pi n$, а не лише малюнком.
    """
    b = rng.choice(_COS_B)
    alpha = sp.acos(b)                       # менший корінь, (0; pi)
    bigger = 2 * sp.pi - alpha
    which, root_of = rng.choice(_COS_INTERVALS)
    ans3 = root_of(alpha)

    def carry_bigger(prev):
        own = _honest_angle(prev.get("less"), 0, 2 * sp.pi, forbid=(sp.pi, alpha))
        return None if own is None else 2 * sp.pi - own

    def carry_third(prev):
        own = _honest_angle(prev.get("less"), 0, sp.pi, forbid=(alpha,))
        return None if own is None else root_of(own)

    return Question(
        key="tq_eq_cos",
        statement=(
            rf"Розв'яжіть рівняння $\cos x = {sp.latex(b)}$."
            + "\n" + r"1) Укажіть МЕНШИЙ корінь із проміжку $[0;\ 2\pi)$: "
            "знайдіть відповідну точку на колі й клацніть по ній – кут "
            "впишеться в поле, де стоїть курсор (спочатку це перше поле; "
            "можна й набрати вручну)."
            + "\n" + r"2) Укажіть більший корінь із проміжку $[0;\ 2\pi)$ – "
            "теж можна кліком: торкніться другого поля й клацніть точку."
            + "\n" + rf"3) Укажіть корінь рівняння з проміжку ${which}$."
            + "\n" + _HINT_ROOTS
        ),
        parts=[
            Part("less", "1)", alpha, kind="expr", points=1, reject=_no_arc),
            Part("more", "2)", bigger, kind="expr", points=1, reject=_no_arc,
                 carry=carry_bigger, carry_from=("less",)),
            Part("third", "3)", ans3, kind="expr", points=1, reject=_no_arc,
                 carry=carry_third, carry_from=("less",)),
        ],
        seconds=240,
        svg=unit_circle(pickable=True),
        params={"b": str(b), "interval": which},
    )


# --------------------------------------------------------------------------
# п.16. Рівняння sin x = b і tg x = b
# --------------------------------------------------------------------------

_SIN_B = [sp.Rational(1, 2), -sp.Rational(1, 2), sp.sqrt(2) / 2,
          -sp.sqrt(2) / 2, sp.sqrt(3) / 2, -sp.sqrt(3) / 2]


def _sin_roots_on(b, hi):
    """Корені sin x = b на [0; hi] перебором серій – для еталона кількості."""
    alpha = sp.asin(b)
    roots = set()
    for n in range(-2, 6):
        for x in (alpha + 2 * sp.pi * n, sp.pi - alpha + 2 * sp.pi * n):
            if 0 <= float(x) <= float(hi) + 1e-12:
                roots.add(sp.nsimplify(x, [sp.pi]))
    return sorted(roots, key=float)


@template("tq_eq_simple")
def _eq_simple(rng: random.Random) -> Question:
    """Найпростіші рівняння sin x = b або tg x = b (п.16) – чергуються.

    sin: арксинус (буває від'ємний), найменший додатний корінь і кількість
    коренів на $[0; K\\pi]$ – вона, на відміну від косинуса, залежить від
    знака b, тож її не вгадаєш за довжиною проміжку.
    tg: арктангенс, найменший додатний корінь і корінь на $(K\\pi; (K+1)\\pi)$ –
    у тангенса він на кожному періоді рівно один.
    """
    is_sin = rng.random() < 0.5
    if is_sin:
        b = rng.choice(_SIN_B)
        alpha = sp.asin(b)
        least = alpha if b > 0 else sp.pi - alpha      # найменший додатний
        # k лише НЕПАРНЕ: тоді коренів k+1 при b > 0 і k-1 при b < 0, тобто
        # відповідь ніколи не дорівнює надрукованому k (при парному k вона
        # збігалася б із ним – безплатний бал за переписане число умови).
        k = rng.choice([3, 5])
        roots = _sin_roots_on(b, k * sp.pi)
        head = rf"Розв'яжіть рівняння $\sin x = {sp.latex(b)}$."
        q1 = rf"1) Обчисліть $\arcsin\left({sp.latex(b)}\right)$."
        q3 = (rf"3) Скільки коренів має рівняння на проміжку "
              rf"$[0;\ {k}\pi]$?")
        parts = [
            Part("arc", "1)", alpha, kind="expr", points=1, reject=_no_arc),
            Part("least", "2)", least, kind="expr", points=1, reject=_no_arc),
            Part("count", "3)", sp.Integer(len(roots)), points=1),
        ]
        params = {"fn": "sin", "b": str(b), "k": k, "count": len(roots)}
    else:
        b = rng.choice(_TG_ARGS) * rng.choice([1, -1])
        alpha = sp.atan(b)
        least = alpha if b > 0 else sp.pi + alpha
        k = rng.choice([1, 2, 3])
        on_interval = least + k * sp.pi if b > 0 else alpha + (k + 1) * sp.pi
        head = rf"Розв'яжіть рівняння ${_TG}\,x = {sp.latex(b)}$."
        q1 = rf"1) Обчисліть $\operatorname{{arctg}}\left({sp.latex(b)}\right)$."
        q3 = (rf"3) Укажіть корінь рівняння з проміжку "
              rf"$({_kpi(k)};\ {_kpi(k + 1)})$ – він там один.")

        def carry_interval(prev, _k=k):
            own = _honest_angle(prev.get("least"), 0, sp.pi, forbid=(least,))
            return None if own is None else own + _k * sp.pi

        parts = [
            Part("arc", "1)", alpha, kind="expr", points=1, reject=_no_arc),
            Part("least", "2)", least, kind="expr", points=1, reject=_no_arc),
            Part("on_interval", "3)", on_interval, kind="expr", points=1,
                 reject=_no_arc, carry=carry_interval, carry_from=("least",)),
        ]
        params = {"fn": "tg", "b": str(b), "k": k}

    return Question(
        key="tq_eq_simple",
        statement=(
            head
            + "\n" + q1
            + "\n" + r"2) Укажіть найменший ДОДАТНИЙ корінь рівняння."
            + "\n" + q3
            + "\n" + _HINT_ROOTS
        ),
        parts=parts,
        seconds=240,
        params=params,
    )


# --------------------------------------------------------------------------
# п.17. Рівняння, які зводяться до алгебраїчних
# --------------------------------------------------------------------------

# Пари (t1, t2): t1 – завжди придатний табличний корінь квадратного рівняння,
# t2 – або теж придатний, або |t2| > 1 і серія відпадає (класика п.17).
_T_VALID = [sp.Rational(1, 2), -sp.Rational(1, 2), sp.Integer(1), sp.Integer(-1)]
_T_INVALID = [sp.Rational(3, 2), -sp.Rational(3, 2), sp.Integer(2),
              sp.Integer(-2), sp.Rational(5, 4)]


def _least_positive(fn: str, t):
    """Найменший додатний x, для якого sin x = t (чи cos x = t), t табличне."""
    if fn == "sin":
        table = {sp.Rational(1, 2): sp.pi / 6, -sp.Rational(1, 2): 7 * sp.pi / 6,
                 sp.Integer(1): sp.pi / 2, sp.Integer(-1): 3 * sp.pi / 2}
    else:
        table = {sp.Rational(1, 2): sp.pi / 3, -sp.Rational(1, 2): 2 * sp.pi / 3,
                 sp.Integer(1): 2 * sp.pi, sp.Integer(-1): sp.pi}
    return table.get(t)


@template("tq_eq_quadratic")
def _eq_quadratic(rng: random.Random) -> Question:
    """Квадратне відносно sin або cos (п.17, задача 2; вправи 17.1–17.2).

    Заміна t = sin x (cos x) дає квадратне рівняння. Хід перевіряється
    полями: корені квадратного; скільки з них узагалі дають розв'язки
    (|t| > 1 – серія відпадає, і це головна пастка пункту); найменший
    додатний корінь самого рівняння.
    """
    fn = rng.choice(["sin", "cos"])
    while True:
        t1 = rng.choice(_T_VALID)
        if not (fn == "cos" and t1 == 1):   # cos x = 1: додатний корінь аж 2pi
            break
    both_valid = rng.random() < 0.5
    while True:
        t2 = rng.choice(_T_VALID) if both_valid else rng.choice(_T_INVALID)
        if t2 != t1 and not (both_valid and fn == "cos" and t2 == 1):
            break
    lo, hi = min(t1, t2), max(t1, t2)

    # (t - t1)(t - t2) = 0 -> цілі коефіцієнти
    tt = sp.Symbol("t")
    poly = sp.expand((tt - t1) * (tt - t2))
    mult = sp.lcm([sp.fraction(c)[1] for c in poly.as_poly(tt).all_coeffs()])
    coeffs = [sp.Integer(c * mult) for c in poly.as_poly(tt).all_coeffs()]
    a, bb, c = coeffs
    if rng.random() < 0.5:                   # щоб старший не завжди був +
        a, bb, c = -a, -bb, -c
    fn_tex = r"\sin" if fn == "sin" else r"\cos"

    def term(coef, power):
        if coef == 0:
            return ""
        sign = "+" if coef > 0 else "-"
        mag = abs(coef)
        head = "" if (mag == 1 and power) else str(mag)
        if power == 2:
            body = rf"{head}\{'sin' if fn == 'sin' else 'cos'}^2 x"
        elif power == 1:
            body = rf"{head}{fn_tex} x"
        else:
            body = str(mag)
        return sign, body

    pieces = [term(a, 2), term(bb, 1), term(c, 0)]
    eq_tex = ""
    for i, piece in enumerate(p for p in pieces if p):
        sign, body = piece
        if i == 0:
            eq_tex += ("-" if sign == "-" else "") + body
        else:
            eq_tex += f" {sign} {body}"

    valid = [t for t in (t1, t2) if abs(t) <= 1]
    least = min((x for t in valid
                 for x in [_least_positive(fn, t)] if x is not None),
                key=float)

    def carry_series(prev):
        own = [prev.get("t_lo"), prev.get("t_hi")]
        try:
            vals = [sp.nsimplify(v) for v in own if v is not None]
            if len(vals) != 2 or set(vals) == {lo, hi}:
                return None
            return sp.Integer(sum(1 for v in vals if abs(float(v)) <= 1))
        except (TypeError, ValueError):
            return None

    def carry_least(prev):
        try:
            vals = [sp.nsimplify(v) for v in (prev.get("t_lo"), prev.get("t_hi"))
                    if v is not None]
            if len(vals) != 2 or set(vals) == {lo, hi}:
                return None
            xs = [_least_positive(fn, v) for v in vals if abs(float(v)) <= 1]
            xs = [x for x in xs if x is not None]
            return min(xs, key=float) if xs else None
        except (TypeError, ValueError):
            return None

    return Question(
        key="tq_eq_quadratic",
        statement=(
            rf"Розв'яжіть рівняння ${eq_tex} = 0$ заміною "
            rf"$t = {fn_tex} x$."
            + "\n" + r"1) Укажіть менший корінь квадратного рівняння."
            + "\n" + r"2) Укажіть більший корінь квадратного рівняння."
            + "\n" + rf"3) Скільки з цих значень $t$ дають корені рівняння "
            rf"${fn_tex} x = t$? (Згадайте область значень.)"
            + "\n" + r"4) Укажіть найменший ДОДАТНИЙ корінь даного рівняння."
            + "\n" + _HINT_ROOTS
        ),
        parts=[
            Part("t_lo", "1) менший $t$:", lo, points=1, reject=_plain),
            Part("t_hi", "2) більший $t$:", hi, points=1, reject=_plain),
            Part("series", "3) скільки придатних:", sp.Integer(len(valid)),
                 points=1, carry=carry_series, carry_from=("t_lo", "t_hi")),
            Part("least", "4) найменший додатний:", least, kind="expr",
                 points=1, reject=_no_arc, carry=carry_least,
                 carry_from=("t_lo", "t_hi")),
        ],
        seconds=260,
        params={"fn": fn, "t1": str(t1), "t2": str(t2),
                "both_valid": bool(both_valid),
                "coeffs": [int(a), int(bb), int(c)]},
    )


# Однорідне: a sin x + b cos x = 0. Пари (запис, tg x).
_HOMOGENEOUS = [
    ((1, -1), sp.Integer(1)),
    ((1, 1), sp.Integer(-1)),
    ((1, "-sqrt3"), sp.sqrt(3)),
    ((1, "sqrt3"), -sp.sqrt(3)),
    (("sqrt3", -1), sp.sqrt(3) / 3),
    (("sqrt3", 1), -sp.sqrt(3) / 3),
]


def _coef_tex(c) -> str:
    if c == 1:
        return ""
    if c == -1:
        return "-"
    if c == "sqrt3":
        return r"\sqrt{3}\,"
    if c == "-sqrt3":
        return r"-\sqrt{3}\,"
    return str(c)


@template("tq_eq_homogeneous")
def _eq_homogeneous(rng: random.Random) -> Question:
    """Однорідне рівняння першого степеня (п.17, вправа 17.3).

    Ділення на cos x (воно законне: якби cos x = 0, то з рівняння й
    sin x = 0, а разом вони нулями не бувають) зводить до tg x = r.
    Серію перевіряє третій пункт: корінь на даному періоді.
    """
    (ca, cb), r = rng.choice(_HOMOGENEOUS)
    alpha = sp.atan(r)
    least = alpha if r > 0 else sp.pi + alpha
    k = rng.choice([1, 2, 3])
    on_interval = least + k * sp.pi if r > 0 else alpha + (k + 1) * sp.pi
    eq_tex = rf"{_coef_tex(ca)}\sin x "
    eq_tex += "+" if (isinstance(cb, int) and cb > 0) or cb == "sqrt3" else "-"
    pos_cb = cb if not isinstance(cb, str) else cb.lstrip("-")
    eq_tex += rf" {_coef_tex(abs(cb) if isinstance(cb, int) else pos_cb)}\cos x"

    def carry_interval(prev, _k=k):
        own = _honest_angle(prev.get("least"), 0, sp.pi, forbid=(least,))
        return None if own is None else own + _k * sp.pi

    return Question(
        key="tq_eq_homogeneous",
        statement=(
            rf"Розв'яжіть рівняння ${eq_tex} = 0$. Поділіть обидві "
            r"частини на $\cos x$ (це законно: якби $\cos x = 0$, то з "
            r"рівняння випливало б і $\sin x = 0$, а разом вони в нуль не "
            "обертаються)."
            + "\n" + rf"1) Чому дорівнює ${_TG}\,x$?"
            + "\n" + r"2) Укажіть найменший ДОДАТНИЙ корінь рівняння."
            + "\n" + rf"3) Укажіть корінь рівняння з проміжку "
            rf"$({_kpi(k)};\ {_kpi(k + 1)})$ – він там один."
            + "\n" + _HINT_ROOTS
        ),
        parts=[
            Part("ratio", rf"1) ${_TG}\,x$ =", r, points=1, reject=_plain),
            Part("least", "2)", least, kind="expr", points=1, reject=_no_arc),
            Part("on_interval", "3)", on_interval, kind="expr", points=1,
                 reject=_no_arc, carry=carry_interval, carry_from=("least",)),
        ],
        seconds=240,
        params={"ca": str(ca), "cb": str(cb), "r": str(r), "k": k},
    )
