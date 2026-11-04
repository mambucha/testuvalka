"""Ймовірність (§14 Мерзляка, 11 клас): класичне визначення.

Кожну відповідь перевіряємо ДРУГИМ, незалежним способом:
  * де шаблон рахує перебором (подільність, парність пар, прості числа) –
    тут звіряємо замкненою формулою або засобами sympy;
  * де шаблон рахує формулою (math.comb, степені) – тут перебираємо всі
    вибірки через itertools.
Тож помилка в одному місці не може «підтвердити сама себе».

Окремо закріплено те, що робить тест стійким до списування: у кожного свої
числа (перевіряємо, що варіантів справді багато), кожна задача багатокрокова,
а «перепиши k-те число умови» не дає бала систематично.

Статистика (§15) – окрема тема, вона в tests/test_statistics.py і поки що не
входить до жодного тесту.
"""

import itertools
import math
import pathlib
import re

import sympy as sp
import yaml

import engine
from app.config import SECRET

# Літеральний "\n" замість переносу; \ne, \nu – валідні команди LaTeX.
_BAD_NEWLINE = re.compile(r"\\n(?![a-zA-Z])")

# Вибір одного предмета – саме означення P = m/n.
SINGLE = ["pb_urn", "pb_cards", "pb_number_kind", "pb_multiples"]
# Рівноможливі результати спершу треба порахувати.
COUNTED = ["pb_digits", "pb_code", "pb_pair_mixed", "pb_pair_parity"]
# Ймовірність через комбінації та межі означення.
SETS = ["pb_all_of_kind", "pb_exactly", "pb_guaranteed", "pb_inverse"]
KEYS = SINGLE + COUNTED + SETS


def _build(key, i):
    return engine.build(key, SECRET, f"учень|{i}", "probability", 1, 0)


def _a(q):
    return {p.key: p.answer for p in q.parts}


# --- склад тесту --------------------------------------------------------

def test_has_12_types_all_from_one_paragraph():
    assert len(KEYS) == len(set(KEYS)) == 12
    assert len(SINGLE) == len(COUNTED) == len(SETS) == 4


def test_yaml_bank_matches_this_module():
    data = yaml.safe_load(pathlib.Path("tests.yaml").read_text(encoding="utf-8"))
    entry = next(t for t in data if t["key"] == "probability")
    assert sorted(entry["bank"]) == sorted(KEYS)
    assert entry["question_count"] == 12
    assert entry["points_per_question"] == 1


def test_no_statistics_in_this_test():
    """§15 – окрема тема, у банку ймовірності її шаблонів бути не має."""
    data = yaml.safe_load(pathlib.Path("tests.yaml").read_text(encoding="utf-8"))
    entry = next(t for t in data if t["key"] == "probability")
    assert not [k for k in entry["bank"] if k.startswith("st_")]
    banned = ("медіан", "мода ", "вибірк", "розмах", "середнє значення",
              "генеральн", "частот")
    for key in KEYS:
        for i in range(6):
            text = _build(key, i).statement.lower()
            for bad in banned:
                assert bad not in text, (key, bad)


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


def test_constant_guess_scores_almost_nothing():
    """Щоб перенесення помилки не стало лазівкою.

    Нуль і одиниця як відповідь є лише в pb_urn (неможлива й достовірна
    події), і там вони беруть рівно одне поле з чотирьох.
    """
    for key in KEYS:
        for i in range(8):
            q = _build(key, i)
            for guess in ("0", "1", "2", "1/2"):
                r = engine.grade(q, {p.key: guess for p in q.parts})
                assert r["score"] <= 1.0, (key, i, guess, r)


def test_answers_are_enterable():
    """Парсер не приймає чисел довших за 9 цифр – відповідь мусить влазити."""
    for key in KEYS:
        for i in range(20):
            for part in _build(key, i).parts:
                value = sp.Rational(part.answer)
                assert len(str(value.p)) <= 9, (key, i, part.key, value)
                assert len(str(value.q)) <= 9, (key, i, part.key, value)
                assert value >= 0, (key, i, part.key, value)


