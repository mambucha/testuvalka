"""Степенева функція та корені — КОМПЛЕКСНИЙ набір (чинний theme2).

Окрім звичних перевірок тут НЕЗАЛЕЖНО перераховується математика кожної задачі
(напр. для раціоналізації: результат × знаменник має дорівнювати чисельнику),
а також закріплено вади, які траплялися в згенерованих варіантах: доданки, що
взаємно знищуються, нульова відповідь, підстановка x=±1, яка вироджує задачу.
"""

import re

import sympy as sp

import engine
from app.config import SECRET

# Літеральний "\n" замість переносу — типова помилка raw-рядка. АЛЕ \ne, \nu —
# валідні команди LaTeX, тож рахуємо лише ті випадки, де далі не латинська літера.
_BAD_NEWLINE = re.compile(r"\\n(?![a-zA-Z])")

POWER_KEYS = [
    "pr_power_values",
    "pr_negative_power",
    "pr_find_exponent",
    "pr_solve_even_power",
    "pr_solve_odd_power",
    "pr_domain_even_root",
]
ROOT_KEYS = [
    "pr_root_of_power_letters",
    "pr_modulus_root",
    "pr_factor_out_letters",
    "pr_simplify_letters",
    "pr_collect_radicals",
    "pr_root_sum_letters",
]
KEYS = POWER_KEYS + ROOT_KEYS
_x, _y = sp.Symbol("x"), sp.Symbol("y")


def _build(key, i):
    return engine.build(key, SECRET, f"учень|{i}", "theme2", 1, 0)


def _a(q):
    return {p.key: p.answer for p in q.parts}


def test_has_12_types_balanced_6_and_6():
    assert len(KEYS) == len(set(KEYS)) == 12
    assert len(POWER_KEYS) == len(ROOT_KEYS) == 6


def test_all_grade_full_on_correct_answers():
    for key in KEYS:
        for i in range(25):
            q = _build(key, i)
            sub = {p.key: str(p.answer) for p in q.parts}
            r = engine.grade(q, sub)
            assert r["score"] == r["max"] == q.max_score, (key, i, r, sub)


def test_garbage_gets_zero():
    for key in KEYS:
        q = _build(key, 4)
        assert engine.grade(q, {p.key: "123456" for p in q.parts})["score"] == 0.0, key


def test_statements_katex_no_literal_newline():
    for key in KEYS:
        q = _build(key, 1)
        assert "$" in q.statement, key
        assert not _BAD_NEWLINE.search(q.statement), key


def test_every_task_is_multistep():
    for key in KEYS:
        assert len(_build(key, 1).parts) >= 2, key


def test_no_rational_exponent_notation():
    """Степеня з раціональним показником тут бути не повинно — це інша тема."""
    for key in KEYS:
        for i in range(10):
            s = _build(key, i).statement
            assert "frac{1}{2}}" not in s.replace(" ", ""), (key, "показник-дріб")
            assert "^{m/n}" not in s, key


def test_timings_calibrated():
    total = 0
    for key in KEYS:
        q = _build(key, 1)
        assert 90 <= q.seconds <= 200, (key, q.seconds)
        total += q.seconds
    assert total <= 1800, total


# --- незалежна перевірка математики --------------------------------------

def test_power_values_math():
    for i in range(30):
        q = _build("pr_power_values", i)
        p, a = q.params, _a(q)
        base = sp.Rational(p["p"], p["q"])
        assert a["v1"] == base ** p["n"] and a["v2"] == (-base) ** p["n"]
        assert sp.denom(a["v1"]) != 1, "відповідь має бути дробом (не під калькулятор)"


def test_negative_power_math():
    for i in range(30):
        q = _build("pr_negative_power", i)
        p, a = q.params, _a(q)
        assert a["v1"] == sp.Rational(1, p["a"] ** p["n"])
        assert a["v2"] == sp.Rational(1, (-p["a"]) ** p["n"])


def test_find_exponent_math():
    """Показник однозначно відновлюється з точки, а друге значення — з парності."""
    for i in range(30):
        q = _build("pr_find_exponent", i)
        p, a = q.params, _a(q)
        assert p["a"] ** a["n"] == p["y"]          # точка справді на графіку
        assert a["val"] == (-p["a"]) ** a["n"]     # парність застосована
        # показник натуральний і єдиний для цієї точки
        others = [k for k in range(1, 13) if p["a"] ** k == p["y"]]
        assert others == [a["n"]], (p, others)


def test_solve_even_power_math():
    for i in range(30):
        q = _build("pr_solve_even_power", i)
        p, a = q.params, _a(q)
        n = 2 * p["k"]
        assert (a["lo"] - p["c"]) ** n == p["a"] == (a["hi"] - p["c"]) ** n
        assert a["lo"] < a["hi"]


def test_solve_odd_power_math():
    for i in range(30):
        q = _build("pr_solve_odd_power", i)
        p, a = q.params, _a(q)
        assert a["root"] ** p["n"] == p["a"]
        assert (a["x"] - p["c"]) ** p["n"] == p["a"]


def test_domain_even_root_math():
    for i in range(30):
        q = _build("pr_domain_even_root", i)
        p, a = q.params, _a(q)
        assert p["b"] - p["a"] * a["bound"] == 0
        assert p["b"] - p["a"] * p["x0"] == a["val"] ** p["n"]


