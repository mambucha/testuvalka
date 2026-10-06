"""Степінь з раціональним показником (§6 Мерзляка, 10 клас).

Кожну відповідь перевіряємо НЕЗАЛЕЖНО: вираз з умови збираємо наново з
`q.params` і спрощуємо засобами sympy, а не повторюємо формулу шаблону.

Окремо закріплено дві речі, на яких шаблони вже ламалися:
  * показник у «зведіть до одного степеня» не має бути нульовим ($x^0 = 1$
    вгадується без жодних перетворень);
  * показники в умові мають бути СПРАВДІ дробовими – якщо вони скорочуються
    до цілих, задача перестає стосуватися теми.

Символьне порівняння тут іде з припущенням `positive=True`, бо дробовий
степінь означений лише для додатної основи. Через це грейдинг помітно
повільніший за інші банки, тож вибірки навмисне невеликі.
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

DEFINITION = ["rp_root_to_power", "rp_single_power"]
VALUES = ["rp_numeric_value", "rp_properties", "rp_same_base"]
TRANSFORM = ["rp_expand_squares", "rp_cube_identity", "rp_reduce_fraction",
             "rp_simplify_expr", "rp_substitution"]
FUNCTION = ["rp_domain", "rp_meaningful"]
KEYS = DEFINITION + VALUES + TRANSFORM + FUNCTION

_x, _y = sp.symbols("x y")
_R = sp.Rational


def _build(key, i):
    return engine.build(key, SECRET, f"учень|{i}", "theme3", 1, 0)


def _a(q):
    return {p.key: p.answer for p in q.parts}


def _same(got, expected):
    """Рівність на додатних значеннях – саме там і живе дробовий степінь."""
    return engine.equal(engine.as_positive(got), engine.as_positive(expected))


# --- склад тесту --------------------------------------------------------

def test_has_12_types_covering_the_paragraph():
    assert len(KEYS) == len(set(KEYS)) == 12
    assert len(DEFINITION) == 2, "означення і перехід корінь <-> степінь"
    assert len(VALUES) == 3, "обчислення і властивості"
    assert len(TRANSFORM) == 5, "перетворення виразів"
    assert len(FUNCTION) == 2, "функція та зміст запису"


def test_yaml_bank_matches_this_module():
    data = yaml.safe_load(pathlib.Path("tests.yaml").read_text(encoding="utf-8"))
    entry = next(t for t in data if t["key"] == "theme3")
    assert entry["bank"] == KEYS
    assert entry["question_count"] == 12
    assert entry["points_per_question"] == 1


def test_all_grade_full_on_correct_answers():
    for key in KEYS:
        for i in range(8):
            q = _build(key, i)
            sub = {p.key: str(p.answer) for p in q.parts}
            r = engine.grade(q, sub)
            assert r["score"] == r["max"] == q.max_score, (key, i, r, sub)


def test_garbage_gets_zero():
    for key in KEYS:
        for i in range(4):
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


def test_positive_base_is_stated_where_variables_appear():
    """Для від'ємної основи дробовий степінь не означений – це має бути в умові."""
    for key in TRANSFORM + DEFINITION:
        for i in range(4):
            s = _build(key, i).statement
            assert "> 0$" in s, (key, "немає умови про додатність")


def test_timings_calibrated():
    total = 0
    for key in KEYS:
        q = _build(key, 1)
        assert 100 <= q.seconds <= 160, (key, q.seconds)
        total += q.seconds
    assert 1350 <= total <= 1650, total          # ~23-27 хв на 12 питань


def test_no_irrational_equations():
    """§7 (ірраціональні рівняння) – наступна тема, сюди не входить."""
    for key in KEYS:
        for i in range(4):
            s = _build(key, i).statement.lower()
            for bad in ("розв'яжіть рівняння", "корені рівняння", "= 0$"):
                assert bad not in s, (key, bad)


# --- стійкість до списування -------------------------------------------

def test_many_variants_per_template():
    for key in KEYS:
        tuples = [tuple(str(p.answer) for p in _build(key, i).parts)
                  for i in range(60)]
        distinct = len(set(tuples))
        top = max(tuples.count(t) for t in set(tuples))
        assert distinct >= 15, (key, "замало варіантів", distinct)
        assert top <= 10, (key, "надто частий варіант", top)


