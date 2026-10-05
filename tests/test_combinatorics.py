"""Комбінаторика (§12–§13 Мерзляка, 11 клас): правила суми й добутку та сполуки.

Кожну відповідь перевіряємо ДРУГИМ, незалежним способом:
  * цифрові задачі шаблон рахує перебором (itertools.product) – тут їх
    перевіряємо замкненими формулами ($m^k$, $A_m^k$ тощо);
  * задачі на сполуки шаблон рахує через math.comb/perm/factorial – тут їх
    перевіряємо ПЕРЕБОРОМ усіх підмножин і перестановок.
Тож помилка у формулі не може «підтвердити сама себе».

Окремо закріплено те, що робить тест стійким до списування: у кожного свій
набір цифр і свої n, k (перевіряємо, що варіантів справді багато), кожна
задача багатокрокова, а відповідь можна ввести – тобто вона не довша за ті
9 цифр, які приймає парсер.
"""

import itertools
import math
import pathlib
import re
from functools import lru_cache

import sympy as sp
import yaml

import engine
from app.config import SECRET

# Літеральний "\n" замість переносу; \ne, \nu – валідні команди LaTeX.
_BAD_NEWLINE = re.compile(r"\\n(?![a-zA-Z])")

RULES = ["cmb_sum_product", "cmb_menu", "cmb_digits_zero",
         "cmb_digits_parity", "cmb_divisible", "cmb_sequences"]
SETS = ["cmb_permutations", "cmb_arrangements_vs_combinations",
        "cmb_team_with_fixed", "cmb_polygon", "cmb_exactly_k", "cmb_two_lines"]
KEYS = RULES + SETS


def _build(key, i):
    return engine.build(key, SECRET, f"учень|{i}", "combinatorics", 1, 0)


def _a(q):
    return {p.key: int(p.answer) for p in q.parts}


# --- склад тесту --------------------------------------------------------

def test_has_12_types_over_both_paragraphs():
    assert len(KEYS) == len(set(KEYS)) == 12
    assert len(RULES) == 6, "§12 – правила суми та добутку"
    assert len(SETS) == 6, "§13 – перестановки, розміщення, комбінації"


def test_yaml_bank_matches_this_module():
    data = yaml.safe_load(pathlib.Path("tests.yaml").read_text(encoding="utf-8"))
    entry = next(t for t in data if t["key"] == "combinatorics")
    assert entry["bank"] == KEYS
    assert entry["question_count"] == 12
    assert entry["points_per_question"] == 1


def test_all_grade_full_on_correct_answers():
    for key in KEYS:
        for i in range(20):
            q = _build(key, i)
            sub = {p.key: str(p.answer) for p in q.parts}
            r = engine.grade(q, sub)
            assert r["score"] == r["max"] == q.max_score, (key, i, r, sub)


def test_garbage_gets_zero():
    for key in KEYS:
        for i in range(6):
            q = _build(key, i)
            r = engine.grade(q, {p.key: "123456" for p in q.parts})
            assert r["score"] == 0.0, (key, i, r)


def test_small_number_in_every_field_scores_almost_nothing():
    """Щоб перенесення помилки не стало лазівкою: «1» всюди – не відповідь."""
    for key in KEYS:
        for i in range(6):
            q = _build(key, i)
            for guess in ("1", "0", "2"):
                r = engine.grade(q, {p.key: guess for p in q.parts})
                assert r["score"] <= 1.0, (key, i, guess, r)


def test_answers_are_enterable():
    """Парсер не приймає чисел довших за 9 цифр – відповідь мусить влазити."""
    for key in KEYS:
        for i in range(20):
            for part in _build(key, i).parts:
                assert len(str(part.answer)) <= 9, (key, i, part.key, part.answer)
                assert int(part.answer) >= 0, (key, i, part.key)


def test_expression_form_accepted():
    """Мерзляк лишає відповідь виразом ($26^3+26^4$) – ми теж приймаємо."""
    q = _build("cmb_sequences", 2)
    m, k = q.params["m"], q.params["k"]
    r = engine.grade(q, {
        "exact": f"{m}^{k}",
        "dist": "*".join(str(m - j) for j in range(k)),
        "both": f"{m}^{k} + {m}^{k + 1}",
    })
    assert r["score"] == r["max"], r


