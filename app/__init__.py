"""Пакет застосунку тестування (M1 — наскрізний цикл видачі й перевірки).

Ядро математики (engine.py) лежить у корені проєкту як окремий модуль верхнього
рівня. Гарантуємо, що корінь є в sys.path незалежно від того, звідки запущено
(uvicorn, pytest, скрипт), — тоді `import engine` працює завжди, зокрема й у
дочірньому процесі safe_grade (він наслідує sys.path батька при spawn).
"""

import sys as _sys
from pathlib import Path as _Path

_root = str(_Path(__file__).resolve().parent.parent)
if _root not in _sys.path:
    _sys.path.insert(0, _root)
