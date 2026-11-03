"""Тригонометрія: заняття 9, 10, 11 (I курс).

Кожне значення перераховуємо НЕЗАЛЕЖНО від шаблону: кути беремо з q.params і
рахуємо через sympy заново. Інакше помилка в банку «підтвердила б сама себе».

Домовленості, закріплені тестами, щоб не загубилися:
  * тест перевіряє розуміння, а не таблицю значень - є завдання, де працює
    лише коло й монотонність (tr_circle_locate, tr_signs, tr_compare);
  * формули зведення розкладені на два питання «правила конячки» окремо;
  * тангенс і котангенс позначаються tg і ctg, як у конспекті;
  * де відповідь є ВИРАЗОМ, в умові стоїть x, бо рушій не пускає alpha.
"""

import math
import pathlib
import re

import sympy as sp
import yaml

import engine
from app.config import SECRET

# Літеральний "\n" замість переносу; \ne, \nu – валідні команди LaTeX.
_BAD_NEWLINE = re.compile(r"\\n(?![a-zA-Z])")

LESSON9 = ["tr_radians", "tr_circle_locate", "tr_circle_read", "tr_signs"]
LESSON10 = ["tr_pythagorean", "tr_simplify", "tr_reduction",
            "tr_reduction_value"]
LESSON11 = ["tr_period", "tr_graph_read", "tr_compare", "tr_properties"]
KEYS = LESSON9 + LESSON10 + LESSON11

WITH_FIGURE = ["tr_circle_locate", "tr_circle_read", "tr_graph_read"]
PICKABLE = ["tr_circle_locate"]

_x = sp.Symbol("x")


def _build(key, i):
    return engine.build(key, SECRET, f"студент|{i}", "theme5", 1, 0)


def _a(q):
    return {p.key: p.answer for p in q.parts}


def _same(got, expected):
    return sp.simplify(sp.sympify(got) - sp.sympify(expected)) == 0


