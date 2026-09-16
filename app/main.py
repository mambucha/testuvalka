"""FastAPI-застосунок і маршрути (контракт розділу 6.3).

Авторизації через Google немає: студент входить, вводячи прізвище+групу; доступ
до спроби далі йде за одноразовим токеном (заголовок X-Attempt-Token), виданим
на старті. Маршрути синхронні (`def`): FastAPI виконує їх у threadpool, тож
блокувальний виклик safe_grade (підпроцес) не блокує цикл подій.
"""

from __future__ import annotations

import logging
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, Query, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas, service, teacher
from app.config import AUTOLOAD, TEACHER_TOKEN
from app.db import SessionLocal, get_db, init_db
from app.load_tests import load_tests

log = logging.getLogger("testuvalka")
WEB_DIR = Path(__file__).resolve().parent.parent / "web"


def _ensure_demo_seed() -> None:
    """Демонстраційний тест для розробки й тестів. Студенти самореєструються
    на старті, тож окремо їх сідити не треба."""
    db = SessionLocal()
    try:
        if not db.scalar(select(models.Test).where(models.Test.key == "demo")):
            db.add(
                models.Test(
                    key="demo",
                    title="Демонстраційний тест",
                    question_count=3,
                    bank_keys=[
                        "linear_system_2x2",
                        "quadratic_roots",
                        "derivative_at_point",
                    ],
                    max_attempts=3,
                    max_reissues=2,
                )
            )
            db.commit()
    finally:
        db.close()


def _maybe_autoload() -> None:
    """Завантажити тести з TESTUVALKA_AUTOLOAD на старті. Помилка YAML не валить
    застосунок — лише лог; наявні тести лишаються доступні."""
    if not AUTOLOAD:
        return
    path = Path(AUTOLOAD)
    if not path.exists():
        log.warning("TESTUVALKA_AUTOLOAD=%s — файл не знайдено, пропускаю", AUTOLOAD)
        return
    try:
        created, updated = load_tests(str(path))
        log.info("Автозавантаження тестів: створено %d, оновлено %d", created, updated)
    except Exception as exc:  # noqa: BLE001 — старт важливіший за один поганий YAML
        log.warning("Автозавантаження тестів не вдалося: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _ensure_demo_seed()
    _maybe_autoload()
    yield


app = FastAPI(title="Testuvalka", lifespan=lifespan)


@app.exception_handler(service.ServiceError)
async def _service_error_handler(request, exc: service.ServiceError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


def _token(x_attempt_token: str = Header(default="", alias="X-Attempt-Token")) -> str:
    return x_attempt_token


@app.post("/api/attempt/start", response_model=schemas.StartOut)
def start(body: schemas.StartIn, db: Session = Depends(get_db)):
    attempt = service.start_attempt(db, body.full_name, body.group, body.test_key)
    return {"attempt_id": attempt.id, "token": attempt.access_token}


@app.get("/api/attempt/{attempt_id}/current", response_model=schemas.CurrentOut)
def current(
    attempt_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(_token),
):
    return service.get_current(db, attempt_id, token)


@app.post("/api/attempt/{attempt_id}/answer", response_model=schemas.AnswerOut)
def answer(
    attempt_id: int,
    body: schemas.AnswerIn,
    db: Session = Depends(get_db),
    token: str = Depends(_token),
):
    return service.submit_answer(db, attempt_id, token, body.answers)


@app.get("/api/attempt/{attempt_id}/review")
def review(
    attempt_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(_token),
):
    return service.review_attempt(db, attempt_id, token)


@app.post("/api/attempt/{attempt_id}/event", status_code=204)
def event(
    attempt_id: int,
    body: schemas.EventIn,
    db: Session = Depends(get_db),
    token: str = Depends(_token),
):
    service.log_event(db, attempt_id, token, body.type, body.payload)
    return Response(status_code=204)


# --- Кабінет викладача ---------------------------------------------------
# Токен приймаємо із заголовка X-Teacher-Token або ?token= (щоб CSV можна було
# завантажити прямим посиланням).


def require_teacher(
    x_teacher_token: str = Header(default="", alias="X-Teacher-Token"),
    token: str = Query(default=""),
) -> bool:
    if not TEACHER_TOKEN:
        raise service.ServiceError(
            503, "кабінет викладача не налаштований (задайте TESTUVALKA_TEACHER_TOKEN)"
        )
    supplied = x_teacher_token or token
    if not supplied or not secrets.compare_digest(supplied, TEACHER_TOKEN):
        raise service.ServiceError(403, "потрібен коректний токен викладача")
    return True


@app.get("/api/teacher/results")
def teacher_results(
    test_key: str, db: Session = Depends(get_db), _: bool = Depends(require_teacher)
):
    csv_text = teacher.results_csv(db, test_key)
    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="results_{test_key}.csv"'},
    )


@app.get("/api/teacher/results_xlsx")
def teacher_results_xlsx(
    test_key: str, db: Session = Depends(get_db), _: bool = Depends(require_teacher)
):
    data = teacher.results_xlsx(db, test_key)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="results_{test_key}.xlsx"'},
    )


@app.get("/api/teacher/anomalies")
def teacher_anomalies(
    test_key: str, db: Session = Depends(get_db), _: bool = Depends(require_teacher)
):
    return {"test_key": test_key, "attempts": teacher.anomalies(db, test_key)}


@app.get("/api/teacher/attempt/{attempt_id}/detail")
def teacher_attempt_detail(
    attempt_id: int, db: Session = Depends(get_db), _: bool = Depends(require_teacher)
):
    return teacher.attempt_detail(db, attempt_id)


# Статичний фронтенд (одна сторінка). Монтуємо ОСТАННІМ, щоб /api/* мали
# пріоритет; html=True віддає index.html на "/".
app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
