"""Тематичне оцінювання за §12–§15 (комбінаторика, ймовірність, §15).

Математику самих задач перевіряють тести їхніх тем – test_combinatorics,
test_probability, test_statistics. Тут перевіряється те, чого там немає:
СЛОТ. Слот – це питання тесту, за яким стоять 2–4 рівноцінні задачі з однієї
теми, і вибір між ними робить сид студента (app/bank/thematic.py).

Отже перевіряємо: що слоти складені саме так, як задумано; що тема питання
від вибору НЕ залежить (інакше мішанина тем гуляла б від студента до
студента, а оцінка за підсумкову роботу має бути порівнянною); що вибір
відтворюється при перезаході й змінюється при перевиданні; що жодна задача
не трапляється в одній роботі двічі; і що через слот не губиться ні
оцінювання, ні перенесення помилки (carry), ні рисунок.
"""

import pathlib
import re

import pytest
import sympy as sp
import yaml

import engine
from app.bank.thematic import EXTRA, SLOTS, SLOW
from app.config import SECRET

TEST_KEY = "probability_thematic"

# Літеральний "\n" замість переносу; \ne, \nu – валідні команди LaTeX.
_BAD_NEWLINE = re.compile(r"\\n(?![a-zA-Z])")

COMBINATORICS = ["mt_rules", "mt_digits", "mt_rules_hard", "mt_formulas",
                 "mt_choose"]
PROBABILITY = ["mt_classic", "mt_numbers", "mt_count_then_chance", "mt_pair",
               "mt_combinations_chance"]
STATISTICS = ["mt_sample_stats", "mt_sample_mean"]
KEYS = COMBINATORICS + PROBABILITY + STATISTICS

# Префікс банку, з якого слот бере задачі: тема питання не залежить від вибору.
TOPIC = {key: "cmb_" for key in COMBINATORICS} | \
        {key: "pb_" for key in PROBABILITY} | \
        {key: "st_" for key in STATISTICS}


def _build(key, i, attempt=1, reissue=0):
    return engine.build(key, SECRET, f"учень|{i}", TEST_KEY, attempt, reissue)


def _a(q):
    return {p.key: p.answer for p in q.parts}


def _shape(key, i):
    return _build(key, i).params["shape"]


def _find(key, shape, limit=200):
    """Перший студент, якому слот видає саму цю задачу."""
    for i in range(limit):
        if _shape(key, i) == shape:
            return i
    raise AssertionError(f"{shape} не трапився в слоті {key}")


def _printed(statement):
    """Числа-ДАНІ умови: розмітка пунктів «1)» і рядок підказки – не дані."""
    lines = []
    for line in statement.split("\n"):
        if line.startswith("("):
            continue
        line = re.sub(r"Запишіть[^?]*?\.", "", line)
        line = re.sub(r"\d\)", "", line)
        lines.append(line)
    return [int(t) for t in re.findall(r"-?\d+", "\n".join(lines))]


# --- склад тесту --------------------------------------------------------

def test_slots_are_declared_as_planned():
    assert list(SLOTS) == KEYS
    assert len(KEYS) == len(set(KEYS)) == 12
    assert len(COMBINATORICS) == len(PROBABILITY) == 5 and len(STATISTICS) == 2
    assert sum(len(v) for v in SLOTS.values()) == 28


def test_no_task_belongs_to_two_slots():
    """Інакше один шаблон міг би дістатися студентові двічі в одній роботі."""
    all_shapes = [s for shapes in SLOTS.values() for s in shapes]
    assert len(all_shapes) == len(set(all_shapes)), sorted(all_shapes)


def test_every_candidate_template_is_registered():
    for key, shapes in SLOTS.items():
        for shape in shapes:
            assert shape in engine.TEMPLATES, (key, shape)


def test_slot_never_changes_the_topic_of_the_question():
    """Тему тримає слот, а не випадок: мішанина тем у всіх однакова."""
    for key, shapes in SLOTS.items():
        for shape in shapes:
            assert shape.startswith(TOPIC[key]), (key, shape)


def test_yaml_bank_matches_this_module():
    data = yaml.safe_load(pathlib.Path("tests.yaml").read_text(encoding="utf-8"))
    entry = next(t for t in data if t["key"] == TEST_KEY)
    assert entry["bank"] == KEYS
    assert entry["question_count"] == 12
    assert entry["points_per_question"] == 1
    # Банк дорівнює кількості питань – отже кожен студент отримує всі 12 слотів,
    # тобто рівно 5 задач з комбінаторики, 5 з ймовірності й 2 на вибіркові
    # характеристики. Саме цього не дав би просто великий банк.
    assert len(entry["bank"]) == entry["question_count"]
    assert entry["restart_after_violations"] is None


