"""Ймовірність і статистика (§14–§15 Мерзляка, 11 клас).

Кожну відповідь перевіряємо ДРУГИМ, незалежним способом:
  * де шаблон рахує перебором (подільність, парність пар) – тут звіряємо
    замкненою формулою;
  * де шаблон рахує формулою (math.comb) – тут перебираємо всі вибірки
    через itertools;
  * показники вибірки (розмах, середнє, медіана, мода) перераховуємо прямо
    за означеннями §15 з розгорнутого переліку даних, не користуючись
    службовими функціями шаблону.
Тож помилка в одному місці не може «підтвердити сама себе».

Окремо закріплено те, що робить тест стійким до списування: у кожного свої
числа (перевіряємо, що варіантів справді багато), кожна задача багатокрокова,
перелічені вибірки друкуються перемішаними, а показники вибірки навмисне
розведені в різні числа.
"""

import itertools
import math
import pathlib
import re
from fractions import Fraction

import sympy as sp
import yaml

import engine
from app.config import SECRET

# Літеральний "\n" замість переносу; \ne, \nu – валідні команди LaTeX.
_BAD_NEWLINE = re.compile(r"\\n(?![a-zA-Z])")

CHANCE = ["pb_urn", "pb_cards", "pb_all_of_kind", "pb_exactly",
          "pb_pair_parity", "pb_inverse"]
STATS = ["st_sample", "st_diagram", "st_frequency", "st_ordered",
         "st_scores", "st_population"]
KEYS = CHANCE + STATS


def _build(key, i):
    return engine.build(key, SECRET, f"учень|{i}", "probability", 1, 0)


def _a(q):
    return {p.key: p.answer for p in q.parts}


def _expand(labels, counts):
    out = []
    for lab, c in zip(labels, counts):
        out.extend([lab] * c)
    return out


def _mean(data):
    """Середнє значення за означенням §15 – через Fraction, не через sympy."""
    return Fraction(sum(data), len(data))


