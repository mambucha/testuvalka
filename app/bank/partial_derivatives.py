"""Лекція 8 (вища математика): функція двох змінних, частинні похідні, екстремум.

Обсяг рівно за матеріалами викладача – лекція 8 і практичні 8, 9:
  * функція двох змінних та її область визначення;
  * частинні похідні першого порядку (решта змінних – сталі);
  * повний диференціал dz = z'_x dx + z'_y dy;
  * похідні другого порядку, мішані та теорема про їх рівність;
  * перевірка, що функція задовольняє задане рівняння;
  * екстремум: стаціонарні точки, A, B, C, Delta = AC - B^2;
  * умовний екстремум методом множників Лагранжа.

Рівень – репродуктивний і продуктивний: функції прості, числа невеликі,
стаціонарні точки цілі. «Творчих» задач (вписаний прямокутник, квадратична
форма) тут нема навмисне. Мета тесту – побачити, засвоєно матеріал чи ні,
а не відсіяти.

Хід розв'язання видно з кроків: окремо кожна похідна, окремо висновок. Саме
тому помилку видно адресно – чи то не те продиференційовано, чи то правило
Delta не зрозуміле.

Варіативність: у кожному шаблоні щонайменше два десятки різних відповідей,
тому переписане в сусіда число майже завжди виявиться чужим.
"""

from __future__ import annotations

import random

import sympy as sp

from engine import Part, Question, template

_x, _y = sp.symbols("x y")

_HINT = ("(Відповідь – вираз зі змінними x, y. Експонента: e^(x*y) або "
         "exp(x*y), логарифм: ln(x).)")

# Там, де всі поля числові, обіцяти «вираз зі змінними» не можна: студент
# шукатиме в умові те, чого в ній немає.
_HINT_NUM = "(Відповіді – числа.)"


def _p(e: int, var: str = "x") -> str:
    """Степінь у LaTeX без зайвої одиниці."""
    return var if e == 1 else rf"{var}^{{{e}}}"


def _c(v: int) -> str:
    """Коефіцієнт 1 не пишемо."""
    return "" if v == 1 else str(v)


def _signed(v: int, body: str = "") -> str:
    """Доданок зі своїм знаком: _signed(-12, 'x') -> ' - 12x'."""
    sign = " + " if v > 0 else " - "
    return sign + (_c(abs(v)) if body else str(abs(v))) + body


def _has(expr, *syms) -> bool:
    """Чи містить відповідь студента хоч одну зі змінних.

    Відповідь-стала (зокрема нуль) не годиться для перенесення помилки:
    нуль – нерухома точка і диференціювання, і підстановки, тож ланцюжок
    підтверджував би сам себе.
    """
    try:
        return bool(sp.sympify(expr).free_symbols & set(syms))
    except Exception:  # noqa: BLE001
        return False


def _nonzero(value):
    """Число з попереднього кроку; нуль і вирази зі змінними не переносимо."""
    try:
        v = sp.sympify(value)
    except Exception:  # noqa: BLE001
        return None
    if v.free_symbols or v == 0:
        return None
    return v


# =========================================================================
#  ЧАСТИННІ ПОХІДНІ ПЕРШОГО ПОРЯДКУ
# =========================================================================

