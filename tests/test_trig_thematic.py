"""Тематичне оцінювання з тригонометрії (§2 «Математика 10» Мерзляка).

Банк theme5 (tr_*) перевіряє test_trigonometry.py, механіку слотів –
test_probability_thematic. Тут:
  * НЕЗАЛЕЖНА математика нових шаблонів п.13 і п.15–17 (tq_*): значення
    перераховуються з надрукованих в умові кутів numeric-ом, аркфункції
    звіряються з означеннями, корені рівнянь – перебором серій;
  * поведінка МІШАНОГО банку: шість гарантованих питань (інтерактив,
    формули, рівняння) + шість слотів, два клікабельні кола на роботу;
  * захист вигляду відповіді: ввід з арк- чи тригонометричними функціями
    в полях «обчисліть» відхиляється, бо значення в нього правильне.
"""

import math
import pathlib
import re

import pytest
import sympy as sp
import yaml

import engine
from app.bank.trig_thematic import SLOTS
from app.config import SECRET

TEST_KEY = "trig_thematic"

DIRECT = ["tr_circle_locate", "tq_addition", "tq_double", "tq_arc",
          "tq_eq_cos", "tq_eq_simple"]
BANK = ["tr_circle_locate", "tt_read", "tt_basics", "tt_identity",
        "tt_reduction", "tt_function", "tq_addition", "tq_double",
        "tq_arc", "tq_eq_cos", "tq_eq_simple", "tt_eq_algebraic"]
EXPECTED_SLOTS = {
    "tt_read": ("tr_circle_read", "tr_graph_read"),
    "tt_basics": ("tr_radians", "tr_signs"),
    "tt_identity": ("tr_pythagorean", "tr_simplify"),
    "tt_reduction": ("tr_reduction", "tr_reduction_value"),
    "tt_function": ("tr_period", "tr_properties", "tr_compare"),
    "tt_eq_algebraic": ("tq_eq_quadratic", "tq_eq_homogeneous"),
}

# Літеральний "\n" замість переносу; \ne, \nu – валідні команди LaTeX.
_BAD_NEWLINE = re.compile(r"\\n(?![a-zA-Z])")


def _build(key, i, attempt=1, reissue=0):
    return engine.build(key, SECRET, f"учень|{i}", TEST_KEY, attempt, reissue)


def _a(q):
    return {p.key: p.answer for p in q.parts}


def _shape(key, i):
    q = _build(key, i)
    return q.params.get("shape", key)


def _num(value) -> float:
    return float(sp.sympify(value))


def _find(key, want, limit=200):
    for i in range(limit):
        q = _build(key, i)
        if q.params.get("shape", key) == want or q.params.get("fn") == want:
            return i, q
    raise AssertionError(f"{want} не трапився в {key}")


# =======================================================================
#  НЕЗАЛЕЖНА МАТЕМАТИКА НОВИХ ШАБЛОНІВ (п.13, п.15–17)
# =======================================================================

def test_addition_math():
    """Значення перераховуємо з НАДРУКОВАНИХ кутів, не з цільового кута."""
    exact_seen = set()
    for i in range(40):
        q = _build("tq_addition", i)
        p, a = q.params, _a(q)
        # доданки нетабличні – згорнути формулою це єдиний шлях
        for angle in (p["a1"], p["b1"], p["a2"], p["b2"]):
            assert angle % 15 != 0 and 0 < angle, (i, p)
        s1 = -1 if p["sin_diff"] else 1
        v1 = (math.sin(math.radians(p["a1"])) * math.cos(math.radians(p["b1"]))
              + s1 * math.cos(math.radians(p["a1"]))
              * math.sin(math.radians(p["b1"])))
        assert abs(v1 - _num(a["fold_sin"])) < 1e-9, (i, p)
        s2 = -1 if p["cos_sum"] else 1
        v2 = (math.cos(math.radians(p["a2"])) * math.cos(math.radians(p["b2"]))
              + s2 * math.sin(math.radians(p["a2"]))
              * math.sin(math.radians(p["b2"])))
        assert abs(v2 - _num(a["fold_cos"])) < 1e-9, (i, p)
        f3 = math.sin if p["f3_is_sin"] else math.cos
        assert abs(f3(math.radians(p["t3"])) - _num(a["exact"])) < 1e-9, (i, p)
        # відповідь третього пункту – точна (ірраціональна), не десяткова
        assert not sp.nsimplify(a["exact"]).is_rational, (i, a["exact"])
        assert a["fold_sin"] != a["fold_cos"], (i, "поля не мають збігатися")
        exact_seen.add(str(a["exact"]))
    assert len(exact_seen) >= 3, exact_seen