def test_probability_fields_are_between_zero_and_one():
    checked = 0
    for key in KEYS:
        for i in range(20):
            q = _build(key, i)
            for part in q.parts:
                if "ймовірність" not in part.label.lower():
                    continue
                assert 0 <= part.answer <= 1, (key, i, part.key, part.answer)
                checked += 1
    assert checked > 0, "жодного поля ймовірності не знайдено"


def test_probabilities_within_a_question_differ():
    """Дві ймовірності в одному питанні не мають збігатися – інакше одна
    вгадана дає другу."""
    for key in KEYS:
        for i in range(20):
            q = _build(key, i)
            probs = [p.answer for p in q.parts
                     if "ймовірність" in p.label.lower()
                     or p.key in ("chance", "even", "same", "first", "tries",
                                  "mixed", "both_boys", "prime", "composite",
                                  "digits", "mult", "notmult", "neither",
                                  "prod", "summa")]
            assert len(probs) == len({str(p) for p in probs}), (key, i, probs)


def test_unreduced_and_decimal_fractions_accepted():
    """Скорочувати дріб не вимагаємо: 5/33, 10/66 і 0,1515... – те саме."""
    for key in KEYS:
        for i in range(8):
            q = _build(key, i)
            sub = {}
            for part in q.parts:
                value = sp.Rational(part.answer)
                sub[part.key] = f"{value.p * 3}/{value.q * 3}"
            r = engine.grade(q, sub)
            assert r["score"] == r["max"], (key, i, r)


def test_decimal_comma_accepted():
    """Студент пише 0,25 – кома як десятковий знак має прийматися."""
    hits = 0
    for i in range(20):
        q = _build("pb_urn", i)
        share = sp.Rational(_a(q)["chance"])
        if share.q not in (2, 4, 5, 8, 10, 16, 20, 25):
            continue                      # не кожен дріб десятковий скінченний
        r = engine.grade(q, {"chance": str(float(share)).replace(".", ",")})
        scored = {d["part"]: d["score"] for d in r["parts"]}
        assert scored["chance"] == 1, (i, share, r)
        hits += 1
    assert hits >= 3, hits


def test_statements_katex_no_literal_newline():
    for key in KEYS:
        for i in range(4):
            q = _build(key, i)
            assert "$" in q.statement, key
            assert not _BAD_NEWLINE.search(q.statement), (key, i)


def test_no_cyrillic_inside_math():
    """Шрифти KaTeX кирилиці не містять – усередині $…$ її бути не має."""
    for key in KEYS:
        for i in range(6):
            s = _build(key, i).statement
            for chunk in re.findall(r"\$\$(.+?)\$\$|\$([^$]+)\$", s):
                math_src = chunk[0] or chunk[1]
                assert not re.search(r"[а-яіїєґА-ЯІЇЄҐ]", math_src), (key, math_src)


def test_every_task_is_multistep():
    for key in KEYS:
        assert len(_build(key, 1).parts) >= 3, key


def test_all_fields_are_numbers():
    for key in KEYS:
        for part in _build(key, 1).parts:
            assert part.kind == "number", (key, part.key)


def test_no_figures():
    """Рисунків у цій темі немає – усе задається словами й числами."""
    for key in KEYS:
        assert _build(key, 3).svg is None, key


def test_timings_calibrated():
    total = 0
    for key in KEYS:
        q = _build(key, 1)
        assert 110 <= q.seconds <= 190, (key, q.seconds)
        total += q.seconds
    assert 1800 <= total <= 2000, total          # ≈30–33 хв на 12 питань
    longer = {"pb_exactly", "pb_pair_parity", "pb_inverse", "pb_cards",
              "pb_number_kind", "pb_guaranteed"}
    for key in longer:
        assert _build(key, 1).seconds >= 160, key


# --- стійкість до списування -------------------------------------------

def test_many_variants_per_template():
    """Головний захист: у сусіда інші числа. Міряємо, скільки їх насправді."""
    for key in KEYS:
        tuples = [tuple(str(v) for v in _a(_build(key, i)).values())
                  for i in range(60)]
        distinct = len(set(tuples))
        top = max(tuples.count(t) for t in set(tuples))
        assert distinct >= 15, (key, "замало варіантів", distinct)
        assert top <= 10, (key, "надто частий варіант", top)