def test_factorial_form_accepted():
    """Підручник записує сполуки факторіалами – цю форму теж приймаємо."""
    for i in range(10):
        q = _build("cmb_arrangements_vs_combinations", i)
        n, k = q.params["n"], q.params["k"]
        r = engine.grade(q, {
            "ordered": f"{n}!/{n - k}!",                  # A(n,k) = n!/(n-k)!
            "unordered": f"{n}!/({n - k}!*{k}!)",         # C(n,k)
            "times": f"{k}!",
        })
        assert r["score"] == r["max"], (i, n, k, r)

    for i in range(10):
        q = _build("cmb_permutations", i)
        n, g = q.params["n"], q.params["g"]
        r = engine.grade(q, {"all": f"{n}!", "firstg": f"{g}!*{n - g}!"})
        scored = {d["part"]: d["score"] for d in r["parts"]}
        assert scored["all"] == 1 and scored["firstg"] == 1, (i, n, g, r)

    for i in range(10):
        q = _build("cmb_team_with_fixed", i)
        n, k = q.params["n"], q.params["k"]
        r = engine.grade(q, {"all": f"{n}!/({n - k}!*{k}!)"})
        assert r["parts"][0]["score"] == 1, (i, n, k, r)


def test_statements_katex_no_literal_newline():
    for key in KEYS:
        for i in range(4):
            q = _build(key, i)
            assert "$" in q.statement, key
            assert not _BAD_NEWLINE.search(q.statement), (key, i)


def test_every_task_is_multistep():
    for key in KEYS:
        assert len(_build(key, 1).parts) >= 2, key


def test_all_fields_are_numbers():
    for key in KEYS:
        for part in _build(key, 1).parts:
            assert part.kind == "number", (key, part.key)


def test_no_figures():
    for key in KEYS:
        assert _build(key, 3).svg is None, key


def test_no_probability_or_statistics():
    """§14–§15 (ймовірність, статистика) – окрема тема, сюди не входить."""
    banned = ("ймовірн", "медіан", "мода ", "вибірк", "частот", "випадков",
              "середнє арифметичне")
    for key in KEYS:
        for i in range(6):
            s = _build(key, i).statement.lower()
            for bad in banned:
                assert bad not in s, (key, bad)


def test_timings_calibrated():
    total = 0
    for key in KEYS:
        q = _build(key, 1)
        assert 100 <= q.seconds <= 170, (key, q.seconds)
        total += q.seconds
    assert 1400 <= total <= 1700, total          # ≈23–28 хв на 12 питань


# --- стійкість до списування -------------------------------------------

def test_many_variants_per_template():
    """Головний захист: у сусіда інші числа. Міряємо, скільки їх насправді."""
    worst = []
    for key in KEYS:
        tuples = [tuple(_a(_build(key, i)).values()) for i in range(60)]
        distinct = len(set(tuples))
        top = max(tuples.count(t) for t in set(tuples))
        worst.append((key, distinct, top))
        assert distinct >= 15, (key, "замало варіантів", distinct)
        assert top <= 10, (key, "надто частий варіант", top)
    # найслабший шаблон усе одно має давати відчутний розкид
    assert min(d for _, d, _ in worst) >= 15, worst


def test_statement_itself_differs_between_students():
    """Умова має відрізнятися ВИДИМО – інакше неясно, що варіанти різні."""
    for key in KEYS:
        first_lines = {_build(key, i).statement.split("\n")[0] for i in range(40)}
        assert len(first_lines) >= 8, (key, len(first_lines))


# =======================================================================
#  §12 – перевіряємо замкненими формулами (шаблон рахує перебором)
# =======================================================================

def test_sum_product_math():
    for i in range(20):
        q = _build("cmb_sum_product", i)
        p, a = q.params, _a(q)
        # перебір помічених маршрутів – незалежно від правила добутку
        via = len(list(itertools.product(range(p["a"]), range(p["b"]))))
        assert a["via"] == via == p["a"] * p["b"], i
        assert a["total"] == via + p["c"], i
        assert a["there_back"] == a["total"] * (a["total"] - 1), i


def test_menu_math():
    for i in range(20):
        q = _build("cmb_menu", i)
        p, a = q.params, _a(q)
        x, y, z = p["a"], p["b"], p["c"]
        # перебір трійок – незалежно від правила добутку
        assert a["full"] == len(list(itertools.product(range(x), range(y),
                                                       range(z)))), (i, p)
        # обід із двох страв різного виду – три попарні добутки
        assert a["two"] == x * y + x * z + y * z, (i, p)
        assert a["one"] == x + y + z, (i, p)
        assert a["full"] > a["two"] > a["one"], (i, p)


def test_digits_zero_math():
    for i in range(20):
        q = _build("cmb_digits_zero", i)
        p, a = q.params, _a(q)
        digits, k = p["digits"], p["k"]
        m = len(digits)
        assert 0 in digits, "саме нуль тут і є пасткою"
        assert a["rep"] == (m - 1) * m ** (k - 1), (i, p)
        assert a["dist"] == (m - 1) * math.perm(m - 1, k - 1), (i, p)
        evens = len([d for d in digits if d % 2 == 0])
        assert a["even_last"] == (m - 1) * m ** (k - 2) * evens, (i, p)
        assert a["rep"] > a["dist"], (i, p)
        assert a["rep"] > a["even_last"] > 0, (i, p)


