"""Завантаження/оновлення тестів із YAML у БД.

    python -m app.load_tests tests.yaml

Шаблони задач — це код (engine.py, app/bank/*). Тут описуються лише ТЕСТИ, що
посилаються на ключі шаблонів. Повторний запуск оновлює наявні тести за ключем
(upsert), нові — створює. Спроби студентів не чіпаються.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import yaml
from sqlalchemy import select

import engine
from app import bank  # noqa: F401  — зареєструвати банкові шаблони перед перевіркою
from app import models
from app.db import SessionLocal, init_db


class LoadError(Exception):
    pass


def _parse_dt(value) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    return datetime.fromisoformat(str(value)).replace(tzinfo=None)


def load_tests(path: str, db=None) -> tuple[int, int]:
    """Прочитати YAML і впорядкувати тести в БД. Повертає (створено, оновлено)."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or []
    if isinstance(data, dict) and "tests" in data:
        data = data["tests"]
    if not isinstance(data, list):
        raise LoadError("YAML має бути списком тестів (або {tests: [...]})")

    own = db is None
    db = db or SessionLocal()
    created = updated = 0
    try:
        for i, t in enumerate(data):
            key = t.get("key")
            if not key:
                raise LoadError(f"тест #{i}: немає обов'язкового поля 'key'")
            bank_keys = list(t.get("bank") or [])
            if not bank_keys:
                raise LoadError(f"тест '{key}': порожній 'bank'")
            unknown = [k for k in bank_keys if k not in engine.TEMPLATES]
            if unknown:
                raise LoadError(
                    f"тест '{key}': невідомі шаблони {unknown}. "
                    f"Доступні: {sorted(engine.TEMPLATES)}"
                )
            qcount = int(t.get("question_count") or len(bank_keys))
            if qcount > len(bank_keys):
                raise LoadError(
                    f"тест '{key}': question_count={qcount} більший за банк "
                    f"({len(bank_keys)}). Ключі не повторюються в межах спроби — "
                    "додайте шаблонів або зменшіть кількість пунктів."
                )
            ppq = t.get("points_per_question")
            if ppq is not None:
                ppq = float(ppq)
                if ppq <= 0:
                    raise LoadError(f"тест '{key}': points_per_question має бути > 0")
            fields = dict(
                title=t.get("title", key),
                question_count=qcount,
                bank_keys=bank_keys,
                opens_at=_parse_dt(t.get("opens_at")),
                closes_at=_parse_dt(t.get("closes_at")),
                max_attempts=int(t.get("max_attempts", 1)),
                max_reissues=int(t.get("max_reissues", 2)),
                points_per_question=ppq,
                restart_after_violations=(
                    int(t["restart_after_violations"])
                    if t.get("restart_after_violations") not in (None, "")
                    else None
                ),
            )
            row = db.scalar(select(models.Test).where(models.Test.key == key))
            if row is None:
                db.add(models.Test(key=key, **fields))
                created += 1
            else:
                for field, value in fields.items():
                    setattr(row, field, value)
                updated += 1
        db.commit()
    finally:
        if own:
            db.close()
    return created, updated


def main(argv=None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        raise SystemExit("вжиток: python -m app.load_tests <файл.yaml>")
    init_db()
    try:
        created, updated = load_tests(argv[0])
    except LoadError as exc:
        raise SystemExit(f"Помилка: {exc}")
    print(f"Готово: створено {created}, оновлено {updated}.")


if __name__ == "__main__":
    main()
