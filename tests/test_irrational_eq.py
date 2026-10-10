"""Ірраціональні рівняння (§7 Мерзляка, 10 клас).

Кожну відповідь перевіряємо НЕЗАЛЕЖНО: рівняння збираємо наново з `q.params`
і розв'язуємо через sympy, а корені ще й підставляємо в початкове рівняння.
Тобто «сторонній чи ні» вирішує підстановка, а не формула шаблону.

Окремо закріплено те, на чому шаблони вже ламалися:
  * однакове «сміття» в усіх полях не має проходити через перенесення –
    крок «який із двох корінь справжній» бере число самого студента, тож
    без охорони він підтверджував би сам себе;
  * поле «скільки коренів» не має бути сталим, інакше воно вгадується.
"""

import pathlib
import re

import pytest
import sympy as sp
import yaml

import engine
from app.config import SECRET

# Літеральний "\n" замість переносу; \ne, \nu – валідні команди LaTeX.
_BAD_NEWLINE = re.compile(r"\\n(?![a-zA-Z])")

SIMPLE = ["ir_simple_power", "ir_odd_degree"]
EXTRANEOUS = ["ir_even_extraneous", "ir_radicals_equal", "ir_quadratic_radicand"]
CHECKS = ["ir_no_roots", "ir_check_roots", "ir_domain"]
SUBST = ["ir_substitution_sqrt", "ir_substitution_cube",
         "ir_substitution_shift", "ir_two_radicals"]
KEYS = SIMPLE + EXTRANEOUS + CHECKS + SUBST

_x = sp.Symbol("x")


def _build(key, i):
    return engine.build(key, SECRET, f"учень|{i}", "theme4", 1, 0)


def _a(q):
    return {p.key: p.answer for p in q.parts}


def _holds(lhs, rhs, value):
    """Чи перетворюється рівняння на правильну рівність при x = value."""
    got = sp.simplify(lhs.subs(_x, value) - rhs.subs(_x, value))
    return got == 0


# --- склад тесту --------------------------------------------------------

def test_has_12_types_covering_the_paragraph():
    assert len(KEYS) == len(set(KEYS)) == 12
    assert len(SIMPLE) == 2 and len(EXTRANEOUS) == 3
    assert len(CHECKS) == 3 and len(SUBST) == 4


def test_yaml_bank_matches_this_module():
    data = yaml.safe_load(pathlib.Path("tests.yaml").read_text(encoding="utf-8"))
    entry = next(t for t in data if t["key"] == "theme4")
    assert entry["bank"] == KEYS
    assert entry["question_count"] == 12
    assert entry["points_per_question"] == 1


def test_all_grade_full_on_correct_answers():
    for key in KEYS:
        for i in range(25):
            q = _build(key, i)
            sub = {p.key: str(p.answer) for p in q.parts}
            r = engine.grade(q, sub)
            assert r["score"] == r["max"] == q.max_score, (key, i, r, sub)


def test_garbage_gets_zero():
    for key in KEYS:
        for i in range(10):
            q = _build(key, i)
            r = engine.grade(q, {p.key: "123456" for p in q.parts})
            assert r["score"] == 0.0, (key, i, r)


def test_statements_katex_no_literal_newline():
    for key in KEYS:
        for i in range(6):
            q = _build(key, i)
            assert "$" in q.statement, key
            assert not _BAD_NEWLINE.search(q.statement), (key, i)


def test_every_task_is_multistep():
    for key in KEYS:
        assert len(_build(key, 1).parts) >= 2, key


def test_no_figures():
    for key in KEYS:
        assert _build(key, 3).svg is None, key


def test_no_zero_coefficients_in_statements():
    r"""Нульовий коефіцієнт стер би корінь із рівняння: було
    «x - 0\sqrt{x + 4} - 5 = 0», тобто задача без жодної ірраціональності."""
    bad_coef = re.compile(r"[+-] 0[A-Za-z\\]")
    for key in KEYS:
        for i in range(60):
            s = _build(key, i).statement
            assert not bad_coef.search(s), (key, i, s.splitlines()[0])
            assert " 0x" not in s and "{0}" not in s, (key, i)


