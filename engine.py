"""
Ядро рушія тестування: генерація параметризованих задач і перевірка відповідей.

Принципи:
  * Клієнт НІКОЛИ не отримує еталонних відповідей. Цей модуль живе тільки на сервері.
  * Параметри задачі детерміновані від (студент, тест, питання, спроба, перевидання).
    Той самий студент при перезаході бачить ті самі числа; нова спроба – нові.
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

    reissue інкрементується, коли питання перевидається після обриву зв'язку –
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
    """Одне поле введення. Питання складається з кількох таких – це і є
    проміжні результати."""

    key: str
    label: str  # підпис поля, LaTeX дозволений
    answer: Any  # еталон: int, float або вираз sympy
    kind: str = "number"  # "number" | "expr"
    tol: float = 1e-6
    points: float = 1.0

    # Вважати x, y, t додатними під час звіряння. Потрібно там, де вираз і так
    # означений лише для додатних значень (степінь з раціональним показником).
    # Без цього sympy не ототожнює sqrt(x*y) і sqrt(x)*sqrt(y) – і має рацію,
    # бо для від'ємних це різні вирази.
    positive: bool = False

    # Перенесення помилки: перерахувати еталон із того, що студент ввів раніше.
    # Сигнатура: (prev: dict[str, sympy-вираз]) -> еталон | None
    # None означає "не вдалося перерахувати" – тоді звіряємо з початковим еталоном.
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
    # сервері з параметрів задачі (еталонів у ньому немає). None – без рисунка.
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
    "factorial": sp.factorial,  # «5!» sympy сам зводить до factorial(5)
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
# global_dict їх ламає. Кладемо рівно необхідне – і нічого зі stdlib.
SAFE_GLOBALS: dict[str, Any] = {
    "Integer": sp.Integer,
    "Float": sp.Float,
    "Rational": sp.Rational,
    "Symbol": sp.Symbol,
}
SAFE_GLOBALS.update(ALLOWED)

_FORBIDDEN = ("__", "lambda", "import", "exec", "eval", "open", "globals", "getattr")

# Факторіал потрібен у комбінаториці: відповідь природно писати як 10!/(7!*3!).
# Але sympy обчислює його ЖАДІБНО вже на етапі парсингу, тож factorial(10**9)
# з'їв би всю пам'ять ще до того, як спрацює таймаут воркера. Тому дозволяємо
# факторіал ЛИШЕ від цілого числа і лише до 50! – у задачах банку найбільше
# n = 26, тож запас величезний, а 50! обчислюється мікросекунди.
_FACT_LIMIT = 50
_FACT_MAX_COUNT = 6

# Показник степеня. Тема «степінь з раціональним показником» вимагає вводу
# виду x^(2/3), тож дробові показники треба і дозволити, і обмежити: старий
# шаблон бачив лише цілі числа, через що 2^(300/1) проходив повз охорону.
_POW_MAX_COUNT = 8
_EXP_LIMIT = 12
_RATIONAL_EXP = _re.compile(r"^\s*([+-]?\d+)\s*(?:/\s*(\d+))?\s*$")


class BadInput(ValueError):
    pass


def _powers(powered: str) -> list[tuple[str, int]]:
    """Для кожного `**`: текст його показника і позиція одразу після показника.

    Для `x**12` це («12», після двійки), для `x**(2/3)` це («2/3», після дужки).
    Дужки рахуємо балансом, тож вкладені `(` не збивають межу показника. Це
    потрібно, щоб побачити вежу `9**(9**9)`: регулярка її не ловила, бо після
    `**` там стоїть дужка, а не атом.
    """
    out: list[tuple[str, int]] = []
    i = 0
    while (j := powered.find("**", i)) >= 0:
        k = j + 2
        while k < len(powered) and powered[k].isspace():
            k += 1
        if k < len(powered) and powered[k] == "(":
            depth, m = 0, k
            while m < len(powered):
                if powered[m] == "(":
                    depth += 1
                elif powered[m] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                m += 1
            out.append((powered[k + 1:m], m + 1))
        else:
            m = k
            if m < len(powered) and powered[m] in "+-":
                m += 1
            while m < len(powered) and (powered[m].isdigit() or powered[m] == "."):
                m += 1
            out.append((powered[k:m], m))
        i = j + 2
    return out


def _check_powers(powered: str) -> None:
    """Степеневі вежі й завеликі показники – синтаксично, ДО parse_expr.

    sympy рахує 9**387420489 просто під час розбору, тобто до будь-якої нашої
    перевірки й до таймауту воркера.
    """
    if powered.count("**") > _POW_MAX_COUNT:
        raise BadInput("надто складний вираз")
    for exp, end in _powers(powered):
        if "**" in exp:
            raise BadInput("степінь у показнику степеня не допускається")
        if "!" in exp:
            raise BadInput("факторіал у показнику степеня не допускається")
        if powered[end:].lstrip().startswith("**"):
            raise BadInput("степенева вежа не допускається")
        m = _RATIONAL_EXP.match(exp)
        if not m:
            continue                      # показник-вираз: числом не вибухне
        num, den = int(m.group(1)), int(m.group(2) or 1)
        if den == 0:
            raise BadInput("нуль у знаменнику показника")
        if abs(num) > _EXP_LIMIT * den:
            raise BadInput(f"надто великий показник степеня (не більше {_EXP_LIMIT})")


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
    _check_powers(powered)
    # Факторіал – так само синтаксично, ДО parse_expr (див. _FACT_LIMIT вище).
    if powered.count("!") > _FACT_MAX_COUNT:
        raise BadInput("надто багато факторіалів")
    for digits in _re.findall(r"(\d*)\s*!", powered):
        if not digits:
            raise BadInput("факторіал можна брати лише від цілого числа")
        if int(digits) > _FACT_LIMIT:
            raise BadInput(f"надто великий факторіал (не більше {_FACT_LIMIT}!)")
    calls = _re.findall(r"factorial\s*\(\s*([^()]*?)\s*\)", powered)
    if len(calls) != powered.count("factorial"):
        raise BadInput("пишіть факторіал як 5! або factorial(5)")
    for arg in calls:
        if not arg.isdigit():
            raise BadInput("факторіал можна брати лише від цілого числа")
        if int(arg) > _FACT_LIMIT:
            raise BadInput(f"надто великий факторіал (не більше {_FACT_LIMIT}!)")
    # 2**10! розкрилося б у 2**3628800 – показник обходить перевірку вище.
    if _re.search(r"\*\*\s*\(?\s*\d*\s*(?:!|factorial)", powered):
        raise BadInput("факторіал у показнику степеня не допускається")
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
    3/4, 0.75 і sqrt(9)/4 – одне й те саме."""
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


_XP, _YP, _TP = sp.symbols("x_pos y_pos t_pos", positive=True)
_POSITIVE_SUBS = {_X: _XP, _Y: _YP, _T: _TP}


def as_positive(expr):
    """Той самий вираз, але зі змінними, оголошеними додатними."""
    try:
        return sp.sympify(expr).subs(_POSITIVE_SUBS)
    except Exception:  # noqa: BLE001
        return expr


def _same(part: Part, got, expected) -> bool:
    if part.positive:
        got, expected = as_positive(got), as_positive(expected)
    return equal(got, expected, part.tol)


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
            if alt is not None and not _same(part, alt, part.answer):
                expected = alt  # студент помилився раніше – звіряємо з його ж логікою
                carried = True

        try:
            value = parse_answer(raw, part.kind)
            parsed[part.key] = value
            ok = _same(part, value, expected)
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
                "carried": carried,  # бал за перенесену помилку – позначаємо для статистики
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
    еталони не подорожують між процесами – вони перераховуються на місці.

    Синтаксичні фільтри в parse_answer ловлять відомі атаки, але sympy – це
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
