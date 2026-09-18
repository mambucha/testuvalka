"""Тема (шкільна математика, заняття 5): степенева функція та корінь n-го степеня.

Обчислення коренів (парних і непарних), властивість з модулем (²ᵏ√(a²ᵏ)=|a|),
значення степеневої функції, дії з коренями (добуток, частка, винесення
множника), порівняння коренів, область визначення y = ⁿ√(ax+b).

ВАЖЛИВО: перетворення графіків елементарними побудовами (зсуви) НЕ входять —
цього в темі ще не було.

Винесення множника дає відповідь-вираз (kind="expr"), тож тут доречні екранна
клавіатура з коренем і живий математичний прев'ю. Решта відповідей — цілі або
прості дроби.
"""

from __future__ import annotations

import random

import sympy as sp

from engine import Part, Question, template

from app.bank.plotting import coordinate_plane

_x = sp.Symbol("x")

# Числа, що НЕ є повними квадратами (для «залишку» під коренем при винесенні).
_NONSQUARE = [2, 3, 5, 6, 7, 10, 11]


def _root_tex(n: int, inner: str) -> str:
    """LaTeX кореня: \\sqrt{...} для n=2, \\sqrt[n]{...} інакше."""
    return rf"\sqrt{{{inner}}}" if n == 2 else rf"\sqrt[{n}]{{{inner}}}"


# --- обчислення коренів --------------------------------------------------


@template("root_value")
def _root_value(rng: random.Random) -> Question:
    """Арифметичний корінь n-го степеня з точного степеня."""
    n = rng.choice([2, 3, 4, 5, 6])
    b = rng.randint(2, 5) if n <= 3 else rng.randint(2, 4)
    a = b**n
    return Question(
        key="root_value",
        statement="Обчисліть корінь:\n$$" + _root_tex(n, str(a)) + "$$",
        parts=[Part("v", "= ", b, points=1)],
        seconds=40,
        params={"n": n, "a": a},
    )


@template("odd_root_negative")
def _odd_root_negative(rng: random.Random) -> Question:
    """Корінь НЕПАРНОГО степеня з від'ємного числа (існує, від'ємний)."""
    n = rng.choice([3, 5])
    b = rng.randint(2, 4) if n == 3 else rng.randint(2, 3)
    a = -(b**n)
    return Question(
        key="odd_root_negative",
        statement=(
            "Обчисліть корінь непарного степеня (він існує для від'ємного "
            "числа):\n$$" + _root_tex(n, str(a)) + "$$"
        ),
        parts=[Part("v", "= ", -b, points=1)],
        seconds=45,
        params={"n": n, "a": a},
    )


@template("root_expression")
def _root_expression(rng: random.Random) -> Question:
    """Обчислення виразу з кількох коренів і коефіцієнтів (як задача 1 заняття)."""
    n1, b1 = rng.choice([3, 5]), rng.randint(2, 3)  # непарний корінь (може бути -)
    a1 = -(b1**n1) if rng.random() < 0.5 else b1**n1
    r1 = round(a1 ** (1 / n1)) if a1 > 0 else -round((-a1) ** (1 / n1))
    n2, b2 = rng.choice([2, 4]), rng.randint(2, 4)  # парний корінь
    a2 = b2**n2
    k = rng.choice([2, 3])
    n3, b3 = 3, rng.randint(2, 4)
    a3 = b3**3
    val = r1 - k * b2 + b3
    return Question(
        key="root_expression",
        statement=(
            "Обчисліть значення виразу:\n$$"
            + _root_tex(n1, str(a1))
            + f" - {k}"
            + _root_tex(n2, str(a2))
            + " + "
            + _root_tex(3, str(a3))
            + "$$"
        ),
        parts=[Part("v", "= ", val, points=1)],
        seconds=90,
        params={"a1": a1, "n1": n1, "a2": a2, "n2": n2, "k": k, "a3": a3},
    )


@template("even_root_modulus")
def _even_root_modulus(rng: random.Random) -> Question:
    """Ключова властивість: ²ᵏ√(a²ᵏ) = |a| (корінь парного степеня невід'ємний)."""
    n = rng.choice([2, 4, 6])
    b = rng.randint(2, 5)
    a = -b  # від'ємна основа, щоб перевірити модуль
    inner = a**n  # додатне
    return Question(
        key="even_root_modulus",
        statement=(
            "Обчисліть (увага: корінь парного степеня завжди невід'ємний):\n$$"
            + _root_tex(n, f"({a})^{{{n}}}")
            + "$$"
        ),
        parts=[Part("v", "= ", b, points=1)],
        seconds=50,
        params={"n": n, "a": a},
    )


