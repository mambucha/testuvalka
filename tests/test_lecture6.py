"""Лекція 6 (вища математика): похідна – таблиця і техніки диференціювання.

Домовленості з викладачем закріплені тестами, щоб їх не втратити:
  * ЗАСТОСУВАНЬ похідної (дотична, швидкість, монотонність, екстремуми) немає –
    їх ще не вивчали;
  * значення похідної В ТОЧЦІ не шукаємо – увесь тест про техніку;
  * тангенс позначається tg, а не tan.

Кожну похідну перераховуємо НЕЗАЛЕЖНО: функцію відтворюємо з `q.params` і
диференціюємо `sp.diff`. Інакше помилка в шаблоні «підтвердила б сама себе».
"""

import pathlib
import re

import sympy as sp
import yaml

import engine
from app.config import SECRET

# Літеральний "\n" замість переносу; \ne, \nu – валідні команди LaTeX.
_BAD_NEWLINE = re.compile(r"\\n(?![a-zA-Z])")

TABLE = ["dv_power_root", "dv_trig_table", "dv_exp_log"]
RULES = ["dv_product", "dv_quotient", "dv_chain_power", "dv_product_chain",
         "dv_chain_exp", "dv_chain_sqrt", "dv_chain_ln"]
SECOND = ["dv_second_poly", "dv_second_trig"]
KEYS = TABLE + RULES + SECOND
_x = sp.Symbol("x")


def _build(key, i):
    return engine.build(key, SECRET, f"учень|{i}", "lecture6", 1, 0)


def _a(q):
    return {p.key: p.answer for p in q.parts}


def _same(got, expected):
    return sp.simplify(got - expected) == 0


# --- склад тесту --------------------------------------------------------

def test_has_12_types_over_all_three_topics():
    assert len(KEYS) == len(set(KEYS)) == 12
    assert len(TABLE) == 3, "таблиця похідних"
    assert len(RULES) == 7, "правила диференціювання"
    assert len(SECOND) == 2, "друга похідна"


def test_yaml_bank_matches_this_module():
    """Банк у tests.yaml і перелік тут не мають розійтися."""
    data = yaml.safe_load(pathlib.Path("tests.yaml").read_text(encoding="utf-8"))
    entry = next(t for t in data if t["key"] == "lecture6")
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
    """Однакове «сміття» в усіх полях не має проходити через carry."""
    for key in KEYS:
        for i in range(5):
            q = _build(key, i)
            r = engine.grade(q, {p.key: "123456" for p in q.parts})
            assert r["score"] == 0.0, (key, i, r)


def test_statements_katex_no_literal_newline():
    for key in KEYS:
        q = _build(key, 1)
        assert "$" in q.statement, key
        assert not _BAD_NEWLINE.search(q.statement), key


def test_every_task_is_multistep():
    for key in KEYS:
        assert len(_build(key, 1).parts) >= 2, key


def test_no_figures():
    """Рисунки тут ні до чого – усе про техніку диференціювання."""
    for key in KEYS:
        assert _build(key, 3).svg is None, key


def test_timings_calibrated():
    total = 0
    for key in KEYS:
        q = _build(key, 1)
        assert 100 <= q.seconds <= 170, (key, q.seconds)
        total += q.seconds
    assert 1200 <= total <= 1700, total          # ≈20–28 хв на 12 питань


# --- домовленості про обсяг --------------------------------------------

def test_no_derivative_at_a_point():
    """«Давай значення похідної в точці не шукати» – усі поля мають бути виразами."""
    for key in KEYS:
        for i in range(6):
            q = _build(key, i)
            s = q.statement.lower()
            for bad in ("точці", "точка", "обчисліть значення", "у точц"):
                assert bad not in s, (key, bad)
            for part in q.parts:
                assert part.kind == "expr", (key, part.key)


def test_final_answer_is_always_an_expression():
    """Відповідь – вираз зі змінною, а не число: одним числом не поділишся."""
    for key in KEYS:
        for i in range(6):
            last = _build(key, i).parts[-1].answer
            assert last.has(_x), (key, i, last)
            assert not last.is_number, (key, i, last)


def test_no_applications_of_derivative():
    """Застосування похідної ще не вивчали – у тесті їх бути не має."""
    banned = ("дотичн", "швидкіст", "швидкост", "монотон", "екстремум",
              "зроста", "спада", "опукл", "асимптот", "кут нахилу",
              "найбільше значення", "найменше значення")
    for key in KEYS:
        for i in range(6):
            s = _build(key, i).statement.lower()
            for bad in banned:
                assert bad not in s, (key, bad)