def test_double_math():
    """Подвійний аргумент: усе звіряється через сам кут, без формул шаблону."""
    for i in range(40):
        q = _build("tq_double", i)
        p, a = q.params, _a(q)

        def to_rad(half):
            kind, val = half
            return math.radians(val) if kind == "deg" else math.pi * val[0] / val[1]

        r1 = to_rad(p["half1"])
        assert abs(2 * math.sin(r1) * math.cos(r1) - _num(a["sin2"])) < 1e-9
        r2 = to_rad(p["half2"])
        assert abs(math.cos(2 * r2) - _num(a["cos2"])) < 1e-9, (i, p)
        # третій пункт: будуємо КОНКРЕТНИЙ кут із даним sin (cos) і беремо
        # від нього cos 2a – формула шаблону в перевірці не бере участі
        given = p["sign"] * p["p"] / p["h"]
        angle = math.asin(given) if p["given_sin"] else math.acos(given)
        assert abs(math.cos(2 * angle) - _num(a["from_given"])) < 1e-9, (i, p)


def test_arc_math():
    """Аркфункції звіряємо з ОЗНАЧЕННЯМИ: функція від відповіді й проміжок."""
    negatives = 0
    for i in range(40):
        q = _build("tq_arc", i)
        p, a = q.params, _a(q)
        b_cos, b_sin, b_tg = (sp.sympify(p[k]) for k in ("b_cos", "b_sin", "b_tg"))
        assert sp.cos(a["acos"]) == b_cos and 0 <= a["acos"] <= sp.pi, (i, p)
        assert sp.sin(a["asin"]) == b_sin, (i, p)
        assert -sp.pi / 2 <= a["asin"] <= sp.pi / 2, (i, p)
        assert sp.tan(a["atg"]) == b_tg, (i, p)
        assert -sp.pi / 2 < a["atg"] < sp.pi / 2, (i, p)
        negatives += sum(1 for b in (b_cos, b_sin, b_tg) if b < 0)
        assert any(b < 0 for b in (b_cos, b_sin, b_tg)), (i, p)
    assert negatives >= 40, negatives


_INTERVALS = {
    r"[-\pi;\ 0]": (-sp.pi, 0),
    r"[2\pi;\ 3\pi]": (2 * sp.pi, 3 * sp.pi),
    r"[-2\pi;\ -\pi]": (-2 * sp.pi, -sp.pi),
}


def _cos_roots_between(b, lo, hi):
    alpha = sp.acos(b)
    out = set()
    for n in range(-3, 4):
        for x in (alpha + 2 * sp.pi * n, -alpha + 2 * sp.pi * n):
            if float(lo) - 1e-12 <= float(x) <= float(hi) + 1e-12:
                out.add(sp.nsimplify(x, [sp.pi]))
    return out


def test_eq_cos_math():
    for i in range(40):
        q = _build("tq_eq_cos", i)
        p, a = q.params, _a(q)
        b = sp.sympify(p["b"])
        assert sp.cos(a["less"]) == b and sp.cos(a["more"]) == b, (i, p)
        assert 0 < a["less"] < a["more"] < 2 * sp.pi, (i, p)
        lo, hi = _INTERVALS[p["interval"]]
        assert lo <= a["third"] <= hi and sp.cos(a["third"]) == b, (i, p)
        # на проміжку [0; 2pi) коренів рівно два, на проміжку пункту 3 – один
        assert _cos_roots_between(b, 0, 2 * sp.pi - sp.Rational(1, 100)) == \
            {a["less"], a["more"]}, (i, p)
        assert _cos_roots_between(b, lo, hi) == {a["third"]}, (i, p)


def _sin_series(b, n_range=range(-3, 8)):
    alpha = sp.asin(b)
    for n in n_range:
        yield alpha + 2 * sp.pi * n
        yield sp.pi - alpha + 2 * sp.pi * n


