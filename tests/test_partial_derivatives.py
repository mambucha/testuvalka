"""Лекція 8 (вища математика): частинні похідні та екстремум функції двох змінних.

Кожну похідну перераховуємо НЕЗАЛЕЖНО: функцію відтворюємо з `q.params` і
диференціюємо `sp.diff`. Інакше помилка в шаблоні «підтвердила б сама себе».

Домовленість із викладачем, закріплена тестами, щоб не втратилася:
  * рівень «не жестити» – стаціонарні точки цілі, числа невеликі, «творчих»
    задач практичних (вписаний прямокутник, квадратична форма) немає;
  * але матеріал має бути видно: у кожному завданні 2-3 поля, і висновок про
    екстремум гуляє між мінімумом, максимумом і «екстремуму немає».
"""

import pathlib
import re

import sympy as sp
import yaml

import engine
from app.config import SECRET

# Літеральний "\n" замість переносу; \ne, \nu – валідні команди LaTeX.
_BAD_NEWLINE = re.compile(r"\\n(?![a-zA-Z])")

FIRST = ["pd_first_poly", "pd_first_log", "pd_first_exp"]
DIFFERENTIAL = ["pd_differential"]
SECOND = ["pd_second_poly", "pd_second_mixed", "pd_identity"]
DOMAIN = ["pd_domain"]
EXTREMUM = ["pd_extremum_full", "pd_extremum_test"]
LAGRANGE = ["pd_lagrange_linear", "pd_lagrange_circle"]
KEYS = FIRST + DIFFERENTIAL + SECOND + DOMAIN + EXTREMUM + LAGRANGE

_x, _y = sp.symbols("x y")


def _build(key, i):
    return engine.build(key, SECRET, f"студент|{i}", "lecture8", 1, 0)


def _a(q):
    return {p.key: p.answer for p in q.parts}


def _same(got, expected):
    return sp.simplify(sp.sympify(got) - sp.sympify(expected)) == 0


# =======================================================================
#  СКЛАД ТЕСТУ
# =======================================================================

def test_twelve_types_covering_the_whole_lecture():
    assert len(KEYS) == len(set(KEYS)) == 12
    assert len(FIRST) == 3, "частинні похідні першого порядку"
    assert len(DIFFERENTIAL) == 1, "повний диференціал"
    assert len(SECOND) == 3, "похідні другого порядку й тотожність"
    assert len(DOMAIN) == 1, "область визначення"
    assert len(EXTREMUM) == 2, "екстремум"
    assert len(LAGRANGE) == 2, "умовний екстремум"


def test_yaml_bank_matches_this_module():
    data = yaml.safe_load(pathlib.Path("tests.yaml").read_text(encoding="utf-8"))
    entry = next(t for t in data if t["key"] == "lecture8")
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
    """Однакове «сміття» в усіх полях не має проходити через carry."""
    for key in KEYS:
        for i in range(8):
            q = _build(key, i)
            r = engine.grade(q, {p.key: "123456" for p in q.parts})
            assert r["score"] == 0.0, (key, i, r)


def test_zero_in_every_field_is_worthless():
    """Нуль – нерухома точка і диференціювання, і підстановки, і суми.

    Якщо carry не відкидає нуль, ланцюжок підтверджує сам себе й тест
    роздає бали за порожню роботу (так уже було в lecture6 – 31.9%).
    """
    total = count = 0
    for key in KEYS:
        for i in range(12):
            q = _build(key, i)
            total += engine.grade(
                q, {p.key: "0" for p in q.parts})["score"] / q.max_score
            count += 1
    assert total / count < 0.08, round(total / count, 3)


def test_single_number_guess_is_weak():
    for guess in ("0", "1", "2", "-1"):
        total = count = 0
        for key in KEYS:
            for i in range(10):
                q = _build(key, i)
                total += engine.grade(
                    q, {p.key: guess for p in q.parts})["score"] / q.max_score
                count += 1
        assert total / count < 0.12, (guess, round(total / count, 3))


