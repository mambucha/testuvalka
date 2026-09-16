"""Бізнес-логіка наскрізного циклу: старт -> поточне питання -> відповідь -> далі.

Правила, які тримає сервер (розділ 6.3 брифу):
  * deadline_at проставляється при видачі питання, на сервері;
  * якщо now > deadline_at і відповіді немає:
      reissue < max_reissues -> перевидати той самий question_key з reissue+1
                                і повним часом (нові числа — seed від reissue);
      інакше                 -> 0 балів за пункт і перейти далі;
  * назад ходу немає: /current віддає рівно поточне питання;
  * правильні відповіді НІКОЛИ не потрапляють у відповідь API, і пізня
    (після дедлайну) відповідь НЕ оцінюється — вона для чисел, яких уже нема.

Годинник клієнта недовірений: дедлайн і його порушення рахуються тільки на
сервері (п. 5.7). Таймер у браузері — лише індикатор.
"""

from __future__ import annotations

import random
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

import engine
from app import grading, models
from app.config import GRADE_TIMEOUT, SECRET


class ServiceError(Exception):
    """Помилка бізнес-логіки з HTTP-кодом для API."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def utcnow() -> datetime:
    """Наивний UTC. SQLite не зберігає tzinfo, тож усе тримаємо в одному форматі
    й порівнюємо naive-to-naive. Годинник клієнта недовірений (п. 5.7)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def student_ident(full_name: str, group: str) -> str:
    """Нормалізована особа студента — використовується як seed-ідентифікатор і
    ключ у журналі. Особу не верифікуємо (бриф це визнає): це самопроголошені
    прізвище+група. Індивідуальні числа (п. 3.5) все одно працюють — різні
    студенти дістають різні варіанти, тож обмін відповідями в чаті групи марний.

    Нормалізація (обрізання, згортання пробілів, нижній регістр) робить особу
    стабільною при повторному вході з дрібними відмінностями в написанні.
    """

    def norm(s: str) -> str:
        return " ".join((s or "").split()).lower()

    return f"{norm(group)}|{norm(full_name)}"


# --------------------------------------------------------------------------
# Внутрішні помічники
# --------------------------------------------------------------------------


def _log(db: Session, attempt_id: int, type_: str, payload: dict[str, Any]) -> None:
    db.add(models.Event(attempt_id=attempt_id, ts=utcnow(), type=type_, payload=payload))


def _authorize(db: Session, attempt_id: int, token: str) -> models.Attempt:
    """Доступ до спроби — за одноразовим токеном, виданим на старті. Без Google
    авторизації особа не перевіряється, але токен не дає однокласнику читати чи
    псувати чужу спробу, просто підставивши attempt_id. 404 (не 403), щоб не
    підтверджувати саме існування спроби."""
    attempt = db.get(models.Attempt, attempt_id)
    if attempt is None or not token or not secrets.compare_digest(
        attempt.access_token, token
    ):
        raise ServiceError(404, "спробу не знайдено")
    return attempt


def _build(attempt: models.Attempt, aq: models.AttemptQuestion) -> engine.Question:
    """Детерміновано перебудовує задачу з її координат. Ті самі числа при
    перезаході; інша спроба або перевидання — інші числа."""
    return engine.build(
        aq.question_key,
        SECRET,
        attempt.student.ident,
        attempt.test.key,
        attempt.attempt_no,
        aq.reissue,
    )


def _pick_question_keys(
    test: models.Test, student: models.Student, attempt_no: int
) -> list[str]:
    """Детерміновано вибирає й упорядковує ключі шаблонів для спроби.

    Той самий студент у тій самій спробі завжди отримує ту саму послідовність
    (потрібно для відновлення сесії); різні студенти — різні.

    Ключ у межах спроби не повторюється: seed задачі не залежить від порядкового
    номера, тож повтор дав би тотожні числа. Тому кількість пунктів обмежена
    розміром банку.
    """
    bank = list(test.bank_keys or [])
    if not bank:
        raise ServiceError(400, f"банк тесту '{test.key}' порожній")
    picker = random.Random(
        engine.seed_for(SECRET, student.ident, test.key, "__sequence__", attempt_no)
    )
    keys = bank[:]
    picker.shuffle(keys)
    count = min(test.question_count, len(keys))
    return keys[:count]


