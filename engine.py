"""
Ядро рушія тестування: генерація параметризованих задач і перевірка відповідей.

Принципи:
  * Клієнт НІКОЛИ не отримує еталонних відповідей. Цей модуль живе тільки на сервері.
  * Параметри задачі детерміновані від (студент, тест, питання, спроба, перевидання).
    Той самий студент при перезаході бачить ті самі числа; нова спроба — нові.
  * Відповідь студента парситься в обмеженому namespace. Ніякого eval.
"""

from __future__ import annotations

import hashlib
import re as _re
import hmac
import random
from dataclasses import dataclass, field
from typing import Any, Callable

import sympy as sp
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

# --------------------------------------------------------------------------
# Детермінований seed
# --------------------------------------------------------------------------


def seed_for(
    secret: bytes,
    student_id: str,
    test_key: str,
    question_key: str,
    attempt_no: int,
    reissue: int = 0,
) -> int:
    """Seed від HMAC: передбачити свій варіант наперед неможливо без secret.

    reissue інкрементується, коли питання перевидається після обриву зв'язку —
    студент отримує ту саму задачу з іншими числами і повним часом.
    """
    msg = f"{student_id}|{test_key}|{question_key}|{attempt_no}|{reissue}".encode()
    digest = hmac.new(secret, msg, hashlib.sha256).digest()
    return int.from_bytes(digest[:8], "big")


# --------------------------------------------------------------------------
# Опис задачі
# --------------------------------------------------------------------------


@dataclass
class Part:
    """Одне поле введення. Питання складається з кількох таких — це і є
    проміжні результати."""

    key: str
    label: str  # підпис поля, LaTeX дозволений
    answer: Any  # еталон: int, float або вираз sympy
    kind: str = "number"  # "number" | "expr"
    tol: float = 1e-6
    points: float = 1.0

    # Перенесення помилки: перерахувати еталон із того, що студент ввів раніше.
    # Сигнатура: (prev: dict[str, sympy-вираз]) -> еталон | None
    # None означає "не вдалося перерахувати" — тоді звіряємо з початковим еталоном.
    carry: Callable[[dict[str, Any]], Any] | None = None
    carry_from: tuple[str, ...] = ()


@dataclass
class Question:
    key: str
    statement: str  # умова, LaTeX
    parts: list[Part]
    seconds: int = 180
    params: dict[str, Any] = field(default_factory=dict)  # для логів і розбору
    # Необов'язковий рисунок до умови: готовий inline-SVG, згенерований на
    # сервері з параметрів задачі (еталонів у ньому немає). None — без рисунка.
    svg: str | None = None

    @property
    def max_score(self) -> float:
        return sum(p.points for p in self.parts)

    def public(self) -> dict:
        """Те, що дозволено віддати в браузер. Еталонів тут немає."""
        return {
            "key": self.key,
            "statement": self.statement,
            "seconds": self.seconds,
            "svg": self.svg,
            "parts": [
                {"key": p.key, "label": p.label, "kind": p.kind, "points": p.points}
                for p in self.parts
            ],
        }


TEMPLATES: dict[str, Callable[[random.Random], Question]] = {}


def template(key: str):
    def deco(fn: Callable[[random.Random], Question]):
        TEMPLATES[key] = fn
        return fn

    return deco


def build(
    question_key: str,
    secret: bytes,
    student_id: str,
    test_key: str,
    attempt_no: int,
    reissue: int = 0,
) -> Question:
    rng = random.Random(
        seed_for(secret, student_id, test_key, question_key, attempt_no, reissue)
    )
    q = TEMPLATES[question_key](rng)
    q.key = question_key
    return q


# --------------------------------------------------------------------------
# Розбір відповіді студента
# --------------------------------------------------------------------------

_X, _Y, _T = sp.symbols("x y t")

ALLOWED = {
    "x": _X,
    "y": _Y,
    "t": _T,
    "pi": sp.pi,
    "e": sp.E,
    "sqrt": sp.sqrt,
    "abs": sp.Abs,
    "exp": sp.exp,
    "ln": sp.log,
    "log": sp.log,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "cot": sp.cot,
    "tg": sp.tan,   # укр. шкільне позначення тангенса (tg = tan)
    "ctg": sp.cot,  # укр. шкільне позначення котангенса (ctg = cot)
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
}

TRANSFORMS = standard_transformations + (implicit_multiplication_application,)

# Трансформації sympy збирають дерево через Integer/Float/Symbol, тому порожній
# global_dict їх ламає. Кладемо рівно необхідне — і нічого зі stdlib.
SAFE_GLOBALS: dict[str, Any] = {
    "Integer": sp.Integer,
    "Float": sp.Float,
    "Rational": sp.Rational,
    "Symbol": sp.Symbol,
}
SAFE_GLOBALS.update(ALLOWED)

_FORBIDDEN = ("__", "lambda", "import", "exec", "eval", "open", "globals", "getattr")


class BadInput(ValueError):
    pass