# --- степенева функція ---------------------------------------------------


@template("power_value")
def _power_value(rng: random.Random) -> Question:
    """Значення степеневої функції y = xⁿ у точці."""
    n = rng.choice([2, 3, 4, 5])
    a = rng.choice([-3, -2, 2, 3])
    if n >= 4:
        a = rng.choice([-2, 2])  # щоб число не було завеликим
    val = a**n
    return Question(
        key="power_value",
        statement=(
            rf"Дано степеневу функцію $y = x^{{{n}}}$."
            "\n"
            rf"Обчисліть її значення в точці $x = {a}$."
        ),
        parts=[Part("v", f"$y({a})$ =", val, points=1)],
        seconds=40,
        params={"n": n, "a": a},
    )


@template("negative_power_value")
def _negative_power_value(rng: random.Random) -> Question:
    """Значення функції з цілим від'ємним показником y = x^(-n) = 1/xⁿ."""
    n = rng.choice([1, 2, 3])
    a = rng.choice([2, 3, -2])
    val = sp.Rational(1, a**n)
    return Question(
        key="negative_power_value",
        statement=(
            rf"Дано функцію $y = x^{{-{n}}} = \dfrac{{1}}{{x^{{{n}}}}}$."
            "\n"
            rf"Обчисліть її значення в точці $x = {a}$."
        ),
        parts=[Part("v", f"$y({a})$ =", val, points=1)],
        seconds=50,
        params={"n": n, "a": a},
    )


@template("power_parity_values")
def _power_parity_values(rng: random.Random) -> Question:
    """Парність степеневої: обчислити f(a) та f(-a) для y=xⁿ.
    Порівняння значень показує парність (парна n -> рівні, непарна -> протилежні)."""
    n = rng.choice([2, 3, 4, 5])
    a = rng.choice([2, 3]) if n <= 3 else 2
    return Question(
        key="power_parity_values",
        statement=(
            rf"Для степеневої функції $y = x^{{{n}}}$ обчисліть $f({a})$ та "
            rf"$f(-{a})$ (порівняння цих значень показує, чи функція парна)."
        ),
        parts=[
            Part("fa", rf"$f({a})$ =", a**n, points=1),
            Part("fna", rf"$f(-{a})$ =", (-a) ** n, points=1),
        ],
        seconds=55,
        params={"n": n, "a": a},
    )


@template("power_compare")
def _power_compare(rng: random.Random) -> Question:
    """Монотонність: порівняти значення xⁿ у двох додатних точках (обчислити обидва)."""
    n = rng.choice([2, 3, 4])
    b1, b2 = 2, 3
    return Question(
        key="power_compare",
        statement=(
            rf"Функція $y = x^{{{n}}}$ зростає на $[0; +\infty)$. Обчисліть її "
            rf"значення в точках $x={b1}$ та $x={b2}$."
        ),
        parts=[
            Part("v1", rf"$f({b1})$ =", b1**n, points=1),
            Part("v2", rf"$f({b2})$ =", b2**n, points=1),
        ],
        seconds=50,
        params={"n": n, "b1": b1, "b2": b2},
    )


@template("power_solve_odd")
def _power_solve_odd(rng: random.Random) -> Question:
    """Обернена дія: розв'язати xⁿ = c для НЕПАРНОГО n (єдиний корінь, можливо <0)."""
    n = rng.choice([3, 5])
    b = rng.randint(2, 4) if n == 3 else rng.randint(2, 3)
    b *= rng.choice([1, -1])
    c = b**n
    return Question(
        key="power_solve_odd",
        statement=(
            rf"Розв'яжіть рівняння $x^{{{n}}} = {c}$."
            "\n(Показник непарний, тож корінь один.)"
        ),
        parts=[Part("x", "$x$ =", b, points=1)],
        seconds=55,
        params={"n": n, "c": c},
    )