def test_substitution_shift_constants_are_collected():
    r"""Сталі в умові мають бути зведені: «x + 3 - 4\sqrt{x+3} - 5» читалося б
    як недороблена робота."""
    for i in range(30):
        q = _build("ir_substitution_shift", i)
        head = q.statement.split("=")[0]
        # знаки ВСЕРЕДИНІ кореня не рахуємо: там «x + 3» на своєму місці
        outside = re.sub(r"\\sqrt\{[^}]*\}", "R", head)
        assert outside.count(" - ") + outside.count(" + ") <= 2, (i, head)


def test_timings_calibrated():
    total = 0
    for key in KEYS:
        q = _build(key, 1)
        assert 100 <= q.seconds <= 160, (key, q.seconds)
        total += q.seconds
    assert 1450 <= total <= 1700, total


# --- стійкість до списування -------------------------------------------

def test_many_variants_per_template():
    for key in KEYS:
        tuples = [tuple(str(p.answer) for p in _build(key, i).parts)
                  for i in range(60)]
        assert len(set(tuples)) >= 15, (key, len(set(tuples)))
        assert max(tuples.count(t) for t in set(tuples)) <= 9, key


def test_count_fields_are_not_constant():
    """Поле «скільки коренів» мусить набувати різних значень – інакше його
    вгадують, не читаючи умови."""
    for key, field in (("ir_simple_power", "cnt"),
                       ("ir_quadratic_radicand", "cnt"),
                       ("ir_no_roots", "cnt"),
                       ("ir_check_roots", "cnt")):
        seen = {int(_a(_build(key, i))[field]) for i in range(40)}
        assert len(seen) >= 2, (key, field, seen)


def test_extraneous_root_alternates():
    """Сторонній корінь має бути то меншим, то більшим: інакше правильною
    завжди виявляється та сама відповідь."""
    for key in ("ir_even_extraneous", "ir_radicals_equal"):
        picks = set()
        for i in range(40):
            a = _a(_build(key, i))
            picks.add("small" if a["root"] == a["small"] else "big")
        assert picks == {"small", "big"}, (key, picks)


def test_single_number_guess_is_weak():
    """Одне й те саме число в усі поля не має приносити відчутних балів."""
    for guess in ("0", "1", "2", "-1"):
        total = count = 0
        for key in KEYS:
            for i in range(12):
                q = _build(key, i)
                total += engine.grade(
                    q, {p.key: guess for p in q.parts})["score"] / q.max_score
                count += 1
        assert total / count < 0.17, (guess, round(total / count, 3))


# =======================================================================
#  НЕЗАЛЕЖНА ПЕРЕВІРКА МАТЕМАТИКИ
# =======================================================================

def test_simple_power_math():
    for i in range(20):
        q = _build("ir_simple_power", i)
        p, a = q.params, _a(q)
        # корінь парного степеня
        assert sp.root(p["a"] * a["x1"] + p["b"], p["n_even"]) == p["c"], (i, p)
        # корінь непарного степеня з ВІД'ЄМНОЮ правою частиною
        assert (p["d"] * a["x2"] + p["e"]) == -(p["f"] ** p["n_odd"]), (i, p)
        assert p["n_even"] % 2 == 0 and p["n_odd"] % 2 == 1, (i, p)
        # третє рівняння: корені є тільки в непарного степеня
        assert a["cnt"] == (1 if p["n3"] % 2 else 0), (i, p)


def test_odd_degree_math():
    for i in range(20):
        q = _build("ir_odd_degree", i)
        p, a = q.params, _a(q)
        n, s, m = p["n"], p["s"], p["m"]
        assert n % 2 == 1, (i, "теорема 7.1 – лише непарний степінь")
        lhs, rhs = sp.root(_x**2 - s * _x, n), sp.root(m, n)
        for v in (a["small"], a["big"]):
            assert _holds(lhs, rhs, v), (i, v, p)   # сторонніх немає
        assert a["small"] < a["big"], i
        roots = sp.solve(sp.Eq(_x**2 - s * _x, m), _x)
        assert sorted(roots) == [a["small"], a["big"]], (i, p)


