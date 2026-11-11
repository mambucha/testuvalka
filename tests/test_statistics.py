"""Математична статистика (§15 Мерзляка, 11 клас).

Чотири з шести шаблонів питають у тематичному оцінюванні
probability_thematic – через слоти (app/bank/thematic.py), а не прямо з банку;
які саме, закріплено нижче окремою перевіркою. Два інші (st_ordered,
st_population) не входять у жоден тест і лишаються покритими, щоб тему можна
було розширити одним рядком і щоб вони не згнили тим часом.

Кожен показник вибірки перераховуємо тут прямо за означеннями §15 з
розгорнутого переліку даних, не чіпаючи службових функцій шаблону, – тож
помилка в них не може «підтвердити сама себе».
"""

import pathlib
import re

import sympy as sp
import yaml

import engine
from app.bank.thematic import SLOTS
from app.config import SECRET

# Літеральний "\n" замість переносу; \ne, \nu – валідні команди LaTeX.
_BAD_NEWLINE = re.compile(r"\\n(?![a-zA-Z])")

KEYS = ["st_sample", "st_diagram", "st_frequency", "st_ordered",
        "st_scores", "st_population"]


def _build(key, i):
    return engine.build(key, SECRET, f"учень|{i}", "statistics", 1, 0)


def _a(q):
    return {p.key: p.answer for p in q.parts}


def _expand(labels, counts):
    out = []
    for lab, c in zip(labels, counts):
        out.extend([lab] * c)
    return out


def _mean(data):
    """Середнє значення за означенням §15 – через Fraction, не через sympy."""
    from fractions import Fraction
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


# --- де саме §15 запитують -----------------------------------------------

# Вибіркові характеристики входять у тематичне оцінювання probability_thematic,
# і то не прямо: там у банку стоять СЛОТИ, за кожним з яких кілька рівноцінних
# задач (app/bank/thematic.py). Окремого тесту на §15 немає – тема мала, її
# двох питань у підсумковій роботі досить.
IN_THEMATIC = ["st_sample", "st_diagram", "st_frequency", "st_scores"]


def test_statistics_is_examined_only_through_the_thematic_slots():
    """Прямо в банку жодного тесту цих ключів нема – лише через слоти."""
    data = yaml.safe_load(pathlib.Path("tests.yaml").read_text(encoding="utf-8"))
    used = {key for entry in data for key in entry["bank"]}
    assert not (used & set(KEYS)), sorted(used & set(KEYS))
    through_slots = {s for shapes in SLOTS.values() for s in shapes}
    assert through_slots & set(KEYS) == set(IN_THEMATIC), \
        sorted(through_slots & set(KEYS))


def test_the_two_unused_templates_stay_covered():
    """st_ordered має поле «так / ні», st_population питає не про вибіркову
    характеристику, тож у слоти вони не пішли. Тести на них лишаються: тему
    можна буде розширити одним рядком, і шаблони не згниють тим часом."""
    assert set(KEYS) - set(IN_THEMATIC) == {"st_ordered", "st_population"}


def test_templates_are_registered_anyway():
    """Зареєстровані мусять лишатися всі: за цими ключами оцінюються спроби,
    які могли бути створені, поки тема стояла в tests.yaml прямо."""
    for key in KEYS:
        assert key in engine.TEMPLATES, key


# --- спільні властивості -------------------------------------------------

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
    for key in KEYS:
        for i in range(8):
            q = _build(key, i)
            for guess in ("0", "1", "2", "1/2"):
                r = engine.grade(q, {p.key: guess for p in q.parts})
                assert r["score"] <= 1.0, (key, i, guess, r)


def test_answers_are_enterable():
    for key in KEYS:
        for i in range(20):
            for part in _build(key, i).parts:
                value = sp.Rational(part.answer)
                assert len(str(abs(value.p))) <= 9, (key, i, part.key, value)
                assert len(str(value.q)) <= 9, (key, i, part.key, value)


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
        text = q.statement
        for marker in ("1)", "2)", "3)", "4)"):
            text = text.replace(marker, "")
        assert not re.search(r"\d", text), (i, q.statement)
        for value, count in zip(q.params["labels"], q.params["counts"]):
            assert f">{count}<" in q.svg or count == 0, (i, count)
            assert f">{value}<" in q.svg, (i, value)


def test_timings_calibrated():
    total = 0
    for key in KEYS:
        q = _build(key, 1)
        assert 110 <= q.seconds <= 190, (key, q.seconds)
        total += q.seconds
    assert 850 <= total <= 1000, total


# --- стійкість до списування -------------------------------------------

def test_many_variants_per_template():
    for key in KEYS:
        tuples = [tuple(str(v) for v in _a(_build(key, i)).values())
                  for i in range(60)]
        distinct = len(set(tuples))
        top = max(tuples.count(t) for t in set(tuples))
        assert distinct >= 15, (key, "замало варіантів", distinct)
        assert top <= 10, (key, "надто частий варіант", top)


def test_diagram_figures_differ_between_students():
    figures = {_build("st_diagram", i).svg for i in range(40)}
    assert len(figures) >= 30, len(figures)


def test_sample_is_printed_shuffled():
    """Перелік не впорядкований – інакше медіана стояла б на відомому місці."""
    unsorted = 0
    for i in range(30):
        shown = _build("st_sample", i).params["shown"]
        if shown != sorted(shown):
            unsorted += 1
    assert unsorted >= 27, unsorted


def test_ordered_ranks_are_spread_over_the_scale():
    """Ні медіана, ні мода не тулляться до одного місця шкали.

    Без цього медіана припадала на середину шкали в 38% варіантів, а мода –
    на перший розмір у 35%, тобто обидві вгадувалися, не рахуючи нічого.
    """
    med, mod = {}, {}
    runs = 120
    for i in range(runs):
        q = _build("st_ordered", i)
        p, a = q.params, _a(q)
        if p["numeric"]:
            m_rank = p["labels"].index(str(a["mode"]))
            d_rank = p["labels"].index(str(a["median"]))
        else:
            m_rank, d_rank = int(a["mode"]) - 1, int(a["median"]) - 1
        mod[m_rank] = mod.get(m_rank, 0) + 1
        med[d_rank] = med.get(d_rank, 0) + 1
    assert max(med.values()) / runs <= 0.35, sorted(med.items())
    assert max(mod.values()) / runs <= 0.35, sorted(mod.items())


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