def test_digits_parity_math():
    for i in range(20):
        q = _build("cmb_digits_parity", i)
        p, a = q.params, _a(q)
        digits, k = p["digits"], p["k"]
        m = len(digits)
        want = 0 if p["even"] else 1
        tails = [d for d in digits if d % 2 == want]
        assert a["tails"] == len(tails), (i, p)
        assert a["total"] == (m - 1) * m ** (k - 2) * len(tails), (i, p)
        # «усі цифри різні» – перебираємо перестановки (інший шлях, ніж product)
        dist = sum(1 for t in itertools.permutations(digits, k)
                   if t[0] != 0 and t[-1] % 2 == want)
        assert a["dist"] == dist, (i, p)


def test_divisible_math():
    for i in range(24):
        q = _build("cmb_divisible", i)
        p, a = q.params, _a(q)
        k, d = p["k"], p["d"]
        assert d in (2, 4, 5, 8, 25), (i, d)
        tail_len = 1 if d in (2, 5) else (3 if d == 8 else 2)
        assert a["tails"] == sum(1 for t in range(10**tail_len) if t % d == 0), (i, p)
        # добуток «перша цифра × вільні × закінчення» – не той шлях, яким
        # шаблон рахує (він ділить межі діапазону націло)
        assert a["total"] == 9 * 10 ** (k - 1 - tail_len) * a["tails"], (i, p)
        if k <= 5:   # для коротких чисел ще й прямий перебір
            lo, hi = 10 ** (k - 1), 10**k
            assert a["total"] == sum(1 for v in range(lo, hi) if v % d == 0), (i, p)


def test_sequences_math():
    for i in range(20):
        q = _build("cmb_sequences", i)
        p, a = q.params, _a(q)
        m, k = p["m"], p["k"]
        assert a["exact"] == m**k, (i, p)
        assert a["dist"] == math.perm(m, k), (i, p)
        assert a["both"] == m**k + m ** (k + 1), (i, p)
        if m <= 8 and k <= 3:          # малі випадки – повним перебором
            assert a["exact"] == len(list(itertools.product(range(m), repeat=k)))
            assert a["dist"] == len(list(itertools.permutations(range(m), k)))


# =======================================================================
#  §13 – перевіряємо ПЕРЕБОРОМ (шаблон рахує формулами)
# =======================================================================

@lru_cache(maxsize=None)
def _perm_count(n, k):
    return sum(1 for _ in itertools.permutations(range(n), k))


@lru_cache(maxsize=None)
def _comb_count(n, k):
    return sum(1 for _ in itertools.combinations(range(n), k))


def test_permutations_math():
    for i in range(20):
        q = _build("cmb_permutations", i)
        p, a = q.params, _a(q)
        n, g = p["n"], p["g"]
        assert a["all"] == math.factorial(n), (i, p)
        assert a["firstg"] == math.factorial(g) * math.factorial(n - g), (i, p)
        if n <= 8:
            # перебір усіх розстановок: підручники – елементи 0..g-1
            allp = list(itertools.permutations(range(n)))
            assert a["all"] == len(allp)
            assert a["firstg"] == sum(1 for t in allp if set(t[:g]) == set(range(g)))
            if p["both_ends"]:
                assert a["third"] == sum(1 for t in allp if t[0] >= g and t[-1] >= g)
            else:
                assert a["third"] == sum(1 for t in allp if t[0] >= g)
        elif p["both_ends"]:
            assert a["third"] == (n - g) * (n - g - 1) * math.factorial(n - 2), (i, p)
        else:
            assert a["third"] == (n - g) * math.factorial(n - 1), (i, p)


def test_arrangements_vs_combinations_math():
    for i in range(24):
        q = _build("cmb_arrangements_vs_combinations", i)
        p, a = q.params, _a(q)
        n, k = p["n"], p["k"]
        assert a["ordered"] == _perm_count(n, k), (i, p)
        assert a["unordered"] == _comb_count(n, k), (i, p)
        assert a["times"] == math.factorial(k), (i, p)
        # власне суть: розміщень рівно в k! разів більше, ніж комбінацій
        assert a["ordered"] == a["unordered"] * a["times"], (i, p)


def test_team_with_fixed_math():
    for i in range(20):
        q = _build("cmb_team_with_fixed", i)
        p, a = q.params, _a(q)
        n, k = p["n"], p["k"]
        teams = list(itertools.combinations(range(n), k))   # староста – елемент 0
        assert a["all"] == len(teams), (i, p)
        assert a["with_head"] == sum(1 for t in teams if 0 in t), (i, p)
        assert a["without"] == sum(1 for t in teams if 0 not in t), (i, p)
        assert a["with_head"] + a["without"] == a["all"], (i, p)


