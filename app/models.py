"""ORM-моделі за схемою розділу 6.2 брифу.

ВАЖЛИВО: у БД НЕ зберігаються еталонні відповіді. Вони завжди перераховуються
з seed рушієм. Це і економія, і гарантія, що вони ніде не витечуть.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Особа = нормалізовані прізвище+група (Google-авторизації немає). Не
    # верифікується, але цього досить для журналу й індивідуальних чисел (3.5).
    ident: Mapped[str] = mapped_column(String, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String, default="")
    group_name: Mapped[str] = mapped_column(String, default="")


class Test(Base):
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String, unique=True, index=True)
    title: Mapped[str] = mapped_column(String, default="")
    opens_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closes_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Скільки пунктів витягти з банку і які шаблони до нього входять.
    question_count: Mapped[int] = mapped_column(Integer, default=10)
    bank_keys: Mapped[list] = mapped_column(JSON, default=list)
    max_attempts: Mapped[int] = mapped_column(Integer, default=1)
    max_reissues: Mapped[int] = mapped_column(Integer, default=2)
    # Вага кожного питання в балах тесту. Якщо задано — кожне питання важить
    # рівно стільки (напр. 0.5), а часткові бали всередині нормуються до неї,
    # тож підсумок = points_per_question * question_count. None -> підсумок є
    # сумою «сирих» балів полів (стара поведінка).
    points_per_question: Mapped[float | None] = mapped_column(Float, nullable=True)


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"), index=True)
    attempt_no: Mapped[int] = mapped_column(Integer)
    # Одноразовий токен доступу до спроби (замість авторизації): видається на
    # старті, клієнт шле його в заголовку. Захищає від читання/псування чужої
    # спроби за вгаданим attempt_id.
    access_token: Mapped[str] = mapped_column(String, index=True, default="")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String, default="active")  # active|finished|voided
    score: Mapped[float] = mapped_column(Float, default=0.0)
    max_score: Mapped[float] = mapped_column(Float, default=0.0)

    student: Mapped["Student"] = relationship("Student")
    test: Mapped["Test"] = relationship("Test")
    questions: Mapped[list["AttemptQuestion"]] = relationship(
        "AttemptQuestion",
        back_populates="attempt",
        order_by="AttemptQuestion.ordinal",
        cascade="all, delete-orphan",
    )


class AttemptQuestion(Base):
    __tablename__ = "attempt_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    question_key: Mapped[str] = mapped_column(String)
    reissue: Mapped[int] = mapped_column(Integer, default=0)
    # Дедлайн проставляється НА СЕРВЕРІ в момент видачі питання (п. 6.3, 5.7).
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_score: Mapped[float] = mapped_column(Float, default=0.0)

    attempt: Mapped["Attempt"] = relationship("Attempt", back_populates="questions")
    answers: Mapped[list["Answer"]] = relationship(
        "Answer", back_populates="question", cascade="all, delete-orphan"
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_question_id: Mapped[int] = mapped_column(
        ForeignKey("attempt_questions.id"), index=True
    )
    part_key: Mapped[str] = mapped_column(String)
    raw: Mapped[str] = mapped_column(String, default="")
    score: Mapped[float] = mapped_column(Float, default=0.0)
    max_points: Mapped[float] = mapped_column(Float, default=0.0)

    question: Mapped["AttemptQuestion"] = relationship(
        "AttemptQuestion", back_populates="answers"
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id"), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime)
    type: Mapped[str] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