@template("pd_first_poly")
def _first_poly(rng: random.Random) -> Question:
    """Частинні похідні многочлена (лекція, приклад 2.1; ПЗ 8, завдання 1).

    Найбазовіше: чи зрозумів студент, що при диференціюванні по x змінна y
    поводиться як стала.
    """
    a = rng.choice([2, 3, 4, 5])
    n = rng.choice([2, 3, 4])
    m = rng.choice([2, 3])
    b = rng.choice([2, 3, 4, 5, 6, 7])
    c = rng.choice([2, 3, 4, 5, 6, 7])
    z = a * _x**n * _y**m + b * _x - c * _y
    zx, zy = sp.diff(z, _x), sp.diff(z, _y)
    x0, y0 = rng.choice([1, 2]), rng.choice([1, 2])
    tex = rf"{_c(a)}{_p(n)}{_p(m, 'y')} + {_c(b)}x - {_c(c)}y"
    return Question(
        key="pd_first_poly",
        statement=(
            rf"Дано функцію $z = {tex}$."
            + "\n" + r"1) Знайдіть $\dfrac{\partial z}{\partial x}$."
            + "\n" + r"2) Знайдіть $\dfrac{\partial z}{\partial y}$."
            + "\n" + rf"3) Обчисліть значення $\dfrac{{\partial z}}{{\partial x}}$"
            rf" у точці $M({x0};\ {y0})$."
            + "\n" + _HINT
        ),
        parts=[
            Part("zx", r"1) $z'_x$ =", zx, kind="expr", points=1),
            Part("zy", r"2) $z'_y$ =", zy, kind="expr", points=1),
            Part("val", rf"3) $z'_x({x0};{y0})$ =", zx.subs({_x: x0, _y: y0}),
                 points=1,
                 carry=lambda prev, _a=x0, _b=y0: (
                     prev["zx"].subs({_x: _a, _y: _b})
                     if _has(prev.get("zx"), _x, _y) else None),
                 carry_from=("zx",)),
        ],
        seconds=150,
        params={"a": a, "n": n, "m": m, "b": b, "c": c, "x0": x0, "y0": y0},
    )


@template("pd_first_log")
def _first_log(rng: random.Random) -> Question:
    """Частинні похідні логарифма – складена функція (ПЗ 8, завдання 4)."""
    a = rng.choice([1, 2, 3, 4, 5])
    b = rng.choice([2, 3, 4, 5, 6, 7])
    k = rng.choice([2, 3])
    inner = a * _x**k + b * _y
    z = sp.log(inner)
    tex = rf"{_c(a)}x^{{{k}}} + {_c(b)}y"
    return Question(
        key="pd_first_log",
        statement=(
            rf"Дано функцію $z = \ln\left({tex}\right)$."
            + "\n" + r"1) Знайдіть $\dfrac{\partial z}{\partial x}$."
            + "\n" + r"2) Знайдіть $\dfrac{\partial z}{\partial y}$."
            + "\n" + _HINT
        ),
        parts=[
            Part("zx", r"1) $z'_x$ =", sp.diff(z, _x), kind="expr", points=1),
            Part("zy", r"2) $z'_y$ =", sp.diff(z, _y), kind="expr", points=1),
        ],
        seconds=140,
        params={"a": a, "b": b, "k": k},
    )


@template("pd_first_exp")
def _first_exp(rng: random.Random) -> Question:
    """Степінь на експоненту; подекуди змінні міняються ролями.

    Переставлені x та y – дешева, але дієва перевірка: хто дивиться на букву,
    а не на позицію, той не схибить.
    """
    a = rng.choice([2, 3, 4, 5])
    b = rng.choice([2, 3, 4, 5, 6, 7])
    swap = rng.random() < 0.5
    u, v = (_y, _x) if swap else (_x, _y)
    nu, nv = ("y", "x") if swap else ("x", "y")
    z = u**a * sp.exp(b * v)
    tex = rf"{_p(a, nu)}e^{{{_c(b)}{nv}}}"
    return Question(
        key="pd_first_exp",
        statement=(
            rf"Дано функцію $z = {tex}$."
            + "\n" + r"1) Знайдіть $\dfrac{\partial z}{\partial x}$."
            + "\n" + r"2) Знайдіть $\dfrac{\partial z}{\partial y}$."
            + "\n" + r"3) Знайдіть мішану похідну "
            r"$\dfrac{\partial^2 z}{\partial x\,\partial y}$."
            + "\n" + _HINT
        ),
        parts=[
            Part("zx", r"1) $z'_x$ =", sp.diff(z, _x), kind="expr", points=1),
            Part("zy", r"2) $z'_y$ =", sp.diff(z, _y), kind="expr", points=1),
            Part("zxy", r"3) $z''_{xy}$ =", sp.diff(z, _x, _y), kind="expr",
                 points=1,
                 carry=lambda prev: (
                     sp.diff(prev["zy"], _x)
                     if _has(prev.get("zy"), _x) else None),
                 carry_from=("zy",)),
        ],
        seconds=160,
        params={"a": a, "b": b, "swap": swap},
    )


