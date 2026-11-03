"""Тригонометрія: заняття 9, 10, 11 (I курс).

Обсяг рівно за інструктивно-методичними картами викладача:

  заняття 9  – радіанна міра кута; одиничне коло; означення sin, cos, tg, ctg
               через координати точки; знаки функцій по чвертях;
  заняття 10 – основні тотожності; формули зведення («правило конячки»);
  заняття 11 – періодичність; властивості та графіки; гармонічні коливання
               (амплітуда A, кутова частота omega, T = 2pi/|omega|).

Тест перевіряє РОЗУМІННЯ, а не таблицю значень. Три завдання тут неможливо
пройти, знаючи лише таблицю:
  * tr_circle_locate – дано умову на координати, точку треба знайти на колі
    самому (зворотний бік означення, і саме його зазвичай не розуміють);
  * tr_signs – чверть за знаками двох функцій (завдання* з ДЗ заняття 9);
  * tr_compare – порівняння без обчислення, самою лише монотонністю, де
    правильна відповідь буває «рівні».

Формули зведення розкладені на два питання «правила конячки» окремо: знак і
зміна назви. Хто вивчив результат напам'ять, а правила не зрозумів, це
покаже.

ПРО ЗМІННУ. Рушій пускає у відповіді лише x, y, t, тож там, де відповідь є
ВИРАЗОМ, в умові стоїть x замість alpha. Де відповідь числова – alpha, як у
конспекті.
"""

from __future__ import annotations

import math
import random

import sympy as sp

from app.bank.plotting import angle_tex, coordinate_plane, unit_circle
from engine import Part, Question, template

_x = sp.Symbol("x")

_TG = r"\operatorname{tg}"
_CTG = r"\operatorname{ctg}"

_HINT_EXPR = ("(Відповідь – вираз зі змінною x. Тангенс: tg(x), котангенс: "
              "ctg(x), число пі: pi.)")
_HINT_NUM = "(Відповіді – числа. Число пі позначається pi, корінь – sqrt().)"

# Кути кола, що НЕ лежать на осях: лише для них має сенс питати чверть і
# відношення ординати до абсциси.
_OFF_AXIS = [(1, 6), (1, 4), (1, 3), (2, 3), (3, 4), (5, 6),
             (7, 6), (5, 4), (4, 3), (5, 3), (7, 4), (11, 6)]


def _ang(num: int, den: int):
    """Кут у радіанах як точний вираз sympy."""
    return sp.pi * sp.Integer(num) / den