def _median(data):
    s = sorted(data)
    n = len(s)
    assert n % 2 or s[n // 2 - 1] == s[n // 2], ("медіана неоднозначна", s)
    return s[n // 2]


def _mode(data):
    freq = {v: data.count(v) for v in set(data)}
    top = max(freq.values())
    modes = [v for v, f in freq.items() if f == top]
    assert len(modes) == 1, ("мода не одна", sorted(data))
    return modes[0]


# --- склад тесту --------------------------------------------------------

def test_has_12_types_over_both_paragraphs():
    assert len(KEYS) == len(set(KEYS)) == 12
    assert len(CHANCE) == 6, "§14 – класичне визначення ймовірності"
    assert len(STATS) == 6, "§15 – елементи математичної статистики"


def test_yaml_bank_matches_this_module():
    data = yaml.safe_load(pathlib.Path("tests.yaml").read_text(encoding="utf-8"))
    entry = next(t for t in data if t["key"] == "probability")
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


def test_constant_guess_scores_almost_nothing():
    """Щоб перенесення помилки не стало лазівкою.

    Нуль і одиниця як відповідь є лише в pb_urn (неможлива й достовірна
    події) та в st_ordered (чи можна обчислити середнє), і там вони беруть
    рівно одне поле з чотирьох.
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


def test_probability_fields_are_between_zero_and_one():
    for key in KEYS:
        for i in range(20):
            q = _build(key, i)
            for part in q.parts:
                if "ймовірність" not in part.label.lower():
                    continue
                assert 0 <= part.answer <= 1, (key, i, part.key, part.answer)


def test_unreduced_and_decimal_fractions_accepted():
    """Скорочувати дріб не вимагаємо: 5/33, 10/66 і 0,1515... – те саме."""
    for key in ("pb_cards", "pb_all_of_kind", "pb_exactly", "pb_pair_parity",
                "st_sample", "st_frequency", "st_scores"):
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
    for i in range(10):
        q = _build("st_scores", i)
        share = sp.Rational(_a(q)["mean"])
        r = engine.grade(q, {"mean": str(float(share)).replace(".", ",")})
        scored = {d["part"]: d["score"] for d in r["parts"]}
        assert scored["mean"] == 1, (i, share, r)


def test_statements_katex_no_literal_newline():
    for key in KEYS:
        for i in range(4):
            q = _build(key, i)
            assert "$" in q.statement or q.svg, key
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


def test_only_diagram_has_a_figure():
    for key in KEYS:
        q = _build(key, 3)
        assert (q.svg is not None) == (key == "st_diagram"), key


def test_diagram_question_has_no_numbers_in_the_statement():
    """Дані st_diagram лежать ЛИШЕ на рисунку – переписувати з умови нічого."""
    for i in range(10):
        q = _build("st_diagram", i)
        assert not re.search(r"\d", q.statement.replace("1)", "").replace("2)", "")
                             .replace("3)", "").replace("4)", "")), (i, q.statement)
        for value, count in zip(q.params["labels"], q.params["counts"]):
            assert f">{count}<" in q.svg or count == 0, (i, count)
            assert f">{value}<" in q.svg, (i, value)


def test_timings_calibrated():
    total = 0
    for key in KEYS:
        q = _build(key, 1)
        assert 110 <= q.seconds <= 190, (key, q.seconds)
        total += q.seconds
    assert 1750 <= total <= 1950, total          # ≈29–33 хв на 12 питань
    for key in ("pb_exactly", "pb_pair_parity", "pb_inverse", "pb_cards"):
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
    """Умова має відрізнятися ВИДИМО – інакше неясно, що варіанти різні.

    Порівнюємо дані, а не вступне речення: у st_frequency та st_ordered числа
    стоять у таблиці другим рядком, а сам вступ однаковий на всі варіанти.
    """
    for key in KEYS:
        if key == "st_diagram":
            continue                 # там умова словесна, числа лише на рисунку
        texts = {_build(key, i).statement for i in range(40)}
        assert len(texts) >= 20, (key, len(texts))
        # Числа умови – окремо: у pb_pair_parity їх лише одне (кількість
        # карток), а варіанти там множаться ще й словом – парний чи непарний,
        # тож для чисел межа нижча.
        data = {tuple(re.findall(r"-?\d+", _build(key, i).statement))
                for i in range(40)}
        assert len(data) >= 15, (key, "числа умови майже не змінюються",
                                 len(data))


def test_diagram_figures_differ_between_students():
    figures = {_build("st_diagram", i).svg for i in range(40)}
    assert len(figures) >= 30, len(figures)


def test_sample_is_printed_shuffled():
    """Перелік не впорядкований – інакше медіана стояла б на відомому місці.

    Саме це й ловило в тригонометрії «перепиши k-те число умови»: якщо дані
    надруковані за зростанням, медіана вибірки з десяти чисел – завжди п'яте
    число умови.
    """
    unsorted = 0
    for i in range(30):
        shown = _build("st_sample", i).params["shown"]
        if shown != sorted(shown):
            unsorted += 1
    assert unsorted >= 27, unsorted


def _printed_numbers(statement):
    """Числа, які студент бачить як ДАНІ умови.

    Викидаємо розмітку пунктів «1)», «2)», рядок-підказку в дужках і легенди
    кодів відповіді («Запишіть 1, якщо можна…», «А – 1, Б – 2…»): це не дані
    задачі. Саме на них спіткнулася перша версія цієї перевірки в
    тригонометрії – вона оголосила дірою кожне поле з відповіддю 1.
    """
    lines = []
    for line in statement.split("\n"):
        if line.startswith("("):                       # підказка про формат
            continue
        line = re.sub(r"Запишіть[^?]*?\.", "", line)   # легенда кодів
        line = re.sub(r"\d\)", "", line)               # розмітка пунктів
        lines.append(line)
    return [int(t) for t in re.findall(r"-?\d+", "\n".join(lines))]


def _binary_parts(key, runs):
    """Поля, відповідь яких узагалі буває лише 0 або 1.

    Їх позиційна метрика міряти не може: один біт нічим не захистиш, крім
    рівного розподілу, а його перевіряють окремі тести на самі шаблони
    (test_scores_math, test_ordered_math). Решту полів міряємо повною мірою.
    """
    seen = {}
    for i in range(runs):
        for part in _build(key, i).parts:
            seen.setdefault(part.key, set()).add(sp.Rational(part.answer))
    return {pk for pk, values in seen.items() if values <= {0, 1}}


def test_no_printed_number_is_the_answer_too_often():
    """«Перепиши k-те число умови» не має давати бала систематично.

    Для кожної позиції серед надрукованих чисел умови рахуємо, як часто вона
    збігається з відповіддю конкретного поля. Нижню межу задає сама задача:
    мода вибірки з дванадцяти чисел неминуче займає 3 позиції з 12, тобто 25%.
    40% означало б правило, яке працює без математики.
    """
    runs = 40
    worst = []
    for key in KEYS:
        binary = _binary_parts(key, runs)
        hits = {}
        for i in range(runs):
            q = _build(key, i)
            printed = _printed_numbers(q.statement)
            for pos, number in enumerate(printed[:12]):
                for part in q.parts:
                    if part.key in binary:
                        continue
                    if sp.Rational(part.answer) == number:
                        hits[(pos, part.key)] = hits.get((pos, part.key), 0) + 1
        if hits:
            rule, best = max(hits.items(), key=lambda kv: kv[1])
            worst.append((key, rule, best / runs))
            assert best / runs <= 0.4, (key, rule, best, runs)
    assert worst, "жодне поле не збіглося з умовою – перевірка нічого не міряє"


def test_constant_answer_profile_over_the_whole_test():
    """Скільки з 12 бере той, хто пише те саме в кожне поле.

    Заміряно на 40 варіантах кожного шаблону. Нулі й одиниці беруть своє в
    pb_urn (неможлива й достовірна події) та в двох бінарних полях – це
    неминуче, бо саме ці значення там і є відповіддю. Правильні відповіді
    дають 12,0, тож запас між знанням і вгадуванням більш як десятикратний.
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
        assert total <= 1.1, (guess, round(total, 2))


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
#  §15 – елементи математичної статистики
# =======================================================================

