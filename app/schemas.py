"""Pydantic-схеми запитів і відповідей API (контракт розділу 6.3).

Жодна зі схем відповіді НЕ містить полів для еталонних відповідей — правильні
відповіді ніколи не потрапляють у браузер.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StartIn(BaseModel):
    test_key: str
    full_name: str  # прізвище (та ім'я) — самопроголошена особа
    group: str


class StartOut(BaseModel):
    attempt_id: int
    token: str  # одноразовий токен доступу до спроби; клієнт зберігає й шле далі


class PartPublic(BaseModel):
    key: str
    label: str
    kind: str
    points: float


class QuestionPublic(BaseModel):
    key: str
    statement: str
    seconds: int
    svg: str | None = None  # необов'язковий рисунок (inline SVG)
    parts: list[PartPublic]


class CurrentOut(BaseModel):
    finished: bool = False
    # Поточне питання (коли спроба активна):
    ordinal: int | None = None
    total: int | None = None
    reissue: int | None = None  # номер перевидання питання (0 — початкове)
    question: QuestionPublic | None = None
    seconds_left: int | None = None
    # Підсумок (коли спроба завершена):
    score: float | None = None
    max_score: float | None = None


class AnswerIn(BaseModel):
    # {part_key: сирий рядок від студента}
    answers: dict[str, str] = Field(default_factory=dict)


class AnswerOut(BaseModel):
    ok: bool
    next: bool
    # Час на питання вийшов до подання: відповідь не оцінено, питання перевидано
    # або обнулено. Клієнт має перезапитати /current.
    expired: bool = False
    finished: bool = False
    score: float | None = None
    max_score: float | None = None


class EventIn(BaseModel):
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