def test_even_extraneous_math():
    for i in range(25):
        q = _build("ir_even_extraneous", i)
        p, a = q.params, _a(q)
        lhs = sp.sqrt(p["a"] * _x + p["b"])
        rhs = -_x if p["minus"] else _x
        assert sorted(sp.solve(sp.Eq(p["a"] * _x + p["b"], _x**2), _x)) == \
            [a["small"], a["big"]], (i, p)
        # рівно один із двох справді задовольняє початкове рівняння
        good = [v for v in (a["small"], a["big"]) if _holds(lhs, rhs, v)]
        assert good == [a["root"]], (i, p, good)


def test_radicals_equal_math():
    for i in range(25):
        q = _build("ir_radicals_equal", i)
        p, a = q.params, _a(q)
        lhs = sp.sqrt(p["a"] * _x + p["b"])
        rhs = sp.sqrt(_x**2 + p["c"] * _x)
        assert sorted(sp.solve(sp.Eq(p["a"] * _x + p["b"], _x**2 + p["c"] * _x),
                               _x)) == [a["small"], a["big"]], (i, p)
        good = [v for v in (a["small"], a["big"])
                if p["a"] * v + p["b"] >= 0 and _holds(lhs, rhs, v)]
        assert good == [a["root"]], (i, p, good)


def test_quadratic_radicand_math():
    for i in range(25):
        q = _build("ir_quadratic_radicand", i)
        p, a = q.params, _a(q)
        lhs, b = sp.sqrt(_x**2 + p["a"] * _x), p["b"]
        for v in (a["small"], a["big"]):
            assert _holds(lhs, sp.Integer(b), v), (i, v, p)   # сторонніх немає
        assert a["small"] < 0 < a["big"], (i, p)
        # третій пункт – та сама ліва частина, лише інша права:
        # від'ємне праворуч неможливе, нуль праворуч дає два корені
        assert p["a"] != 0, (i, "інакше це |x| = b, а не квадратний тричлен")
        assert a["cnt"] == (0 if p["negative"] else 2), (i, p)
        tail = q.statement.rsplit("=", 1)[1]
        assert (f"-{p['b']}" in tail) if p["negative"] else ("0" in tail), (i, tail)


def test_no_roots_math():
    for i in range(25):
        q = _build("ir_no_roots", i)
        p, a = q.params, _a(q)
        assert a["cnt"] == p["n_empty"] and 2 <= a["cnt"] <= 3, (i, p)
        assert q.statement.count("$") >= 8, (i, "чотири рівняння в умові")


def test_check_roots_math():
    for i in range(25):
        q = _build("ir_check_roots", i)
        p, a = q.params, _a(q)
        aa, bb, nums = p["a"], p["b"], p["nums"]
        assert aa != 0, (i, "рівняння мусить лишитися квадратним")
        assert a["dom"] == sum(1 for v in nums if aa * v + bb >= 0), (i, p)
        good = sum(1 for v in nums
                   if aa * v + bb >= 0 and sp.sqrt(aa * v + bb) == v)
        assert a["cnt"] == good, (i, p)
        assert a["lp"] == sp.sqrt(aa * p["p"] + bb), (i, p)


def test_domain_math():
    for i in range(25):
        q = _build("ir_domain", i)
        p, a = q.params, _a(q)
        lo, hi = a["lo"], a["hi"]
        assert lo < hi, (i, p)
        # межі саме там, де підкореневі вирази міняють знак
        assert p["a"] * lo + p["b"] == 0, (i, p)
        assert p["d"] - p["c"] * hi == 0, (i, p)
        assert a["cnt"] == len([v for v in range(-30, 31) if lo <= v <= hi]), (i, p)


def test_substitution_sqrt_math():
    for i in range(25):
        q = _build("ir_substitution_sqrt", i)
        p, a = q.params, _a(q)
        k, t = p["k"], sp.Symbol("t")
        assert sorted(sp.solve(k * t**2 + p["b"] * t + p["c"], t)) == \
            [a["t1"], a["t2"]], (i, p)
        assert a["t1"] < 0 < a["t2"], (i, "саме від'ємне t і відкидаємо")
        # підстановка в початкове рівняння
        val = k * a["x"] + p["b"] * sp.sqrt(a["x"]) + p["c"]
        assert sp.simplify(val) == 0, (i, p)