def _current_question(attempt: models.Attempt) -> models.AttemptQuestion | None:
    """Перше (за порядком) ще не здане питання. None — усі пройдено."""
    for aq in attempt.questions:  # relationship уже відсортований за ordinal
        if aq.submitted_at is None:
            return aq
    return None


def _finish(db: Session, attempt: models.Attempt) -> None:
    ppq = attempt.test.points_per_question
    if ppq:
        # Кожне питання важить ppq; часткові бали всередині нормуються до неї.
        total = sum(
            ppq * ((aq.score or 0.0) / aq.max_score)
            for aq in attempt.questions
            if aq.max_score
        )
        attempt.score = round(total, 4)
    else:
        attempt.score = sum((aq.score or 0.0) for aq in attempt.questions)
    attempt.status = "finished"
    attempt.finished_at = utcnow()
    _log(db, attempt.id, "finish", {"score": attempt.score, "max": attempt.max_score})


def _finished_payload(attempt: models.Attempt) -> dict:
    return {"finished": True, "score": attempt.score, "max_score": attempt.max_score}


def _handle_expiry(db: Session, attempt: models.Attempt, aq: models.AttemptQuestion) -> bool:
    """Обробка виходу за дедлайн поточного питання (п. 3.3, 6.3).

    Спрацьовує, лише коли питання видане (started_at стоїть), ще не здане і час
    вийшов. Тоді: поки є ліміт перевидань — перевидати ту саму задачу з новими
    числами й повним часом; коли ліміт вичерпано — 0 балів за пункт і далі.

    Скидаємо started_at/deadline_at у None: свіжий дедлайн поставить наступна
    видача (_issue), а нові числа дасть build з reissue+1. Повертає True, якщо
    стан змінено.
    """
    if aq.started_at is None or aq.submitted_at is not None:
        return False
    if aq.deadline_at is None or utcnow() <= aq.deadline_at:
        return False

    _log(
        db,
        attempt.id,
        "expire",
        {"ordinal": aq.ordinal, "question_key": aq.question_key, "reissue": aq.reissue},
    )
    if aq.reissue < attempt.test.max_reissues:
        aq.reissue += 1
        aq.started_at = None
        aq.deadline_at = None
        _log(db, attempt.id, "reissue", {"ordinal": aq.ordinal, "reissue": aq.reissue})
    else:
        aq.score = 0.0
        aq.submitted_at = utcnow()
        _log(db, attempt.id, "zero_after_reissues", {"ordinal": aq.ordinal})
    return True


def _issue(db: Session, attempt: models.Attempt, aq: models.AttemptQuestion) -> engine.Question:
    """Видача питання: будуємо задачу і ставимо серверний дедлайн (один раз)."""
    q = _build(attempt, aq)
    if aq.started_at is None:
        now = utcnow()
        aq.started_at = now
        aq.deadline_at = now + timedelta(seconds=q.seconds)
        aq.max_score = q.max_score
        _log(
            db,
            attempt.id,
            "issue",
            {"ordinal": aq.ordinal, "question_key": aq.question_key, "reissue": aq.reissue},
        )
    return q


# --------------------------------------------------------------------------
# Публічні операції (викликаються з маршрутів)
# --------------------------------------------------------------------------


def _get_or_create_student(
    db: Session, full_name: str, group: str
) -> models.Student:
    full_name = (full_name or "").strip()
    group = (group or "").strip()
    if not full_name or not group:
        raise ServiceError(400, "вкажіть прізвище та групу")
    ident = student_ident(full_name, group)
    student = db.scalar(select(models.Student).where(models.Student.ident == ident))
    if student is None:
        student = models.Student(ident=ident, full_name=full_name, group_name=group)
        db.add(student)
        db.flush()  # отримати student.id
    return student


