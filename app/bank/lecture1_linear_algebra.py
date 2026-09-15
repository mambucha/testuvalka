"""Лекція 1: визначники та системи лінійних рівнянь (Крамер, Гаус).

Формат — «кілька полів із проміжними результатами» там, де він природний
(Крамер: Δ -> x_i, з перенесенням помилки), і одне поле для швидких обчислень
(визначник, мінор, доповнення). Прийом: спершу задаємо цілу відповідь, потім із
неї виводимо умову.

Конвенція запису: проза текстом, математика в $...$ / $$...$$, переноси — \n.
Крамер 2×2 вже є в engine.py як `linear_system_2x2`.
"""

from __future__ import annotations

import random

import sympy as sp

from engine import Part, Question, template


# --- допоміжні для LaTeX і обчислень ------------------------------------


def _rows_latex(rows):
    return r"\\".join(" & ".join(str(x) for x in r) for r in rows)


def _vmatrix(rows):
    return r"\begin{vmatrix}" + _rows_latex(rows) + r"\end{vmatrix}"


def _bmatrix(rows):
    return r"\begin{bmatrix}" + _rows_latex(rows) + r"\end{bmatrix}"


def _det3(m):
    return (
        m[0][0] * m[1][1] * m[2][2]
        + m[0][1] * m[1][2] * m[2][0]
        + m[0][2] * m[1][0] * m[2][1]
        - m[0][2] * m[1][1] * m[2][0]
        - m[0][1] * m[1][0] * m[2][2]
        - m[0][0] * m[1][2] * m[2][1]
    )


def _lin_row(coeffs, rhs, varnames=("x_1", "x_2", "x_3")):
    """Рядок рівняння: [2,-3,1],5 -> '2x_1 - 3x_2 + x_3 = 5'."""
    terms = []
    for k, v in zip(coeffs, varnames):
        if k == 0:
            continue
        mag = abs(k)
        coef = "" if mag == 1 else str(mag)
        if not terms:
            terms.append(("-" if k < 0 else "") + coef + v)
        else:
            terms.append((" + " if k > 0 else " - ") + coef + v)
    if not terms:
        terms.append("0")
    return "".join(terms) + f" = {rhs}"


def _system_latex(A, b):
    rows = [_lin_row(A[r], b[r]) for r in range(len(A))]
    return r"$$\begin{cases}" + r"\\".join(rows) + r"\end{cases}$$"


# --- визначники ----------------------------------------------------------


@template("det_2x2")
def _det_2x2(rng: random.Random) -> Question:
    while True:
        a, b, c, d = (rng.randint(-6, 6) for _ in range(4))
        val = a * d - b * c
        if val != 0 and abs(val) <= 50:
            break
    return Question(
        key="det_2x2",
        statement="Обчисліть визначник:\n$$" + _vmatrix([[a, b], [c, d]]) + "$$",
        parts=[Part("d", r"$\Delta$ =", val, points=1)],
        seconds=60,
        params={"a": a, "b": b, "c": c, "d": d},
    )


@template("det_3x3_sarrus")
def _det_3x3_sarrus(rng: random.Random) -> Question:
    while True:
        m = [[rng.randint(-4, 4) for _ in range(3)] for _ in range(3)]
        val = _det3(m)
        if val != 0 and abs(val) <= 120:
            break
    return Question(
        key="det_3x3_sarrus",
        statement="Обчисліть визначник (правило Саррюса):\n$$" + _vmatrix(m) + "$$",
        parts=[Part("d", r"$\Delta$ =", val, points=1)],
        seconds=120,
        params={"m": m},
    )