def test_equivalent_forms_accepted():
    """Основа додатна, тож усі ці записи – той самий вираз."""
    q = _build("rp_root_to_power", 0)
    m, n = q.params["m"], q.params["n"]
    for form in (f"x^({m}/{n})", f"(x^{m})^(1/{n})", f"(x^(1/{n}))^{m}"):
        r = engine.grade(q, {"expr": form})
        got = next(d for d in r["parts"] if d["part"] == "expr")
        assert got["score"] == 1, (form, r)

    q = _build("rp_expand_squares", 1)
    k = q.params["k"]
    if k == 2:                      # (x^(1/2)·y^(1/2)) = sqrt(x·y) лише для x,y>0
        assert _same(sp.sqrt(_x * _y), sp.sqrt(_x) * sp.sqrt(_y))


# =======================================================================
#  НЕЗАЛЕЖНА ПЕРЕВІРКА МАТЕМАТИКИ
# =======================================================================

def test_root_to_power_math():
    for i in range(12):
        q = _build("rp_root_to_power", i)
        p, a = q.params, _a(q)
        c, n, m = p["c"], p["n"], p["m"]
        assert math.gcd(m, n) == 1, (i, "дріб має бути нескоротним")
        assert a["r"] == _R(m, n), (i, p)
        # корінь n-го степеня зі степеня m – те саме, що x^(m/n)
        assert _same(a["expr"], sp.root(_x**m, n)), (i, p)
        assert a["val"] == sp.Integer(c) ** m, (i, p)
        assert sp.Integer(c**n) ** _R(m, n) == a["val"], (i, p)


def test_single_power_math():
    exponents = set()
    for i in range(20):
        q = _build("rp_single_power", i)
        p, a = q.params, _a(q)
        aa, bb, dd, base = p["a"], p["b"], p["d"], p["base"]
        r = Fraction(1, aa) + Fraction(1, bb) + (
            -Fraction(1, dd) if p["divide"] else Fraction(1, dd))
        exponents.add(r)
        assert a["r"] == _R(r.numerator, r.denominator), (i, p)
        assert r.denominator > 1, (i, "цілий показник вгадується без перетворень")
        lcm = math.lcm(aa, bb, dd)
        assert a["val"] == sp.Integer(base) ** _R((r * lcm).numerator,
                                                 (r * lcm).denominator), (i, p)
        # той самий вираз, зібраний з коренів
        built = sp.root(_x, aa) * sp.root(_x, bb)
        built = built / sp.root(_x, dd) if p["divide"] else built * sp.root(_x, dd)
        assert _same(a["expr"], built), (i, p)
    assert len(exponents) >= 4, exponents


def test_numeric_value_math():
    for i in range(12):
        q = _build("rp_numeric_value", i)
        p, a = q.params, _a(q)
        u, qq, pp = p["u"], p["q"], p["p"]
        w, s, k = p["w"], p["s"], p["k"]
        assert a["first"] == sp.Integer(u**qq) ** _R(pp, qq), (i, p)
        assert a["second"] == sp.Integer(w**s) ** _R(-k, s), (i, p)
        assert a["prod"] == a["first"] * a["second"], (i, p)
        assert Fraction(pp, qq).denominator > 1, (i, "показник має бути дробовим")
        assert Fraction(k, s).denominator > 1, (i, "показник має бути дробовим")


def test_properties_math():
    for i in range(12):
        q = _build("rp_properties", i)
        p, a = q.params, _a(q)
        b = p["b"]
        pp, qq, rr = (Fraction(p["p"]), Fraction(p["q"]), Fraction(p["r"]))
        u, v = Fraction(p["u"]), Fraction(p["v"])
        # усі показники в умові мають бути дробовими, інакше тема ні до чого
        for fr in (pp, qq, rr, u, v):
            assert fr.denominator > 1, (i, "показник скоротився до цілого", fr)
        assert pp + qq - rr == a["k1"], (i, p)
        assert u * v == p["k2"], (i, p)
        assert a["val2"] == sp.Integer(b) ** p["k2"], (i, p)
        assert a["val"] == a["val2"] * sp.Integer(b) ** a["k1"], (i, p)
        # власне перевірка властивостей, зібрана наново
        assert (sp.Integer(b) ** _R(pp.numerator, pp.denominator)
                * sp.Integer(b) ** _R(qq.numerator, qq.denominator)
                / sp.Integer(b) ** _R(rr.numerator, rr.denominator)
                == sp.Integer(b) ** a["k1"]), (i, p)
        assert ((sp.Integer(b) ** _R(u.numerator, u.denominator))
                ** _R(v.numerator, v.denominator) == a["val2"]), (i, p)


