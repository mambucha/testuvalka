"""Лекція 1: матриці, визначники та їхні властивості, метод Крамера.

Фокус: обчислення визначників (2×2, 3×3 Саррюс, трикутний), властивості
визначників, дії над матрицями (kA, A+B, aA+bB, транспонування) і метод Крамера
(2×2 — у engine.py; 3×3 — ЧАСТКОВО: головний визначник + одна невідома).

Прийом: спершу задаємо цілу відповідь, потім із неї виводимо умову — усі
відповіді цілі (зручні числа). Конвенція запису: проза текстом, математика в
$...$ / $$...$$, переноси рядків — \n.
"""

from __future__ import annotations

import random

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


@template("det_scalar_multiple")
def _det_scalar_multiple(rng: random.Random) -> Question:
    """Властивість: множення матриці n×n на число c множить визначник на c^n."""
    base = rng.choice([-1, 1]) * rng.randint(2, 9)  # Δ(A)
    c = rng.choice([2, 3, -2])
    ans = (c ** 3) * base  # 3×3 -> c^3
    return Question(
        key="det_scalar_multiple",
        statement=(
            rf"Матриця $A$ має розмір $3\times3$, її визначник $\Delta(A) = {base}$."
            "\n"
            rf"Знайдіть визначник матриці ${c}A$ (кожен елемент помножено на ${c}$)."
        ),
        parts=[Part("d", f"$\\Delta({c}A)$ =", ans, points=1)],
        seconds=60,
        params={"base": base, "c": c},
    )


# --- дії над матрицями ---------------------------------------------------


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


@template("matrix_transpose_element")
def _matrix_transpose_element(rng: random.Random) -> Question:
    while True:
        m = [[rng.randint(-6, 6) for _ in range(3)] for _ in range(3)]
        i, j = rng.randint(1, 3), rng.randint(1, 3)
        val = m[j - 1][i - 1]  # (A^T)_{ij} = A_{ji}
        if val != 0:
            break
    return Question(
        key="matrix_transpose_element",
        statement=(
            f"Знайдіть елемент $(A^T)_{{{i}{j}}}$ транспонованої матриці:\n$$A = "
            + _bmatrix(m)
            + "$$"
        ),
        parts=[Part("e", f"$(A^T)_{{{i}{j}}}$ =", val, points=1)],
        seconds=45,
        params={"m": m, "i": i, "j": j},
    )


@template("matrix_linear_combination_element")
def _matrix_linear_combination_element(rng: random.Random) -> Question:
    while True:
        A = [[rng.randint(-5, 5) for _ in range(3)] for _ in range(3)]
        B = [[rng.randint(-5, 5) for _ in range(3)] for _ in range(3)]
        a = rng.choice([-3, -2, 2, 3])
        bcoef = rng.choice([-3, -2, 2, 3])
        i, j = rng.randint(1, 3), rng.randint(1, 3)
        val = a * A[i - 1][j - 1] + bcoef * B[i - 1][j - 1]
        if val != 0:
            break
    return Question(
        key="matrix_linear_combination_element",
        statement=(
            rf"Дано матриці $A$, $B$ і числа $a={a}$, $b={bcoef}$. "
            rf"Знайдіть елемент $(aA + bB)_{{{i}{j}}}$:\n$$A = "
            + _bmatrix(A)
            + r",\quad B = "
            + _bmatrix(B)
            + "$$"
        ),
        parts=[Part("e", f"$(aA+bB)_{{{i}{j}}}$ =", val, points=1)],
        seconds=60,
        params={"A": A, "B": B, "a": a, "b": bcoef, "i": i, "j": j},
    )


# --- метод Крамера (3×3, ЧАСТКОВО: Δ + одна невідома) --------------------


@template("cramer_3x3")
def _cramer_3x3(rng: random.Random) -> Question:
    """Частковий Крамер: знайти головний визначник Δ і ОДНУ невідому (не всі
    три) — легше за арифметикою, але метод той самий (заміна стовпця на вільні
    члени + ділення). Перенесення помилки: x_k рахується зі студентового Δ."""
    while True:
        A = [[rng.randint(-3, 3) for _ in range(3)] for _ in range(3)]
        det = _det3(A)
        if det != 0 and abs(det) <= 40:
            break
    x = [rng.randint(-4, 4) for _ in range(3)]
    b = [sum(A[r][c] * x[c] for c in range(3)) for r in range(3)]

    k = rng.randint(0, 2)  # яку невідому шукати (0 -> x_1)
    Ak = [[b[r] if c == k else A[r][c] for c in range(3)] for r in range(3)]
    Dk = _det3(Ak)  # = det * x[k]

    def carry_xk(prev):
        d = prev.get("det")
        if d is None or d == 0:
            return None
        return Dk / d  # x_k зі студентового визначника

    var = f"x_{k + 1}"
    return Question(
        key="cramer_3x3",
        statement=(
            r"Розв'яжіть систему методом Крамера. Знайдіть головний визначник "
            rf"$\Delta$ та невідому ${var}$:" + "\n" + _system_latex(A, b)
        ),
        parts=[
            Part("det", r"$\Delta$ =", det, points=1),
            Part(f"{var}", f"${var}$ =", x[k], points=1, carry=carry_xk, carry_from=("det",)),
        ],
        seconds=210,
        params={"A": A, "b": b, "var": var},
    )
