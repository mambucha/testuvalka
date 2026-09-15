"""Обгортка оцінювання: той самий жорсткий таймаут у підпроцесі, що й
engine.safe_grade, але в контексті застосунку.

Навіщо окремо від engine.safe_grade: воркер має бути в модулі, який імпортує
банк шаблонів (app.bank). На Windows підпроцеси створюються через spawn — дочірній
процес заново імпортує модуль воркера; імпортуючи app.grading, він тягне і
app.bank, тож банкові шаблони зареєстровані й там. Якби воркер жив у engine
(engine не знає про app.bank), build() у дочірньому процесі не знайшов би
банкових ключів.

Тут же природне місце майбутнього рефакторингу (п. 5.8): замінити пул на-запит
одним довгоживучим теплим пулом і знизити таймаут до ~3 с.
"""

from __future__ import annotations

import concurrent.futures as _cf

import engine
from app import bank  # noqa: F401  — реєстрація банкових шаблонів (side-effect)


def _grade_worker(args):
    qk, secret, student_id, test_key, attempt_no, reissue, submitted = args
    q = engine.build(qk, secret, student_id, test_key, attempt_no, reissue)
    return engine.grade(q, submitted)


def safe_grade(
    question_key: str,
    secret: bytes,
    student_id: str,
    test_key: str,
    attempt_no: int,
    submitted: dict[str, str],
    reissue: int = 0,
    timeout: float = 3.0,
) -> dict:
    args = (question_key, secret, student_id, test_key, attempt_no, reissue, submitted)
    with _cf.ProcessPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_grade_worker, args)
        try:
            return fut.result(timeout=timeout)
        except _cf.TimeoutError:
            for proc in pool._processes.values():
                proc.kill()
            q = engine.build(
                question_key, secret, student_id, test_key, attempt_no, reissue
            )
            return {
                "score": 0.0,
                "max": q.max_score,
                "parts": [],
                "error": "перевірка перевищила ліміт часу",
            }
