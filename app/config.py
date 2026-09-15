"""Конфігурація застосунку. Читається один раз на імпорті.

SECRET МУСИТЬ БУТИ СТАЛИМ (п. 5.6 брифу): зміна секрету змінює параметри всіх
задач усіх студентів. У проді задається через змінну оточення й не комітиться.
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path

# Корінь проєкту (де лежать engine.py і, за замовчуванням, файл БД).
ROOT = Path(__file__).resolve().parent.parent

# .env читаємо, якщо є. python-dotenv необов'язковий — без нього беремо оточення.
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except Exception:  # noqa: BLE001
    pass


def _load_secret() -> bytes:
    value = os.getenv("TESTUVALKA_SECRET")
    if not value:
        # Дев-режим: працюємо, але голосно попереджаємо. У проді env обов'язковий.
        warnings.warn(
            "TESTUVALKA_SECRET не заданий — використовую небезпечний дев-секрет. "
            "У проді задайте сталий секрет через оточення (п. 5.6 брифу).",
            stacklevel=2,
        )
        value = "dev-insecure-secret-change-me"
    return value.encode()


SECRET: bytes = _load_secret()

# БД: SQLite на етапі розробки, Postgres у проді.
_default_db = (ROOT / "testuvalka.db").as_posix()
DATABASE_URL: str = os.getenv("TESTUVALKA_DATABASE_URL", f"sqlite:///{_default_db}")

# Ліміт часу на оцінювання в підпроцесі (п. 5.1). Тут він великий, бо на етапі
# розробки пул створюється на кожен запит і воркер холодно імпортує sympy
# (див. п. 5.8). У проді з довгоживучим теплим пулом це впаде до ~3 с.
GRADE_TIMEOUT: float = float(os.getenv("TESTUVALKA_GRADE_TIMEOUT", "15"))

# Токен доступу викладача до кабінету (CSV-журнал, сигнали аномалій). Якщо не
# заданий — кабінет вимкнено (краще 503, ніж відкритий доступ до оцінок).
TEACHER_TOKEN: str = os.getenv("TESTUVALKA_TEACHER_TOKEN", "")

# Шлях до YAML із тестами, який завантажується на старті застосунку (upsert).
# Зручно для хостингу без шелу: оновити тести = git push -> редеплой. Порожньо —
# нічого не вантажимо на старті (лишається лише демо-тест).
AUTOLOAD: str = os.getenv("TESTUVALKA_AUTOLOAD", "")