def test_ukrainian_tg_notation():
    """В українській школі тангенс – tg, котангенс – ctg."""
    for key in KEYS:
        for i in range(6):
            s = _build(key, i).statement
            assert r"\tan" not in s, (key, "має бути \\operatorname{tg}")
            assert r"\cot" not in s, (key, "має бути \\operatorname{ctg}")
    assert r"\operatorname{tg}" in _build("dv_trig_table", 0).statement


def test_no_stray_unit_coefficient():
    """«1 tg x» у перших двох доданках теж: коефіцієнт 1 не пишемо."""
    for i in range(30):
        s = _build("dv_trig_table", i).statement
        assert r"1\operatorname{tg}" not in s, i
        assert r"1\sin" not in s and r"1\cos" not in s, i


# --- таблиця похідних ---------------------------------------------------

def test_power_root_math():
    for i in range(20):
        q = _build("dv_power_root", i)
        p, a = q.params, _a(q)
        head = p["a"] * _x ** p["n"]
        f = head + p["b"] * sp.sqrt(_x) + sp.Integer(p["c"]) / _x
        assert _same(a["d1"], sp.diff(head, _x)), (i, a["d1"])
        assert _same(a["dy"], sp.diff(f, _x)), (i, a["dy"])
        # похідна кореня дає x^(-1/2) – саме той крок таблиці, що найчастіше гублять
        assert a["dy"].has(_x ** sp.Rational(-1, 2)), (i, a["dy"])
        assert a["dy"].has(_x ** -2), (i, a["dy"])


def test_trig_table_math():
    for i in range(20):
        q = _build("dv_trig_table", i)
        p, a = q.params, _a(q)
        head = p["a"] * sp.sin(_x) + p["b"] * sp.cos(_x)
        f = head + p["c"] * sp.tan(_x)
        assert _same(a["d1"], sp.diff(head, _x)), (i, a["d1"])
        assert _same(a["dy"], sp.diff(f, _x)), (i, a["dy"])


def test_exp_log_math():
    for i in range(20):
        q = _build("dv_exp_log", i)
        p, a = q.params, _a(q)
        power = sp.Integer(p["base"]) ** _x
        f = p["a"] * sp.exp(_x) + p["b"] * sp.log(_x) + power
        assert _same(a["d1"], sp.diff(power, _x)), (i, a["d1"])
        assert _same(a["dy"], sp.diff(f, _x)), (i, a["dy"])
        assert a["d1"].has(sp.log), ("(aˣ)' = aˣ·ln a", i)


# --- правила диференціювання -------------------------------------------

def test_product_rule_math():
    for i in range(25):
        q = _build("dv_product", i)
        p, a = q.params, _a(q)
        u, v = sp.sympify(p["u"]), sp.sympify(p["v"])
        assert _same(a["du"], sp.diff(u, _x)), i
        assert _same(a["dv"], sp.diff(v, _x)), i
        assert _same(a["dy"], sp.diff(u * v, _x)), i
        assert _same(a["dy"], a["du"] * v + u * a["dv"]), ("(uv)' = u'v + uv'", i)


def test_quotient_rule_math():
    for i in range(25):
        q = _build("dv_quotient", i)
        p, a = q.params, _a(q)
        u, v = _x**2 + p["a"], _x + p["b"]
        assert _same(a["num"], sp.diff(u, _x) * v - u * sp.diff(v, _x)), i
        assert sp.expand(a["num"]) == a["num"], ("чисельник просили розкрити", i)
        assert _same(a["dy"], sp.diff(u / v, _x)), i
        assert _same(a["dy"], a["num"] / v**2), i


def test_chain_power_math():
    for i in range(25):
        q = _build("dv_chain_power", i)
        p, a = q.params, _a(q)
        inner, n = p["a"] * _x**2 + p["b"], p["n"]
        assert _same(a["du"], sp.diff(inner, _x)), i
        assert _same(a["dy"], sp.diff(inner**n, _x)), i
        assert _same(a["dy"], n * inner ** (n - 1) * a["du"]), i


def test_product_chain_math():
    for i in range(25):
        q = _build("dv_product_chain", i)
        p, a = q.params, _a(q)
        v = sp.sin(p["k"] * _x) if p["use_sin"] else sp.cos(p["k"] * _x)
        assert _same(a["dv"], sp.diff(v, _x)), i
        assert _same(a["dy"], sp.diff(_x * v, _x)), i
        # множник k від внутрішньої функції не має загубитися
        assert a["dv"].has(sp.Integer(p["k"])), i


def test_chain_exp_math():
    for i in range(25):
        q = _build("dv_chain_exp", i)
        p, a = q.params, _a(q)
        inner = p["a"] * _x**2 + p["b"]
        assert _same(a["du"], sp.diff(inner, _x)), i
        assert _same(a["dy"], sp.diff(sp.exp(inner), _x)), i