def test_eq_simple_sin_math():
    seen_counts = set()
    for i in range(80):
        q = _build("tq_eq_simple", i)
        if q.params["fn"] != "sin":
            continue
        p, a = q.params, _a(q)
        b = sp.sympify(p["b"])
        assert sp.sin(a["arc"]) == b, (i, p)
        assert -sp.pi / 2 <= a["arc"] <= sp.pi / 2, (i, p)
        # найменший додатний – перебором серій
        positive = sorted(x for x in _sin_series(b) if float(x) > 1e-12)
        assert a["least"] == sp.nsimplify(positive[0], [sp.pi]), (i, p)
        # кількість на [0; k*pi] – теж перебором, і вона не дорівнює k
        k = p["k"]
        count = len({sp.nsimplify(x, [sp.pi]) for x in _sin_series(b)
                     if -1e-12 <= float(x) <= float(k * sp.pi) + 1e-12})
        assert int(a["count"]) == count == p["count"], (i, p)
        assert k % 2 == 1 and count != k, (i, p, "k лише непарне")
        seen_counts.add(count)
    assert len(seen_counts) >= 3, seen_counts


def test_eq_simple_tg_math():
    for i in range(80):
        q = _build("tq_eq_simple", i)
        if q.params["fn"] != "tg":
            continue
        p, a = q.params, _a(q)
        b = sp.sympify(p["b"])
        assert sp.tan(a["arc"]) == b, (i, p)
        assert -sp.pi / 2 < a["arc"] < sp.pi / 2, (i, p)
        roots = sorted((sp.atan(b) + sp.pi * n for n in range(-2, 8)),
                       key=float)
        positive = [x for x in roots if float(x) > 1e-12]
        assert a["least"] == sp.nsimplify(positive[0], [sp.pi]), (i, p)
        k = p["k"]
        inside = [x for x in roots
                  if float(k * sp.pi) + 1e-12 < float(x) < float((k + 1) * sp.pi) - 1e-12]
        assert len(inside) == 1, (i, p)
        assert a["on_interval"] == sp.nsimplify(inside[0], [sp.pi]), (i, p)


def _least_positive_for(fn, t):
    """Найменший додатний корінь sin x = t чи cos x = t – перебором серій."""
    if fn == "sin":
        series = [x for x in _sin_series(t)]
    else:
        alpha = sp.acos(t)
        series = [s * alpha + 2 * sp.pi * n for n in range(-2, 4) for s in (1, -1)]
    positive = sorted((x for x in series if float(x) > 1e-12), key=float)
    return sp.nsimplify(positive[0], [sp.pi])


def test_eq_quadratic_math():
    both_seen = set()
    for i in range(40):
        q = _build("tq_eq_quadratic", i)
        p, a = q.params, _a(q)
        ca, cb, cc = p["coeffs"]
        # корені справді є коренями НАДРУКОВАНОГО квадратного рівняння
        for t in (a["t_lo"], a["t_hi"]):
            assert ca * t**2 + cb * t + cc == 0, (i, p)
        assert a["t_lo"] < a["t_hi"], (i, p)
        valid = [t for t in (a["t_lo"], a["t_hi"]) if abs(t) <= 1]
        assert int(a["series"]) == len(valid) in (1, 2), (i, p)
        if not p["both_valid"]:
            assert len(valid) == 1, (i, p)
        least = min((_least_positive_for(p["fn"], t) for t in valid), key=float)
        assert a["least"] == least and float(least) > 0, (i, p)
        both_seen.add(len(valid))
    assert both_seen == {1, 2}, both_seen


def _coef(c):
    return {"1": 1, "-1": -1, "sqrt3": math.sqrt(3),
            "-sqrt3": -math.sqrt(3)}[str(c)]