def test_sample_math():
    for i in range(24):
        q = _build("st_sample", i)
        p, a = q.params, _a(q)
        data = p["data"]
        assert sorted(p["shown"]) == data, "надруковане і є вибіркою"
        assert a["range"] == max(data) - min(data), (i, data)
        assert a["mean"] == _mean(data), (i, data)
        assert a["median"] == _median(data), (i, data)
        assert a["mode"] == _mode(data), (i, data)
        # усі чотири показники різні, а розмах і середнє ще й не серед даних
        assert len({str(v) for v in a.values()}) == 4, (i, data, a)
        assert a["range"] not in data and a["mean"] not in data, (i, data)


def test_diagram_math():
    for i in range(24):
        q = _build("st_diagram", i)
        p, a = q.params, _a(q)
        data = _expand(p["labels"], p["counts"])
        assert a["n"] == len(data) == sum(p["counts"]), (i, p)
        assert len(data) % 2 == 1, "обсяг непарний – медіана однозначна"
        assert a["range"] == max(data) - min(data), (i, p)
        assert a["mode"] == _mode(data), (i, p)
        assert a["median"] == _median(data), (i, p)
        assert len({str(v) for v in a.values()}) == 4, (i, p, a)


def test_diagram_range_counts_only_values_that_occurred():
    """Розмах – за значеннями, які СПРАВДІ трапилися, а не за краями осі."""
    narrower = 0
    for i in range(40):
        p = _build("st_diagram", i).params
        if p["counts"][0] == 0 or p["counts"][-1] == 0:
            narrower += 1
            data = _expand(p["labels"], p["counts"])
            assert max(data) - min(data) < len(p["labels"]) - 1, (i, p)
    assert narrower >= 5, ("порожніх крайніх стовпчиків майже не трапляється",
                           narrower)


def test_frequency_math():
    for i in range(24):
        q = _build("st_frequency", i)
        p, a = q.params, _a(q)
        data = _expand(p["values"], p["freqs"])
        assert a["n"] == len(data) == sum(p["freqs"]), (i, p)
        assert a["total"] == sum(data), (i, p)
        assert a["mean"] == _mean(data), (i, p)
        # середнє не ціле й не серед значень – інакше його можна було б угадати
        assert a["mean"] != int(a["mean"]), (i, p)
        assert a["mean"] not in p["values"], (i, p)
        assert min(p["freqs"]) >= 2, "усі частоти 2+, щоб «у N випадках» було правильно"