def _split_numbers(s: str) -> list[str]:
    out, cur = [], ""
    for ch in s:
        if ch.isdigit():
            cur += ch
        else:
            if cur:
                out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    return out


def parse_answer(raw: str, kind: str = "number"):
    """Перетворює введений рядок на вираз sympy. Кидає BadInput на сміття.

    ВАЖЛИВО: викликати з жорстким таймаутом у воркері (sympy вішається на
    зловмисно підібраному вводі, напр. 9**9**9). Див. safe_check нижче.
    """
    s = (raw or "").strip()
    if not s:
        raise BadInput("порожня відповідь")
    if len(s) > 200:
        raise BadInput("надто довгий вираз")
    low = s.lower()
    for bad in _FORBIDDEN:
        if bad in low:
            raise BadInput("недопустимий символ")
    # Степенева вежа виду 9**9**9 вішає sympy НА ЕТАПІ ПАРСИНГУ, тобто
    # до будь-якої нашої перевірки. Ріжемо синтаксично, ще до parse_expr.
    powered = s.replace("^", "**")
    if powered.count("**") > 4:
        raise BadInput("надто складний вираз")
    # 9**9**9 — права асоціативність дає 9**387420489 і вішає sympy.
    # Шукаємо два ** підряд через один атом: x**2+y**2 сюди не потрапляє,
    # бо між ними стоїть знак операції.
    if _re.search(r"\*\*\s*[A-Za-z0-9.]+\s*\*\*", powered):
        raise BadInput("надто складний вираз")
    for exponent in _re.findall(r"\*\*\s*(\d+)", powered):
        if int(exponent) > 12:
            raise BadInput("надто великий показник степеня")
    if any(len(tok) > 9 for tok in _split_numbers(powered)):
        raise BadInput("надто велике число")
    if kind == "number":
        s = s.replace(",", ".")  # десяткова кома
    s = s.replace("^", "**")
    try:
        expr = parse_expr(
            s, local_dict=ALLOWED, global_dict=SAFE_GLOBALS, transformations=TRANSFORMS
        )
    except Exception as exc:  # noqa: BLE001
        raise BadInput(f"не вдалося розібрати: {exc}") from exc
    if expr.free_symbols - {_X, _Y, _T}:
        raise BadInput("невідома змінна у відповіді")
    return expr


def equal(got, expected, tol: float = 1e-6) -> bool:
    """Порівняння з точністю до алгебраїчної еквівалентності.
    3/4, 0.75 і sqrt(9)/4 — одне й те саме."""
    try:
        diff = sp.simplify(sp.sympify(got) - sp.sympify(expected))
    except Exception:  # noqa: BLE001
        return False
    if diff == 0:
        return True
    try:
        return abs(complex(diff.evalf())) <= tol
    except Exception:  # noqa: BLE001
        return False


# --------------------------------------------------------------------------
# Оцінювання питання
# --------------------------------------------------------------------------


def grade(question: Question, submitted: dict[str, str]) -> dict:
    """submitted: {part_key: сирий рядок}. Повертає бали і розбір по частинах.

    Частини обробляються по порядку, щоб carry бачив уже розібрані попередні
    відповіді студента.
    """
    parsed: dict[str, Any] = {}
    detail: list[dict] = []
    total = 0.0

    for part in question.parts:
        raw = submitted.get(part.key, "")
        expected = part.answer
        carried = False

        if part.carry and all(k in parsed for k in part.carry_from):
            alt = part.carry(parsed)
            if alt is not None and not equal(alt, part.answer, part.tol):
                expected = alt  # студент помилився раніше — звіряємо з його ж логікою
                carried = True

        try:
            value = parse_answer(raw, part.kind)
            parsed[part.key] = value
            ok = equal(value, expected, part.tol)
        except BadInput as exc:
            value, ok = None, False
            detail.append(
                {
                    "part": part.key,
                    "raw": raw,
                    "score": 0.0,
                    "max": part.points,
                    "error": str(exc),
                }
            )
            continue

        score = part.points if ok else 0.0
        total += score
        detail.append(
            {
                "part": part.key,
                "raw": raw,
                "score": score,
                "max": part.points,
                "carried": carried,  # бал за перенесену помилку — позначаємо для статистики
            }
        )

    return {"score": total, "max": question.max_score, "parts": detail}


# ==========================================================================
# Шаблони задач
# ==========================================================================
#
# Прийом, що економить найбільше часу: спершу задаємо ВІДПОВІДЬ цілими
# числами, потім із неї виводимо умову. Красиві числа без перебору.


