"""Тематичне оцінювання за §1–§7 (функції, корені, раціональний показник).

Тест підсумковий, тож половина завдань бере готові шаблони з theme2–theme4.
Тут перевіряємо: що банк збирається саме так, як задумано, що НОВІ шаблони
рахують правильно (математику звіряємо незалежно), і що структура завдань
лишається покроковою – бо саме кроки й дають змогу бачити хід розв'язання.
"""

import math
import pathlib
import re
from fractions import Fraction

import pytest
import sympy as sp
import yaml

import engine
from app.config import SECRET

# Літеральний "\n" замість переносу; \ne, \nu – валідні команди LaTeX.
_BAD_NEWLINE = re.compile(r"\\n(?![a-zA-Z])")

# Відповідники десяти завдань контрольної роботи + два додаткові.
NEW = ["tf_domain_pair", "tf_graph_properties", "tf_bring_under_letters",
       "tf_root_of_root", "tf_domain_combined", "tf_fraction_actions",
       "tf_substitution_quartic"]
REUSED = ["rp_numeric_value", "pr_factor_out_letters", "pr_rationalize",
          "mz_simplify_sign", "rp_properties"]
KEYS = ["tf_domain_pair", "tf_graph_properties", "rp_numeric_value",
        "pr_factor_out_letters", "tf_bring_under_letters", "tf_root_of_root",
        "pr_rationalize", "tf_domain_combined", "tf_fraction_actions",
        "tf_substitution_quartic", "mz_simplify_sign", "rp_properties"]

_x, _y = sp.symbols("x y")


def _build(key, i):
    return engine.build(key, SECRET, f"учень|{i}", "functions_thematic", 1, 0)


def _a(q):
    return {p.key: p.answer for p in q.parts}


def _same(got, expected):
    return engine.equal(engine.as_positive(got), engine.as_positive(expected))


# --- склад тесту --------------------------------------------------------

def test_bank_covers_every_task_of_the_reference():
    assert len(KEYS) == len(set(KEYS)) == 12
    assert set(NEW) | set(REUSED) == set(KEYS)
    assert len(NEW) == 7 and len(REUSED) == 5


def test_yaml_bank_matches_this_module():
    data = yaml.safe_load(pathlib.Path("tests.yaml").read_text(encoding="utf-8"))
    entry = next(t for t in data if t["key"] == "functions_thematic")
    assert entry["bank"] == KEYS
    assert entry["question_count"] == 12
    assert entry["points_per_question"] == 1


def test_all_grade_full_on_correct_answers():
    for key in KEYS:
        for i in range(15):
            q = _build(key, i)
            sub = {p.key: str(p.answer) for p in q.parts}
            r = engine.grade(q, sub)
            assert r["score"] == r["max"] == q.max_score, (key, i, r, sub)


def test_garbage_gets_zero():
    for key in KEYS:
        for i in range(8):
            q = _build(key, i)
            r = engine.grade(q, {p.key: "123456" for p in q.parts})
            assert r["score"] == 0.0, (key, i, r)


def test_every_task_shows_the_solution_path():
    """Сенс роботи – бачити ХІД розв'язання, тож одного поля ніде не досить."""
    for key in KEYS:
        assert len(_build(key, 1).parts) >= 2, key


def test_statements_katex_no_literal_newline():
    for key in KEYS:
        for i in range(6):
            q = _build(key, i)
            assert "$" in q.statement, key
            assert not _BAD_NEWLINE.search(q.statement), (key, i)
            assert "- -" not in q.statement and "+ -" not in q.statement, (key, i)


def test_only_the_graph_task_has_a_figure():
    for key in KEYS:
        q = _build(key, 3)
        if key == "tf_graph_properties":
            assert q.svg and "<svg" in q.svg, key
        else:
            assert q.svg is None, key


def test_timings_calibrated():
    total = sum(_build(key, 1).seconds for key in KEYS)
    # Найважчим завданням викладач попросив додати по хвилині, тож підсумкова
    # помітно довша за тематичні тести.
    assert 1800 <= total <= 2050, total          # ~30–34 хв
    hard = {"tf_root_of_root", "tf_fraction_actions", "tf_substitution_quartic",
            "tf_bring_under_letters"}
    for key in hard:
        assert _build(key, 1).seconds >= 200, key


