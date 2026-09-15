"""Лекція 1: коректність усіх шаблонів банку + нормалізація балів (0,5/питання).

Коректність шаблонів перевіряємо в тому ж процесі (engine.grade), без підпроцесу
— швидко. Нормалізацію балів — наскрізь через API.
"""

import textwrap

import sympy as sp

import engine
from app.config import SECRET
from app.load_tests import load_tests
from support import StudentClient, correct_answers

LECTURE1_KEYS = [
    "det_2x2",
    "det_3x3_sarrus",
    "det_triangular",
    "minor_3x3",
    "cofactor_3x3",
    "expansion_by_row",
    "determinant_property",
    "matrix_scalar_element",
    "matrix_sum_element",
    "inverse_2x2",
    "linear_system_2x2",
    "cramer_3x3",
    "gauss_3x3",
]


def test_all_lecture1_templates_grade_full_on_correct_answers():
    """Кожен шаблон: побудова -> правильні відповіді з еталонів -> повний бал.
    Ловить неузгодженість умова/параметри/відповідь і помилки в carry."""
    for key in LECTURE1_KEYS:
        q = engine.build(key, SECRET, "перевірка|студент", "t", 1, 0)
        answers = {p.key: str(p.answer) for p in q.parts}
        result = engine.grade(q, answers)
        assert result["score"] == result["max"] == q.max_score, (
            key,
            result,
            answers,
        )
        assert q.max_score >= 1  # хоча б одне поле


def test_lecture1_statements_use_katex_delimiters():
    """Умови й підписи дотримуються конвенції: математика в $...$/$$...$$."""
    for key in LECTURE1_KEYS:
        q = engine.build(key, SECRET, "s|s", "t", 1, 0)
        assert "$" in q.statement


def test_equivalent_answer_forms_are_accepted():
    """Різні записи однакового числа зараховуються (приклад користувача:
    5/2 = 10/4 = 2,5). Це властивість ядра (алгебраїчна еквівалентність)."""
    q = engine.Question(
        key="t", statement="", parts=[engine.Part("a", "a", sp.Rational(5, 2))]
    )
    for form in ["5/2", "10/4", "2.5", "2,5", "2.50", "15/6"]:
        result = engine.grade(q, {"a": form})
        assert result["score"] == 1.0, form

    # Ціла відповідь так само приймається у різних формах.
    qi = engine.Question(
        key="t", statement="", parts=[engine.Part("d", "d", 13)]
    )
    for form in ["13", "26/2", "13.0", "39/3"]:
        assert engine.grade(qi, {"d": form})["score"] == 1.0, form


def test_inverse_2x2_fractional_entry_accepts_decimal():
    """На реальному шаблоні: якщо елемент оберненої дробовий, десятковий запис
    теж зараховується."""
    # Знайдемо екземпляр inverse_2x2 із дробовим елементом (|Δ|=2).
    q = None
    for attempt in range(60):
        cand = engine.build("inverse_2x2", SECRET, f"s|{attempt}", "t", 1, 0)
        if any(p.answer.q != 1 for p in cand.parts if hasattr(p.answer, "q")):
            q = cand
            break
    assert q is not None, "не знайдено дробового прикладу — малоймовірно"

    submitted = {}
    for p in q.parts:
        val = p.answer
        if hasattr(val, "q") and val.q == 2:  # половинка -> подаємо десятковим
            submitted[p.key] = str(float(val))  # напр. "1.5"
        else:
            submitted[p.key] = str(val)
    result = engine.grade(q, submitted)
    assert result["score"] == result["max"], (submitted, result)


def _load_ppq_test(tmp_path, keys, count):
    path = tmp_path / "ppq.yaml"
    path.write_text(
        textwrap.dedent(
            f"""
            - key: ppqtest
              title: PPQ
              question_count: {count}
              points_per_question: 0.5
              bank: [{", ".join(keys)}]
              max_attempts: 1
            """
        ),
        encoding="utf-8",
    )
    load_tests(str(path))


def test_points_per_question_full_correct(client, tmp_path):
    """Два питання по 0,5 -> максимум 1,0; усе правильно -> 1,0."""
    _load_ppq_test(tmp_path, ["det_2x2", "matrix_sum_element"], 2)
    s = StudentClient(client)
    s.start("ppqtest")
    while True:
        cur = s.current_json()
        if cur.get("finished"):
            final = cur
            break
        s.answer(correct_answers(cur["question"]["key"], test_key="ppqtest"))
    assert final["max_score"] == 1.0
    assert final["score"] == 1.0


def test_points_per_question_partial(client, tmp_path):
    """Одне питання правильно, друге порожнє -> рівно 0,5 з 1,0 (кожне важить
    0,5 незалежно від кількості полів)."""
    _load_ppq_test(tmp_path, ["det_2x2", "cramer_3x3"], 2)
    s = StudentClient(client)
    s.start("ppqtest")

    first = s.current_json()
    s.answer(correct_answers(first["question"]["key"], test_key="ppqtest"))
    second = s.current_json()
    empty = {p["key"]: "" for p in second["question"]["parts"]}
    s.answer(empty)

    final = s.current_json()
    assert final["finished"] is True
    assert final["max_score"] == 1.0
    assert final["score"] == 0.5