def test_polygon_math():
    for i in range(24):
        q = _build("cmb_polygon", i)
        p, a = q.params, _a(q)
        n, r = p["n"], p["r"]
        assert a["tri"] == _comb_count(n, 3), (i, p)
        assert a["poly"] == _comb_count(n, r), (i, p)
        # діагоналі / усі відрізки – перебором пар вершин циклу
        pairs = list(itertools.combinations(range(n), 2))
        adjacent = sum(1 for u, v in pairs if (v - u) % n in (1, n - 1))
        assert adjacent == n, "сусідніх пар у n-кутнику рівно n"
        want = len(pairs) - adjacent if p["diagonals"] else len(pairs)
        assert a["third"] == want, (i, p)


def test_exactly_k_math():
    for i in range(10):
        q = _build("cmb_exactly_k", i)
        p, a = q.params, _a(q)
        n, m, s, k = p["n"], p["m"], p["s"], p["a"]
        # мулярі – елементи 0..m-1; перебираємо всі ланки й рахуємо потрібні
        good = sum(1 for t in itertools.combinations(range(n), s)
                   if len([v for v in t if v < m]) == k)
        assert a["total"] == good, (i, p)
        assert a["masons"] == _comb_count(m, k), (i, p)
        assert a["others"] == _comb_count(n - m, s - k), (i, p)
        assert a["masons"] * a["others"] == good, (i, p)


def test_two_lines_math():
    for i in range(20):
        q = _build("cmb_two_lines", i)
        p, a = q.params, _a(q)
        np_, nq = p["p"], p["q"]
        # точки 0..np_-1 на прямій a, решта – на прямій b
        tri = [t for t in itertools.combinations(range(np_ + nq), 3)
               if 0 < len([v for v in t if v < np_]) < 3]
        assert a["total"] == len(tri), (i, p)
        assert a["on_a"] == sum(1 for t in tri
                                if len([v for v in t if v < np_]) == 2), (i, p)
        assert a["on_b"] == sum(1 for t in tri
                                if len([v for v in t if v < np_]) == 1), (i, p)
        assert a["on_a"] + a["on_b"] == a["total"], (i, p)


# --- перенесення помилки (carry) ---------------------------------------

def test_carry_sum_product_keeps_later_steps():
    for i in range(8):
        q = _build("cmb_sum_product", i)
        p, a = q.params, _a(q)
        wrong = a["via"] + 3
        total = wrong + p["c"]
        r = engine.grade(q, {"via": str(wrong), "total": str(total),
                             "there_back": str(total * (total - 1))})
        assert r["score"] == 2.0 and r["max"] == 3, (i, r)


def test_carry_exactly_k_multiplies_own_steps():
    for i in range(8):
        q = _build("cmb_exactly_k", i)
        a = _a(q)
        wrong = a["masons"] + 1
        r = engine.grade(q, {"masons": str(wrong), "others": str(a["others"]),
                             "total": str(wrong * a["others"])})
        assert r["score"] == 2.0 and r["max"] == 3, (i, r)


def test_carry_team_without_is_difference():
    for i in range(8):
        q = _build("cmb_team_with_fixed", i)
        a = _a(q)
        wrong = a["with_head"] + 5
        r = engine.grade(q, {"all": str(a["all"]), "with_head": str(wrong),
                             "without": str(a["all"] - wrong)})
        assert r["score"] == 2.0 and r["max"] == 3, (i, r)


def test_carry_divisible_scales_tail_count():
    for i in range(8):
        q = _build("cmb_divisible", i)
        p, a = q.params, _a(q)
        k, d = p["k"], p["d"]
        tail_len = 1 if d in (2, 5) else (3 if d == 8 else 2)
        factor = 9 * 10 ** (k - 1 - tail_len)
        wrong = a["tails"] + 1
        r = engine.grade(q, {"tails": str(wrong), "total": str(wrong * factor)})
        assert r["score"] == 1.0 and r["max"] == 2, (i, r)


def test_carry_ratio_survives_wrong_first_steps():
    """У скільки разів більше – від СВОЇХ двох чисел."""
    hits = 0
    for i in range(20):
        q = _build("cmb_arrangements_vs_combinations", i)
        a = _a(q)
        ordered = a["ordered"] * 2          # помилилися вдвічі в обох пунктах
        unordered = a["unordered"] * 2
        r = engine.grade(q, {"ordered": str(ordered), "unordered": str(unordered),
                             "times": str(sp.Rational(ordered, unordered))})
        assert r["score"] == 1.0 and r["max"] == 3, (i, r)
        hits += 1
    assert hits == 20