def test_statement_itself_differs_between_students():
    """Умова має відрізнятися ВИДИМО – інакше неясно, що варіанти різні."""
    for key in KEYS:
        texts = {_build(key, i).statement for i in range(40)}
        assert len(texts) >= 20, (key, len(texts))
        data = {tuple(re.findall(r"-?\d+", _build(key, i).statement))
                for i in range(40)}
        assert len(data) >= 15, (key, "числа умови майже не змінюються",
                                 len(data))


def _printed_numbers(statement):
    """Числа, які студент бачить як ДАНІ умови.

    Викидаємо розмітку пунктів «1)», «2)» і рядок-підказку в дужках: це не
    дані задачі. Саме на них спіткнулася перша версія цієї перевірки в
    тригонометрії – вона оголосила дірою кожне поле з відповіддю 1.
    """
    lines = []
    for line in statement.split("\n"):
        if line.startswith("("):                       # підказка про формат
            continue
        lines.append(re.sub(r"\d\)", "", line))
    return [int(t) for t in re.findall(r"-?\d+", "\n".join(lines))]


def test_no_printed_number_is_the_answer_too_often():
    """«Перепиши k-те число умови» не має давати бала систематично.

    Для кожної позиції серед надрукованих чисел умови рахуємо, як часто вона
    збігається з відповіддю конкретного поля. 40% означало б правило, яке
    працює без математики.
    """
    runs = 40
    worst = []
    for key in KEYS:
        hits = {}
        for i in range(runs):
            q = _build(key, i)
            printed = _printed_numbers(q.statement)
            for pos, number in enumerate(printed[:12]):
                for part in q.parts:
                    if sp.Rational(part.answer) == number:
                        hits[(pos, part.key)] = hits.get((pos, part.key), 0) + 1
        if hits:
            rule, best = max(hits.items(), key=lambda kv: kv[1])
            worst.append((key, rule, best / runs))
            assert best / runs <= 0.4, (key, rule, best, runs)
    assert worst, "жодне поле не збіглося з умовою – перевірка нічого не міряє"


def test_constant_answer_profile_over_the_whole_test():
    """Скільки з 12 бере той, хто пише те саме в кожне поле.

    Заміряно на 40 варіантах кожного шаблону. Нуль і одиниця беруть своє в
    pb_urn (неможлива й достовірна події) – це неминуче, бо саме ці значення
    там і є відповіддю. Правильні відповіді дають 12,0, тож запас між знанням
    і вгадуванням більш як десятикратний.
    """
    runs = 40
    for guess in ("0", "1", "2", "3", "1/2", "10"):
        total = 0.0
        for key in KEYS:
            got = 0.0
            for i in range(runs):
                q = _build(key, i)
                r = engine.grade(q, {p.key: guess for p in q.parts})
                got += r["score"] / q.max_score
            total += got / runs
        assert total <= 0.8, (guess, round(total, 2))


# =======================================================================
#  §14 – класичне визначення ймовірності
# =======================================================================

def test_urn_math():
    for i in range(24):
        q = _build("pb_urn", i)
        p, a = q.params, _a(q)
        counts = p["counts"]
        assert a["total"] == sum(counts), (i, p)
        assert a["chance"] == sp.Rational(counts[p["pick"]], sum(counts)), (i, p)
        assert a["never"] == 0, "неможлива подія"
        assert a["sure"] == 1, "достовірна подія"
        assert p["absent"] not in p["present"], (i, p)