def test_root_of_power_letters_math():
    """Спрощений вираз у степені n має дати підкореневий."""
    for i in range(30):
        q = _build("pr_root_of_power_letters", i)
        p, a = q.params, _a(q)
        coef = -(p["c"] ** p["n"]) if p["neg"] else p["c"] ** p["n"]
        assert sp.simplify(a["simp"] ** p["n"] - coef * _x ** p["n"]) == 0
        assert a["simp"].has(_x), "відповідь має бути в буквах"
        assert p["x0"] != 1


def test_modulus_root_is_nonnegative_for_negative_x():
    for i in range(30):
        q = _build("pr_modulus_root", i)
        p, a = q.params, _a(q)
        assert sp.simplify(a["simp"] - (-p["c"] * _x)) == 0
        assert a["val"] > 0, "корінь парного степеня невід'ємний"
        assert p["x0"] < -1


def test_factor_out_letters_math():
    """(множник перед коренем)^n * (те, що під коренем) = підкореневий вираз."""
    degrees = set()
    for i in range(40):
        q = _build("pr_factor_out_letters", i)
        p, a = q.params, _a(q)
        n = p["n"]
        degrees.add(n)
        assert sp.simplify(a["coef"] ** n * a["rad"] - p["inner"] * _x**n) == 0
        assert a["rad"] == p["r"]
    assert degrees == {2, 3}, ("корінь має бути не лише квадратним", degrees)


def test_simplify_letters_math():
    for i in range(30):
        q = _build("pr_simplify_letters", i)
        p, a = q.params, _a(q)
        n, k, m = p["n"], p["k"], p["m"]
        assert sp.simplify(a["simp"] ** n - _x ** (n * k) * _y ** (n * m)) == 0
        assert p["y0"] != 1, "y=1 не впливав би на результат"


def test_collect_radicals_math():
    degrees = set()
    for i in range(50):
        q = _build("pr_collect_radicals", i)
        p, a = q.params, _a(q)
        n = p["n"]
        degrees.add(n)
        assert p["c2"] != p["c3"], "доданки взаємно знищуються"
        assert a["coef"] == p["c1"] + p["c2"] - p["c3"] > 0
        assert a["rad"] == p["r"]
        # кожен доданок справді зводиться до спільного кореня
        for c in (p["c1"], p["c2"], p["c3"]):
            assert sp.root((c**n) * p["r"], n) == c * sp.root(p["r"], n)
    assert degrees == {2, 3}, ("корінь має бути не лише квадратним", degrees)


def test_root_sum_letters_math():
    for i in range(30):
        q = _build("pr_root_sum_letters", i)
        p, a = q.params, _a(q)
        assert sp.simplify(a["t1"] - p["c1"] * _x) == 0
        assert sp.simplify(a["t2"] - p["c2"] * _x) == 0
        assert sp.simplify(a["total"] - (p["c1"] + p["c2"]) * _x) == 0


def test_rationalize_math():
    """ЗАПАСНИЙ шаблон (у тест не входить). Найсильніша перевірка: результат × знаменник = чисельник."""
    for i in range(30):
        q = _build("pr_rationalize", i)
        p, a = q.params, _a(q)
        denom = sp.sqrt(p["a"]) - sp.sqrt(p["b"])
        assert sp.simplify(a["res"] * denom - p["c"]) == 0
        assert sp.simplify(a["conj"] - (sp.sqrt(p["a"]) + sp.sqrt(p["b"]))) == 0
        assert sp.simplify(a["res"] - a["conj"]) != 0, "відповідь збіглася зі сполученим"


# --- перенесення помилки --------------------------------------------------

def test_carry_only_where_the_step_changes_the_value():
    """Для НЕПАРНОГО n перенесення працює: знак справді змінюється, тож студент
    показав застосування парності. Для ПАРНОГО n перенесення свідомо немає —
    інакше однакове сміття у двох полях зараховувалося б."""
    odd_seen = even_seen = 0
    for i in range(40):
        q = _build("pr_power_values", i)
        n = q.params["n"]
        wrong = _a(q)["v1"] + 1
        mine = wrong * (1 if n % 2 == 0 else -1)
        r = engine.grade(q, {"v1": str(wrong), "v2": str(mine)})
        if n % 2:
            assert r["score"] == 1.0, ("непарний n: крок мав перенестися", i, r)
            odd_seen += 1
        else:
            assert r["score"] == 0.0, ("парний n: перенесення бути не повинно", i, r)
            even_seen += 1
    assert odd_seen and even_seen, (odd_seen, even_seen)


def test_carry_wrong_term_keeps_sum_step():
    """Помилився в одному доданку, але суму склав зі СВОЇХ — крок зараховано."""
    for i in range(10):
        q = _build("pr_root_sum_letters", i)
        a = _a(q)
        bad_t1 = a["t1"] + _x
        r = engine.grade(q, {
            "t1": str(bad_t1), "t2": str(a["t2"]), "total": str(bad_t1 + a["t2"]),
        })
        assert r["score"] == 2.0 and r["max"] == 3, (i, r)