@template("power_solve_even")
def _power_solve_even(rng: random.Random) -> Question:
    """Обернена дія: розв'язати x^(2k) = c для ПАРНОГО степеня (два корені ±)."""
    n = rng.choice([2, 4])
    b = rng.randint(2, 5) if n == 2 else rng.randint(2, 3)
    c = b**n
    return Question(
        key="power_solve_even",
        statement=(
            rf"Розв'яжіть рівняння $x^{{{n}}} = {c}$."
            "\n(Показник парний, тож коренів два. Запишіть менший і більший.)"
        ),
        parts=[
            Part("lo", "менший =", -b, points=1),
            Part("hi", "більший =", b, points=1),
        ],
        seconds=60,
        params={"n": n, "c": c},
    )


@template("power_parity_symbolic")
def _power_parity_symbolic(rng: random.Random) -> Question:
    """Розуміння парності символьно: знайти ВИРАЗ f(-x) для y = xⁿ.
    Парна (n парне) -> xⁿ; непарна -> -xⁿ. Відповідь-вираз (клавіатура+прев'ю)."""
    n = rng.choice([2, 3, 4, 5, 6])
    fneg = sp.expand((-_x) ** n)
    return Question(
        key="power_parity_symbolic",
        statement=(
            rf"Дано степеневу функцію $y = x^{{{n}}}$. Щоб дослідити її на "
            r"парність, знайдіть і спростіть вираз $f(-x)$."
        ),
        parts=[Part("fneg", "$f(-x)$ =", fneg, kind="expr", points=1)],
        seconds=55,
        params={"n": n},
    )


@template("power_parity_apply")
def _power_parity_apply(rng: random.Random) -> Question:
    """Застосування властивості парності БЕЗ повторного обчислення: відомо
    значення в точці, знайти в протилежній, спираючись на парність/непарність."""
    n = rng.choice([2, 3, 4, 5, 6])
    a = rng.choice([2, 3])
    v = a**n
    even = (n % 2 == 0)
    fneg = v if even else -v
    kind_word = "парна" if even else "непарна"
    return Question(
        key="power_parity_apply",
        statement=(
            rf"Функція $y = x^{{{n}}}$ є {kind_word}. Відомо, що $f({a}) = {v}$."
            "\nКористуючись цією властивістю (не обчислюючи степінь заново), "
            rf"знайдіть $f(-{a})$."
        ),
        parts=[Part("v", f"$f(-{a})$ =", fneg, points=1)],
        seconds=50,
        params={"n": n, "a": a},
    )


@template("root_simplify_var")
def _root_simplify_var(rng: random.Random) -> Question:
    """Спрощення кореня з буквами (застосування властивості ⁿ√(xᵏ)=x^(k/n)).
    Вважаємо змінні додатними (щоб без модуля), як у задачах заняття."""
    n = rng.choice([2, 3, 4])
    kx = rng.randint(2, 4)  # показник x у відповіді
    ky = rng.randint(2, 4)  # показник y у відповіді
    ex, ey = n * kx, n * ky  # під коренем x^(n·kx) y^(n·ky)
    ans = _x**kx * sp.Symbol("y") ** ky
    inner = rf"x^{{{ex}}} y^{{{ey}}}"
    return Question(
        key="root_simplify_var",
        statement=(
            "Спростіть вираз (вважайте $x>0$, $y>0$):\n$$" + _root_tex(n, inner) + "$$"
        ),
        parts=[Part("v", "= ", ans, kind="expr", points=1)],
        seconds=75,
        params={"n": n, "kx": kx, "ky": ky},
    )


@template("power_graph_value")
def _power_graph_value(rng: random.Random) -> Question:
    """РИСУНОК: графік степеневої y=x² (парабола); зчитати значення в точці."""
    t = rng.choice([-2, -1, 1, 2])
    y = t * t
    svg = coordinate_plane(parabolas=[(1, 0, 0)], points=[(t, y)])
    return Question(
        key="power_graph_value",
        statement=(
            "На рисунку зображено графік степеневої функції $y = x^2$ "
            "(позначено одну точку). Визначте координати цієї точки: абсцису "
            "$x$ та значення функції $y$."
        ),
        parts=[
            Part("x", "$x$ =", t, points=1),
            Part("y", "$y$ =", y, points=1),
        ],
        seconds=50,
        params={"t": t},
        svg=svg,
    )


# --- дії з коренями ------------------------------------------------------