@template("linear_system_2x2")
def _linear_system(rng: random.Random) -> Question:
    while True:
        a, b, c, d = (rng.randint(-9, 9) for _ in range(4))
        det = a * d - b * c
        if det != 0 and abs(det) <= 40 and a and d:
            break
    x0, y0 = rng.randint(-6, 6), rng.randint(-6, 6)
    e, f = a * x0 + b * y0, c * x0 + d * y0

    def carry_x(prev):
        D = prev.get("det")
        if D is None or D == 0:
            return None
        return (e * d - b * f) / D

    def carry_y(prev):
        D = prev.get("det")
        if D is None or D == 0:
            return None
        return (a * f - e * c) / D

    return Question(
        key="linear_system_2x2",
        statement=(
            "Розв'яжіть систему методом Крамера:\n"
            rf"$$\begin{{cases}}{a}x {b:+}y = {e}\\{c}x {d:+}y = {f}\end{{cases}}$$"
        ),
        parts=[
            Part("det", r"Головний визначник $\Delta$ =", det, points=1),
            Part("x", "$x$ =", x0, points=1, carry=carry_x, carry_from=("det",)),
            Part("y", "$y$ =", y0, points=1, carry=carry_y, carry_from=("det",)),
        ],
        seconds=150,
        params={"a": a, "b": b, "c": c, "d": d, "e": e, "f": f},
    )


@template("quadratic_roots")
def _quadratic(rng: random.Random) -> Question:
    while True:
        x1, x2 = rng.randint(-8, 8), rng.randint(-8, 8)
        a = rng.choice([1, 1, 2, -1, 3])
        if x1 != x2:
            break
    b, c = -a * (x1 + x2), a * x1 * x2
    disc = b * b - 4 * a * c
    lo, hi = min(x1, x2), max(x1, x2)

    def carry_lo(prev):
        D = prev.get("disc")
        if D is None:
            return None
        r1, r2 = (-b - sp.sqrt(D)) / (2 * a), (-b + sp.sqrt(D)) / (2 * a)
        return sp.Min(r1, r2)

    def carry_hi(prev):
        D = prev.get("disc")
        if D is None:
            return None
        r1, r2 = (-b - sp.sqrt(D)) / (2 * a), (-b + sp.sqrt(D)) / (2 * a)
        return sp.Max(r1, r2)

    return Question(
        key="quadratic_roots",
        statement=rf"Розв'яжіть рівняння: ${a}x^2 {b:+}x {c:+} = 0$",
        parts=[
            Part("disc", "Дискримінант $D$ =", disc, points=1),
            Part("lo", "Менший корінь =", lo, points=1, carry=carry_lo, carry_from=("disc",)),
            Part("hi", "Більший корінь =", hi, points=1, carry=carry_hi, carry_from=("disc",)),
        ],
        seconds=120,
        params={"a": a, "b": b, "c": c},
    )


@template("derivative_at_point")
def _derivative(rng: random.Random) -> Question:
    a, b, n = rng.randint(2, 7), rng.randint(1, 9), rng.choice([2, 3])
    x0 = rng.randint(1, 4)
    inner = a * _X**n + b
    f = inner * sp.cos(_X) if rng.random() < 0.5 else inner * sp.exp(_X)
    df = sp.simplify(sp.diff(f, _X))

    return Question(
        key="derivative_at_point",
        statement=(
            rf"Дано $f(x) = {sp.latex(f)}$." "\n"
            rf"Знайдіть похідну та її значення в точці $x_0 = {x0}$."
        ),
        parts=[
            Part("df", "$f'(x)$ =", df, kind="expr", points=2),
            Part(
                "value",
                rf"$f'({x0})$ =",
                sp.simplify(df.subs(_X, x0)),
                points=1,
                carry=lambda prev: (
                    sp.simplify(prev["df"].subs(_X, x0)) if "df" in prev else None
                ),
                carry_from=("df",),
            ),
        ],
        seconds=240,
        params={"f": str(f), "x0": x0},
    )


# --------------------------------------------------------------------------
# Обгортка з жорстким таймаутом
# --------------------------------------------------------------------------


def _worker(args) -> dict:
    qk, secret, student_id, test_key, attempt_no, reissue, submitted = args
    q = build(qk, secret, student_id, test_key, attempt_no, reissue)
    return grade(q, submitted)


def safe_grade(
    question_key: str,
    secret: bytes,
    student_id: str,
    test_key: str,
    attempt_no: int,
    submitted: dict[str, str],
    reissue: int = 0,
    timeout: float = 3.0,
) -> dict:
    """Оцінювання в окремому процесі з жорстким лімітом часу.

    У воркер передаються лише координати задачі, а не сам об'єкт: Question
    містить замикання в carry і не серіалізується. Заразом це означає, що
    еталони не подорожують між процесами — вони перераховуються на місці.

    Синтаксичні фільтри в parse_answer ловлять відомі атаки, але sympy — це
    повноцінна CAS, і припускати, що ви передбачили все, не можна.
    На проді викликати саме цю функцію, а не grade().
    """
    import concurrent.futures as _cf

    args = (question_key, secret, student_id, test_key, attempt_no, reissue, submitted)
    with _cf.ProcessPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_worker, args)
        try:
            return fut.result(timeout=timeout)
        except _cf.TimeoutError:
            for proc in pool._processes.values():
                proc.kill()
            q = build(question_key, secret, student_id, test_key, attempt_no, reissue)
            return {
                "score": 0.0,
                "max": q.max_score,
                "parts": [],
                "error": "перевірка перевищила ліміт часу",
            }