def test_many_variants_per_template():
    for key in KEYS:
        tuples = [tuple(str(p.answer) for p in _build(key, i).parts)
                  for i in range(60)]
        assert len(set(tuples)) >= 15, (key, len(set(tuples)))
        assert max(tuples.count(t) for t in set(tuples)) <= 10, key


def test_single_number_guess_is_weak():
    for guess in ("0", "1", "2"):
        total = count = 0
        for key in KEYS:
            for i in range(10):
                q = _build(key, i)
                total += engine.grade(
                    q, {p.key: guess for p in q.parts})["score"] / q.max_score
                count += 1
        assert total / count < 0.15, (guess, round(total / count, 3))


# =======================================================================
#  НЕЗАЛЕЖНА ПЕРЕВІРКА НОВИХ ШАБЛОНІВ
# =======================================================================

def test_domain_pair_math():
    for i in range(20):
        q = _build("tf_domain_pair", i)
        p, a = q.params, _a(q)
        # знаменник дробу обертається на нуль саме там
        assert p["a"] * a["hole"] - p["b"] == 0, (i, p)
        # під коренем нуль саме на межі, і лівіше вираз від'ємний
        assert p["c"] * a["edge"] - p["d"] == 0, (i, p)
        assert p["c"] * (a["edge"] - 1) - p["d"] < 0, (i, p)
        assert a["first"] == sp.ceiling(a["edge"]), (i, p)
        assert a["edge"] != a["first"], (i, "межа не має бути цілою")


def test_domain_combined_math():
    for i in range(20):
        q = _build("tf_domain_combined", i)
        p, a = q.params, _a(q)
        edge = sp.Rational(p["b"], p["a"])
        # СТРОГА нерівність: на самій межі корінь у знаменнику дає нуль
        assert p["b"] - p["a"] * a["last"] > 0, (i, p)
        assert p["b"] - p["a"] * (a["last"] + 1) <= 0, (i, p)
        assert a["hole"] == max(0, p["c"]), (i, p)
        want = [v for v in range(-5, 6)
                if v < edge and v != 0 and v != p["c"]]
        assert a["cnt"] == len(want), (i, p, want)


def test_graph_properties_math():
    rising_seen = set()
    for i in range(25):
        q = _build("tf_graph_properties", i)
        p, a = q.params, _a(q)
        xs, ys = p["xs"], p["ys"]
        assert len(xs) == len(ys) >= 4, (i, p)
        assert xs == sorted(xs), (i, "вузли мають іти зліва направо")
        assert all(-6 < v < 6 for v in ys), (i, "графік має вміщатися в полотно")
        # напрямок на сусідніх ланках різний – інакше «скільки проміжків»
        # не мало б однозначної відповіді
        dirs = [ys[k + 1] - ys[k] > 0 for k in range(len(ys) - 1)]
        assert all(dirs[k] != dirs[k + 1] for k in range(len(dirs) - 1)), (i, ys)
        assert a["dmin"] == xs[0], (i, p)
        assert a["emax"] == max(ys), (i, p)
        assert a["rising"] == sum(dirs), (i, p)
        rising_seen.add(int(a["rising"]))
        # у рисунку стільки ж ланок, скільки в даних
        assert q.svg.count("stroke-width=\"2.4\"") >= len(dirs), (i, "ланки")
    assert len(rising_seen) >= 2, ("кількість проміжків має різнитися",
                                   rising_seen)


def test_bring_under_letters_math():
    for i in range(20):
        q = _build("tf_bring_under_letters", i)
        p, a = q.params, _a(q)
        n, k, m, e, pp = p["n"], p["k"], p["m"], p["e"], p["p"]
        assert m * n <= 12, (i, "показник має лишатися в межах парсера")
        assert _same(a["power"], (k * _x**m) ** n), (i, p)
        # внесення: (k x^m)^n * y / (k^n x^p) = x^e y
        assert _same(a["inner"], (k * _x**m) ** n * _y / (k**n * _x**pp)), (i, p)
        # і числова перевірка
        value = sp.root(sp.Integer(p["x0"]) ** e * p["y0"], n)
        assert a["val"] == value, (i, p)