def test_statements_katex_no_literal_newline():
    for key in KEYS:
        for i in range(8):
            q = _build(key, i)
            assert "$" in q.statement, key
            assert not _BAD_NEWLINE.search(q.statement), (key, i)


def test_every_task_is_multistep():
    for key in KEYS:
        assert len(_build(key, 1).parts) >= 2, key


def test_no_figures():
    for key in KEYS:
        assert _build(key, 3).svg is None, key


def test_no_stray_unit_coefficient():
    """Коефіцієнт 1 не пишемо: «1x^{2}», «1y», «1\\ln y» читалося б як недогляд."""
    bad = re.compile(r"(?<![\d.])1(?=[xy\\])")
    for key in KEYS:
        for i in range(40):
            s = _build(key, i).statement
            for line in s.splitlines():
                assert not bad.search(line), (key, i, line)


def test_no_zero_terms_in_statements():
    for key in KEYS:
        for i in range(40):
            s = _build(key, i).statement
            assert " 0x" not in s and " 0y" not in s, (key, i)
            assert "{0}" not in s, (key, i)


def test_hint_matches_the_kind_of_fields():
    """Де всі поля числові, підказка не має обіцяти «вираз зі змінними x, y»:
    студент шукатиме в умові те, чого в ній немає."""
    for key in KEYS:
        q = _build(key, 1)
        has_expr = any(p.kind == "expr" for p in q.parts)
        promises_expr = "вираз зі змінними" in q.statement
        assert promises_expr == has_expr, (key, has_expr)
        assert "Відповід" in q.statement, key


def test_timings_are_generous():
    """«Дуже не жестити» – часу з запасом, але тест лишається в межах пари."""
    total = 0
    for key in KEYS:
        q = _build(key, 1)
        assert 140 <= q.seconds <= 190, (key, q.seconds)
        total += q.seconds
    assert 1900 <= total <= 2200, total           # ~32–36 хв на 12 питань
    # Лагранж – найдовше: там ще й систему складати
    for key in LAGRANGE:
        assert _build(key, 1).seconds >= 190, key


def test_many_variants_per_template():
    """Менш як два десятки варіантів – і переписане в сусіда число підійде."""
    for key in KEYS:
        tuples = [tuple(str(p.answer) for p in _build(key, i).parts)
                  for i in range(80)]
        assert len(set(tuples)) >= 20, (key, len(set(tuples)))
        assert max(tuples.count(t) for t in set(tuples)) <= 12, key


def test_answers_stay_in_allowed_symbols():
    """Рушій пускає лише x, y, t – усе інше студент не зможе ввести."""
    for key in KEYS:
        for i in range(15):
            for part in _build(key, i).parts:
                extra = sp.sympify(part.answer).free_symbols - {_x, _y}
                assert not extra, (key, part.key, extra)


# =======================================================================
#  НЕЗАЛЕЖНА ПЕРЕВІРКА МАТЕМАТИКИ
# =======================================================================

def test_first_poly_math():
    for i in range(25):
        q = _build("pd_first_poly", i)
        p, a = q.params, _a(q)
        z = (p["a"] * _x ** p["n"] * _y ** p["m"]
             + p["b"] * _x - p["c"] * _y)
        assert _same(a["zx"], sp.diff(z, _x)), (i, a["zx"])
        assert _same(a["zy"], sp.diff(z, _y)), (i, a["zy"])
        assert _same(a["val"],
                     sp.diff(z, _x).subs({_x: p["x0"], _y: p["y0"]})), i
        # по x змінна y лишається, по y – лишається x: суть «решта – сталі»
        assert a["zx"].has(_y), (i, a["zx"])
        assert a["zy"].has(_x), (i, a["zy"])