@template("det_triangular")
def _det_triangular(rng: random.Random) -> Question:
    while True:
        diag = [rng.randint(-5, 5) for _ in range(3)]
        if all(diag) and abs(diag[0] * diag[1] * diag[2]) <= 60:
            break
    upper = rng.random() < 0.5
    m = [[0, 0, 0] for _ in range(3)]
    for r in range(3):
        for c in range(3):
            if r == c:
                m[r][c] = diag[r]
            elif (c > r and upper) or (c < r and not upper):
                m[r][c] = rng.randint(-4, 4)
    val = diag[0] * diag[1] * diag[2]
    return Question(
        key="det_triangular",
        statement="Обчисліть визначник трикутної матриці:\n$$" + _vmatrix(m) + "$$",
        parts=[Part("d", r"$\Delta$ =", val, points=1)],
        seconds=60,
        params={"m": m},
    )


@template("minor_3x3")
def _minor_3x3(rng: random.Random) -> Question:
    while True:
        m = [[rng.randint(-4, 4) for _ in range(3)] for _ in range(3)]
        i, j = rng.randint(1, 3), rng.randint(1, 3)
        sub = [[m[r][c] for c in range(3) if c != j - 1] for r in range(3) if r != i - 1]
        minor = sub[0][0] * sub[1][1] - sub[0][1] * sub[1][0]
        if minor != 0 and abs(minor) <= 50:
            break
    return Question(
        key="minor_3x3",
        statement=(
            f"Для матриці знайдіть мінор $M_{{{i}{j}}}$ "
            f"(викресліть {i}-й рядок і {j}-й стовпець):\n$$" + _bmatrix(m) + "$$"
        ),
        parts=[Part("m", f"$M_{{{i}{j}}}$ =", minor, points=1)],
        seconds=90,
        params={"m": m, "i": i, "j": j},
    )


@template("cofactor_3x3")
def _cofactor_3x3(rng: random.Random) -> Question:
    while True:
        m = [[rng.randint(-4, 4) for _ in range(3)] for _ in range(3)]
        i, j = rng.randint(1, 3), rng.randint(1, 3)
        sub = [[m[r][c] for c in range(3) if c != j - 1] for r in range(3) if r != i - 1]
        minor = sub[0][0] * sub[1][1] - sub[0][1] * sub[1][0]
        cof = ((-1) ** (i + j)) * minor
        if cof != 0 and abs(cof) <= 50:
            break
    return Question(
        key="cofactor_3x3",
        statement=(
            f"Знайдіть алгебраїчне доповнення $A_{{{i}{j}}}$ елемента матриці:\n$$"
            + _bmatrix(m)
            + "$$"
        ),
        parts=[Part("a", f"$A_{{{i}{j}}}$ =", cof, points=1)],
        seconds=100,
        params={"m": m, "i": i, "j": j},
    )


# --- операції над матрицями ---------------------------------------------


@template("matrix_scalar_element")
def _matrix_scalar_element(rng: random.Random) -> Question:
    while True:
        m = [[rng.randint(-6, 6) for _ in range(3)] for _ in range(3)]
        k = rng.choice([-3, -2, 2, 3, 4])
        i, j = rng.randint(1, 3), rng.randint(1, 3)
        val = k * m[i - 1][j - 1]
        if val != 0:  # уникаємо плутанини з нульовою відповіддю
            break
    return Question(
        key="matrix_scalar_element",
        statement=(
            f"Дано матрицю $A$ і число $k={k}$. Знайдіть елемент $(kA)_{{{i}{j}}}$:\n"
            f"$$A = " + _bmatrix(m) + "$$"
        ),
        parts=[Part("e", f"$(kA)_{{{i}{j}}}$ =", val, points=1)],
        seconds=45,
        params={"m": m, "k": k, "i": i, "j": j},
    )