def test_root_of_root_math():
    """Хід саме шкільний: внести під внутрішній корінь, тоді корінь з кореня.

    Через раціональний показник задача теж розв'язується, але викладач
    показував її інакше, тож і кроки мають бути такі.
    """
    for i in range(25):
        q = _build("tf_root_of_root", i)
        p, a = q.params, _a(q)
        n, m, aa, b = p["n"], p["m"], p["a"], p["b"]
        assert math.gcd(b, m) == 1, (i, "внутрішній корінь не має скорочуватися")
        # 1) внесення множника під внутрішній корінь
        assert a["under"] == aa * m + b, (i, p)
        # 2) правило кореня з кореня
        assert a["deg"] == n * m, (i, p)
        # 3) значення: той самий вираз, зібраний з коренів
        built = sp.root(_x**aa * sp.root(_x**b, m), n)
        assert sp.simplify(built.subs(_x, p["x0"]) - a["val"]) == 0, (i, p)
        # результат мусить лишатися коренем, а не просто x
        assert 2 <= p["d"] <= 8 and p["d"] != p["e"], (i, p)
        # в умові немає раціонального показника
        assert "frac" not in q.statement, (i, "умова не має вести через степінь")


def test_fraction_actions_math():
    for i in range(20):
        q = _build("tf_fraction_actions", i)
        p, a = q.params, _a(q)
        k, c = p["k"], p["c"]
        first = k * (_x - c**2 * _y) / (sp.sqrt(_x) - c * sp.sqrt(_y))
        second = k * (_x - c**2 * _y) / (sp.sqrt(_x) + c * sp.sqrt(_y))
        assert _same(a["first"], first), (i, p)
        assert _same(a["second"], second), (i, p)
        assert _same(a["diff"], first - second), (i, p)
        assert _same(a["diff"], 2 * k * c * sp.sqrt(_y)), (i, p)


def test_substitution_quartic_math():
    for i in range(20):
        q = _build("tf_substitution_quartic", i)
        p, a = q.params, _a(q)
        t = sp.Symbol("t")
        assert sorted(sp.solve(t**2 - p["b"] * t + p["c"], t)) == \
            [a["t1"], a["t2"]], (i, p)
        assert 0 < a["t1"] < a["t2"], (i, "обидва значення t мають бути додатні")
        # підстановка в початкове рівняння
        for tv in (a["t1"], a["t2"]):
            xv = tv**4 - p["a"]
            left = sp.sqrt(xv + p["a"])
            right = p["b"] * sp.root(xv + p["a"], 4) - p["c"]
            assert sp.simplify(left - right) == 0, (i, tv, p)
        assert a["x"] == a["t2"] ** 4 - p["a"], (i, p)


# --- перенесення помилки ------------------------------------------------

def test_carry_rounds_up_own_boundary():
    for i in range(10):
        q = _build("tf_domain_pair", i)
        a = _a(q)
        wrong = a["edge"] + sp.Rational(1, 2)
        r = engine.grade(q, {"hole": "0", "edge": str(wrong),
                             "first": str(sp.ceiling(wrong))})
        scored = {d["part"]: d["score"] for d in r["parts"]}
        assert scored["first"] == 1, (i, r)


def test_carry_does_not_confirm_itself():
    """Округлення цілого числа дає саме себе – таке перенесення заборонене."""
    for i in range(10):
        q = _build("tf_domain_pair", i)
        for g in ("7", "123456", "0"):
            r = engine.grade(q, {p.key: g for p in q.parts})
            assert r["score"] <= 1.0, (i, g, r)


@pytest.mark.parametrize("key", KEYS)
def test_answers_are_enterable(key):
    for i in range(6):
        for part in _build(key, i).parts:
            engine.parse_answer(str(part.answer), part.kind)