def test_first_log_math():
    for i in range(25):
        q = _build("pd_first_log", i)
        p, a = q.params, _a(q)
        z = sp.log(p["a"] * _x ** p["k"] + p["b"] * _y)
        assert _same(a["zx"], sp.diff(z, _x)), (i, a["zx"])
        assert _same(a["zy"], sp.diff(z, _y)), (i, a["zy"])
        # складена: у знаменнику має лишитися весь внутрішній вираз
        assert a["zx"].has(_x) and a["zx"].has(_y), (i, a["zx"])


def test_first_exp_math():
    for i in range(30):
        q = _build("pd_first_exp", i)
        p, a = q.params, _a(q)
        u, v = (_y, _x) if p["swap"] else (_x, _y)
        z = u ** p["a"] * sp.exp(p["b"] * v)
        assert _same(a["zx"], sp.diff(z, _x)), (i, a["zx"])
        assert _same(a["zy"], sp.diff(z, _y)), (i, a["zy"])
        assert _same(a["zxy"], sp.diff(z, _x, _y)), (i, a["zxy"])


def test_first_exp_swaps_variables():
    """Переставлені x та y мусять справді траплятися – інакше перевірка пуста."""
    seen = {_build("pd_first_exp", i).params["swap"] for i in range(30)}
    assert seen == {True, False}


def test_differential_math():
    for i in range(25):
        q = _build("pd_differential", i)
        p, a = q.params, _a(q)
        z = p["a"] * _x**2 * _y**3 + p["b"] * _x - p["c"] * _y
        at = {_x: p["x0"], _y: p["y0"]}
        assert _same(a["zx"], sp.diff(z, _x)), (i, a["zx"])
        assert _same(a["zy"], sp.diff(z, _y)), (i, a["zy"])
        assert _same(a["dz"],
                     sp.diff(z, _x).subs(at) * p["dx"]
                     + sp.diff(z, _y).subs(at) * p["dy"]), (i, a["dz"])
        assert p["dx"] != 0 and p["dy"] != 0, i


def test_second_poly_math():
    for i in range(25):
        q = _build("pd_second_poly", i)
        p, a = q.params, _a(q)
        z = p["a"] * _x**3 - p["b"] * _x * _y + p["c"] * _y**2
        assert _same(a["zxx"], sp.diff(z, _x, 2)), (i, a["zxx"])
        assert _same(a["zxy"], sp.diff(z, _x, _y)), (i, a["zxy"])
        assert _same(a["zyy"], sp.diff(z, _y, 2)), (i, a["zyy"])
        # теорема про рівність мішаних – перевіряємо, що еталон їй не суперечить
        assert _same(sp.diff(z, _x, _y), sp.diff(z, _y, _x)), i


def test_second_mixed_math():
    for i in range(25):
        q = _build("pd_second_mixed", i)
        p, a = q.params, _a(q)
        z = p["a"] * _x ** p["k"] * sp.log(_y) + sp.sin(p["b"] * _x)
        assert _same(a["zx"], sp.diff(z, _x)), (i, a["zx"])
        assert _same(a["zxy"], sp.diff(z, _x, _y)), (i, a["zxy"])
        assert _same(a["zyy"], sp.diff(z, _y, 2)), (i, a["zyy"])
        # похідна по y синуса не бачить: саме це й перевіряємо завданням
        assert not a["zxy"].has(sp.sin) and not a["zxy"].has(sp.cos), i
        assert not a["zyy"].has(sp.sin) and not a["zyy"].has(sp.cos), i
        assert a["zx"].has(sp.cos), (i, a["zx"])


def test_identity_math():
    for i in range(25):
        q = _build("pd_identity", i)
        p, a = q.params, _a(q)
        z = sp.log(_x ** p["a"] * _y ** p["b"])
        assert _same(a["zx"], sp.diff(z, _x)), (i, a["zx"])
        assert _same(a["zy"], sp.diff(z, _y)), (i, a["zy"])
        # вся суть: у сумі змінні скорочуються, лишається a + b
        assert _same(a["sum"], p["a"] + p["b"]), (i, a["sum"])
        assert sp.sympify(a["sum"]).is_number, (i, a["sum"])
        assert a["zx"] != a["zy"], i          # інакше carry підтвердив би себе


