"""Банк шаблонів задач по темах.

Кожен модуль теми реєструє свої шаблони через декоратор engine.template, тож
достатньо імпортувати його тут — і ключі стають доступними у build()/grade().
Додати тему = покласти поряд новий модуль і додати рядок import нижче.

Зразкові шаблони (linear_system_2x2, quadratic_roots, derivative_at_point)
лишаються в engine.py як приклад формату. Нові теми викладач додає сюди.

ВАЖЛИВО: цей пакет імпортується і в дочірньому процесі оцінювання (через
app.grading), тож усі шаблони банку зареєстровані й там — див. app/grading.py.
"""

from app.bank import algebra_lines  # noqa: F401
from app.bank import lecture1_linear_algebra  # noqa: F401
from app.bank import lecture2_lines  # noqa: F401
from app.bank import theme1_functions  # noqa: F401
from app.bank import lecture3_conics  # noqa: F401
from app.bank import theme2_powers_roots  # noqa: F401
from app.bank import integral1_antiderivative  # noqa: F401
