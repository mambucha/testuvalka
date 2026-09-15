"""Тема: рівняння прямої за двома точками (зразок додавання шаблону в банк).

Демонструє формат «кілька полів із проміжними результатами» + перенесення
помилки (carry): k -> b (з k) -> значення y (з k і b). Прийом як у брифі —
спершу задаємо цілу відповідь (k, b), потім із неї виводимо умову.
"""

from __future__ import annotations

import random

from engine import Part, Question, template


@template("line_through_two_points")
def _line_through_two_points(rng: random.Random) -> Question:
    # Спершу відповідь цілими: нахил k і вільний член b. Далі — дві точки з них.
    while True:
        k = rng.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5])
        b = rng.randint(-8, 8)
        x1, x2 = rng.randint(-6, 6), rng.randint(-6, 6)
        x0 = rng.randint(-6, 6)
        if x1 != x2:  # дві різні точки, інакше нахил невизначений
            break
    y1, y2 = k * x1 + b, k * x2 + b
    y0 = k * x0 + b

    def carry_b(prev):
        # b з ВЖЕ введеного студентом k: якщо k помилковий, b звіряємо з його логіки.
        kk = prev.get("k")
        return None if kk is None else y1 - kk * x1

    def carry_y(prev):
        kk, bb = prev.get("k"), prev.get("b")
        return None if kk is None or bb is None else kk * x0 + bb

    return Question(
        key="line_through_two_points",
        statement=(
            rf"Пряма проходить через точки $A({x1};\,{y1})$ і $B({x2};\,{y2})$." "\n"
            rf"Знайдіть кутовий коефіцієнт $k$, вільний член $b$ "
            rf"та значення $y$ у точці $x={x0}$."
        ),
        parts=[
            Part("k", "$k$ =", k, points=1),
            Part("b", "$b$ =", b, points=1, carry=carry_b, carry_from=("k",)),
            Part(
                "y0",
                rf"$y({x0})$ =",
                y0,
                points=1,
                carry=carry_y,
                carry_from=("k", "b"),
            ),
        ],
        seconds=90,
        params={"k": k, "b": b, "x1": x1, "y1": y1, "x2": x2, "y2": y2, "x0": x0},
    )