# =========================================================================
#  ПОВНИЙ ДИФЕРЕНЦІАЛ
# =========================================================================

@template("pd_differential")
def _differential(rng: random.Random) -> Question:
    """Повний диференціал (ПЗ 8, завдання 2).

    Два перші кроки – множники при dx і dy, тобто ті самі частинні похідні.
    Третій показує, чи студент розуміє, що з диференціалом роблять далі:
    підставляють числа.
    """
    a = rng.choice([2, 3, 4, 5])
    b = rng.choice([2, 3, 4, 5, 6])
    c = rng.choice([2, 3, 4, 5, 6, 7])
    z = a * _x**2 * _y**3 + b * _x - c * _y
    zx, zy = sp.diff(z, _x), sp.diff(z, _y)
    x0, y0 = rng.choice([1, 2]), rng.choice([1, 2])
    dx, dy = rng.choice([1, 2, 3]), rng.choice([-3, -2, -1, 1, 2])
    at = {_x: x0, _y: y0}
    dz = zx.subs(at) * dx + zy.subs(at) * dy
    tex = rf"{_c(a)}x^{{2}}y^{{3}} + {_c(b)}x - {_c(c)}y"
    return Question(
        key="pd_differential",
        statement=(
            rf"Дано функцію $z = {tex}$. Повний диференціал обчислюють за "
            r"формулою $dz = \dfrac{\partial z}{\partial x}dx + "
            r"\dfrac{\partial z}{\partial y}dy$."
            + "\n1) Запишіть множник при $dx$."
            + "\n2) Запишіть множник при $dy$."
            + "\n" + rf"3) Обчисліть $dz$ у точці $M({x0};\ {y0})$ при "
            rf"$dx = {dx}$ і $dy = {dy}$."
            + "\n" + _HINT
        ),
        parts=[
            Part("zx", "1) множник при $dx$:", zx, kind="expr", points=1),
            Part("zy", "2) множник при $dy$:", zy, kind="expr", points=1),
            Part("dz", "3) $dz$ =", dz, points=1,
                 carry=lambda prev, _at=at, _d=(dx, dy): (
                     prev["zx"].subs(_at) * _d[0] + prev["zy"].subs(_at) * _d[1]
                     if (_has(prev.get("zx"), _x, _y)
                         or _has(prev.get("zy"), _x, _y)) else None),
                 carry_from=("zx", "zy")),
        ],
        seconds=170,
        params={"a": a, "b": b, "c": c, "x0": x0, "y0": y0, "dx": dx, "dy": dy},
    )


# =========================================================================
#  ПОХІДНІ ДРУГОГО ПОРЯДКУ
# =========================================================================

@template("pd_second_poly")
def _second_poly(rng: random.Random) -> Question:
    """Три похідні другого порядку (ПЗ 8, завдання 3)."""
    a = rng.choice([1, 2, 3, 4])
    b = rng.choice([2, 3, 4, 5, 6])
    c = rng.choice([2, 3, 4, 5])
    z = a * _x**3 - b * _x * _y + c * _y**2
    tex = rf"{_c(a)}x^{{3}} - {_c(b)}xy + {_c(c)}y^{{2}}"
    return Question(
        key="pd_second_poly",
        statement=(
            rf"Дано функцію $z = {tex}$."
            + "\n" + r"1) Знайдіть $\dfrac{\partial^2 z}{\partial x^2}$."
            + "\n" + r"2) Знайдіть мішану похідну "
            r"$\dfrac{\partial^2 z}{\partial x\,\partial y}$."
            + "\n" + r"3) Знайдіть $\dfrac{\partial^2 z}{\partial y^2}$."
            + "\n" + _HINT
        ),
        parts=[
            Part("zxx", r"1) $z''_{xx}$ =", sp.diff(z, _x, 2), kind="expr",
                 points=1),
            Part("zxy", r"2) $z''_{xy}$ =", sp.diff(z, _x, _y), kind="expr",
                 points=1),
            Part("zyy", r"3) $z''_{yy}$ =", sp.diff(z, _y, 2), kind="expr",
                 points=1),
        ],
        seconds=150,
        params={"a": a, "b": b, "c": c},
    )