@template("matrix_sum_element")
def _matrix_sum_element(rng: random.Random) -> Question:
    while True:
        A = [[rng.randint(-6, 6) for _ in range(3)] for _ in range(3)]
        B = [[rng.randint(-6, 6) for _ in range(3)] for _ in range(3)]
        i, j = rng.randint(1, 3), rng.randint(1, 3)
        val = A[i - 1][j - 1] + B[i - 1][j - 1]
        if val != 0:  # уникаємо плутанини з нульовою відповіддю
            break
    return Question(
        key="matrix_sum_element",
        statement=(
            f"Знайдіть елемент $(A+B)_{{{i}{j}}}$:\n$$A = "
            + _bmatrix(A)
            + r",\quad B = "
            + _bmatrix(B)
            + "$$"
        ),
        parts=[Part("e", f"$(A+B)_{{{i}{j}}}$ =", val, points=1)],
        seconds=45,
        params={"A": A, "B": B, "i": i, "j": j},
    )


# --- системи -------------------------------------------------------------


@template("cramer_3x3")
def _cramer_3x3(rng: random.Random) -> Question:
    # Спершу відповідь (x) цілими, потім матриця A з ненульовим визначником.
    while True:
        A = [[rng.randint(-3, 3) for _ in range(3)] for _ in range(3)]
        det = _det3(A)
        if det != 0 and abs(det) <= 40:
            break
    x = [rng.randint(-4, 4) for _ in range(3)]
    b = [sum(A[r][c] * x[c] for c in range(3)) for r in range(3)]

    # Δ_i — визначник із заміненим i-м стовпцем на стовпець вільних членів.
    def _replace_col(i):
        return [[b[r] if c == i else A[r][c] for c in range(3)] for r in range(3)]

    Di = [_det3(_replace_col(i)) for i in range(3)]  # Di[i] = det * x[i]

    def _carry(i):
        def f(prev):
            d = prev.get("det")
            if d is None or d == 0:
                return None
            return Di[i] / d  # x_i зі студентового визначника (перенесення помилки)

        return f

    return Question(
        key="cramer_3x3",
        statement="Розв'яжіть систему методом Крамера:\n" + _system_latex(A, b),
        parts=[
            Part("det", r"$\Delta$ =", det, points=1),
            Part("x1", "$x_1$ =", x[0], points=1, carry=_carry(0), carry_from=("det",)),
            Part("x2", "$x_2$ =", x[1], points=1, carry=_carry(1), carry_from=("det",)),
            Part("x3", "$x_3$ =", x[2], points=1, carry=_carry(2), carry_from=("det",)),
        ],
        seconds=300,
        params={"A": A, "b": b},
    )


@template("gauss_3x3")
def _gauss_3x3(rng: random.Random) -> Question:
    while True:
        A = [[rng.randint(-3, 3) for _ in range(3)] for _ in range(3)]
        if _det3(A) != 0:
            break
    x = [rng.randint(-5, 5) for _ in range(3)]
    b = [sum(A[r][c] * x[c] for c in range(3)) for r in range(3)]
    return Question(
        key="gauss_3x3",
        statement="Розв'яжіть систему методом Гауса:\n" + _system_latex(A, b),
        parts=[
            Part("x1", "$x_1$ =", x[0], points=1),
            Part("x2", "$x_2$ =", x[1], points=1),
            Part("x3", "$x_3$ =", x[2], points=1),
        ],
        seconds=300,
        params={"A": A, "b": b},
    )