def test_domain_math():
    closed_seen = set()
    for i in range(40):
        q = _build("pd_domain", i)
        p, a = q.params, _a(q)
        closed_seen.add(p["closed"])
        r2 = p["r"] ** 2
        assert a["radius"] == p["r"], (i, a["radius"])
        # лічильник точок перераховуємо з нуля
        want = sum(1 for px, py in p["pts"]
                   if (px * px + py * py <= r2 if p["closed"]
                       else px * px + py * py < r2))
        assert a["cnt"] == want, (i, a["cnt"], want, p["pts"])
        assert _same(a["val"], sp.sqrt(r2) if p["closed"] else sp.log(r2)), i
    assert closed_seen == {True, False}, "мають бути і корінь, і логарифм"


def test_domain_always_lists_a_border_point():
    """Без точки з межі різниця між коренем і логарифмом не видна у відповіді."""
    for i in range(40):
        p = _build("pd_domain", i).params
        r2 = p["r"] ** 2
        assert any(px * px + py * py == r2 for px, py in p["pts"]), (i, p["pts"])
        assert len(p["pts"]) == 5, i


def test_domain_point_list_matches_statement():
    for i in range(20):
        q = _build("pd_domain", i)
        for px, py in q.params["pts"]:
            assert f"({px};\\ {py})" in q.statement, (i, px, py)


def test_extremum_full_math():
    for i in range(30):
        q = _build("pd_extremum_full", i)
        p, a = q.params, _a(q)
        s, x0, y0 = p["sign"], p["x0"], p["y0"]
        c, d = 2 * p["a"] * x0 * s, 2 * p["b"] * y0 * s
        z = s * (p["a"] * _x**2 + p["b"] * _y**2) - c * _x - d * _y + p["e"]
        assert _same(a["zx"], sp.diff(z, _x)), (i, a["zx"])
        # стаціонарність перевіряємо підстановкою, а не повтором формули
        assert sp.diff(z, _x).subs({_x: x0, _y: y0}) == 0, i
        assert sp.diff(z, _y).subs({_x: x0, _y: y0}) == 0, i
        assert a["x0"] == x0, (i, a["x0"])
        assert _same(a["zval"], sp.expand(z).subs({_x: x0, _y: y0})), i
        # екстремум справжній: Delta = AC - B^2 > 0
        A = sp.diff(z, _x, 2)
        B = sp.diff(z, _x, _y)
        C = sp.diff(z, _y, 2)
        assert A * C - B**2 > 0, i


def test_extremum_full_has_both_minimum_and_maximum():
    signs = {_build("pd_extremum_full", i).params["sign"] for i in range(30)}
    assert signs == {1, -1}


def test_extremum_test_math():
    for i in range(40):
        q = _build("pd_extremum_test", i)
        p, a = q.params, _a(q)
        z = _x**3 - 3 * p["a"] ** 2 * _x + p["b"] * _y**2
        at = {_x: p["px"], _y: 0}
        A = sp.diff(z, _x, 2).subs(at)
        B = sp.diff(z, _x, _y).subs(at)
        C = sp.diff(z, _y, 2).subs(at)
        # точка справді стаціонарна
        assert sp.diff(z, _x).subs(at) == 0, (i, p)
        assert sp.diff(z, _y).subs(at) == 0, (i, p)
        assert a["A"] == A, (i, a["A"], A)
        assert a["delta"] == A * C - B**2, (i, a["delta"])
        want = 0 if A * C - B**2 < 0 else (1 if A > 0 else 2)
        assert a["kind"] == want, (i, a["kind"], want, p)


def test_extremum_test_covers_all_three_conclusions():
    """Мінімум, максимум і «екстремуму немає» мусять траплятися всі три.

    Інакше правило $\\Delta$ можна вгадати, не застосовуючи.
    """
    kinds = [_build("pd_extremum_test", i).params["kind"] for i in range(60)]
    assert set(kinds) == {0, 1, 2}, sorted(set(kinds))
    for k in (0, 1, 2):
        assert kinds.count(k) >= 8, (k, kinds.count(k))