@template("pd_second_mixed")
def _second_mixed(rng: random.Random) -> Question:
    """Похідні другого порядку від x*ln(y) + sin(bx) – приклад 2.2 лекції.

    Тут є і логарифм, і тригонометрія, тож похідна по y не зачіпає синус
    зовсім: видно, чи студент справді тримає другу змінну за сталу.
    """
    a = rng.choice([1, 2, 3, 4, 5])
    b = rng.choice([1, 2, 3, 4])
    k = rng.choice([1, 2])
    z = a * _x**k * sp.log(_y) + sp.sin(b * _x)
    tex = rf"{_c(a)}{_p(k)}\ln y + \sin {_c(b)}x"
    return Question(
        key="pd_second_mixed",
        statement=(
            rf"Дано функцію $z = {tex}$, де $y > 0$."
            + "\n" + r"1) Знайдіть $\dfrac{\partial z}{\partial x}$."
            + "\n" + r"2) Знайдіть мішану похідну "
            r"$\dfrac{\partial^2 z}{\partial x\,\partial y}$."
            + "\n" + r"3) Знайдіть $\dfrac{\partial^2 z}{\partial y^2}$."
            + "\n" + _HINT
        ),
        parts=[
            Part("zx", r"1) $z'_x$ =", sp.diff(z, _x), kind="expr", points=1,
                 positive=True),
            Part("zxy", r"2) $z''_{xy}$ =", sp.diff(z, _x, _y), kind="expr",
                 points=1, positive=True,
                 carry=lambda prev: (
                     sp.diff(prev["zx"], _y)
                     if _has(prev.get("zx"), _y) else None),
                 carry_from=("zx",)),
            Part("zyy", r"3) $z''_{yy}$ =", sp.diff(z, _y, 2), kind="expr",
                 points=1, positive=True),
        ],
        seconds=170,
        params={"a": a, "b": b, "k": k},
    )


@template("pd_identity")
def _identity(rng: random.Random) -> Question:
    """Перевірка, що функція задовольняє рівняння (ПЗ 8, завдання 6).

    Третій крок складається з перших двох, тому видно, чи студент доводить
    тотожність, чи просто вгадує. Відповідь тут – стала, і це вся суть:
    змінні мусять скоротитися.
    """
    a = rng.choice([2, 3, 4, 5, 6, 7])
    b = rng.choice([2, 3, 4, 5, 6, 7])
    z = sp.log(_x**a * _y**b)
    zx, zy = sp.diff(z, _x), sp.diff(z, _y)
    total = sp.simplify(_x * zx + _y * zy)
    tex = rf"\ln\left(x^{{{a}}}y^{{{b}}}\right)"
    return Question(
        key="pd_identity",
        statement=(
            rf"Дано функцію $z = {tex}$, де $x > 0$ і $y > 0$."
            + "\n" + r"1) Знайдіть $\dfrac{\partial z}{\partial x}$."
            + "\n" + r"2) Знайдіть $\dfrac{\partial z}{\partial y}$."
            + "\n" + r"3) Обчисліть вираз $x\dfrac{\partial z}{\partial x} + "
            r"y\dfrac{\partial z}{\partial y}$ і спростіть його."
            + "\n" + _HINT
        ),
        parts=[
            Part("zx", r"1) $z'_x$ =", zx, kind="expr", points=1,
                 positive=True),
            Part("zy", r"2) $z'_y$ =", zy, kind="expr", points=1,
                 positive=True),
            Part("sum", r"3) $xz'_x + yz'_y$ =", total, kind="expr", points=1,
                 positive=True,
                 carry=lambda prev: (
                     sp.simplify(_x * prev["zx"] + _y * prev["zy"])
                     if (_has(prev.get("zx"), _x, _y)
                         and _has(prev.get("zy"), _x, _y)
                         and sp.simplify(prev["zx"] - prev["zy"]) != 0)
                     else None),
                 carry_from=("zx", "zy")),
        ],
        seconds=170,
        params={"a": a, "b": b},
    )