def test_substitution_cube_math():
    for i in range(25):
        q = _build("ir_substitution_cube", i)
        p, a = q.params, _a(q)
        k, t = p["k"], sp.Symbol("t")
        assert sorted(sp.solve(k * t**2 + p["b"] * t + p["c"], t)) == \
            [a["t1"], a["t2"]], (i, p)
        # Кубічний корінь буває від'ємним, тож годяться ОБИДВА значення.
        # Беремо саме ДІЙСНИЙ корінь: sp.cbrt(-64) повертає комплексний
        # головний корінь, а в школі це -4.
        for tv in (a["t1"], a["t2"]):
            root = sp.real_root(tv**3, 3)
            assert root == tv, (i, tv, "дійсний кубічний корінь")
            val = k * root**2 + p["b"] * root + p["c"]
            assert sp.simplify(val) == 0, (i, tv, p)
        assert a["sum"] == a["t1"] ** 3 + a["t2"] ** 3, (i, p)


def test_substitution_shift_math():
    for i in range(25):
        q = _build("ir_substitution_shift", i)
        p, a = q.params, _a(q)
        t = sp.Symbol("t")
        assert sorted(sp.solve(t**2 + p["b"] * t + p["c"], t)) == \
            [a["t1"], a["t2"]], (i, p)
        assert a["t1"] < 0 < a["t2"], i
        val = (a["x"] + p["a"]) + p["b"] * sp.sqrt(a["x"] + p["a"]) + p["c"]
        assert sp.simplify(val) == 0, (i, p)


def test_two_radicals_math():
    for i in range(25):
        q = _build("ir_two_radicals", i)
        p, a = q.params, _a(q)
        lhs = sp.sqrt(_x + p["a"]) + sp.sqrt(_x + p["b"])
        assert _holds(lhs, sp.Integer(p["p"] + p["q"]), a["x"]), (i, p)
        assert a["lo"] == max(-p["a"], -p["b"]), (i, p)
        assert a["x"] >= a["lo"], (i, "корінь мусить бути в області визначення")
        assert a["val"] == sp.sqrt(a["x"] + p["a"]), (i, p)
        # у цій темі «корінь» означає і корінь рівняння, і радикал, тож
        # у підписах полів цього слова бути не повинно
        for part in q.parts[1:]:
            assert "корінь" not in part.label.lower(), (i, part.label)
        assert p["p"] != p["q"], (i, "однакові корені зробили б задачу вдвічі простішою")


# --- перенесення помилки (carry) ---------------------------------------

def test_carry_keeps_the_right_choice():
    """Помилилися в коренях наслідку, але сторонній відкинули правильно."""
    for key in ("ir_even_extraneous", "ir_radicals_equal"):
        for i in range(10):
            q = _build(key, i)
            a = _a(q)
            take_small = a["root"] == a["small"]
            ws, wb = a["small"] - 1, a["big"] + 1
            r = engine.grade(q, {"small": str(ws), "big": str(wb),
                                 "root": str(ws if take_small else wb)})
            assert r["score"] == 1.0 and r["max"] == 3, (key, i, r)


def test_carry_rejects_equal_garbage():
    """Однакове число в обох полях – не впорядкована пара коренів, тож
    переносити нічого: інакше третій крок підтверджував би сам себе."""
    for key in ("ir_even_extraneous", "ir_radicals_equal"):
        for i in range(10):
            for g in ("123456", "7", "0"):
                q = _build(key, i)
                r = engine.grade(q, {p.key: g for p in q.parts})
                assert r["score"] <= 1.0, (key, i, g, r)


@pytest.mark.parametrize("key", KEYS)
def test_answers_are_enterable(key):
    for i in range(8):
        for part in _build(key, i).parts:
            engine.parse_answer(str(part.answer), part.kind)