def test_chain_sqrt_math():
    for i in range(25):
        q = _build("dv_chain_sqrt", i)
        p, a = q.params, _a(q)
        inner = p["a"] * _x + p["b"]
        assert _same(a["du"], sp.diff(inner, _x)), i
        assert _same(a["dy"], sp.diff(sp.sqrt(inner), _x)), i


def test_chain_ln_math():
    degrees = set()
    for i in range(25):
        q = _build("dv_chain_ln", i)
        p, a = q.params, _a(q)
        degrees.add(p["n"])
        inner = p["a"] * _x ** p["n"] + p["b"]
        assert _same(a["du"], sp.diff(inner, _x)), i
        assert _same(a["dy"], sp.diff(sp.log(inner), _x)), i
    assert degrees == {1, 2}, ("внутрішня функція має бути і лінійна, і квадратна",
                               degrees)


# --- друга похідна ------------------------------------------------------

def test_second_poly_math():
    for i in range(25):
        q = _build("dv_second_poly", i)
        p, a = q.params, _a(q)
        f = p["a"] * _x**4 + p["b"] * _x**3 + p["c"] * _x**2
        assert _same(a["d1"], sp.diff(f, _x)), i
        assert _same(a["d2"], sp.diff(f, _x, 2)), i
        assert _same(a["d2"], sp.diff(a["d1"], _x)), i
        assert sp.degree(a["d2"], _x) == 2, i
        assert sp.expand(a["d2"]) == a["d2"], ("еталон має бути розкритий", i)


def test_second_trig_math():
    for i in range(25):
        q = _build("dv_second_trig", i)
        p, a = q.params, _a(q)
        f = p["a"] * (sp.sin(p["k"] * _x) if p["use_sin"] else sp.cos(p["k"] * _x))
        assert _same(a["d1"], sp.diff(f, _x)), i
        assert _same(a["d2"], sp.diff(f, _x, 2)), i
        assert _same(a["d2"], -p["k"] ** 2 * f), ("y'' = -k²y", i)


# --- стійкість до списування -------------------------------------------

def test_variants_differ_between_students():
    """У кожного свої коефіцієнти – готова відповідь сусіда не підходить."""
    for key in KEYS:
        finals = {str(_build(key, i).parts[-1].answer) for i in range(40)}
        assert len(finals) >= 5, (key, len(finals))


def test_equivalent_student_forms_accepted():
    """Порівняння символьне: форма запису відповіді не має значення."""
    q = _build("dv_trig_table", 0)
    p = q.params
    # (tg x)' записують і як 1/cos²x, і як 1 + tg²x – приймаємо обидві
    r = engine.grade(q, {
        "d1": f"{p['a']}*cos(x) - {p['b']}*sin(x)",
        "dy": f"{p['a']}*cos(x) - {p['b']}*sin(x) + {p['c']}*(1 + tg(x)^2)",
    })
    assert r["score"] == r["max"], r

    q = _build("dv_product", 0)
    a = _a(q)
    # e^x і exp(x) – те саме; розкритий добуток теж приймається
    sub = {k: str(v).replace("exp(x)", "e^x") for k, v in a.items()}
    sub["dy"] = str(sp.expand(a["dy"])).replace("exp(x)", "e^x")
    assert engine.grade(q, sub)["score"] == q.max_score, sub


# --- перенесення помилки (carry) ---------------------------------------

def test_carry_product_rule_keeps_two_of_three():
    for i in range(10):
        q = _build("dv_product", i)
        p, a = q.params, _a(q)
        u, v = sp.sympify(p["u"]), sp.sympify(p["v"])
        wrong_du = a["du"] + 1
        r = engine.grade(q, {
            "du": str(wrong_du),
            "dv": str(a["dv"]),
            "dy": str(sp.expand(wrong_du * v + u * a["dv"])),
        })
        assert r["score"] == 2.0 and r["max"] == 3, (i, r)


def test_carry_second_derivative_follows_first():
    """Помилилися в y' – але y'' від СВОГО y' знайдено правильно."""
    for i in range(10):
        q = _build("dv_second_poly", i)
        a = _a(q)
        wrong_d1 = a["d1"] + _x**2
        r = engine.grade(q, {"d1": str(wrong_d1),
                             "d2": str(sp.diff(wrong_d1, _x))})
        assert r["score"] == 1.0 and r["max"] == 2, (i, r)


def test_carry_chain_rule_keeps_second_step():
    for i in range(10):
        q = _build("dv_chain_power", i)
        p, a = q.params, _a(q)
        inner, n = p["a"] * _x**2 + p["b"], p["n"]
        wrong_du = a["du"] + 1
        r = engine.grade(q, {"du": str(wrong_du),
                             "dy": str(n * inner ** (n - 1) * wrong_du)})
        assert r["score"] == 1.0 and r["max"] == 2, (i, r)