def test_eq_homogeneous_math():
    for i in range(40):
        q = _build("tq_eq_homogeneous", i)
        p, a = q.params, _a(q)
        ca, cb = _coef(p["ca"]), _coef(p["cb"])
        # обидва заявлені корені задовольняють САМЕ рівняння з умови
        for x in (a["least"], a["on_interval"]):
            fx = float(x)
            assert abs(ca * math.sin(fx) + cb * math.cos(fx)) < 1e-9, (i, p)
        assert sp.tan(a["least"]) == a["ratio"], (i, p)
        # найменший додатний: лівіше за нього кореня немає
        r = float(a["ratio"])
        base = math.atan(r)
        candidates = sorted(base + math.pi * n for n in range(-2, 8))
        first = min(x for x in candidates if x > 1e-12)
        assert abs(float(a["least"]) - first) < 1e-9, (i, p)
        k = p["k"]
        inside = [x for x in candidates
                  if k * math.pi + 1e-9 < x < (k + 1) * math.pi - 1e-9]
        assert len(inside) == 1 and abs(float(a["on_interval"]) - inside[0]) < 1e-9


# =======================================================================
#  СКЛАД ТЕСТУ: гарантовані питання + слоти
# =======================================================================

def test_bank_matches_yaml_and_slots():
    data = yaml.safe_load(pathlib.Path("tests.yaml").read_text(encoding="utf-8"))
    entry = next(t for t in data if t["key"] == TEST_KEY)
    assert entry["bank"] == BANK
    assert entry["question_count"] == len(BANK) == 12
    assert entry["points_per_question"] == 1
    assert entry["restart_after_violations"] is None
    assert SLOTS == EXPECTED_SLOTS


def test_slot_candidates_do_not_overlap_anything():
    """Жодна задача не може трапитися в роботі двічі: ні між слотами, ні зі
    звичайними позиціями банку."""
    everything = list(DIRECT)
    for shapes in SLOTS.values():
        everything.extend(shapes)
    assert len(everything) == len(set(everything)), sorted(everything)
    for key, shapes in SLOTS.items():
        for shape in shapes:
            assert shape in engine.TEMPLATES, (key, shape)


def test_guaranteed_questions_are_guaranteed():
    """Інтерактив, формули додавання, аркфункції й найпростіші рівняння
    викладач просив дати КОЖНОМУ – вони стоять у банку прямо, без жеребу."""
    for key in DIRECT:
        assert key not in SLOTS
        assert key in BANK
    # банк дорівнює кількості питань: кожен студент бачить усі 12 позицій
    assert len(BANK) == 12


def test_every_paper_has_two_interactive_and_one_figure():
    for i in range(30):
        pickable = plain_fig = 0
        for key in BANK:
            q = _build(key, i)
            if q.svg and "uc-dot" in q.svg and "data-ins" in q.svg:
                pickable += 1
            elif q.svg:
                plain_fig += 1
        assert pickable == 2, (i, pickable)
        assert plain_fig == 1, (i, plain_fig)


def test_choice_is_reproducible_for_the_same_attempt():
    for key in SLOTS:
        for i in range(12):
            q1, q2 = _build(key, i), _build(key, i)
            assert q1.params["shape"] == q2.params["shape"], (key, i)
            assert q1.statement == q2.statement, (key, i)


def test_reissue_keeps_the_task_and_changes_only_the_numbers():
    """Перевидання – не «перекид» жеребу (та сама вимога, що й у
    probability_thematic: інакше вихід із вкладки фільтрував би задачі)."""
    same_numbers = 0
    for key in BANK:
        for i in range(15):
            for re_no in (1, 2):
                q0, q1 = _build(key, i), _build(key, i, reissue=re_no)
                assert q0.params.get("shape", key) == \
                    q1.params.get("shape", key), (key, i, re_no)
            if _build(key, i).statement == _build(key, i, reissue=1).statement:
                same_numbers += 1
    assert same_numbers <= 40, same_numbers


def test_second_attempt_rerolls_the_slotted_tasks():
    changed = 0
    for key in SLOTS:
        for i in range(20):
            if _shape(key, i) != _build(key, i, attempt=2).params["shape"]:
                changed += 1
    assert changed >= 35, changed


def test_every_candidate_really_shows_up():
    runs = 240
    for key, shapes in SLOTS.items():
        seen = [_shape(key, i) for i in range(runs)]
        assert set(seen) == set(shapes), (key, sorted(set(seen)))
        expected = runs / len(shapes)
        for shape in shapes:
            assert seen.count(shape) > expected * 0.6, (key, shape,
                                                        seen.count(shape))