def test_same_base_math():
    for i in range(12):
        q = _build("rp_same_base", i)
        p, a = q.params, _a(q)
        pp, qq, rr = p["p"], p["q"], p["r"]
        for num, den in ((pp, 4), (qq, 3), (rr, 2)):
            assert num % den, (i, "показник скоротився до цілого")
        first = (sp.Integer(16) ** _R(pp, 4) * sp.Integer(8) ** _R(qq, 3)
                 / sp.Integer(4) ** _R(rr, 2))
        assert first == sp.Integer(2) ** a["k"], (i, p)
        assert a["val"] == first, (i, p)
        second = sp.Integer(27) ** _R(p["s"], 3) / sp.Integer(9) ** _R(p["t"], 2)
        assert a["val3"] == second, (i, p)


def test_expand_squares_math():
    for i in range(12):
        q = _build("rp_expand_squares", i)
        p, a = q.params, _a(q)
        k, n, c, a1, b1 = p["k"], p["n"], p["c"], p["a1"], p["b1"]
        assert k != n, (i, "показники двох пунктів мають відрізнятися")
        built = ((_x**_R(1, k) + c * _y**_R(1, k))
                 * (_x**_R(1, k) - c * _y**_R(1, k)))
        assert _same(a["diff"], built), (i, p)
        assert _same(a["sq"], (a1 * _x**_R(1, n) + b1 * _y**_R(1, n)) ** 2), (i, p)
        assert a["diff"] != a["sq"], i


def test_cube_identity_math():
    for i in range(12):
        q = _build("rp_cube_identity", i)
        p, a = q.params, _a(q)
        c, e, w = p["c"], p["e"], p["w"]
        assert c != e, (i, "два пункти мають відрізнятися")
        minus = ((_x**_R(1, 3) - c)
                 * (_x**_R(2, 3) + c * _x**_R(1, 3) + c**2))
        plus = ((_x**_R(1, 3) + e)
                * (_x**_R(2, 3) - e * _x**_R(1, 3) + e**2))
        assert _same(a["minus"], minus), (i, p)
        assert _same(a["plus"], plus), (i, p)
        assert a["val"] == w**3 - c**3, (i, p)


def test_reduce_fraction_math():
    for i in range(12):
        q = _build("rp_reduce_fraction", i)
        p, a = q.params, _a(q)
        c, d, w = p["c"], p["d"], p["w"]
        assert _same(a["first"], (_x - c**2) / (_x**_R(1, 2) + c)), (i, p)
        assert _same(a["second"], (_x - d**3) / (_x**_R(1, 3) - d)), (i, p)
        assert a["val"] == w**2 + d * w + d**2, (i, p)


def test_simplify_expr_math():
    for i in range(12):
        q = _build("rp_simplify_expr", i)
        p, a = q.params, _a(q)
        a1, b1, c1, d1, n, m = (p["a1"], p["b1"], p["c1"], p["d1"], p["n"], p["m"])
        assert c1 != d1, (i, "вираз згорнувся б у добуток")
        px, py = _R(1, n), _R(1, m)
        built = ((a1 * _x**px + b1 * _y**py) * (_x**px - c1 * _y**py)
                 - (_x**px + d1 * _y**py) * (_x**px - d1 * _y**py))
        assert _same(a["expr"], built), (i, p)
        assert a["coef"] == a1 - 1, (i, p)
        assert sp.expand(built).coeff(_x**_R(2, n)) == a["coef"], (i, p)