# =========================================================================
#  ОБЛАСТЬ ВИЗНАЧЕННЯ
# =========================================================================

@template("pd_domain")
def _domain(rng: random.Random) -> Question:
    """Область визначення функції двох змінних (лекція, приклад 1.1).

    Корінь дає замкнений круг, логарифм – відкритий. Серед перелічених точок
    завжди є хоч одна з межі, тож ця різниця змінює відповідь: саме на ній
    і видно, чи означення області визначення зрозуміле, чи завчене.
    """
    r = rng.choice([2, 3, 4, 5, 6, 7])
    closed = rng.random() < 0.5                      # корінь чи логарифм
    r2 = r * r
    border = [(r, 0), (0, r), (-r, 0), (0, -r)]
    others = [(0, 0), (1, 1), (1, 0), (0, 1), (-1, 1),
              (r, r), (r + 1, 0), (0, r + 1)]
    pts = [rng.choice(border)] + rng.sample(others, 4)
    rng.shuffle(pts)

    def ok(px: int, py: int) -> bool:
        s = px * px + py * py
        return s <= r2 if closed else s < r2

    inside = sum(1 for px, py in pts if ok(px, py))
    head = (rf"\sqrt{{{r2} - x^{{2}} - y^{{2}}}}" if closed
            else rf"\ln\left({r2} - x^{{2}} - y^{{2}}\right)")
    listing = ", ".join(rf"$({px};\ {py})$" for px, py in pts)
    note = "" if closed else " (відповідь можна залишити з логарифмом)"
    return Question(
        key="pd_domain",
        statement=(
            rf"Дано функцію $z = {head}$."
            + "\n1) Областю визначення цієї функції є круг. Чому дорівнює "
            "його радіус?"
            + "\n" + rf"2) Скільки з точок {listing} належать області "
            "визначення?"
            + "\n" + rf"3) Обчисліть значення $z$ у точці $(0;\ 0)${note}."
            + "\n" + _HINT_NUM
        ),
        parts=[
            Part("radius", "1) радіус круга:", sp.Integer(r), points=1),
            Part("cnt", "2) точок в області:", sp.Integer(inside), points=1),
            Part("val", "3) $z(0;0)$ =",
                 sp.Integer(r) if closed else sp.log(r2), points=1),
        ],
        seconds=160,
        params={"r": r, "closed": closed, "pts": pts, "inside": inside},
    )


# =========================================================================
#  ЕКСТРЕМУМ
# =========================================================================