# =======================================================================
#  ОЦІНЮВАННЯ, ВИГЛЯД ВІДПОВІДІ, CARRY
# =======================================================================

def test_all_grade_full_on_correct_answers():
    for key in BANK:
        for i in range(40):
            q = _build(key, i)
            r = engine.grade(q, {p.key: str(p.answer) for p in q.parts})
            assert r["score"] == r["max"] == q.max_score, (key, i, r)


def test_garbage_gets_zero():
    for key in BANK:
        for i in range(12):
            q = _build(key, i)
            r = engine.grade(q, {p.key: "123456" for p in q.parts})
            assert r["score"] == 0.0, (key, i, q.params.get("shape", key), r)


def test_every_task_shows_the_solution_path():
    """Одного поля немає ніде; два – лише в tr_simplify з theme5."""
    for key in BANK:
        for i in range(20):
            q = _build(key, i)
            floor = 2 if q.params.get("shape") == "tr_simplify" else 3
            assert len(q.parts) >= floor, (key, i, q.params.get("shape"))


def test_arc_functions_in_input_are_refused():
    """«arccos(1/2)» дорівнює еталону за значенням, але обчислити – це і є
    задача, тож такий ввід відхиляється, а не оцінюється."""
    refused = checked = 0
    for key in ("tq_arc", "tq_eq_cos", "tq_eq_simple", "tq_eq_quadratic",
                "tq_eq_homogeneous", "tq_addition", "tq_double"):
        for i in range(8):
            q = _build(key, i)
            sub = {}
            cheat = set()
            for p in q.parts:
                if p.reject is not None:
                    sub[p.key] = f"acos(cos({p.answer}))"
                    cheat.add(p.key)
                else:
                    sub[p.key] = str(p.answer)
            if not cheat:
                continue
            r = engine.grade(q, sub)
            checked += 1
            for d in r["parts"]:
                if d["part"] in cheat:
                    assert d["score"] == 0.0, (key, i, d)
                    assert "error" in d, (key, i, d)
                    refused += 1
    assert checked >= 50 and refused >= 150, (checked, refused)


def test_plain_fields_refuse_trig_in_input():
    """Поля «обчисліть» не приймають і sin/cos/tg: переписана в радіанах
    умова теж дорівнює еталону за значенням."""
    for i in range(10):
        q = _build("tq_addition", i)
        sub = {p.key: str(p.answer) for p in q.parts}
        sub["fold_sin"] = f"({sub['fold_sin']})*sin(pi/2)"
        r = engine.grade(q, sub)
        d = next(d for d in r["parts"] if d["part"] == "fold_sin")
        assert d["score"] == 0.0 and "error" in d, (i, d)


def test_carry_eq_cos_follows_own_smaller_root():
    """Неправильний менший корінь – але більший і третій рахуються з нього."""
    carried = 0
    for i in range(30):
        q = _build("tq_eq_cos", i)
        a = _a(q)
        own = a["less"] + sp.pi / 7          # «не той» кут у (0; pi)
        if not (0 < float(own) < float(sp.pi)):
            continue
        lo, hi = _INTERVALS[q.params["interval"]]
        third = {(-sp.pi, 0): -own, (2 * sp.pi, 3 * sp.pi): 2 * sp.pi + own,
                 (-2 * sp.pi, -sp.pi): own - 2 * sp.pi}[(lo, hi)]
        r = engine.grade(q, {"less": str(own), "more": str(2 * sp.pi - own),
                             "third": str(third)})
        assert r["score"] == 2.0 and r["max"] == 3, (i, r)
        carried += sum(1 for d in r["parts"] if d.get("carried"))
    assert carried >= 40, carried


def test_carry_homogeneous_interval_follows_own_least():
    for i in range(40):
        q = _build("tq_eq_homogeneous", i)
        p, a = q.params, _a(q)
        own = a["least"] + sp.pi / 9
        if not (0 < float(own) < float(sp.pi)):
            continue
        r = engine.grade(q, {"ratio": str(a["ratio"]), "least": str(own),
                             "on_interval": str(own + p["k"] * sp.pi)})
        assert r["score"] == 2.0 and r["max"] == 3, (i, p, r)