def test_cards_math():
    for i in range(24):
        q = _build("pb_cards", i)
        p, a = q.params, _a(q)
        n, d, e = p["n"], p["d"], p["e"]
        # замкнені формули проти перебору, яким рахує шаблон
        assert a["mult"] == sp.Rational(n // d, n), (i, p)
        assert a["notmult"] == sp.Rational(n - n // e, n), (i, p)
        both = n // (d * e // math.gcd(d, e))
        neither = n - n // d - n // e + both       # включення й виключення
        assert a["neither"] == sp.Rational(neither, n), (i, p)
        assert 0 < a["neither"] < 1, (i, p)


def test_all_of_kind_math():
    for i in range(20):
        q = _build("pb_all_of_kind", i)
        p, a = q.params, _a(q)
        n, m, k = p["n"], p["m"], p["k"]
        # перебір усіх вибірок: потрібні – ті, що цілком лежать у перших m
        picks = list(itertools.combinations(range(n), k))
        good = [t for t in picks if all(v < m for v in t)]
        assert a["total"] == len(picks) == math.comb(n, k), (i, p)
        assert a["good"] == len(good) == math.comb(m, k), (i, p)
        assert a["chance"] == sp.Rational(len(good), len(picks)), (i, p)
        assert a["chance"] < sp.Rational(1, 2), "задача має бути нетривіальна"


def test_exactly_math():
    for i in range(20):
        q = _build("pb_exactly", i)
        p, a = q.params, _a(q)
        y, b, s, k = p["y"], p["b"], p["s"], p["a"]
        picks = list(itertools.combinations(range(y + b), s))
        good = [t for t in picks if len([v for v in t if v < y]) == k]
        assert a["total"] == len(picks), (i, p)
        assert a["good"] == len(good), (i, p)
        assert a["good"] == math.comb(y, k) * math.comb(b, s - k), (i, p)
        assert a["chance"] == sp.Rational(len(good), len(picks)), (i, p)


def test_pair_parity_math():
    both_asked = set()
    for i in range(30):
        q = _build("pb_pair_parity", i)
        p, a = q.params, _a(q)
        n = p["n"]
        odd, even = (n + 1) // 2, n // 2
        all_pairs = math.comb(n, 2)
        # замкнені формули проти перебору, яким рахує шаблон:
        # добуток непарний <=> обидва числа непарні;
        # сума парна <=> обидва числа однієї парності
        odd_prod = math.comb(odd, 2)
        even_sum = math.comb(odd, 2) + math.comb(even, 2)
        want_prod = odd_prod if p["prod_odd"] else all_pairs - odd_prod
        want_sum = even_sum if p["sum_even"] else all_pairs - even_sum
        assert a["pairs"] == all_pairs, (i, p)
        assert a["prod"] == sp.Rational(want_prod, all_pairs), (i, p)
        assert a["summa"] == sp.Rational(want_sum, all_pairs), (i, p)
        assert a["prod"] != a["summa"], (i, p)
        both_asked.add((p["prod_odd"], p["sum_even"]))
    assert len(both_asked) == 4, ("усі чотири поєднання питань мусять "
                                  "траплятися", both_asked)


def test_inverse_math():
    """Обернена задача мусить мати рівно той розв'язок, що й в еталоні."""
    for i in range(24):
        q = _build("pb_inverse", i)
        p, a = q.params, _a(q)
        num, den, diff = p["num"], p["den"], p["diff"]
        total, more, less = a["total"], a["more"], a["less"]
        assert more + less == total, (i, p)
        assert more - less == diff, (i, p)
        assert sp.Rational(more, total) == sp.Rational(num, den), (i, p)
        # і розв'язок єдиний: перебираємо всі можливі загальні кількості
        fits = [t for t in range(2, 400)
                if sp.Rational(num * t, den).is_integer
                and 2 * sp.Rational(num * t, den) - t == diff]
        assert fits == [total], (i, p, fits)


# =======================================================================
def test_number_kind_math():
    asked = set()
    for i in range(30):
        q = _build("pb_number_kind", i)
        p, a = q.params, _a(q)
        n = p["n"]
        asked.add(p["two"])
        # sympy.isprime – незалежний від пробного ділення в шаблоні
        primes = [k for k in range(1, n + 1) if sp.isprime(k)]
        composite = [k for k in range(1, n + 1) if k > 1 and not sp.isprime(k)]
        digits = [k for k in range(1, n + 1) if (k >= 10) == p["two"]]
        assert a["prime"] == sp.Rational(len(primes), n), (i, p)
        assert a["composite"] == sp.Rational(len(composite), n), (i, p)
        assert a["digits"] == sp.Rational(len(digits), n), (i, p)
        # суть пастки: одиниця не належить до жодної з двох груп
        assert len(primes) + len(composite) == n - 1, (i, p)
        assert a["prime"] + a["composite"] != 1, (i, p)
    assert asked == {True, False}, "питати треба і про дво-, і про одноцифрові"


def test_multiples_math():
    for i in range(24):
        q = _build("pb_multiples", i)
        p, a = q.params, _a(q)
        k, d = p["k"], p["d"]
        # замкнені формули проти прямого підрахунку, яким рахує шаблон
        assert a["total"] == 9 * 10 ** (k - 1), (i, p)
        hi, lo = 10**k - 1, 10 ** (k - 1) - 1
        assert a["good"] == hi // d - lo // d, (i, p)
        assert a["chance"] == sp.Rational(int(a["good"]), int(a["total"])), (i, p)
        assert a["chance"] < sp.Rational(1, 2), (i, p)


def test_digits_math():
    for i in range(24):
        q = _build("pb_digits", i)
        p, a = q.params, _a(q)
        digits, k = p["digits"], p["k"]
        m = len(digits)
        assert 0 not in digits, "нуля серед цифр немає – це пастка §12, не §14"
        # перебір усіх чисел: набір малий, це не залежить від правила добутку
        numbers = list(itertools.product(digits, repeat=k))
        assert a["total"] == len(numbers) == m**k, (i, p)
        even = [t for t in numbers if t[-1] % 2 == 0]
        same = [t for t in numbers if len(set(t)) == 1]
        assert a["even"] == sp.Rational(len(even), len(numbers)), (i, p)
        assert a["same"] == sp.Rational(len(same), len(numbers)), (i, p)
        assert a["same"] == sp.Rational(1, m ** (k - 1)), (i, p)


def test_code_math():
    distinct_seen = any_seen = 0
    for i in range(30):
        q = _build("pb_code", i)
        p, a = q.params, _a(q)
        k = p["k"]
        if p["distinct"]:
            distinct_seen += 1
            want = math.perm(10, k)
            # перебір: скільки k-ок різних цифр
            assert want == len(list(itertools.permutations(range(10), k)))
        else:
            any_seen += 1
            want = 10**k
            if k <= 3:
                assert want == len(list(itertools.product(range(10), repeat=k)))
        assert a["total"] == want, (i, p)
        assert a["first"] == sp.Rational(1, want), (i, p)
        assert a["tries"] == sp.Rational(p["tries"], want), (i, p)
        # кілька спроб кращі за одну, але далеко не певність
        assert a["first"] < a["tries"] < sp.Rational(1, 2), (i, p)
    assert distinct_seen >= 8 and any_seen >= 8, (distinct_seen, any_seen)


def test_pair_mixed_math():
    for i in range(24):
        q = _build("pb_pair_mixed", i)
        p, a = q.params, _a(q)
        boys, girls = p["boys"], p["girls"]
        # перебір усіх пар, як у задачі 2 підручника: хлопці – 0..boys-1
        pairs = list(itertools.combinations(range(boys + girls), 2))
        mixed = [t for t in pairs if (t[0] < boys) != (t[1] < boys)]
        both = [t for t in pairs if t[0] < boys and t[1] < boys]
        assert a["pairs"] == len(pairs) == math.comb(boys + girls, 2), (i, p)
        assert a["mixed"] == sp.Rational(len(mixed), len(pairs)), (i, p)
        assert a["both_boys"] == sp.Rational(len(both), len(pairs)), (i, p)
        # група мала – її справді можна виписати руками, як у підручнику
        assert len(pairs) <= 36, (i, p)


def test_guaranteed_math():
    for i in range(24):
        q = _build("pb_guaranteed", i)
        p, a = q.params, _a(q)
        white, red, need = p["white"], p["red"], p["need"]
        # найгірший випадок прямим перебором: скільки куль може вийти підряд
        # «не тих» перед тим, як набереться потрібне
        worst_white = red + need        # усі червоні могли піти першими
        worst_red = white + 1
        assert a["white_sure"] == worst_white, (i, p)
        assert a["red_sure"] == worst_red, (i, p)
        # а менша кількість уже не гарантує – саме це й означає «P = 1»
        assert worst_white - 1 < need + red, (i, p)
        assert a["first"] == sp.Rational(white, white + red), (i, p)
        assert a["white_sure"] <= white + red, "більше, ніж є, вийняти не можна"
        assert a["red_sure"] <= white + red, (i, p)



# --- перенесення помилки (carry) ---------------------------------------

def test_carry_urn_keeps_probability_with_own_total():
    """Неправильне n – але ймовірність із цього ж n зараховується."""
    for i in range(10):
        q = _build("pb_urn", i)
        p = q.params
        wrong = sum(p["counts"]) + 4
        r = engine.grade(q, {
            "total": str(wrong),
            "chance": str(sp.Rational(p["counts"][p["pick"]], wrong)),
            "never": "0", "sure": "1",
        })
        assert r["score"] == 3.0 and r["max"] == 4, (i, r)


def test_carry_ratio_in_combination_tasks():
    for key in ("pb_all_of_kind", "pb_exactly"):
        for i in range(10):
            q = _build(key, i)
            a = _a(q)
            good = int(a["good"]) + 2            # помилилися в чисельнику
            r = engine.grade(q, {
                "total": str(a["total"]), "good": str(good),
                "chance": str(sp.Rational(good, int(a["total"]))),
            })
            assert r["score"] == 2.0 and r["max"] == 3, (key, i, r)


def test_carry_inverse_chain():
    """Помилкове загальне число – але далі студент послідовний."""
    scored_some = 0
    for i in range(20):
        q = _build("pb_inverse", i)
        p, a = q.params, _a(q)
        wrong = int(a["total"]) + p["den"]        # інше, але ділиться на den
        more = sp.Rational(p["num"] * wrong, p["den"])
        r = engine.grade(q, {
            "total": str(wrong), "more": str(more), "less": str(wrong - more),
        })
        assert r["score"] == 2.0 and r["max"] == 3, (i, p, r)
        scored_some += 1
    assert scored_some == 20


def test_carry_never_rewards_zero_or_one_everywhere():
    """Перенесення не має перетворювати «0» і «1» у правильні відповіді.

    Перерахувати еталон із виродженої відповіді рушій може – важливо, щоб той
    перерахунок не збігся з нею ж. Саме це й ловилося: сума $1$ на обсяг $1$
    давала середнє $1$, і третє поле st_frequency зараховувалося задарма.
    """
    for key in KEYS:
        for i in range(10):
            q = _build(key, i)
            for guess in ("0", "1"):
                r = engine.grade(q, {p.key: guess for p in q.parts})
                paid = [d for d in r["parts"] if d.get("carried") and d["score"]]
                assert not paid, (key, i, guess, paid)

def test_carry_code_scales_with_own_total():
    """Неправильна кількість варіантів – але обидві ймовірності з неї ж."""
    for i in range(12):
        q = _build("pb_code", i)
        p, a = q.params, _a(q)
        wrong = int(a["total"]) * 2
        r = engine.grade(q, {
            "total": str(wrong),
            "first": str(sp.Rational(1, wrong)),
            "tries": str(sp.Rational(p["tries"], wrong)),
        })
        assert r["score"] == 2.0 and r["max"] == 3, (i, p, r)


def test_carry_pair_mixed_uses_own_pair_count():
    for i in range(12):
        q = _build("pb_pair_mixed", i)
        p, a = q.params, _a(q)
        wrong = int(a["pairs"]) + 4
        mixed = p["boys"] * p["girls"]
        both = math.comb(p["boys"], 2)
        r = engine.grade(q, {
            "pairs": str(wrong),
            "mixed": str(sp.Rational(mixed, wrong)),
            "both_boys": str(sp.Rational(both, wrong)),
        })
        assert r["score"] == 2.0 and r["max"] == 3, (i, p, r)


def test_carry_digits_same_follows_own_total():
    for i in range(12):
        q = _build("pb_digits", i)
        p, a = q.params, _a(q)
        m = len(p["digits"])
        wrong = int(a["total"]) + m        # інше, але ділиться на m
        r = engine.grade(q, {
            "total": str(wrong),
            "even": str(a["even"]),
            "same": str(sp.Rational(m, wrong)),
        })
        assert r["score"] == 2.0 and r["max"] == 3, (i, p, r)


def test_carry_multiples_ratio():
    for i in range(12):
        q = _build("pb_multiples", i)
        a = _a(q)
        good = int(a["good"]) + 3
        r = engine.grade(q, {
            "total": str(a["total"]), "good": str(good),
            "chance": str(sp.Rational(good, int(a["total"]))),
        })
        assert r["score"] == 2.0 and r["max"] == 3, (i, r)