def _quarter(num: int, den: int) -> int:
    """Чверть, у якій лежить кут (для кутів не на осях)."""
    deg = 180.0 * num / den % 360.0
    return int(deg // 90) + 1


def _quarter_deg(deg: float) -> int:
    return int(deg % 360.0 // 90) + 1


def _sign(value) -> int:
    """Знак точного виразу: 1, -1 або 0."""
    v = float(sp.N(value))
    if abs(v) < 1e-9:
        return 0
    return 1 if v > 0 else -1


def _deg_tex(deg: int) -> str:
    return rf"{deg}^\circ"


def _num_or_none(value):
    """Число з попередньої відповіді студента; нуль і вирази зі змінними –
    не годяться для перенесення помилки (нуль самопідтвердний, змінна тут
    узагалі не на місці)."""
    if value is None:
        return None
    try:
        v = sp.sympify(value)
        if v.free_symbols or v == 0:
            return None
        float(sp.N(v))
    except Exception:  # noqa: BLE001
        return None
    return v


def _ratio(top, bottom):
    """Відношення двох попередніх відповідей, якщо обидві придатні."""
    a, b = _num_or_none(top), _num_or_none(bottom)
    if a is None or b is None:
        return None
    return sp.simplify(a / b)


def _ratio_on_circle(top, bottom):
    """Відношення власних синуса й косинуса студента – але лише якщо його
    пара справді лежить на одиничному колі.

    Без цієї умови поле діставалося б безплатно: хто написав усюди одиницю,
    дістав би tg = 1/1 = 1 і бал за третій крок. Перевірка не формальна, а по
    суті теми – основна тотожність sin^2 + cos^2 = 1 саме про це. Порядок
    аргументів задає, це tg чи ctg; сама умова кола симетрична.
    """
    a, b = _num_or_none(top), _num_or_none(bottom)
    if a is None or b is None:
        return None
    if sp.simplify(a**2 + b**2 - 1) != 0:
        return None
    return sp.simplify(a / b)


def _reciprocal(value):
    """Обернене до попередньої відповіді.

    Одиниця й мінус одиниця відкидаються: вони обернені самі до себе, тож
    ланцюжок підтверджував би сам себе. У піфагорових трійках катети різні,
    отже справжній tg ніколи не дорівнює +-1 – нічого правильного не
    втрачаємо.
    """
    v = _num_or_none(value)
    if v is None or v == 1 or v == -1:
        return None
    return sp.simplify(1 / v)


# =========================================================================
#  ЗАНЯТТЯ 9. РАДІАНИ, КОЛО, ЗНАКИ
# =========================================================================

@template("tr_radians")
def _radians(rng: random.Random) -> Question:
    """Переведення градуси <-> радіани і чверть кута (заняття 9, завдання 1-3).

    Найбазовіше, але третій пункт уже не формула: від'ємний кут або кут
    більший за оберт треба спершу звести, і тут видно, чи зрозуміле саме
    коло, а не правило множення на pi/180.
    """
    deg = rng.choice([30, 45, 75, 105, 120, 135, 150, 210, 225, 240, 300, 315, 330])
    num, den = rng.choice([(1, 6), (1, 4), (2, 3), (3, 4), (5, 6), (7, 6),
                           (5, 4), (4, 3), (5, 3), (7, 4), (11, 6)])
    # Кут для чверті: навмисно від'ємний або більший за повний оберт.
    odd = rng.choice([-100, -135, -200, -290, 400, 460, 530, 620, 700, -400])
    rad = sp.Rational(deg, 180) * sp.pi
    back = 180 * num // den if (180 * num) % den == 0 else sp.Rational(180 * num, den)
    return Question(
        key="tr_radians",
        statement=(
            rf"1) Переведіть кут ${_deg_tex(deg)}$ у радіани."
            + "\n" + rf"2) Переведіть кут ${angle_tex(num, den)}$ рад у градуси "
            r"(у відповідь запишіть лише число)."
            + "\n" + rf"3) У якій чверті лежить кут ${_deg_tex(odd)}$? "
            r"Запишіть номер чверті."
            + "\n" + _HINT_NUM
        ),
        parts=[
            Part("rad", "1) у радіанах:", rad, kind="expr", points=1),
            Part("deg", "2) у градусах:", sp.sympify(back), points=1),
            Part("quarter", "3) чверть:", sp.Integer(_quarter_deg(odd)), points=1),
        ],
        seconds=170,
        params={"deg": deg, "num": num, "den": den, "odd": odd,
                "quarter": _quarter_deg(odd)},
    )


@template("tr_circle_locate")
def _circle_locate(rng: random.Random) -> Question:
    """ІНТЕРАКТИВНЕ КОЛО: за умовою на координати знайти саму точку.

    Означення працює в обидва боки, але в підручнику й на дошці майже завжди
    йдуть від кута до координат. Тут навпаки: дано координату й знак другої,
    а кут треба знайти на колі. Таблицею значень це не береться – потрібно
    розуміти, де кут лежить.

    Точки на колі клікабельні: клац вписує кут у поле (так само, як це робить
    екранна клавіатура). Відповідь лишається звичайним виразом, тож рушій
    оцінювання тут ні до чого.
    """
    num, den = rng.choice(_OFF_AXIS)
    t = _ang(num, den)
    co, si = sp.cos(t), sp.sin(t)
    by_cos = rng.random() < 0.5
    if by_cos:
        known = rf"\cos\alpha = {sp.latex(co)}"
        other = r"\sin\alpha > 0" if _sign(si) > 0 else r"\sin\alpha < 0"
    else:
        known = rf"\sin\alpha = {sp.latex(si)}"
        other = r"\cos\alpha > 0" if _sign(co) > 0 else r"\cos\alpha < 0"
    # Що саме питати другим. Кутів поза осями дванадцять, тож без цього
    # чергування на шаблон припадало б лише два десятки наборів відповідей,
    # а в групі тридцять студентів.
    ask2 = rng.choice(["other", "tg", "ctg"])
    if ask2 == "other":
        ask2_tex = r"$\sin\alpha$" if by_cos else r"$\cos\alpha$"
        ask2_val = si if by_cos else co
    elif ask2 == "tg":
        ask2_tex = f"${_TG}" + r"\,\alpha$"
        ask2_val = sp.tan(t)
    else:
        ask2_tex = f"${_CTG}" + r"\,\alpha$"
        ask2_val = sp.cot(t)
    return Question(
        key="tr_circle_locate",
        statement=(
            rf"Відомо, що ${known}$ і ${other}$, причому "
            r"$\alpha \in [0;\ 2\pi)$."
            + "\nЗнайдіть цю точку на колі й клацніть по ній – кут впишеться "
            "в перше поле. Можна й просто набрати його вручну."
            + "\n" + r"1) Чому дорівнює кут $\alpha$?"
            + "\n" + rf"2) Чому дорівнює {ask2_tex}?"
            + "\n" + r"3) У якій чверті лежить кут $\alpha$?"
            + "\n" + _HINT_NUM
        ),
        parts=[
            Part("angle", r"1) $\alpha$ =", t, kind="expr", points=1),
            Part("other", f"2) {ask2_tex} =", ask2_val, points=1),
            Part("quarter", "3) чверть:", sp.Integer(_quarter(num, den)), points=1),
        ],
        seconds=200,
        svg=unit_circle(pickable=True),
        params={"num": num, "den": den, "by_cos": by_cos, "ask2": ask2,
                "quarter": _quarter(num, den)},
    )


@template("tr_circle_read")
def _circle_read(rng: random.Random) -> Question:
    """РИСУНОК: точка позначена на колі, записати її функції.

    Пряме означення заняття 9: косинус – абсциса, синус – ордината. Третім
    питаємо одне з чотирьох: тангенс, котангенс або координату симетричної
    точки.

    Чергування потрібне не лише для різноманіття. Кутів поза осями всього
    дванадцять, тож без нього на шаблон вийшло б дванадцять наборів
    відповідей – а в групі тридцять студентів. Симетрія ж тут не випадкова
    гостя: саме з неї на наступному занятті виводяться формули зведення.
    """
    num, den = rng.choice(_OFF_AXIS)
    t = _ang(num, den)
    co, si = sp.cos(t), sp.sin(t)
    kind = rng.choice(["tg", "ctg", "sym_x", "sym_y"])
    if kind == "tg":
        label, third = rf"${_TG}\,\alpha$", sp.tan(t)
        ask = rf"3) Чому дорівнює ${_TG}\,\alpha$?"
    elif kind == "ctg":
        label, third = rf"${_CTG}\,\alpha$", sp.cot(t)
        ask = rf"3) Чому дорівнює ${_CTG}\,\alpha$?"
    elif kind == "sym_x":
        label, third = r"ордината $P_1$", -si
        ask = (r"3) Точку $P$ відбили симетрично відносно осі $Ox$ і дістали "
               r"точку $P_1$. Чому дорівнює ордината точки $P_1$?")
    else:
        label, third = r"абсциса $P_1$", -co
        ask = (r"3) Точку $P$ відбили симетрично відносно осі $Oy$ і дістали "
               r"точку $P_1$. Чому дорівнює абсциса точки $P_1$?")

    def _third_carry(prev, _k=kind):
        if _k == "tg":
            return _ratio_on_circle(prev.get("sin"), prev.get("cos"))
        if _k == "ctg":
            return _ratio_on_circle(prev.get("cos"), prev.get("sin"))
        src = _num_or_none(prev.get("sin" if _k == "sym_x" else "cos"))
        return None if src is None else -src

    return Question(
        key="tr_circle_read",
        statement=(
            r"На одиничному колі точка $P$ отримана поворотом точки "
            r"$P_0(1;\ 0)$ на кут $\alpha$ (див. рисунок)."
            + "\n" + r"1) Чому дорівнює $\cos\alpha$?"
            + "\n" + r"2) Чому дорівнює $\sin\alpha$?"
            + "\n" + ask
            + "\n" + _HINT_NUM
        ),
        parts=[
            Part("cos", r"1) $\cos\alpha$ =", co, points=1),
            Part("sin", r"2) $\sin\alpha$ =", si, points=1),
            Part("third", f"3) {label} =", third, points=1,
                 carry=_third_carry, carry_from=("cos", "sin")),
        ],
        seconds=180,
        svg=unit_circle(marked=[(num, den)], radius_to=(num, den)),
        params={"num": num, "den": den, "kind": kind},
    )


@template("tr_signs")
def _signs(rng: random.Random) -> Question:
    """Знаки по чвертях, у тому числі у зворотний бік (заняття 9, завдання* ДЗ).

    Третій пункт – це і є розуміння: за знаками ДВОХ функцій назвати чверть.
    Кожна окремо лишає дві можливості, разом – рівно одну.
    """
    a = rng.choice([100, 120, 140, 160, 170, 200, 215, 250, 280, 310, 340, 350])
    b = rng.choice([110, 130, 190, 210, 230, 260, 290, 300, 320, 335])
    # Знак добутку вибираємо ЗАЗДАЛЕГІДЬ і під нього добираємо третій кут.
    # Інакше додатний випадав частіше, і відповідь «1» коштувала пів задачі.
    prod = rng.choice([1, -1])
    need = prod * _sign(sp.sin(sp.rad(a))) * _sign(sp.cos(sp.rad(b)))
    c = rng.choice([cc for cc in (115, 155, 195, 245, 265, 305, 325, 345)
                    if _sign(sp.tan(sp.rad(cc))) == need])
    # Другий пункт – кут у радіанах, а не той самий, що в добутку: інакше
    # відповідь на нього просто переписувалася б із розв'язання першого.
    rad_q = rng.choice(_OFF_AXIS)
    # Пара знаків, що однозначно задає чверть.
    quarter = rng.choice([1, 2, 3, 4])
    pair = rng.choice(["sin_ctg", "cos_tg", "sin_cos", "tg_sin"])
    mid = _ang(2 * quarter - 1, 4)                   # середина чверті
    names = {"sin_ctg": (r"\sin\alpha", _CTG + r"\,\alpha",
                         sp.sin(mid), sp.cot(mid)),
             "cos_tg": (r"\cos\alpha", _TG + r"\,\alpha",
                        sp.cos(mid), sp.tan(mid)),
             "sin_cos": (r"\sin\alpha", r"\cos\alpha",
                         sp.sin(mid), sp.cos(mid)),
             "tg_sin": (_TG + r"\,\alpha", r"\sin\alpha",
                        sp.tan(mid), sp.sin(mid))}
    n1, n2, v1, v2 = names[pair]
    cond = (f"${n1} {'>' if _sign(v1) > 0 else '<'} 0$ і "
            f"${n2} {'>' if _sign(v2) > 0 else '<'} 0$")
    return Question(
        key="tr_signs",
        statement=(
            rf"1) Визначте знак добутку $\sin {_deg_tex(a)} \cdot "
            rf"\cos {_deg_tex(b)} \cdot {_TG}\,{_deg_tex(c)}$. "
            r"Запишіть 1, якщо він додатний, і $-1$, якщо від'ємний."
            + "\n" + rf"2) У якій чверті лежить кут ${angle_tex(*rad_q)}$ рад?"
            + "\n" + rf"3) Відомо, що {cond}. У якій чверті лежить кут "
            r"$\alpha$?"
            + "\n" + _HINT_NUM
        ),
        parts=[
            Part("prod", "1) знак добутку:", sp.Integer(prod), points=1),
            Part("qb", "2) чверть:", sp.Integer(_quarter(*rad_q)), points=1),
            Part("quarter", "3) чверть:", sp.Integer(quarter), points=1),
        ],
        seconds=190,
        params={"a": a, "b": b, "c": c, "prod": prod, "pair": pair,
                "quarter": quarter, "rad_q": list(rad_q)},
    )


# =========================================================================
#  ЗАНЯТТЯ 10. ТОТОЖНОСТІ ТА ФОРМУЛИ ЗВЕДЕННЯ
# =========================================================================

# Піфагорові трійки: дають «гарні» дроби, як -8/17 у прикладі викладача.
_TRIPLES = [(3, 4, 5), (4, 3, 5), (5, 12, 13), (12, 5, 13), (8, 15, 17),
            (15, 8, 17), (7, 24, 25), (24, 7, 25), (20, 21, 29), (21, 20, 29)]


@template("tr_pythagorean")
def _pythagorean(rng: random.Random) -> Question:
    """Дано одну функцію і чверть – знайти решту (заняття 10, задача 1).

    Знак добувається не з формули, а з чверті: основна тотожність дає обидва
    варіанти, і вибір між ними – єдине місце, де видно розуміння.
    """
    p, q, h = rng.choice(_TRIPLES)
    quarter = rng.choice([1, 2, 3, 4])
    given_cos = rng.random() < 0.5
    sx = 1 if quarter in (1, 4) else -1               # знак косинуса
    sy = 1 if quarter in (1, 2) else -1               # знак синуса
    co = sx * sp.Rational(p, h)
    si = sy * sp.Rational(q, h)
    bounds = {1: (r"0", r"\dfrac{\pi}{2}"), 2: (r"\dfrac{\pi}{2}", r"\pi"),
              3: (r"\pi", r"\dfrac{3\pi}{2}"), 4: (r"\dfrac{3\pi}{2}", r"2\pi")}
    lo, hi = bounds[quarter]
    known = (rf"\cos\alpha = {sp.latex(co)}" if given_cos
             else rf"\sin\alpha = {sp.latex(si)}")
    ask = r"\sin\alpha" if given_cos else r"\cos\alpha"
    first = si if given_cos else co
    return Question(
        key="tr_pythagorean",
        statement=(
            rf"Відомо, що ${known}$, причому ${lo} < \alpha < {hi}$ "
            rf"({quarter} чверть)."
            + "\n" + rf"1) Знайдіть ${ask}$."
            + "\n" + rf"2) Знайдіть ${_TG}\,\alpha$."
            + "\n" + rf"3) Знайдіть ${_CTG}\,\alpha$."
            + "\n" + _HINT_NUM
        ),
        parts=[
            Part("first", rf"1) ${ask}$ =", first, points=1),
            # tg = sin/cos. Відоме з умови лишається знаменником або
            # чисельником залежно від того, що саме дали.
            Part("tg", rf"2) ${_TG}\,\alpha$ =", si / co, points=1,
                 carry=lambda prev, _c=given_cos, _co=co, _si=si: (
                     _ratio(prev.get("first"), _co) if _c
                     else _ratio(_si, prev.get("first"))),
                 carry_from=("first",)),
            Part("ctg", rf"3) ${_CTG}\,\alpha$ =", co / si, points=1,
                 carry=lambda prev: _reciprocal(prev.get("tg")),
                 carry_from=("tg",)),
        ],
        seconds=190,
        params={"p": p, "q": q, "h": h, "quarter": quarter,
                "given_cos": given_cos},
    )


# Кістяки на спрощення: (вираз, що питаємо на кроці 1, відповідь кроку 1).
# Вираз будуємо від множника a, тож результат у кожного студента свій.
def _simplify_shapes():
    s, c = sp.sin(_x), sp.cos(_x)
    tg, ctg = sp.tan(_x), sp.cot(_x)
    return [
        (r"\dfrac{1-\sin^{2}x}{\cos x}\cdot" + _TG + r"\,x",
         (1 - s**2) / c * tg, r"$1-\sin^{2}x$", c**2),
        (r"\dfrac{1-\cos^{2}x}{\sin x}\cdot" + _CTG + r"\,x",
         (1 - c**2) / s * ctg, r"$1-\cos^{2}x$", s**2),
        (r"\left(\sin x+\cos x\right)^{2}-2\sin x\cos x",
         (s + c)**2 - 2 * s * c, r"$\left(\sin x+\cos x\right)^{2}$",
         1 + 2 * s * c),
        (r"\dfrac{\cos^{2}x}{1-\sin x}-\sin x",
         c**2 / (1 - s) - s, r"$\dfrac{\cos^{2}x}{1-\sin x}$", 1 + s),
        (r"\dfrac{1}{\cos^{2}x}-" + _TG + r"^{2}x",
         1 / c**2 - tg**2, r"$\dfrac{1}{\cos^{2}x}$", 1 + tg**2),
        (_TG + r"\,x\cdot" + _CTG + r"\,x+\sin^{2}x",
         tg * ctg + s**2, "$" + _TG + r"\,x\cdot" + _CTG + r"\,x$",
         sp.Integer(1)),
    ]


@template("tr_simplify")
def _simplify(rng: random.Random) -> Question:
    """Спрощення через основні тотожності (заняття 10, практична, завдання 1).

    Проміжний крок питаємо окремо: саме в ньому застосовується тотожність.
    Хто вгадав відповідь з вигляду, на кроці не втримається.
    """
    tex, expr, step_q, step_a = rng.choice(_simplify_shapes())
    a = rng.choice([2, 3, 4, 5, 6, 7])
    total = sp.simplify(a * expr)
    return Question(
        key="tr_simplify",
        statement=(
            rf"Спростіть вираз $\;{a}\left({tex}\right)$."
            + "\n" + rf"1) Спершу спростіть лише {step_q}."
            + "\n2) Запишіть, чому дорівнює весь вираз."
            + "\n" + _HINT_EXPR
        ),
        parts=[
            Part("step", "1) =", step_a, kind="expr", points=1),
            Part("total", "2) весь вираз =", total, kind="expr", points=1),
        ],
        seconds=180,
        params={"a": a, "tex": tex},
    )


# Формули зведення: кут виду base +- x, де base – «вертикальний» (pi/2, 3pi/2)
# або «горизонтальний» (pi, 2pi).
_BASES = [((1, 2), r"\dfrac{\pi}{2}", True), ((1, 1), r"\pi", False),
          ((3, 2), r"\dfrac{3\pi}{2}", True), ((2, 1), r"2\pi", False)]
_FUNCS = [("sin", r"\sin", sp.sin), ("cos", r"\cos", sp.cos),
          ("tg", _TG, sp.tan), ("ctg", _CTG, sp.cot)]


@template("tr_reduction")
def _reduction(rng: random.Random) -> Question:
    """Формули зведення, розкладені за «правилом конячки» (заняття 10).

    Правило викладача – це рівно два питання: який знак і чи змінюється
    назва. Саме їх і питаємо окремо, а результат – третім. Хто завчив
    відповідь, а правила не зрозумів, провалить перші два поля при
    правильному третьому, і це буде видно.
    """
    (bn, bd), btex, flips = rng.choice(_BASES)
    fname, ftex, fn = rng.choice(_FUNCS)
    plus = rng.random() < 0.5
    base = _ang(bn, bd)
    arg = base + _x if plus else base - _x
    result = sp.simplify(fn(arg))
    # Чверть, у якій лежить кут при гострому x, і знак початкової функції там.
    probe = float(sp.N(base)) + (0.2 if plus else -0.2)
    quarter = _quarter_deg(math.degrees(probe))
    sign = _sign(fn(sp.Float(probe)))
    sgn = r"\pm" if sign == 0 else ("+" if sign > 0 else "-")
    return Question(
        key="tr_reduction",
        statement=(
            rf"Зведіть вираз $\;{ftex}\left({btex} "
            rf"{'+' if plus else '-'} x\right)\;$ до функції кута $x$ "
            r"(вважайте $x$ гострим кутом)."
            + "\n" + rf"1) У якій чверті лежить кут ${btex} "
            rf"{'+' if plus else '-'} x$? Запишіть номер чверті."
            + "\n2) Чи змінюється назва функції на кофункцію? Запишіть 1 – "
            "так, 0 – ні."
            + "\n3) Запишіть результат зведення."
            + "\n" + _HINT_EXPR
        ),
        parts=[
            Part("quarter", "1) чверть:", sp.Integer(quarter), points=1),
            Part("flip", "2) назва змінюється (1/0):",
                 sp.Integer(1 if flips else 0), points=1),
            Part("result", "3) результат:", result, kind="expr", points=1),
        ],
        seconds=200,
        params={"base": [bn, bd], "func": fname, "plus": plus,
                "quarter": quarter, "flips": flips, "sign": sgn},
    )


@template("tr_reduction_value")
def _reduction_value(rng: random.Random) -> Question:
    """Обчислення значень через зведення (заняття 10, завдання 4 і ДЗ 5).

    Шлях викладача: 225 = 180 + 45. Тому окремо питаємо чверть і той самий
    гострий кут, через який зводиться даний, а вже потім значення.
    """
    # Лише кути, що зводяться до 30, 45 або 60 градусів: інакше «обчисліть»
    # не має точної відповіді (sin 160 – це sin(pi/9), а не табличне число).
    deg = rng.choice([120, 135, 150, 210, 225, 240, 300, 315, 330])
    fname, ftex, fn = rng.choice(_FUNCS)
    val = sp.simplify(fn(sp.rad(deg)))
    ref = deg % 180
    ref = 180 - ref if ref > 90 else ref
    return Question(
        key="tr_reduction_value",
        statement=(
            rf"Обчисліть ${ftex}\,{_deg_tex(deg)}$ за допомогою формул "
            r"зведення."
            + "\n" + rf"1) У якій чверті лежить кут ${_deg_tex(deg)}$?"
            + "\n2) Через функцію якого гострого кута зводиться даний? "
            r"(Наприклад, для $225^\circ = 180^\circ + 45^\circ$ це "
            r"$45^\circ$.) Запишіть лише число градусів."
            + "\n" + rf"3) Чому дорівнює ${ftex}\,{_deg_tex(deg)}$?"
            + "\n" + _HINT_NUM
        ),
        parts=[
            Part("quarter", "1) чверть:", sp.Integer(_quarter_deg(deg)),
                 points=1),
            Part("ref", "2) гострий кут (у градусах):", sp.Integer(ref),
                 points=1),
            Part("val", rf"3) ${ftex}\,{_deg_tex(deg)}$ =", val, points=1),
        ],
        seconds=190,
        params={"deg": deg, "func": fname, "ref": ref,
                "quarter": _quarter_deg(deg)},
    )


# =========================================================================
#  ЗАНЯТТЯ 11. ПЕРІОД, ГРАФІКИ, ВЛАСТИВОСТІ
# =========================================================================

@template("tr_period")
def _period(rng: random.Random) -> Question:
    """Головний період (заняття 11, задача 1 і завдання 1).

    Ключова думка задачі викладача: період не залежить від зсувів, лише від
    коефіцієнта біля x. Тому в першому пункті зсув навмисне є – і він нічого
    не змінює. У другому функція з періодом pi, а не 2pi.
    """
    w1 = rng.choice([sp.Integer(2), sp.Integer(3), sp.Integer(4),
                     sp.Rational(1, 2), sp.Rational(2, 3), sp.Rational(3, 4),
                     sp.Rational(1, 3), sp.Rational(5, 2)])
    w2 = rng.choice([sp.Integer(2), sp.Integer(3), sp.Integer(5),
                     sp.Rational(1, 3), sp.Rational(1, 2), sp.Rational(2, 5)])
    shift = rng.choice([(1, 4), (1, 3), (1, 6), (2, 3), (3, 4)])
    outer = rng.choice(["sin", "cos"])
    otex = r"\sin" if outer == "sin" else r"\cos"
    inner = rng.choice(["tg", "ctg"])
    itex = _TG if inner == "tg" else _CTG
    a = rng.choice([2, 3, 4, 5])
    return Question(
        key="tr_period",
        statement=(
            rf"1) Знайдіть головний період функції "
            rf"$y = {a}{otex}\left({sp.latex(w1)}x - "
            rf"{angle_tex(*shift)}\right)$."
            + "\n" + rf"2) Знайдіть головний період функції "
            rf"$y = {itex}\left({sp.latex(w2)}x\right)$."
            + "\n3) Чому дорівнює найбільше значення функції з пункту 1?"
            + "\n" + _HINT_NUM
        ),
        parts=[
            Part("t1", "1) період:", sp.simplify(2 * sp.pi / w1), kind="expr",
                 points=1),
            Part("t2", "2) період:", sp.simplify(sp.pi / w2), kind="expr",
                 points=1),
            Part("amp", "3) найбільше значення:", sp.Integer(a), points=1),
        ],
        seconds=180,
        params={"w1": str(w1), "w2": str(w2), "a": a, "outer": outer,
                "inner": inner, "shift": list(shift)},
    )


@template("tr_graph_read")
def _graph_read(rng: random.Random) -> Question:
    """РИСУНОК: прочитати властивості з графіка гармонічного коливання.

    Період беремо цілим (omega = pi/k), щоб його було видно на сітці, а не
    вгадувати між поділками. Третій пункт – нулі на видимому проміжку: це
    вже читання графіка, а не формула амплітуди.
    """
    a = rng.choice([1, 2, 3, 4, 5])
    k = rng.choice([1, 2, 3])
    use_cos = rng.random() < 0.5
    if use_cos:
        fn = lambda xx: a * math.cos(math.pi * xx / k)      # noqa: E731
        zeros = sum(1 for n in range(-20, 21)
                    if abs(k / 2 + k * n) <= 6 + 1e-9)
    else:
        fn = lambda xx: a * math.sin(math.pi * xx / k)      # noqa: E731
        zeros = sum(1 for n in range(-20, 21) if abs(k * n) <= 6 + 1e-9)
    return Question(
        key="tr_graph_read",
        statement=(
            r"На рисунку – графік гармонічного коливання "
            r"$y = A\sin\omega x$ або $y = A\cos\omega x$."
            + "\n1) Чому дорівнює амплітуда $A$?"
            + "\n2) Чому дорівнює головний період цієї функції?"
            + "\n" + r"3) Скільки нулів має функція на проміжку $[-6;\ 6]$?"
            + "\n" + _HINT_NUM
        ),
        parts=[
            Part("amp", "1) амплітуда:", sp.Integer(a), points=1),
            Part("period", "2) період:", sp.Integer(2 * k), points=1),
            Part("zeros", "3) нулів:", sp.Integer(zeros), points=1),
        ],
        seconds=190,
        svg=coordinate_plane(curves=[(fn, -6, 6)]),
        params={"a": a, "k": k, "use_cos": use_cos, "zeros": zeros},
    )


# Пари для порівняння. Рівність трапляється навмисне: sin 160 = sin 20, і це
# найцінніший випадок – формулою його не взяти, лише колом.
def _is_table(deg: int) -> bool:
    """Чи є кут табличним – тобто чи можна його просто обчислити."""
    return deg % 30 == 0 or deg % 45 == 0


def _compare_pairs():
    """Пари для порівняння, збалансовані за відповіддю.

    Жоден із кутів не табличний: інакше завдання розв'язувалося б
    обчисленням, а воно про монотонність і коло. Рівність трапляється
    навмисне (sin 160 = sin 20) – це найцінніший випадок, бо механічне
    «більший кут – більше значення» на ньому й провалюється.
    """
    out = []
    for a in (10, 20, 40, 50, 70, 80):
        out.append(("sin", a, 180 - a))              # рівні  -> 0
        out.append(("sin", a, a + 15))               # обидва гострі -> -1
        out.append(("sin", 180 - a, a + 15))         # зведення, потім -> -1
        out.append(("sin", 180 - a, a - 7))          # зведення, потім -> +1
    for a in (10, 20, 40, 50, 70, 80):
        out.append(("cos", a, 360 - a))              # рівні  -> 0
        out.append(("cos", a, a + 25))               # спадає -> +1
        out.append(("cos", 180 - a, 180 + a))        # рівні  -> 0
    kept = []
    for f, p, q in out:
        if p <= 0 or q <= 0 or (_is_table(p) and _is_table(q)):
            continue
        fn = math.sin if f == "sin" else math.cos
        diff = fn(math.radians(p)) - fn(math.radians(q))
        # Або рівні, або з відчутним відривом. Пара на кшталт sin 100 і sin 95
        # різниться на одну соту: міркування правильне, та перевіряє вже не
        # розуміння, а віру в те, що 80 менше за 85.
        if abs(diff) < 1e-9 or abs(diff) > 0.05:
            kept.append((f, p, q))
    return kept


@template("tr_compare")
def _compare(rng: random.Random) -> Question:
    """Порівняння без обчислення (заняття 11, завдання 4; ДЗ 5 заняття 9).

    Жодне з трьох значень не є табличним – вони й не мають обчислюватися.
    Працює лише монотонність і коло. Випадок «рівні» навмисне трапляється:
    хто механічно пише «менше, бо кут менший», на ньому спіткнеться.
    """
    f1, a1, b1 = rng.choice(_compare_pairs())
    ftex = r"\sin" if f1 == "sin" else r"\cos"
    fn = sp.sin if f1 == "sin" else sp.cos
    c1 = _sign(fn(sp.rad(a1)) - fn(sp.rad(b1)))
    # друга пара – у радіанах, як у задачі викладача
    # Три пари на «менше», три на «більше» і три на «рівні»: інакше відповідь
    # перекошена, і вгадування одним числом дає пів задачі.
    p2, q2 = rng.choice([(sp.Rational(6, 5), sp.Rational(13, 10)),
                         (sp.Rational(7, 6), sp.Rational(5, 4)),
                         (sp.Rational(4, 3), sp.Rational(3, 2)),
                         (sp.Rational(1, 5), sp.Rational(3, 10)),
                         (sp.Rational(2, 3), sp.Rational(5, 6)),
                         (sp.Rational(9, 5), sp.Rational(17, 10)),
                         (sp.Rational(1, 5), sp.Rational(9, 5)),
                         (sp.Rational(3, 10), sp.Rational(17, 10)),
                         (sp.Rational(2, 5), sp.Rational(8, 5))])
    c2 = _sign(sp.cos(p2 * sp.pi) - sp.cos(q2 * sp.pi))
    # Третій пункт навмисне НЕ код: два закодованих поля поспіль надто легко
    # вгадати. Тут питаємо той гострий кут, через який зводиться кут пари, –
    # саме це знання й стоїть за відповіддю «рівні».
    # Питати можна лише про НЕгострий кут: у гострого кут зведення дорівнює
    # йому самому, і пункт роздавався б безплатно.
    if b1 > 90:
        target = b1
    elif a1 > 90:
        target = a1
    else:
        # Обидва гострі (чиста монотонність у пункті 1) – тоді беремо
        # симетричний до b1 відносно тієї самої осі, що й у формулі зведення.
        target = 180 - b1 if f1 == "sin" else 360 - b1
    ref = target % 180
    ref = 180 - ref if ref > 90 else ref
    cofn = r"\sin" if f1 == "sin" else r"\cos"
    return Question(
        key="tr_compare",
        statement=(
            r"Порівняйте, НЕ обчислюючи значень."
            + "\n" + rf"1) ${ftex} {_deg_tex(a1)}$ і ${ftex} {_deg_tex(b1)}$. "
            r"Запишіть $1$, якщо перше більше, $-1$, якщо менше, і $0$, "
            r"якщо вони рівні."
            + "\n" + rf"2) $\cos {sp.latex(p2)}\pi$ і "
            rf"$\cos {sp.latex(q2)}\pi$ – так само $1$, $-1$ або $0$."
            + "\n" + rf"3) До якого гострого кута зводиться "
            rf"${cofn} {_deg_tex(target)}$? Тобто знайдіть такий гострий "
            rf"кут $\beta$, що ${cofn} {_deg_tex(target)}$ дорівнює "
            rf"${cofn}\,\beta$ або $-{cofn}\,\beta$. "
            r"Запишіть лише число градусів кута $\beta$."
            + "\n" + _HINT_NUM
        ),
        parts=[
            Part("c1", "1) (1, -1 або 0):", sp.Integer(c1), points=1),
            Part("c2", "2) (1, -1 або 0):", sp.Integer(c2), points=1),
            Part("ref", r"3) $\beta$ (у градусах):", sp.Integer(ref), points=1),
        ],
        seconds=200,
        params={"f1": f1, "a1": a1, "b1": b1, "c1": c1,
                "p2": str(p2), "q2": str(q2), "c2": c2,
                "target": target, "ref": ref},
    )


@template("tr_properties")
def _properties(rng: random.Random) -> Question:
    """Властивості функції: парність, нулі, множина значень (заняття 11).

    Парність тут не вивчається напам'ять: множник A і коефіцієнт біля x її
    не змінюють, тож відповідь залежить лише від того, синус це чи косинус.
    А найменший додатний нуль залежить уже від коефіцієнта.
    """
    a = rng.choice([2, 3, 4, 5, 6])
    use_cos = rng.random() < 0.5
    k = rng.choice([2, 4, 6]) if use_cos else rng.choice([1, 2, 3, 4, 5])
    ftex = r"\cos" if use_cos else r"\sin"
    zero = sp.Rational(k, 2) if use_cos else sp.Integer(k)
    neg = rng.random() < 0.5                          # мінус перед A
    sign = -1 if neg else 1
    head = rf"-{a}" if neg else f"{a}"
    return Question(
        key="tr_properties",
        statement=(
            rf"Дано функцію $y = {head}{ftex}\dfrac{{\pi x}}{{{k}}}$."
            + "\n1) Функція парна чи непарна? Запишіть 1 – парна, "
            "0 – непарна."
            + "\n2) Чому дорівнює найменший додатний нуль функції?"
            + "\n3) Чому дорівнює найбільше значення функції?"
            + "\n" + _HINT_NUM
        ),
        parts=[
            Part("parity", "1) парність (1/0):",
                 sp.Integer(1 if use_cos else 0), points=1),
            Part("zero", "2) найменший додатний нуль:", zero, points=1),
            Part("max", "3) найбільше значення:", sp.Integer(a), points=1),
        ],
        seconds=180,
        params={"a": a, "k": k, "use_cos": use_cos, "neg": neg,
                "sign": sign},
    )