@template("pd_extremum_test")
def _extremum_test(rng: random.Random) -> Question:
    """Достатня умова екстремуму: A, Delta = AC - B^2 і висновок.

    Точку для дослідження беремо випадково з двох стаціонарних, а знак
    коефіцієнта при y^2 гуляє, тож відповіддю буває і мінімум, і максимум,
    і «екстремуму немає». Вивчити напам'ять нічого не вийде – правило
    доводиться застосувати.
    """
    a = rng.choice([1, 2, 3])
    b = rng.choice([-3, -2, -1, 1, 2, 3])
    z = _x**3 - 3 * a * a * _x + b * _y**2
    px = rng.choice([a, -a])                       # стаціонарні: (a;0), (-a;0)
    A = sp.diff(z, _x, 2).subs({_x: px, _y: 0})
    B = sp.diff(z, _x, _y).subs({_x: px, _y: 0})
    C = sp.diff(z, _y, 2).subs({_x: px, _y: 0})
    delta = sp.expand(A * C - B**2)
    kind = 0 if delta < 0 else (1 if A > 0 else 2)
    tex = "x^{3}" + _signed(-3 * a * a, "x") + _signed(b, "y^{2}")
    return Question(
        key="pd_extremum_test",
        statement=(
            rf"Дано функцію $z = {tex}$. Відомо, що $M({px};\ 0)$ – "
            "стаціонарна точка цієї функції."
            + "\n" + r"Нагадаємо позначення: $A = z''_{xx}(M)$, "
            r"$B = z''_{xy}(M)$, $C = z''_{yy}(M)$, $\Delta = AC - B^2$."
            + "\n1) Чому дорівнює $A$?"
            + "\n" + r"2) Чому дорівнює $\Delta$?"
            + "\n3) Який висновок про точку $M$? Запишіть: 1 – мінімум, "
            "2 – максимум, 0 – екстремуму немає."
            + "\n" + _HINT_NUM
        ),
        parts=[
            Part("A", "1) $A$ =", A, points=1),
            Part("delta", r"2) $\Delta$ =", delta, points=1),
            Part("kind", "3) висновок (0, 1 або 2):", sp.Integer(kind),
                 points=1),
        ],
        seconds=180,
        params={"a": a, "b": b, "px": px, "A": int(A), "B": int(B),
                "C": int(C), "delta": int(delta), "kind": kind},
    )


@template("pd_extremum_full")
def _extremum_full(rng: random.Random) -> Question:
    """Кроки 1, 2 і 6 алгоритму лекції: продиференціювати, знайти стаціонарну
    точку, обчислити в ній значення функції.

    Достатню умову (A, B, C, Delta) питає окремо pd_extremum_test, тож ці два
    завдання разом покривають увесь алгоритм і ніде не повторюються. Функція
    тут найпростіша з можливих – одна стаціонарна точка, перехресної похідної
    немає: рівень «не жестити».
    """
    a = rng.choice([1, 2, 3])
    b = rng.choice([1, 2, 3])
    sign = rng.choice([1, -1])                     # угору чи вниз
    x0 = rng.choice([-2, -1, 1, 2])
    y0 = rng.choice([-2, -1, 1, 2])
    c, d = 2 * a * x0 * sign, 2 * b * y0 * sign
    e = rng.choice([-5, -3, 3, 5])
    z = sign * (a * _x**2 + b * _y**2) - c * _x - d * _y + e
    zval = sp.expand(z).subs({_x: x0, _y: y0})
    head = (rf"{_c(a)}x^{{2}} + {_c(b)}y^{{2}}" if sign > 0
            else rf"-{_c(a)}x^{{2}} - {_c(b)}y^{{2}}")
    tex = head + _signed(-c, "x") + _signed(-d, "y") + _signed(e)
    return Question(
        key="pd_extremum_full",
        statement=(
            rf"Дослідіть на екстремум функцію $z = {tex}$."
            + "\n" + r"1) Знайдіть $\dfrac{\partial z}{\partial x}$."
            + "\n2) Прирівнявши обидві частинні похідні до нуля, знайдіть "
            "абсцису $x_0$ стаціонарної точки."
            + "\n3) Чому дорівнює екстремальне значення функції?"
            + "\n" + _HINT
        ),
        parts=[
            Part("zx", r"1) $z'_x$ =", sp.diff(sp.expand(z), _x), kind="expr",
                 points=1),
            Part("x0", "2) $x_0$ =", sp.Integer(x0), points=1),
            Part("zval", "3) екстремальне значення $z$ =", zval, points=1),
        ],
        seconds=180,
        params={"a": a, "b": b, "sign": sign, "x0": x0, "y0": y0, "e": e},
    )