def start_attempt(
    db: Session, full_name: str, group: str, test_key: str
) -> models.Attempt:
    test = db.scalar(select(models.Test).where(models.Test.key == test_key))
    if test is None:
        raise ServiceError(404, "тест не знайдено")

    now = utcnow()
    if test.opens_at and now < test.opens_at:
        raise ServiceError(403, "тест ще не відкрито")
    if test.closes_at and now > test.closes_at:
        raise ServiceError(403, "тест уже закрито")

    student = _get_or_create_student(db, full_name, group)

    # Уже є активна спроба — повертаємо її (відновлення сесії, а не нова спроба).
    active = db.scalar(
        select(models.Attempt).where(
            models.Attempt.student_id == student.id,
            models.Attempt.test_id == test.id,
            models.Attempt.status == "active",
        )
    )
    if active is not None:
        return active

    # Ліміт спроб: voided не рахуються — аномальна спроба потребує нової (п. 3.4).
    used = (
        db.scalar(
            select(func.count())
            .select_from(models.Attempt)
            .where(
                models.Attempt.student_id == student.id,
                models.Attempt.test_id == test.id,
                models.Attempt.status != "voided",
            )
        )
        or 0
    )
    if used >= test.max_attempts:
        raise ServiceError(403, "вичерпано ліміт спроб")

    # Номер спроби для seed рахуємо по ВСІХ спробах (зокрема voided), щоб числа
    # нової спроби не збіглися з жодною попередньою.
    total = (
        db.scalar(
            select(func.count())
            .select_from(models.Attempt)
            .where(
                models.Attempt.student_id == student.id,
                models.Attempt.test_id == test.id,
            )
        )
        or 0
    )
    attempt_no = total + 1

    # Валідуємо банк ДО створення спроби, щоб не лишати сирітних рядків.
    keys = _pick_question_keys(test, student, attempt_no)

    attempt = models.Attempt(
        student_id=student.id,
        test_id=test.id,
        attempt_no=attempt_no,
        started_at=now,
        status="active",
        access_token=secrets.token_urlsafe(24),
    )
    db.add(attempt)
    db.flush()  # отримати attempt.id

    max_total = 0.0
    for ordinal, qkey in enumerate(keys):
        q = engine.build(qkey, SECRET, student.ident, test.key, attempt_no, 0)
        db.add(
            models.AttemptQuestion(
                attempt_id=attempt.id,
                ordinal=ordinal,
                question_key=qkey,
                reissue=0,
                max_score=q.max_score,  # «сирий» максимум питання (знаменник нормування)
            )
        )
        max_total += q.max_score
    # Якщо задано вагу питання — підсумок тесту це вага × кількість питань.
    ppq = test.points_per_question
    attempt.max_score = ppq * len(keys) if ppq else max_total

    _log(db, attempt.id, "start", {"attempt_no": attempt_no, "count": len(keys)})
    db.commit()
    return attempt


def get_current(db: Session, attempt_id: int, token: str) -> dict:
    attempt = _authorize(db, attempt_id, token)

    if attempt.status != "active":
        return _finished_payload(attempt)

    aq = _current_question(attempt)
    if aq is None:
        _finish(db, attempt)
        db.commit()
        return _finished_payload(attempt)

    # Студент повернувся: якщо час поточного питання вийшов — перевидати або
    # обнулити ще ДО показу (п. 3.3), потім перерахувати поточне питання.
    changed = _handle_expiry(db, attempt, aq)
    if changed:
        aq = _current_question(attempt)
        if aq is None:
            _finish(db, attempt)
            db.commit()
            return _finished_payload(attempt)

    newly_issued = aq.started_at is None
    q = _issue(db, attempt, aq)
    if newly_issued or changed:
        db.commit()

    seconds_left = int((aq.deadline_at - utcnow()).total_seconds())
    return {
        "finished": False,
        "ordinal": aq.ordinal,
        "total": len(attempt.questions),
        "reissue": aq.reissue,
        "question": q.public(),
        "seconds_left": max(0, seconds_left),
    }