def test_ordered_math():
    numeric_seen = non_numeric_seen = 0
    for i in range(30):
        q = _build("st_ordered", i)
        p, a = q.params, _a(q)
        labels, counts = p["labels"], p["counts"]
        data = _expand(range(len(labels)), counts)       # працюємо з НОМЕРАМИ
        assert a["n"] == len(data) == sum(counts), (i, p)
        assert len(data) % 2 == 1, "обсяг непарний – медіана однозначна"
        rank_mode, rank_median = _mode(data), _median(data)
        if p["numeric"]:
            numeric_seen += 1
            assert a["mode"] == int(labels[rank_mode]), (i, p)
            assert a["median"] == int(labels[rank_median]), (i, p)
            assert a["mean_ok"] == 1, "числові дані – середнє існує"
        else:
            non_numeric_seen += 1
            assert a["mode"] == rank_mode + 1, (i, p)
            assert a["median"] == rank_median + 1, (i, p)
            assert a["mean_ok"] == 0, "§15: середнє визначають лише для чисел"
        assert a["mode"] != a["median"], (i, p)
    # обидві половини мусять траплятися – інакше четверте поле вгадується
    assert numeric_seen >= 8 and non_numeric_seen >= 8, (numeric_seen,
                                                         non_numeric_seen)


def test_ordered_non_numeric_scale_is_really_non_numeric():
    for i in range(40):
        p = _build("st_ordered", i).params
        if p["numeric"]:
            continue
        for lab in p["labels"]:
            assert not lab.isdigit(), (i, lab)
            assert set(lab) <= set("XSML"), (i, lab)


def test_scores_math():
    ones = zeros = 0
    for i in range(30):
        q = _build("st_scores", i)
        p, a = q.params, _a(q)
        percents, correct = p["percents"], p["correct"]
        assert sum(percents) == 100, (i, p)
        # вибірка з нулів та одиниць на 100 учнів – розгортаємо й міряємо
        data = [1] * percents[correct] + [0] * (100 - percents[correct])
        assert a["mean"] == _mean(data), (i, p)
        assert a["median"] == _median(data), (i, p)
        assert a["mode"] == percents.index(max(percents)) + 1, (i, p)
        assert sorted(percents)[-1] > sorted(percents)[-2], "мода мусить бути одна"
        if a["median"] == 1:
            ones += 1
            assert a["mode"] == correct + 1, "більшість відповіла правильно"
        else:
            zeros += 1
            assert a["mode"] != correct + 1, "мода припала на хибний варіант"
    # обидва випадки мусять траплятися – інакше медіана вгадується сталою
    assert ones >= 8 and zeros >= 8, (ones, zeros)


def test_population_math():
    for i in range(24):
        q = _build("st_population", i)
        p, a = q.params, _a(q)
        lo, hi, sample = p["lo"], p["hi"], p["sample"]
        assert len(sample) == 5 and len(set(sample)) == 5, (i, p)
        assert all(lo <= v <= hi for v in sample), (i, p)
        # обсяг сукупності рахуємо перебором діапазону, а не формулою
        assert a["population"] == len(range(lo, hi + 1)), (i, p)
        assert a["span"] == hi - lo, (i, p)
        assert a["population"] - a["span"] == 1, "та сама одиниця, що й плутають"
        assert a["spread"] == max(sample) - min(sample), (i, p)
        assert a["median"] == _median(sample), (i, p)
        assert a["spread"] < a["span"], "вибірка вужча за сукупність"
        assert min(sample) < 0 < max(sample), "числа різнозначні"


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


def test_carry_frequency_mean_is_own_sum_over_own_n():
    for i in range(10):
        q = _build("st_frequency", i)
        a = _a(q)
        total = int(a["total"]) + 5
        r = engine.grade(q, {
            "n": str(a["n"]), "total": str(total),
            "mean": str(sp.Rational(total, int(a["n"]))),
        })
        assert r["score"] == 2.0 and r["max"] == 3, (i, r)


def test_carry_population_span_is_own_size_minus_one():
    for i in range(10):
        q = _build("st_population", i)
        a = _a(q)
        wrong = int(a["population"]) + 7
        r = engine.grade(q, {
            "population": str(wrong), "span": str(wrong - 1),
            "spread": str(a["spread"]), "median": str(a["median"]),
        })
        assert r["score"] == 3.0 and r["max"] == 4, (i, r)


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