@template("expansion_by_row")
def _expansion_by_row(rng: random.Random) -> Question:
    """Розклад визначника 3×3 за першим рядком: A_{1j} -> Δ (з перенесенням)."""
    while True:
        m = [[rng.randint(-4, 4) for _ in range(3)] for _ in range(3)]
        det = _det3(m)
        if det != 0 and abs(det) <= 120:
            break

    def _minor(i, j):
        sub = [[m[r][c] for c in range(3) if c != j] for r in range(3) if r != i]
        return sub[0][0] * sub[1][1] - sub[0][1] * sub[1][0]

    # Алгебраїчні доповнення першого рядка (0-based j: знак (-1)^j).
    cof = [((-1) ** j) * _minor(0, j) for j in range(3)]
    a1 = m[0]

    def carry_det(prev):
        keys = ("c11", "c12", "c13")
        if not all(k in prev for k in keys):
            return None
        return a1[0] * prev["c11"] + a1[1] * prev["c12"] + a1[2] * prev["c13"]

    return Question(
        key="expansion_by_row",
        statement=(
            "Обчисліть визначник розкладом за першим рядком: знайдіть алгебраїчні "
            "доповнення $A_{11}, A_{12}, A_{13}$ та сам визначник.\n$$" + _vmatrix(m) + "$$"
        ),
        parts=[
            Part("c11", r"$A_{11}$ =", cof[0], points=1),
            Part("c12", r"$A_{12}$ =", cof[1], points=1),
            Part("c13", r"$A_{13}$ =", cof[2], points=1),
            Part(
                "det",
                r"$\Delta$ =",
                det,
                points=1,
                carry=carry_det,
                carry_from=("c11", "c12", "c13"),
            ),
        ],
        seconds=180,
        params={"m": m},
    )


@template("determinant_property")
def _determinant_property(rng: random.Random) -> Question:
    """Властивості визначника: як зміниться Δ після операції над рядками."""
    base = rng.choice([-1, 1]) * rng.randint(2, 12)
    variant = rng.choice(["mult", "transpose", "swap", "addrow"])
    if variant == "mult":
        k = rng.choice([2, 3, -2])
        ans = base * k
        desc = f"один рядок помножено на ${k}$"
    elif variant == "transpose":
        ans = base
        desc = "матрицю транспоновано"
    elif variant == "swap":
        ans = -base
        desc = "переставлено місцями два рядки"
    else:  # addrow
        ans = base
        desc = "до одного рядка додано інший, помножений на число"
    return Question(
        key="determinant_property",
        statement=(
            rf"Відомо, що визначник квадратної матриці $A$ дорівнює $\Delta = {base}$."
            "\n"
            f"Знайдіть визначник матриці, отриманої з $A$ так: {desc}."
        ),
        parts=[Part("d", r"$\Delta'$ =", ans, points=1)],
        seconds=60,
        params={"base": base, "variant": variant},
    )


@template("inverse_2x2")
def _inverse_2x2(rng: random.Random) -> Question:
    """Обернена 2×2: Δ + чотири елементи A^{-1} (з перенесенням від Δ).

    Тримаємо |Δ| = 1 — тоді елементи оберненої ЦІЛІ (зручні числа). Дробові
    відповіді grader теж приймає (напр. 3/2 чи 1.5), але тут їх свідомо уникаємо.
    """
    while True:
        a, b, c, d = (rng.randint(-5, 5) for _ in range(4))
        det = a * d - b * c
        if det in (1, -1):
            break
    adj = {"b11": d, "b12": -b, "b21": -c, "b22": a}  # приєднана / транспонована
    inv = {key: sp.Rational(val, det) for key, val in adj.items()}

    def _carry(entry):
        num = adj[entry]

        def f(prev):
            D = prev.get("det")
            if D is None or D == 0:
                return None
            return num / D

        return f

    def _p(entry, label):
        return Part(entry, label, inv[entry], points=1, carry=_carry(entry), carry_from=("det",))

    return Question(
        key="inverse_2x2",
        statement=(
            "Знайдіть визначник і елементи оберненої матриці $A^{-1}$:\n$$A = "
            + _bmatrix([[a, b], [c, d]])
            + "$$"
        ),
        parts=[
            Part("det", r"$\Delta$ =", det, points=1),
            _p("b11", r"$(A^{-1})_{11}$ ="),
            _p("b12", r"$(A^{-1})_{12}$ ="),
            _p("b21", r"$(A^{-1})_{21}$ ="),
            _p("b22", r"$(A^{-1})_{22}$ ="),
        ],
        seconds=240,
        params={"a": a, "b": b, "c": c, "d": d},
    )