def test_lagrange_linear_math():
    for i in range(30):
        q = _build("pd_lagrange_linear", i)
        p, a = q.params, _a(q)
        lam = sp.Symbol("lam")
        L = _x**2 + _y**2 + lam * (p["a"] * _x + p["b"] * _y - p["c"])
        sol = sp.solve([sp.diff(L, _x), sp.diff(L, _y), sp.diff(L, lam)],
                       [_x, _y, lam], dict=True)
        assert len(sol) == 1, (i, sol)
        got = sol[0]
        assert a["lam"] == got[lam], (i, a["lam"], got[lam])
        assert a["x0"] == got[_x], (i, a["x0"], got[_x])
        assert a["zval"] == got[_x] ** 2 + got[_y] ** 2, (i, a["zval"])
        # точка лежить на прямій зв'язку
        assert p["a"] * got[_x] + p["b"] * got[_y] == p["c"], i


def test_lagrange_circle_math():
    for i in range(30):
        q = _build("pd_lagrange_circle", i)
        p, a = q.params, _a(q)
        lam = sp.Symbol("lam")
        L = (p["a"] * _x + p["b"] * _y
             + lam * (_x**2 + _y**2 - p["r2"]))
        sol = sp.solve([sp.diff(L, _x), sp.diff(L, _y), sp.diff(L, lam)],
                       [_x, _y, lam], dict=True)
        vals = sorted(p["a"] * s[_x] + p["b"] * s[_y] for s in sol)
        assert len(vals) == 2, (i, vals)
        assert a["zmin"] == vals[0], (i, a["zmin"], vals)
        assert a["zmax"] == vals[1], (i, a["zmax"], vals)
        # абсциса точки максимуму – ціла, як і решта відповідей
        best = max(sol, key=lambda s: p["a"] * s[_x] + p["b"] * s[_y])
        assert a["x0"] == best[_x], (i, a["x0"], best[_x])
        assert sp.sympify(a["x0"]).is_integer, (i, a["x0"])


def test_lagrange_circle_min_is_not_zero():
    """Нульовий мінімум зробив би carry з найбільшого значення самопідтвердним."""
    for i in range(30):
        a = _a(_build("pd_lagrange_circle", i))
        assert a["zmin"] != 0 and a["zmax"] != 0, i


# =======================================================================
#  ПЕРЕНЕСЕННЯ ПОМИЛКИ
# =======================================================================

def test_carry_rewards_consistent_continuation():
    """Схибив у похідній, але далі діяв правильно – другий крок зараховуємо."""
    q = _build("pd_first_poly", 2)
    wrong = sp.diff(q.params["a"] * _x ** q.params["n"] * _y ** q.params["m"],
                    _x) + 1           # зіпсований вільний член
    sub = {"zx": str(wrong), "zy": "0",
           "val": str(wrong.subs({_x: q.params["x0"], _y: q.params["y0"]}))}
    r = engine.grade(q, sub)
    detail = {d["part"]: d["score"] for d in r["parts"]}
    assert detail["zx"] == 0.0
    assert detail["val"] > 0, r


def test_carry_does_not_accept_zero_chain():
    """Нуль у першому полі не має робити нуль у наступному «правильним»."""
    for key, first, nxt in (("pd_first_poly", "zx", "val"),
                            ("pd_first_exp", "zy", "zxy"),
                            ("pd_second_mixed", "zx", "zxy"),
                            ("pd_lagrange_circle", "zmax", "zmin")):
        for i in range(6):
            q = _build(key, i)
            sub = {p.key: "0" for p in q.parts}
            r = engine.grade(q, sub)
            detail = {d["part"]: d["score"] for d in r["parts"]}
            assert detail[first] == 0.0, (key, i)
            assert detail[nxt] == 0.0, (key, i, r)