# =========================================================================
#  УМОВНИЙ ЕКСТРЕМУМ (МЕТОД ЛАГРАНЖА)
# =========================================================================

@template("pd_lagrange_linear")
def _lagrange_linear(rng: random.Random) -> Question:
    """Умовний екстремум z = x^2 + y^2 при лінійному зв'язку (ПЗ 9, приклад 2).

    Множник Лагранжа питаємо першим навмисне: його не дістати з геометрії
    задачі, лише з системи. Хто обійшов метод, на цьому полі й спіткнеться.
    """
    a = rng.choice([1, 2, 3, 4, 5])
    b = rng.choice([1, 2, 3, 4, 5])
    k = rng.choice([1, 2, 3])
    c = k * (a * a + b * b)
    x0, y0 = a * k, b * k
    lam = -2 * k
    tex = rf"{_c(a)}x + {_c(b)}y = {c}"
    return Question(
        key="pd_lagrange_linear",
        statement=(
            r"Знайдіть умовний екстремум функції $z = x^{2} + y^{2}$ за умови "
            rf"${tex}$."
            + "\n" + r"Функція Лагранжа: $L = x^{2} + y^{2} + \lambda\left("
            + rf"{_c(a)}x + {_c(b)}y - {c}" + r"\right)$."
            + "\n" + r"1) Знайдіть множник $\lambda$."
            + "\n2) Знайдіть $x_0$ – абсцису точки умовного екстремуму."
            + "\n3) Чому дорівнює екстремальне значення $z$?"
            + "\n" + _HINT_NUM
        ),
        parts=[
            Part("lam", r"1) $\lambda$ =", sp.Integer(lam), points=1),
            Part("x0", "2) $x_0$ =", sp.Integer(x0), points=1),
            Part("zval", "3) $z$ =", sp.Integer(x0 * x0 + y0 * y0), points=1),
        ],
        seconds=190,
        params={"a": a, "b": b, "k": k, "c": c, "x0": x0, "y0": y0, "lam": lam},
    )


@template("pd_lagrange_circle")
def _lagrange_circle(rng: random.Random) -> Question:
    """Лінійна функція на колі (ПЗ 9, завдання 1.1 і 3).

    Тут два розв'язки – максимум і мінімум, тож видно, чи студент довів
    дослідження до кінця, а не спинився на першій знайденій точці.
    """
    a, b = rng.choice([(3, 4), (4, 3), (1, 2), (2, 1), (2, 3), (3, 2),
                       (1, 3), (3, 1), (5, 12), (12, 5), (1, 4), (4, 1)])
    m = rng.choice([1, 2, 3])
    r2 = m * m * (a * a + b * b)
    zmax = m * (a * a + b * b)
    tex = rf"{_c(a)}x + {_c(b)}y"
    return Question(
        key="pd_lagrange_circle",
        statement=(
            rf"Знайдіть найбільше і найменше значення функції $z = {tex}$ "
            rf"на колі $x^{{2}} + y^{{2}} = {r2}$."
            + "\n" + r"Функція Лагранжа: $L = " + tex
            + rf" + \lambda\left(x^{{2}} + y^{{2}} - {r2}\right)$."
            + "\n1) Знайдіть абсцису $x_0$ точки, у якій $z$ найбільше."
            + "\n2) Чому дорівнює найбільше значення $z$?"
            + "\n3) Чому дорівнює найменше значення $z$?"
            + "\n" + _HINT_NUM
        ),
        parts=[
            Part("x0", "1) $x_0$ =", sp.Integer(a * m), points=1),
            Part("zmax", "2) найбільше $z$ =", sp.Integer(zmax), points=1),
            Part("zmin", "3) найменше $z$ =", sp.Integer(-zmax), points=1,
                 carry=lambda prev: (
                     -prev["zmax"] if _nonzero(prev.get("zmax")) is not None
                     else None),
                 carry_from=("zmax",)),
        ],
        seconds=190,
        params={"a": a, "b": b, "m": m, "r2": r2, "zmax": zmax},
    )