def test_substitution_math():
    for i in range(12):
        q = _build("rp_substitution", i)
        p, a = q.params, _a(q)
        n, c, d = p["n"], p["c"], p["d"]
        top = _x**_R(2, n)
        assert _same(a["first"], (top - c**2) / (_x**_R(1, n) + c)), (i, p)
        assert _same(a["second"], (top - d**2) / (_x**_R(1, n) - d)), (i, p)
        assert _same(a["total"], a["first"] + a["second"]), (i, p)


def test_domain_math():
    signs, counts = set(), set()
    for i in range(16):
        q = _build("rp_domain", i)
        p, a = q.params, _a(q)
        n, m, negative = p["n"], p["m"], p["negative"]
        signs.add(negative)
        r = _R(-m, n) if negative else _R(m, n)
        # нуль у області визначення лише для ДОДАТНОГО показника
        want = sum(1 for v in p["pool"] if v > 0 or (v == 0 and not negative))
        assert a["cnt"] == want, (i, p)
        assert any(v < 0 for v in p["pool"]), (i, "від'ємне число - обов'язкова пастка")
        assert p["v1"] in p["pool"] and p["v2"] in p["pool"], (i, p)
        assert a["v1"] == sp.Integer(p["v1"]) ** r, (i, p)
        assert a["v2"] == sp.Integer(p["v2"]) ** r, (i, p)
        counts.add(int(a["cnt"]))
    assert signs == {True, False}, "мають траплятися і додатні, і від'ємні показники"
    assert len(counts) >= 3, ("кількість чисел в області має відчутно різнитися", counts)


def test_meaningful_math():
    counts = set()
    for i in range(24):
        q = _build("rp_meaningful", i)
        p, a = q.params, _a(q)
        c, n, s, m = p["c"], p["n"], p["s"], p["m"]
        assert n % 2 == 1, (i, "корінь з від'ємного існує лише непарного степеня")
        counts.add(int(a["cnt"]))
        assert 2 <= a["cnt"] <= 4, (i, a["cnt"])
        assert a["root"] == -c and (-c) ** n == -(c**n), (i, p)
        assert a["pow"] == sp.Integer(c**s) ** _R(-m, s), (i, p)
    # якби змістовних записів завжди було порівну, перший пункт вгадувався б
    assert len(counts) >= 2, counts


# --- перенесення помилки (carry) ---------------------------------------

def test_carry_wrong_exponent_keeps_later_steps():
    for i in range(6):
        q = _build("rp_root_to_power", i)
        p = q.params
        wrong = _R(p["m"] + 1, p["n"])
        r = engine.grade(q, {
            "r": str(wrong),
            "expr": f"x^({wrong.p}/{wrong.q})",
            "val": str(sp.Integer(p["c"]) ** (wrong * p["n"])),
        })
        assert r["score"] == 2.0 and r["max"] == 3, (i, r)


def test_carry_sum_of_own_fractions():
    for i in range(6):
        q = _build("rp_substitution", i)
        a = _a(q)
        wrong_first = a["first"] + 1
        r = engine.grade(q, {
            "first": str(wrong_first),
            "second": str(a["second"]),
            "total": str(sp.expand(wrong_first + a["second"])),
        })
        assert r["score"] == 2.0 and r["max"] == 3, (i, r)


def test_carry_does_not_rescue_garbage():
    """Однакове сміття в усіх полях не має проходити через перенесення."""
    for key in ("rp_root_to_power", "rp_single_power", "rp_substitution",
                "rp_properties"):
        for guess in ("1", "0", "2"):
            q = _build(key, 2)
            r = engine.grade(q, {p.key: guess for p in q.parts})
            assert r["score"] <= 1.0, (key, guess, r)


# --- швидкодія ----------------------------------------------------------

def test_grading_fits_the_worker_budget():
    """Воркер убиває перевірку через 3 с – символьне спрощення має вкластися."""
    import time
    for key in KEYS:
        q = _build(key, 5)
        sub = {p.key: str(p.answer) for p in q.parts}
        start = time.perf_counter()
        engine.grade(q, sub)
        spent = time.perf_counter() - start
        assert spent < 1.5, (key, round(spent, 2))


@pytest.mark.parametrize("key", KEYS)
def test_answers_are_enterable(key):
    """Відповідь мусить проходити через парсер: межі на цифри й показники."""
    for i in range(6):
        for part in _build(key, i).parts:
            engine.parse_answer(str(part.answer), part.kind)