def test_emphasis_is_on_combinatorics_and_probability():
    assert len(COMBINATORICS) + len(PROBABILITY) == 10
    assert len(STATISTICS) * 3 < len(COMBINATORICS) + len(PROBABILITY)


# --- вибір задачі в слоті -----------------------------------------------

def test_every_candidate_really_shows_up():
    """Жодна задача не лишається мертвою, і частки близькі до рівних."""
    runs = 240
    for key, shapes in SLOTS.items():
        seen = [_shape(key, i) for i in range(runs)]
        assert set(seen) == set(shapes), (key, sorted(set(seen)))
        expected = runs / len(shapes)
        for shape in shapes:
            assert seen.count(shape) > expected * 0.6, (key, shape,
                                                        seen.count(shape))


def test_choice_is_reproducible_for_the_same_attempt():
    """Перезахід у тест не має підміняти задачу – інакше втрачалася б робота."""
    for key in KEYS:
        for i in range(12):
            assert _shape(key, i) == _shape(key, i), key
            q1, q2 = _build(key, i), _build(key, i)
            assert q1.statement == q2.statement, (key, i)


def test_reissue_can_change_the_task_not_only_the_numbers():
    """Вихід із тесту перевидає питання – разом з ним змінюється й задача."""
    changed = 0
    for key, shapes in SLOTS.items():
        if len(shapes) == 1:
            continue
        for i in range(20):
            if _build(key, i, reissue=1).params["shape"] != _shape(key, i):
                changed += 1
    assert changed >= 60, changed


def test_students_get_different_sets_of_tasks():
    """Головне проти списування між групами: у кожного своя дванадцятка."""
    papers = [tuple(_shape(key, i) for key in KEYS) for i in range(60)]
    assert len(set(papers)) >= 58, len(set(papers))


def test_nobody_gets_the_same_task_twice():
    for i in range(60):
        shapes = [_shape(key, i) for key in KEYS]
        assert len(shapes) == len(set(shapes)) == 12, (i, shapes)


def test_shape_is_recorded_for_the_journal():
    """У журналі стоїть ключ слота, тож сама задача має лишитися в параметрах."""
    for key, shapes in SLOTS.items():
        for i in range(10):
            q = _build(key, i)
            assert q.key == key, (key, q.key)
            assert q.params["shape"] in shapes, (key, q.params["shape"])


# --- оцінювання ---------------------------------------------------------

def test_all_grade_full_on_correct_answers():
    for key in KEYS:
        for i in range(40):
            q = _build(key, i)
            sub = {p.key: str(p.answer) for p in q.parts}
            r = engine.grade(q, sub)
            assert r["score"] == r["max"] == q.max_score, (key, i, r, sub)


def test_garbage_gets_zero():
    for key in KEYS:
        for i in range(12):
            q = _build(key, i)
            r = engine.grade(q, {p.key: "123456" for p in q.parts})
            assert r["score"] == 0.0, (key, i, q.params["shape"], r)


def test_every_task_shows_the_solution_path():
    """Сенс роботи – бачити ХІД розв'язання, тож одного поля ніде не досить."""
    for key in KEYS:
        for i in range(20):
            q = _build(key, i)
            assert len(q.parts) >= 2, (key, q.params["shape"])


def test_all_fields_are_numbers():
    for key in KEYS:
        for i in range(10):
            for part in _build(key, i).parts:
                assert part.kind == "number", (key, part.key)


def test_no_binary_field_anywhere():
    """Поле «так / ні» вгадується з половини – у підсумковій роботі його нема."""
    for key in KEYS:
        for i in range(30):
            for part in _build(key, i).parts:
                assert "$1$ / $0$" not in part.label, (key, part.label)


def test_carry_survives_the_slot():
    """Шаблони з перенесенням помилки приходять через слот разом з ним."""
    with_carry = set()
    for key in KEYS:
        for i in range(60):
            q = _build(key, i)
            if any(p.carry for p in q.parts):
                with_carry.add(q.params["shape"])
    assert len(with_carry) >= 17, sorted(with_carry)


def test_carry_still_grades_the_own_chain():
    """Наскрізно: своя кількість – і ймовірність, порахована саме з неї."""
    i = _find("mt_numbers", "pb_multiples")
    q = _build("mt_numbers", i)
    a = _a(q)
    good = int(a["good"]) + 3
    r = engine.grade(q, {"total": str(a["total"]), "good": str(good),
                         "chance": str(sp.Rational(good, int(a["total"])))})
    assert r["score"] == 2.0 and r["max"] == 3, r
    assert any(d["part"] == "chance" and d["carried"] for d in r["parts"]), r