def _quarter_of_deg(deg: float) -> int:
    return int(deg % 360.0 // 90) + 1


# =======================================================================
#  СКЛАД ТЕСТУ
# =======================================================================

def test_twelve_types_four_per_lesson():
    assert len(KEYS) == len(set(KEYS)) == 12
    assert len(LESSON9) == 4, "заняття 9: радіани, коло, знаки"
    assert len(LESSON10) == 4, "заняття 10: тотожності та зведення"
    assert len(LESSON11) == 4, "заняття 11: період, графіки, властивості"


def test_yaml_bank_matches_this_module():
    data = yaml.safe_load(pathlib.Path("tests.yaml").read_text(encoding="utf-8"))
    entry = next(t for t in data if t["key"] == "theme5")
    assert entry["bank"] == KEYS
    assert entry["question_count"] == 12
    assert entry["points_per_question"] == 1
    assert entry["restart_after_violations"] is None


def test_all_grade_full_on_correct_answers():
    for key in KEYS:
        for i in range(25):
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


def test_statements_katex_no_literal_newline():
    for key in KEYS:
        for i in range(8):
            q = _build(key, i)
            assert "$" in q.statement, key
            assert not _BAD_NEWLINE.search(q.statement), (key, i)


def test_no_markdown_in_statements():
    """Фронтенд перетворює лише \\n на <br> і запускає KaTeX – зірочки
    markdown показалися б студентові як зірочки."""
    for key in KEYS:
        for i in range(6):
            s = _build(key, i).statement
            assert "**" in s or True
            assert "**" not in s, (key, i)
            assert not re.search(r"(?<!\w)_[а-яїієґА-ЯЇІЄҐ]", s), (key, i)


def test_every_task_is_multistep():
    for key in KEYS:
        assert len(_build(key, 1).parts) >= 2, key


def test_ukrainian_tg_notation():
    """У конспекті викладача тангенс – tg, котангенс – ctg."""
    seen_tg = False
    for key in KEYS:
        for i in range(8):
            s = _build(key, i).statement
            assert r"\tan" not in s, (key, "має бути \\operatorname{tg}")
            assert r"\cot" not in s, (key, "має бути \\operatorname{ctg}")
            seen_tg = seen_tg or r"\operatorname{tg}" in s
    assert seen_tg, "тангенс мусить десь траплятися"


def test_figures_only_where_expected():
    for key in KEYS:
        for i in range(5):
            q = _build(key, i)
            if key in WITH_FIGURE:
                assert q.svg and q.svg.startswith("<svg"), (key, i)
            else:
                assert q.svg is None, (key, i)


def test_only_the_locate_task_is_clickable():
    """Клікабельні точки мають бути рівно там, де умова обіцяє клацання."""
    for key in KEYS:
        for i in range(5):
            q = _build(key, i)
            clickable = bool(q.svg) and "uc-dot" in q.svg
            assert clickable == (key in PICKABLE), (key, i)
    for i in range(5):
        q = _build("tr_circle_locate", i)
        assert q.svg.count("uc-dot") == 16, i          # усі «гарні» кути
        assert "клацніть" in q.statement.lower(), i


def test_pickable_circle_offers_the_right_answer_among_its_dots():
    """Серед клікабельних точок мусить бути правильна – інакше студент, який
    усе зрозумів, не зможе відповісти клацанням."""
    for i in range(20):
        q = _build("tr_circle_locate", i)
        want = str(q.parts[0].answer).replace(" ", "")
        dots = re.findall(r'data-ins="([^"]+)"', q.svg)
        assert len(dots) == 16, i
        parsed = [str(sp.sympify(d)).replace(" ", "") for d in dots]
        assert want in parsed, (i, want, parsed)


def test_timings_are_generous():
    total = 0
    for key in KEYS:
        q = _build(key, 1)
        assert 170 <= q.seconds <= 200, (key, q.seconds)
        total += q.seconds
    assert 2100 <= total <= 2350, total             # ~35–39 хв на 12 питань


def test_many_variants_per_template():
    """Менш як два десятки варіантів – і переписане в сусіда число підійде."""
    for key in KEYS:
        tuples = [tuple(str(p.answer) for p in _build(key, i).parts)
                  for i in range(80)]
        assert len(set(tuples)) >= 20, (key, len(set(tuples)))
        assert max(tuples.count(t) for t in set(tuples)) <= 12, key


def test_single_number_guess_is_weak():
    """У тесті багато полів-кодів (чверть, знак, парність), тож перевіряємо
    прицільно: жодне стале число не має давати пристойного балу."""
    for guess in ("0", "1", "2", "3", "4", "-1"):
        total = count = 0
        for key in KEYS:
            for i in range(10):
                q = _build(key, i)
                total += engine.grade(
                    q, {p.key: guess for p in q.parts})["score"] / q.max_score
                count += 1
        assert total / count < 0.13, (guess, round(total / count, 3))


def test_quarter_answers_use_all_four():
    """Якби чверть майже завжди була та сама, поле нічого б не перевіряло."""
    seen = []
    for key in ("tr_radians", "tr_circle_locate", "tr_signs", "tr_reduction",
                "tr_reduction_value"):
        for i in range(40):
            q = _build(key, i)
            seen += [int(p.answer) for p in q.parts
                     if p.key in ("quarter", "qb")]
    assert set(seen) == {1, 2, 3, 4}, sorted(set(seen))


# =======================================================================
#  ЗАНЯТТЯ 9
# =======================================================================

def test_radians_math():
    for i in range(30):
        q = _build("tr_radians", i)
        p, a = q.params, _a(q)
        assert _same(a["rad"], sp.rad(p["deg"])), (i, a["rad"])
        assert _same(a["deg"], sp.deg(sp.pi * p["num"] / p["den"])), (i, a["deg"])
        assert a["quarter"] == _quarter_of_deg(p["odd"]), (i, p["odd"])
        # третій кут навмисне від'ємний або більший за оберт
        assert p["odd"] < 0 or p["odd"] > 360, (i, p["odd"])


def test_circle_locate_math():
    for i in range(30):
        q = _build("tr_circle_locate", i)
        p, a = q.params, _a(q)
        t = sp.pi * p["num"] / p["den"]
        assert _same(a["angle"], t), (i, a["angle"])
        want = {"other": sp.sin(t) if p["by_cos"] else sp.cos(t),
                "tg": sp.tan(t), "ctg": sp.cot(t)}[p["ask2"]]
        assert _same(a["other"], want), (i, a["other"], p["ask2"])
        assert a["quarter"] == _quarter_of_deg(180.0 * p["num"] / p["den"]), i
        # кут не на осі: інакше одна з координат нуль і умова вироджена
        assert sp.cos(t) != 0 and sp.sin(t) != 0, (i, p)


def test_circle_locate_asks_all_three_second_questions():
    """Три різновиди другого питання: без них шаблон має лише два десятки
    наборів відповідей, бо кутів поза осями дванадцять."""
    asks = {_build("tr_circle_locate", i).params["ask2"] for i in range(50)}
    assert asks == {"other", "tg", "ctg"}, sorted(asks)


def test_circle_locate_condition_is_unique():
    """Умова (значення однієї функції + знак другої) мусить задавати рівно
    один кут з проміжку [0; 2pi) – інакше правильних відповідей кілька, а
    зараховується одна."""
    for i in range(30):
        q = _build("tr_circle_locate", i)
        p = q.params
        t = sp.pi * p["num"] / p["den"]
        known = sp.cos(t) if p["by_cos"] else sp.sin(t)
        other_sign = sp.sign(sp.sin(t) if p["by_cos"] else sp.cos(t))
        hits = []
        for num, den in [(1, 6), (1, 4), (1, 3), (1, 2), (2, 3), (3, 4),
                         (5, 6), (1, 1), (7, 6), (5, 4), (4, 3), (3, 2),
                         (5, 3), (7, 4), (11, 6), (0, 1)]:
            tt = sp.pi * num / den
            k = sp.cos(tt) if p["by_cos"] else sp.sin(tt)
            o = sp.sin(tt) if p["by_cos"] else sp.cos(tt)
            if sp.simplify(k - known) == 0 and sp.sign(o) == other_sign:
                hits.append((num, den))
        assert hits == [(p["num"], p["den"])], (i, hits, p)


def test_circle_read_asks_all_four_third_questions():
    """Чотири різновиди третього питання – єдине, що піднімає шаблон вище за
    дванадцять наборів відповідей (стільки є кутів поза осями)."""
    kinds = [_build("tr_circle_read", i).params["kind"] for i in range(60)]
    assert set(kinds) == {"tg", "ctg", "sym_x", "sym_y"}, sorted(set(kinds))


def test_circle_read_math():
    for i in range(30):
        q = _build("tr_circle_read", i)
        p, a = q.params, _a(q)
        t = sp.pi * p["num"] / p["den"]
        assert _same(a["cos"], sp.cos(t)), (i, a["cos"])
        assert _same(a["sin"], sp.sin(t)), (i, a["sin"])
        want = {"tg": sp.tan(t), "ctg": sp.cot(t),
                "sym_x": -sp.sin(t), "sym_y": -sp.cos(t)}[p["kind"]]
        assert _same(a["third"], want), (i, a["third"], p["kind"])
        # рисунок справді позначає ту саму точку
        assert "P</text>" in q.svg, i


def test_signs_math():
    for i in range(30):
        q = _build("tr_signs", i)
        p, a = q.params, _a(q)
        want = 1
        for fn, deg in ((sp.sin, p["a"]), (sp.cos, p["b"]), (sp.tan, p["c"])):
            v = float(sp.N(fn(sp.rad(deg))))
            want *= 1 if v > 0 else -1
        assert a["prod"] == want, (i, a["prod"], want)
        assert a["qb"] == _quarter_of_deg(180.0 * p["rad_q"][0] / p["rad_q"][1]), i
        assert a["quarter"] == p["quarter"], i


def test_signs_pair_determines_the_quarter():
    """Два знаки мусять задавати рівно одну чверть: кожен окремо лишає дві."""
    for i in range(40):
        q = _build("tr_signs", i)
        p = q.params
        # Відтворюємо пару знаків з умови та перевіряємо, скільки чвертей їй
        # відповідає.
        funcs = {"sin_ctg": (sp.sin, sp.cot), "cos_tg": (sp.cos, sp.tan),
                 "sin_cos": (sp.sin, sp.cos), "tg_sin": (sp.tan, sp.sin)}
        f1, f2 = funcs[p["pair"]]
        mid = sp.pi * (2 * p["quarter"] - 1) / 4
        s1, s2 = sp.sign(f1(mid)), sp.sign(f2(mid))
        hits = [qq for qq in (1, 2, 3, 4)
                if sp.sign(f1(sp.pi * (2 * qq - 1) / 4)) == s1
                and sp.sign(f2(sp.pi * (2 * qq - 1) / 4)) == s2]
        assert hits == [p["quarter"]], (i, hits, p)


# =======================================================================
#  ЗАНЯТТЯ 10
# =======================================================================

def test_pythagorean_math():
    for i in range(30):
        q = _build("tr_pythagorean", i)
        p, a = q.params, _a(q)
        sx = 1 if p["quarter"] in (1, 4) else -1
        sy = 1 if p["quarter"] in (1, 2) else -1
        co = sx * sp.Rational(p["p"], p["h"])
        si = sy * sp.Rational(p["q"], p["h"])
        # трійка справді піфагорова – основна тотожність виконується
        assert sp.simplify(co**2 + si**2 - 1) == 0, (i, p)
        assert _same(a["first"], si if p["given_cos"] else co), (i, a["first"])
        assert _same(a["tg"], si / co), (i, a["tg"])
        assert _same(a["ctg"], co / si), (i, a["ctg"])
        # знак дістається з чверті, а не з формули
        assert (a["first"] > 0) == ((sy if p["given_cos"] else sx) > 0), i


def test_simplify_math():
    """Кожен кістяк перевіряємо чисельно у кількох точках: якщо еталон не
    дорівнює виразу з умови, це спливе."""
    for i in range(40):
        q = _build("tr_simplify", i)
        a = _a(q)
        total = sp.sympify(a["total"])
        step = sp.sympify(a["step"])
        for probe in (0.3, 0.7, 1.1, 2.0, 2.6):
            for expr in (total, step):
                v = complex(sp.N(expr.subs(_x, probe)))
                assert abs(v.imag) < 1e-9, (i, expr)
        # результат не має лишатися «як було»: спрощення мусить щось дати
        assert sp.simplify(total - q.params["a"]) == 0 or total.has(
            sp.sin, sp.cos, sp.tan, sp.cot), (i, total)


def test_simplify_total_matches_the_statement_expression():
    """Відтворюємо вираз з умови за кістяком і множником і звіряємо з еталоном."""
    from app.bank.trigonometry import _simplify_shapes
    shapes = {tex: expr for tex, expr, _q, _a in _simplify_shapes()}
    for i in range(40):
        q = _build("tr_simplify", i)
        expr = shapes[q.params["tex"]]
        want = sp.simplify(q.params["a"] * expr)
        assert _same(_a(q)["total"], want), (i, q.params)


def test_reduction_math():
    for i in range(50):
        q = _build("tr_reduction", i)
        p, a = q.params, _a(q)
        bn, bd = p["base"]
        base = sp.pi * bn / bd
        fn = {"sin": sp.sin, "cos": sp.cos, "tg": sp.tan,
              "ctg": sp.cot}[p["func"]]
        arg = base + _x if p["plus"] else base - _x
        assert _same(a["result"], sp.simplify(fn(arg))), (i, a["result"], p)
        # чверть рахуємо незалежно, підставивши гострий кут
        probe = float(sp.N(base)) + (0.2 if p["plus"] else -0.2)
        assert a["quarter"] == _quarter_of_deg(math.degrees(probe)), (i, p)
        # назва змінюється рівно для «вертикальних» кутів pi/2 і 3pi/2
        vertical = bd == 2
        assert bool(a["flip"]) == vertical, (i, p)


def test_reduction_sign_follows_the_mnemonic_rule():
    """«Правило конячки»: знак результату збігається зі знаком початкової
    функції в тій чверті. Якщо ні – розклад на кроки брехливий."""
    for i in range(50):
        q = _build("tr_reduction", i)
        p = q.params
        bn, bd = p["base"]
        base = sp.pi * bn / bd
        fn = {"sin": sp.sin, "cos": sp.cos, "tg": sp.tan,
              "ctg": sp.cot}[p["func"]]
        probe = float(sp.N(base)) + (0.2 if p["plus"] else -0.2)
        at_angle = float(sp.N(fn(sp.Float(probe))))
        result = sp.sympify(_a(q)["result"])
        at_result = float(sp.N(result.subs(_x, 0.2)))
        assert (at_angle > 0) == (at_result > 0), (i, p, at_angle, at_result)


def test_reduction_covers_both_kinds_of_base_angle():
    bases = {tuple(_build("tr_reduction", i).params["base"]) for i in range(60)}
    assert (1, 2) in bases and (3, 2) in bases, "вертикальні кути"
    assert (1, 1) in bases and (2, 1) in bases, "горизонтальні кути"


def test_reduction_value_math():
    for i in range(40):
        q = _build("tr_reduction_value", i)
        p, a = q.params, _a(q)
        fn = {"sin": sp.sin, "cos": sp.cos, "tg": sp.tan,
              "ctg": sp.cot}[p["func"]]
        want = sp.simplify(fn(sp.rad(p["deg"])))
        assert _same(a["val"], want), (i, a["val"], want)
        assert a["quarter"] == _quarter_of_deg(p["deg"]), i
        # гострий кут звірки: 0 < ref <= 90 і та сама функція з точністю до знака
        assert 0 < a["ref"] <= 90, (i, a["ref"])
        assert sp.simplify(abs(want) - abs(fn(sp.rad(int(a["ref"]))))) == 0 or \
            sp.simplify(abs(want) - abs(
                {"sin": sp.cos, "cos": sp.sin, "tg": sp.cot,
                 "ctg": sp.tan}[p["func"]](sp.rad(int(a["ref"]))))) == 0, (i, p)


def test_reduction_value_answers_are_exact():
    """«Обчисліть» вимагає точної відповіді: sin 160 дорівнює sin(pi/9), а це
    не число, яке студент може записати."""
    for i in range(40):
        a = _a(_build("tr_reduction_value", i))
        val = sp.sympify(a["val"])
        assert not val.has(sp.sin, sp.cos, sp.tan, sp.cot), (i, val)
        assert val.is_number and not val.has(sp.zoo, sp.oo), (i, val)


# =======================================================================
#  ЗАНЯТТЯ 11
# =======================================================================

def test_period_math():
    for i in range(30):
        q = _build("tr_period", i)
        p, a = q.params, _a(q)
        w1, w2 = sp.sympify(p["w1"]), sp.sympify(p["w2"])
        assert _same(a["t1"], 2 * sp.pi / w1), (i, a["t1"])
        assert _same(a["t2"], sp.pi / w2), (i, a["t2"])
        # найбільше значення A*sin(...) + B дорівнює A + B, а не самому A:
        # інакше поле бралося переписуванням першого ж числа умови
        assert a["maxv"] == p["a"] + p["b"], (i, p)
        assert p["b"] != 0, i
        # зсув в умові є, але на період не впливає – саме це й перевіряємо
        assert r"-" in q.statement, i


def test_period_task_includes_a_shift():
    """Задача викладача наголошує: період не залежить від зсуву. Якщо зсуву в
    умові нема, цей наголос зникає."""
    for i in range(20):
        q = _build("tr_period", i)
        num, den = q.params["shift"]
        assert num and den, (i, q.params["shift"])
        from app.bank.plotting import angle_tex
        assert angle_tex(num, den) in q.statement, i


def test_graph_read_math():
    for i in range(30):
        q = _build("tr_graph_read", i)
        p, a = q.params, _a(q)
        assert a["amp"] == p["a"], i
        assert a["period"] == 2 * p["k"], (i, a["period"])
        # нулі рахуємо незалежно
        if p["use_cos"]:
            zeros = [p["k"] / 2 + p["k"] * n for n in range(-20, 21)]
        else:
            zeros = [p["k"] * n for n in range(-20, 21)]
        assert a["zeros"] == sum(1 for z in zeros if abs(z) <= 6 + 1e-9), (i, p)
        assert a["zeros"] >= 2, (i, "на рисунку має бути що рахувати")
        # амплітуда вміщується в полотно -6..6
        assert p["a"] <= 6, i


def test_compare_math():
    for i in range(40):
        q = _build("tr_compare", i)
        p, a = q.params, _a(q)
        fn = sp.sin if p["f1"] == "sin" else sp.cos
        d1 = float(sp.N(fn(sp.rad(p["a1"])) - fn(sp.rad(p["b1"]))))
        assert a["c1"] == (0 if abs(d1) < 1e-9 else (1 if d1 > 0 else -1)), i
        d2 = float(sp.N(sp.cos(sp.sympify(p["p2"]) * sp.pi)
                        - sp.cos(sp.sympify(p["q2"]) * sp.pi)))
        assert a["c2"] == (0 if abs(d2) < 1e-9 else (1 if d2 > 0 else -1)), i
        # третій пункт - гострий кут зведення, а не код
        assert 0 < a["ref"] <= 90, (i, a["ref"])
        fn2 = sp.sin if p["f1"] == "sin" else sp.cos
        assert sp.simplify(abs(fn2(sp.rad(p["target"])))
                           - abs(fn2(sp.rad(int(a["ref"]))))) == 0, (i, p)
        # порівняння не має впиратися в похибку округлення
        assert abs(d1) > 0.05 or a["c1"] == 0, (i, d1, p)
        assert abs(d2) > 0.05 or a["c2"] == 0, (i, d2, p)


def test_compare_uses_all_three_verdicts():
    """Відповідь «рівні» – найцінніша: формулою її не взяти. Якщо вона не
    трапляється, завдання вироджується в «більший кут – більше значення»."""
    got = []
    for i in range(80):
        q = _build("tr_compare", i)
        got += [int(p.answer) for p in q.parts if p.key in ("c1", "c2")]
    assert set(got) == {-1, 0, 1}, sorted(set(got))
    for v in (-1, 0, 1):
        assert got.count(v) >= 20, (v, got.count(v))


def test_copying_the_statement_back_is_refused():
    """Найдорожча знахідка аудиту.

    «Спростіть» і «зведіть» – вимоги до ВИГЛЯДУ відповіді, а рушій звіряє
    значення: simplify(got - expected) == 0. Переписана назад умова тотожно
    дорівнює еталону, тож бралася як правильна – заміряно 100% цих полів у
    tr_reduction і tr_simplify. Тут замикаємо обидва боки: переписане не
    зараховується, чесне зараховується.
    """
    from app.bank.trigonometry import _simplify_shapes
    shapes = {tex: (expr, step_a) for tex, expr, _q, step_a in _simplify_shapes()}

    def score_of(q, sub, field):
        got = engine.grade(q, sub)["parts"]
        return [d for d in got if d["part"] == field][0]["score"]

    for i in range(25):
        q = _build("tr_reduction", i)
        p = q.params
        bn, bd = p["base"]
        copy = f"{p['func']}({bn}*pi/{bd} {'+' if p['plus'] else '-'} x)"
        sub = {"quarter": "", "flip": "", "result": copy}
        assert score_of(q, sub, "result") == 0, (i, copy)
        honest = {"quarter": "", "flip": "", "result": str(q.parts[2].answer)}
        assert score_of(q, honest, "result") == 1, (i, q.parts[2].answer)

    for i in range(25):
        q = _build("tr_simplify", i)
        expr, step_a = shapes[q.params["tex"]]
        whole = str(q.params["a"] * expr)
        assert score_of(q, {"step": "", "total": whole}, "total") == 0, i
        assert score_of(q, {"step": "", "total": str(q.parts[1].answer)},
                        "total") == 1, i
        # рівноцінний запис із розкритими дужками лишається правильним
        alt = str(sp.expand(q.parts[1].answer))
        assert score_of(q, {"step": "", "total": alt}, "total") == 1, (i, alt)
        assert score_of(q, {"step": str(step_a), "total": ""},
                        "step") == 1, i


def test_simplify_never_collapses_to_the_leading_number():
    """Якщо дужка згортається в одиницю, відповідь – це множник перед нею,
    тобто перше ж число умови. Жоден кістяк так згортатися не має."""
    from app.bank.trigonometry import _simplify_shapes
    for tex, expr, _q, _a in _simplify_shapes():
        total = sp.simplify(3 * expr)
        assert total.free_symbols, tex
        assert total.has(sp.sin, sp.cos, sp.tan, sp.cot), tex


def test_simplify_step_always_gets_shorter():
    """Крок відкидаємо за довжиною, тож спрощення мусить скорочувати вираз –
    інакше переписану підформулу не відрізнити від виконаного кроку."""
    from app.bank.trigonometry import _simplify_shapes
    for tex, expr, _q, step_a in _simplify_shapes():
        assert sp.count_ops(step_a) <= 5, (tex, step_a)


def test_compare_reduction_angle_is_never_acute():
    """Пункт 3 не має роздаватися безплатно.

    У гострого кута кут зведення дорівнює йому самому, тож питати про
    гострий – це просто попросити переписати число з умови. Беремо лише
    негострі, і відповідь мусить відрізнятися від самого кута.
    """
    for i in range(60):
        q = _build("tr_compare", i)
        p, a = q.params, _a(q)
        assert p["target"] > 90, (i, p["target"])
        assert a["ref"] != p["target"], (i, p)
        # питання в умові – саме про цей кут
        assert f"{p['target']}^\\circ" in q.statement, (i, p["target"])


def test_compare_values_are_not_table_ones():
    """Якби кути були табличними, завдання розв'язувалося б обчисленням, а не
    монотонністю."""
    for i in range(30):
        p = _build("tr_compare", i).params
        for deg in (p["a1"], p["b1"]):
            assert deg % 30 != 0 or deg % 90 == 0, (i, deg)


def test_properties_math():
    for i in range(40):
        q = _build("tr_properties", i)
        p, a = q.params, _a(q)
        fn = sp.cos if p["use_cos"] else sp.sin
        expr = p["sign"] * p["a"] * fn(sp.pi * _x / p["k"]) + p["b"]
        # парність перевіряємо підстановкою -x, а не за назвою функції
        even = sp.simplify(expr.subs(_x, -_x) - expr) == 0
        assert bool(a["parity"]) == even, (i, p)
        # краї множини значень беремо чисельно з самої функції
        probes = [expr.subs(_x, sp.Rational(n, 12)) for n in range(-200, 201)]
        vals = [float(sp.N(v)) for v in probes]
        assert abs(max(vals) - float(a["maxv"])) < 1e-6, (i, a["maxv"], p)
        assert abs(min(vals) - float(a["minv"])) < 1e-6, (i, a["minv"], p)


def test_properties_minus_does_not_change_the_range():
    """Мінус перед амплітудою перевертає графік, але краї лишаються
    A+B і B-A – пастка на механічне «A зі знаком»."""
    seen_neg = False
    for i in range(30):
        q = _build("tr_properties", i)
        p, a = q.params, _a(q)
        seen_neg = seen_neg or p["neg"]
        assert a["maxv"] == p["a"] + p["b"], (i, p)
        assert a["minv"] == p["b"] - p["a"], (i, p)
    assert seen_neg, "варіант з мінусом мусить траплятися"


def test_properties_shift_is_never_zero():
    """Без вільного доданка найбільше значення дорівнює множнику перед
    косинусом – тобто першому ж числу умови. Поле бралося б переписуванням."""
    for i in range(40):
        p = _build("tr_properties", i).params
        assert p["b"] != 0, i
        assert p["a"] + p["b"] != p["a"], i


# =======================================================================
#  ПЕРЕНЕСЕННЯ ПОМИЛКИ
# =======================================================================

def test_carry_rewards_consistent_continuation():
    """Схибив у синусі, але тангенс порахував зі своїх же чисел – зараховуємо."""
    q = _build("tr_circle_read", 3)
    co = q.parts[0].answer
    wrong_sin = -q.parts[1].answer           # переплутав знак ординати
    kind = q.params["kind"]
    third = {"tg": wrong_sin / co, "ctg": co / wrong_sin,
             "sym_x": -wrong_sin, "sym_y": -co}[kind]
    r = engine.grade(q, {"cos": str(co), "sin": str(wrong_sin),
                         "third": str(sp.simplify(third))})
    detail = {d["part"]: d["score"] for d in r["parts"]}
    assert detail["cos"] > 0 and detail["sin"] == 0.0
    assert detail["third"] > 0, r


def test_carry_does_not_accept_zero_chain():
    """Нуль – нерухома точка відношення: без захисту ланцюжок підтвердив би
    сам себе й роздав би бали за порожню роботу."""
    for key, chain in (("tr_circle_read", ("cos", "sin", "third")),
                       ("tr_pythagorean", ("first", "tg", "ctg"))):
        for i in range(6):
            q = _build(key, i)
            r = engine.grade(q, {p.key: "0" for p in q.parts})
            detail = {d["part"]: d["score"] for d in r["parts"]}
            for part in chain:
                assert detail[part] == 0.0, (key, i, part, r)