def submit_answer(
    db: Session, attempt_id: int, token: str, answers: dict[str, str]
) -> dict:
    attempt = _authorize(db, attempt_id, token)
    if attempt.status != "active":
        raise ServiceError(409, "спроба вже завершена")

    aq = _current_question(attempt)
    if aq is None:
        _finish(db, attempt)
        db.commit()
        raise ServiceError(409, "усі питання вже пройдено")

    # Час вийшов до подання? Відповідь НЕ оцінюємо: вона для чисел, яких уже
    # нема (п. 3.3). Перевидаємо або обнуляємо і просимо клієнта взяти /current.
    if _handle_expiry(db, attempt, aq):
        nxt = _current_question(attempt)
        if nxt is None:
            _finish(db, attempt)
            db.commit()
            return {
                "ok": False,
                "expired": True,
                "next": False,
                "finished": True,
                "score": attempt.score,
                "max_score": attempt.max_score,
            }
        db.commit()
        return {"ok": False, "expired": True, "next": True}

    # Якщо клієнт шле відповідь без попереднього /current — видаємо зараз, щоб
    # не втратити роботу студента (дедлайн виставиться цим же викликом).
    _issue(db, attempt, aq)

    # Оцінювання ЗАВЖДИ через safe_grade (п. 5.1): жорсткий таймаут у підпроцесі,
    # у воркер їдуть лише координати задачі, еталони не подорожують між процесами.
    # Обгортка grading.safe_grade реєструє й банк шаблонів у дочірньому процесі.
    result = grading.safe_grade(
        aq.question_key,
        SECRET,
        attempt.student.ident,
        attempt.test.key,
        attempt.attempt_no,
        answers,
        reissue=aq.reissue,
        timeout=GRADE_TIMEOUT,
    )

    # Зберігаємо відповіді по частинах — лише сирий ввід і бали, без еталонів.
    for part in result.get("parts", []):
        db.add(
            models.Answer(
                attempt_question_id=aq.id,
                part_key=part["part"],
                raw=str(part.get("raw", ""))[:1000],
                score=part.get("score", 0.0),
                max_points=part.get("max", 0.0),
            )
        )
    aq.score = result["score"]
    aq.max_score = result["max"]
    aq.submitted_at = utcnow()
    _log(
        db,
        attempt.id,
        "submit",
        {"ordinal": aq.ordinal, "score": result["score"], "max": result["max"]},
    )

    nxt = _current_question(attempt)
    if nxt is None:
        _finish(db, attempt)
        db.commit()
        return {
            "ok": True,
            "next": False,
            "finished": True,
            "score": attempt.score,
            "max_score": attempt.max_score,
        }

    db.commit()
    return {"ok": True, "next": True}


def log_event(
    db: Session, attempt_id: int, token: str, type_: str, payload: dict
) -> None:
    attempt = _authorize(db, attempt_id, token)
    _log(db, attempt.id, type_, payload)
    db.commit()


def review_attempt(db: Session, attempt_id: int, token: str) -> dict:
    """Розбір для студента (за токеном спроби, лише після завершення). Показує
    по кожному питанню бал і, для помилок, правильну відповідь. Числа спроби
    одноразові, тож показ еталонів безпечний. Телеметрії тут немає."""
    attempt = _authorize(db, attempt_id, token)
    if attempt.status != "finished":
        raise ServiceError(409, "розбір буде доступний після завершення тесту")

    questions = []
    for aq in sorted(attempt.questions, key=lambda q: q.ordinal):
        try:
            built = _build(attempt, aq)
            ref = {p.key: p for p in built.parts}
            order = [p.key for p in built.parts]
        except Exception:  # noqa: BLE001 — шаблон могли змінити після спроби
            ref, order = {}, None

        stored = {a.part_key: a for a in aq.answers}
        keys = order if order is not None else [a.part_key for a in aq.answers]
        parts = []
        for pk in keys:
            p = ref.get(pk)
            a = stored.get(pk)
            got = a.score if a else 0.0
            mx = a.max_points if a else (p.points if p else 0.0)
            parts.append(
                {
                    "label": p.label if p else pk,
                    "raw": a.raw if a else "",
                    "expected": str(p.answer) if p else "—",
                    "correct": bool(mx and got >= mx),
                }
            )
        if aq.score is None:
            verdict = "ні"
        elif aq.max_score and aq.score >= aq.max_score:
            verdict = "повністю"
        elif aq.score > 0:
            verdict = "частково"
        else:
            verdict = "ні"
        questions.append(
            {
                "score": aq.score or 0.0,
                "max_score": aq.max_score,
                "verdict": verdict,
                "parts": parts,
            }
        )
    return {"score": attempt.score, "max_score": attempt.max_score, "questions": questions}
