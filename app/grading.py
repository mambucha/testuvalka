"""Оцінювання в окремому процесі з жорстким таймаутом (п. 5.1) — тепер через
ОДИН довгоживучий пул зі start-методом "spawn".

Чому spawn, а не fork: сервер багатопотоковий (FastAPI виконує синхронні
маршрути у threadpool, плюс телеметрія). fork із такого процесу періодично
дає дедлок у дочірньому процесі (успадковані замки, які ніхто не відпустить) —
саме це виглядало як «натиснув Відповісти, а наступне питання не вантажиться».
spawn стартує чистий процес без успадкованих замків, тож дедлок неможливий.

Чому довгоживучий пул (а не на кожен запит): spawn-воркер холодно імпортує
sympy (~1-2 с). Тримаємо пул теплим — sympy імпортується раз на воркер, і кожне
подальше оцінювання займає мілісекунди (це і був рефакторинг із п. 5.8).

Модуль імпортує app.bank, тож банкові шаблони зареєстровані й у воркерах (spawn
заново імпортує цей модуль у дочірньому процесі).
"""

from __future__ import annotations

import atexit
import concurrent.futures as _cf
import multiprocessing as _mp
import threading

import engine
from app import bank  # noqa: F401  — реєстрація банкових шаблонів (side-effect)

_CTX = _mp.get_context("spawn")
_MAX_WORKERS = 2
_pool: _cf.ProcessPoolExecutor | None = None
_lock = threading.Lock()


def _grade_worker(args):
    qk, secret, student_id, test_key, attempt_no, reissue, submitted = args
    q = engine.build(qk, secret, student_id, test_key, attempt_no, reissue)
    return engine.grade(q, submitted)


def _get_pool() -> _cf.ProcessPoolExecutor:
    global _pool
    if _pool is None:
        with _lock:
            if _pool is None:
                _pool = _cf.ProcessPoolExecutor(
                    max_workers=_MAX_WORKERS, mp_context=_CTX
                )
    return _pool


def _reset_pool() -> None:
    """Викинути поточний пул (напр. після зависання воркера). Дочірні процеси
    вбиваємо, щоб завислий не тримав ресурси; наступне оцінювання створить пул
    заново."""
    global _pool
    with _lock:
        old, _pool = _pool, None
    if old is not None:
        try:
            for proc in list(old._processes.values()):
                proc.kill()
        except Exception:  # noqa: BLE001
            pass
        old.shutdown(wait=False, cancel_futures=True)


def _timeout_result(question_key, secret, student_id, test_key, attempt_no, reissue, msg):
    q = engine.build(question_key, secret, student_id, test_key, attempt_no, reissue)
    return {"score": 0.0, "max": q.max_score, "parts": [], "error": msg}


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
    try:
        fut = _get_pool().submit(_grade_worker, args)
        return fut.result(timeout=timeout)
    except _cf.TimeoutError:
        # Малоймовірно (синтаксичні фільтри в parse_answer ловлять відомі атаки),
        # але якщо воркер завис — пересоздаємо пул і повертаємо 0 за пункт.
        _reset_pool()
        return _timeout_result(
            question_key, secret, student_id, test_key, attempt_no, reissue,
            "перевірка перевищила ліміт часу",
        )
    except _cf.BrokenProcessPool:
        _reset_pool()
        return _timeout_result(
            question_key, secret, student_id, test_key, attempt_no, reissue,
            "збій воркера оцінювання",
        )


atexit.register(_reset_pool)
