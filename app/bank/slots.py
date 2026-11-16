"""Механіка СЛОТІВ – спільна для всіх тематичних тестів.

Слот – це одне питання тесту, за яким стоїть не один шаблон, а кілька
рівноцінних з тієї самої теми. Котрий дістанеться студентові, вирішує його
власний HMAC-сид. Навіщо це потрібно і чому саме так, розказано в
app/bank/thematic.py – першому тесті на слотах; тут лише механіка.

ДВІ ВЛАСТИВОСТІ ЖЕРЕБУ, які не можна зламати (стережуть їх тести
test_probability_thematic і test_trig_thematic):
  * жереб СТАЛИЙ між перевиданнями питання. Перевидання за порушення
    доброчесності не карається балами й може повторюватися до 15 разів –
    якби воно перекидало жереб, вихід із вкладки став би безплатним
    виловлюванням найлегшої задачі слота. Тому жереб сіється без reissue:
    перевидання міняє числа, а задачу – ні;
  * нова СПРОБА перекидає і задачі, і числа (attempt_no входить у сид).
"""

import random

from engine import TEMPLATES, Question, build_context, seed_for, template


class SlotBank:
    """Набір слотів одного тесту: реєструє шаблони-слоти й пам'ятає склад."""

    def __init__(self) -> None:
        self.slots: dict[str, tuple[str, ...]] = {}
        self.bonus: dict[str, int] = {}

    def add(self, key: str, *candidates: str, bonus: int = 0) -> None:
        """Реєструє слот як звичайний шаблон, що пускає один із рівноцінних."""

        def build(rng: random.Random) -> Question:
            chosen = _pick(rng, candidates)
            q = TEMPLATES[chosen](rng)
            q.seconds += bonus
            # Ключем питання рушій поставить ключ слота (engine.build), тож
            # справжній шаблон лишаємо в параметрах: видно в журналі й у
            # розборі, яку саме задачу отримав студент.
            q.params = dict(q.params, shape=chosen)
            return q

        template(key)(build)
        self.slots[key] = candidates
        self.bonus[key] = bonus


def _pick(rng: random.Random, candidates: tuple[str, ...]) -> str:
    """Задача слота. Жереб сталий між перевиданнями – див. шапку модуля."""
    if len(candidates) == 1:
        return candidates[0]
    ctx = build_context()
    if ctx is None:  # шаблон покликали повз engine.build – поводимось як рушій
        return rng.choice(candidates)
    secret, student, test, key, attempt_no, _reissue = ctx
    picker = random.Random(seed_for(secret, student, test, key, attempt_no, 0))
    return picker.choice(candidates)