@template("root_product")
def _root_product(rng: random.Random) -> Question:
    """Добуток коренів: √(k²m)·√m = k·m (результат цілий).
    Будуємо a=k²·m, b=m, тоді √a·√b = √(k²m²) = k·m гарантовано ціле."""
    k = rng.randint(2, 4)
    m = rng.randint(2, 5)
    a, b = k * k * m, m
    ans = k * m  # √(k²m)·√m = km
    return Question(
        key="root_product",
        statement=(
            "Обчисліть добуток коренів:\n$$\\sqrt{" + str(a) + r"} \cdot \sqrt{" + str(b) + "}$$"
        ),
        parts=[Part("v", "= ", ans, points=1)],
        seconds=50,
        params={"a": a, "b": b},
    )


@template("root_quotient")
def _root_quotient(rng: random.Random) -> Question:
    """Частка коренів: √a/√b = √(a/b) (результат цілий)."""
    r = rng.randint(2, 7)
    b = rng.randint(2, 5)
    a = r * r * b
    return Question(
        key="root_quotient",
        statement=(
            "Обчисліть частку коренів:\n$$\\dfrac{\\sqrt{" + str(a) + r"}}{\sqrt{" + str(b) + "}}$$"
        ),
        parts=[Part("v", "= ", r, points=1)],
        seconds=50,
        params={"a": a, "b": b},
    )


@template("root_simplify")
def _root_simplify(rng: random.Random) -> Question:
    """Винесення множника з-під квадратного кореня: √(k²·m) = k√m.
    Відповідь — ВИРАЗ (тут доречні клавіатура з коренем і прев'ю)."""
    k = rng.randint(2, 5)
    m = rng.choice(_NONSQUARE)
    a = k * k * m
    return Question(
        key="root_simplify",
        statement=(
            r"Винесіть множник з-під знака кореня (запишіть у вигляді $k\sqrt{m}$):"
            "\n$$\\sqrt{" + str(a) + "}$$"
        ),
        parts=[Part("v", "= ", k * sp.sqrt(m), kind="expr", points=1)],
        seconds=70,
        params={"k": k, "m": m},
    )


@template("power_of_root")
def _power_of_root(rng: random.Random) -> Question:
    """Степінь кореня: (√a)^k = a^(k/2) (ціле, бо k парне)."""
    a = rng.choice([2, 3, 5, 7])
    k = rng.choice([2, 4, 6])
    val = a ** (k // 2)
    return Question(
        key="power_of_root",
        statement=(
            "Обчисліть степінь кореня:\n$$\\left(\\sqrt{" + str(a) + f"}}\\right)^{{{k}}}$$"
        ),
        parts=[Part("v", "= ", val, points=1)],
        seconds=45,
        params={"a": a, "k": k},
    )


@template("compare_roots_lcm")
def _compare_roots_lcm(rng: random.Random) -> Question:
    """Порівняння коренів різних степенів: спільний показник — це НСК степенів."""
    n1, n2 = rng.choice([(4, 3), (6, 4), (3, 2), (6, 9), (4, 6)])
    lcm = sp.ilcm(n1, n2)
    a1, a2 = rng.randint(2, 6), rng.randint(2, 6)
    return Question(
        key="compare_roots_lcm",
        statement=(
            f"Щоб порівняти корені $\\sqrt[{n1}]{{{a1}}}$ і $\\sqrt[{n2}]{{{a2}}}$, "
            "їх зводять до спільного показника."
            "\nЗнайдіть цей спільний показник (НСК показників коренів)."
        ),
        parts=[Part("v", "показник =", int(lcm), points=1)],
        seconds=55,
        params={"n1": n1, "n2": n2},
    )


@template("root_function_domain")
def _root_function_domain(rng: random.Random) -> Question:
    """Область визначення y = ⁿ√(ax+b) для ПАРНОГО n: ax+b ≥ 0 -> x ≥ -b/a."""
    n = rng.choice([2, 4, 6])
    a = rng.choice([1, 2, 3])
    x0 = rng.randint(-5, 5)
    b = -a * x0  # межа -b/a = x0 ціла
    return Question(
        key="root_function_domain",
        statement=(
            rf"Дано функцію $y = {_root_tex(n, f'{a}x {b:+d}')}$ (корінь парного "
            "степеня)."
            "\nОбласть визначення має вигляд $[x_0; +\\infty)$. Знайдіть ліву "
            "межу $x_0$."
        ),
        parts=[Part("x0", "$x_0$ =", x0, points=1)],
        seconds=50,
        params={"n": n, "a": a, "b": b},
    )