def test_carry_quadratic_series_and_least_follow_own_roots():
    """Корені квадратного не ті – але придатність і найменший корінь свої."""
    done = 0
    for i in range(60):
        q = _build("tq_eq_quadratic", i)
        p, a = q.params, _a(q)
        own = sorted([sp.Rational(-1, 2), sp.Integer(-2)])
        if set(own) == {a["t_lo"], a["t_hi"]}:
            continue
        least = _least_positive_for(p["fn"], sp.Rational(-1, 2))
        r = engine.grade(q, {"t_lo": str(own[0]), "t_hi": str(own[1]),
                             "series": "1", "least": str(least)})
        scored = {d["part"]: d["score"] for d in r["parts"]}
        assert scored["series"] == 1.0 and scored["least"] == 1.0, (i, p, r)
        done += 1
    assert done >= 40, done


def test_carry_does_not_reward_constant_input():
    for key in BANK:
        for i in range(10):
            q = _build(key, i)
            for guess in ("2", "pi"):
                r = engine.grade(q, {p.key: guess for p in q.parts})
                for d in r["parts"]:
                    if d.get("carried"):
                        assert d["score"] == 0.0, (key, i, guess, d)


# =======================================================================
#  УМОВИ, ЧАС, БЕЗПЛАТНІ БАЛИ
# =======================================================================

def test_statements_katex_no_literal_newline():
    for key in BANK:
        for i in range(12):
            q = _build(key, i)
            assert "$" in q.statement or q.svg, key
            assert not _BAD_NEWLINE.search(q.statement), (key, i)
            assert "- -" not in q.statement and "+ -" not in q.statement, (key, i)


def test_no_cyrillic_inside_math():
    for key in BANK:
        for i in range(12):
            s = _build(key, i).statement
            for chunk in re.findall(r"\$\$(.+?)\$\$|\$([^$]+)\$", s):
                math_src = chunk[0] or chunk[1]
                assert not re.search(r"[а-яіїєґА-ЯІЇЄҐ]", math_src), (key, math_src)


def test_timings_calibrated():
    totals = [sum(_build(key, i).seconds for key in BANK) for i in range(40)]
    assert 2400 <= min(totals) and max(totals) <= 2650, (min(totals), max(totals))
    assert max(totals) - min(totals) <= 150, (min(totals), max(totals))


def test_many_variants_per_position():
    for key in BANK:
        tuples = [tuple(str(p.answer) for p in _build(key, i).parts)
                  for i in range(60)]
        assert len(set(tuples)) >= 15, (key, len(set(tuples)))
        assert max(tuples.count(t) for t in set(tuples)) <= 10, key


def test_single_number_guess_is_weak():
    for guess in ("0", "1", "2", "1/2", "pi", "pi/6"):
        total = 0.0
        for key in BANK:
            for i in range(10):
                q = _build(key, i)
                total += engine.grade(
                    q, {p.key: guess for p in q.parts})["score"] / q.max_score
        assert total / 10 < 1.3, (guess, round(total / 10, 2))


def _printed(statement):
    """Числа-ДАНІ умови: рядок підказки, розмітку пунктів і посилання на
    пункти підручника («п.15–16») даними не вважаємо."""
    lines = []
    for line in statement.split("\n"):
        if line.startswith("("):
            continue
        line = re.sub(r"п\.\s*\d+(–\d+)?", "", line)
        line = re.sub(r"\d\)", "", line)
        lines.append(line)
    return [int(t) for t in re.findall(r"-?\d+", "\n".join(lines))]


def test_copying_a_printed_number_is_weak():
    for pick in (0, -1):
        total = runs = 0
        for key in BANK:
            for i in range(15):
                q = _build(key, i)
                nums = _printed(q.statement)
                guess = str(nums[pick]) if nums else "1"
                total += engine.grade(
                    q, {p.key: guess for p in q.parts})["score"] / q.max_score
                runs += 1
        assert total / 15 < 0.7, (pick, round(total / 15, 2))


@pytest.mark.parametrize("key", BANK)
def test_answers_are_enterable(key):
    for i in range(10):
        for part in _build(key, i).parts:
            engine.parse_answer(str(part.answer), part.kind)