# --- умова --------------------------------------------------------------

def test_statements_katex_no_literal_newline():
    for key in KEYS:
        for i in range(12):
            q = _build(key, i)
            assert "$" in q.statement or q.svg, key
            assert not _BAD_NEWLINE.search(q.statement), (key, i)
            assert "- -" not in q.statement and "+ -" not in q.statement, (key, i)


def test_no_cyrillic_inside_math():
    """Шрифти KaTeX кирилиці не містять – усередині $…$ її бути не має."""
    for key in KEYS:
        for i in range(12):
            s = _build(key, i).statement
            for chunk in re.findall(r"\$\$(.+?)\$\$|\$([^$]+)\$", s):
                math_src = chunk[0] or chunk[1]
                assert not re.search(r"[а-яіїєґА-ЯІЇЄҐ]", math_src), (key, math_src)


def test_only_the_diagram_task_has_a_figure():
    for key in KEYS:
        for i in range(30):
            q = _build(key, i)
            if q.params["shape"] == "st_diagram":
                assert q.svg and "<svg" in q.svg, (key, i)
            else:
                assert q.svg is None, (key, q.params["shape"])


def test_statistics_slots_ask_for_the_characteristics_of_a_sample():
    """§15 – це розмах, середнє значення, медіана й мода (та обсяг вибірки).

    Про генеральну сукупність тут не питаємо: це не вибіркова характеристика,
    тому шаблон st_population до слотів і не взято.
    """
    words = ("розмах", "середнє", "медіана", "мода", "обсяг", "сума")
    for key in STATISTICS:
        for i in range(20):
            q = _build(key, i)
            labels = " ".join(p.label for p in q.parts).lower()
            assert sum(w in labels for w in words) >= 2, (key, labels)
            assert "генеральн" not in labels, (key, q.params["shape"])
            assert len(q.parts) >= 3, (key, q.params["shape"])


def test_timings_calibrated():
    """Робота має вкладатися в пару, і час майже не залежить від жеребу."""
    totals = [sum(_build(key, i).seconds for key in KEYS) for i in range(40)]
    assert 2100 <= min(totals) and max(totals) <= 2400, (min(totals), max(totals))
    assert max(totals) - min(totals) <= 300, (min(totals), max(totals))


def test_combinatorics_and_probability_got_extra_time():
    """Викладач переглянув тест: на §12–§14 часу було замало, на §15 досить.

    Надбавка живе в слоті, а не в шаблоні, – час окремих тестів combinatorics
    і probability, які студенти вже здавали, лишається незмінним.
    """
    assert all(SLOW[key] == EXTRA for key in COMBINATORICS + PROBABILITY), SLOW
    assert all(SLOW[key] == 0 for key in STATISTICS), SLOW
    for key in KEYS:
        for i in range(10):
            q = _build(key, i)
            # Скільки та сама задача триває поза підсумковою роботою.
            plain = {engine.build(q.params["shape"], SECRET, f"учень|{j}",
                                  "probability", 1, 0).seconds for j in range(5)}
            assert q.seconds - SLOW[key] in plain, (key, q.params["shape"],
                                                    q.seconds, plain)


# --- безплатні бали -----------------------------------------------------

def test_many_variants_per_slot():
    for key in KEYS:
        tuples = [tuple(str(p.answer) for p in _build(key, i).parts)
                  for i in range(60)]
        assert len(set(tuples)) >= 20, (key, len(set(tuples)))
        assert max(tuples.count(t) for t in set(tuples)) <= 8, key


def test_single_number_guess_is_weak():
    for guess in ("0", "1", "2", "3", "4", "1/2"):
        total = 0.0
        for key in KEYS:
            for i in range(10):
                q = _build(key, i)
                total += engine.grade(
                    q, {p.key: guess for p in q.parts})["score"] / q.max_score
        assert total / 12 < 1.2, (guess, round(total / 12, 2))


def test_copying_a_printed_number_is_weak():
    """«Перепиши перше (останнє) число умови в усі поля» не має давати балів."""
    for pick in (0, -1):
        total = 0.0
        for key in KEYS:
            for i in range(20):
                q = _build(key, i)
                nums = _printed(q.statement)
                guess = str(nums[pick]) if nums else "1"
                total += engine.grade(
                    q, {p.key: guess for p in q.parts})["score"] / q.max_score
        assert total / 20 < 0.6, (pick, round(total / 20, 2))


@pytest.mark.parametrize("key", KEYS)
def test_answers_are_enterable(key):
    for i in range(10):
        for part in _build(key, i).parts:
            engine.parse_answer(str(part.answer), part.kind)
