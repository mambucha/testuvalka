"""Ймовірність і статистика: §14–§15 підручника Мерзляка (математика, 11 клас).

Обсяг:
  * §14 «Класичне визначення ймовірності випадкової події»: $P(A) = m/n$ над
    рівноможливими результатами, достовірна ($P = 1$) і неможлива ($P = 0$)
    події, подільність і заперечення на скінченній множині, ймовірність через
    комбінації (задача 3 з §14), обернена задача «дано ймовірність – знайти
    кількість» (вправи 14.17, 14.18);
  * §15 «Елементи математичної статистики»: генеральна сукупність і вибірка,
    розмах, середнє значення, медіана, мода; дані переліком, стовпчиковою
    діаграмою, таблицею частот і впорядкованою нечисловою шкалою.

Комбінаторика (§12–§13) – окрема тема, вона в app/bank/combinatorics.py. Тут
сполуки вживаються як ІНСТРУМЕНТ (у двох задачах на ймовірність), а не як
предмет: власних питань на перестановки й розміщення немає.

Репрезентативності вибірки серед питань немає свідомо: це суто словесне
міркування («опитування на концерті не показує популярності артиста»), а рушій
приймає лише число або вираз. Питання з відповіддю «так / ні» – це монетка, і
один біт коштував би стільки ж, скільки обчислена ймовірність.

Двох бітів усе ж не уникнути, бо такою є сама величина: медіана вибірки з
нулів та одиниць у st_scores і «чи можна тут обчислити середнє» в st_ordered.
Обидва захищені єдиним можливим способом – рівним розподілом: половина
варіантів кожного шаблону дає «так», половина «ні» (заміряно на 2000
варіантах: 50/50 в обох).

ЧОМУ ЦЕ СТІЙКЕ ДО СПИСУВАННЯ. Відповідь тут – число, тож захист тримається на
параметрах і на тому, що в полі має стояти не переписане з умови:
  * у кожного свої кількості, свої дільники, своя вибірка – на шаблон
    щонайменше 15 різних наборів відповідей (міряє
    test_many_variants_per_template);
  * кожна задача на 3–4 поля: один переписаний результат нічого не дає;
  * st_diagram узагалі не має чисел в умові – вони лише на рисунку;
  * вибірки в st_sample і st_population друкуються ПЕРЕМІШАНИМИ, тож ні
    медіана, ні мода не стоять на наперед відомому місці переліку;
  * у st_ordered ранги моди й медіани вибираються наперед, а частоти
    будуються під них – інакше медіана тулиться до середини шкали, а мода
    до країв, і обидві вгадуються, не рахуючи нічого;
  * побудова вибірок навмисне розводить розмах, середнє, медіану й моду –
    чотири різні числа, тож одне вгадане не підказує решти.

Нуль і одиниця як ЗНАЧЕННЯ ЙМОВІРНОСТІ є лише в pb_urn (неможлива й достовірна
події) – це саме та пара, яку означує §14. Стала «0» в усіх полях бере там
одне поле з чотирьох, стала «1» – теж одне.

ДРОБИ. Еталон ймовірності – sp.Rational, а рушій звіряє значення через
simplify, тож 5/33, 10/66 і 30/198 проходять однаково: скорочувати дріб
студент не зобов'язаний. Про це сказано в підказці до умови.
"""

from __future__ import annotations

import itertools
import math
import random

import sympy as sp

from engine import Part, Question, template

from app.bank.plotting import bar_chart

# Ймовірність – дріб, і зводити його до нескоротного ми не вимагаємо.
_HINT_P = ("(Ймовірність можна записати звичайним дробом 5/12, десятковим 0,25 "
           "або нескороченим виразом 10/24 – усе одно зарахується.)")
_HINT_N = ("(Відповідь – число. Можна й виразом, як набираєте: 6*5/2, "
           "12!/(9!*3!). Знак факторіала є на клавіатурі.)")
_HINT_NP = ("(Кількість можна писати виразом: 6*5/2, 12!/(9!*3!). Ймовірність – "
            "дробом 5/12 або 0,25; скорочувати дріб не обов'язково.)")
_HINT_M = ("(Середнє значення можна записати десятковим дробом 5,7 або "
           "звичайним 57/10.)")
_HINT_C = "(Усі чотири відповіді – цілі числа; медіана може бути від'ємною.)"


# --------------------------------------------------------------------------
# Перенесення помилки
# --------------------------------------------------------------------------

def _count(value):
    """Ціле додатне з попередньої відповіді або None, якщо переносити нічого."""
    if value is None or getattr(value, "free_symbols", set()):
        return None
    try:
        if value != int(value) or int(value) <= 0:
            return None
    except (TypeError, ValueError):
        return None
    return int(value)


def _honest(p):
    """Перерахований еталон годиться лише тоді, коли він не 0 і не 1.

    Інакше студент, який пише «0» або «1» в кожне поле, підтверджував би сам
    себе: і нуль, і одиниця є нерухомими точками будь-якого такого дробу.
    None означає «звіряти з початковим еталоном».
    """
    if p is None:
        return None
    try:
        if p == 0 or p == 1:
            return None
    except TypeError:
        return None
    return p


def _whole(value):
    """Кількість, перерахована з відповіді студента: мусить бути цілою й > 0."""
    try:
        if value <= 0 or value != int(value):
            return None
    except (TypeError, ValueError):
        return None
    return sp.Integer(int(value))


def _carry_ratio(num_key, den_key):
    """Ймовірність як частка ДВОХ своїх попередніх кількостей."""
    def _fn(prev):
        num, den = _count(prev.get(num_key)), _count(prev.get(den_key))
        if num is None or den is None:
            return None
        return _honest(sp.Rational(num, den))
    return _fn


def _carry_over(num, den_key):
    """Ймовірність зі СВОЇМ знаменником: чисельник правильний, n – студента."""
    def _fn(prev):
        den = _count(prev.get(den_key))
        return None if den is None else _honest(sp.Rational(num, den))
    return _fn


def _carry_share(num, den, key):
    """Частина від свого цілого: num/den від того, що студент назвав цілим."""
    def _fn(prev):
        whole = _count(prev.get(key))
        return None if whole is None else _whole(sp.Rational(num * whole, den))
    return _fn


def _carry_minus(key, minus):
    def _fn(prev):
        got = _count(prev.get(key))
        if got is None or got - minus == got:
            return None
        return _whole(got - minus)
    return _fn


def _carry_diff(whole_key, part_key):
    def _fn(prev):
        whole, part = _count(prev.get(whole_key)), _count(prev.get(part_key))
        if whole is None or part is None or whole == part:
            return None
        return _whole(whole - part)
    return _fn


def _carry_mean(total_key, n_key):
    """Середнє як «своя сума, поділена на своє n».

    Через _honest, бо інакше «1» у кожному полі брало б бал задарма: сума 1
    на обсяг 1 дає середнє 1, і студент підтверджував би сам себе. Виміряно –
    до цієї поправки стала «1» брала третину питання.
    """
    def _fn(prev):
        total, n = _count(prev.get(total_key)), _count(prev.get(n_key))
        if total is None or n is None:
            return None
        return _honest(sp.Rational(total, n))
    return _fn


# --------------------------------------------------------------------------
# Дрібні помічники
# --------------------------------------------------------------------------

def _agree(n: int, forms: tuple[str, str, str]) -> str:
    """Узгодження іменника з числівником: форми для 1, для 2-4 і для 5+.

    Свідома копія такого самого помічника з combinatorics.py: це чиста
    мовна дрібниця, і зв'язувати через неї два модулі банку не варто.
    """
    one, few, many = forms
    n10, n100 = n % 10, n % 100
    if n10 == 1 and n100 != 11:
        return one
    if n10 in (2, 3, 4) and n100 not in (12, 13, 14):
        return few
    return many


def _table(rows) -> str:
    """Таблиця у вигляді LaTeX-масиву: рядки вже готові списки клітинок.

    Дані §15 підручник подає саме таблицею, і це єдиний спосіб обійтися без
    узгодження числівників в умові: у клітинці стоїть число без іменника.
    Кирилиці всередині математики немає – шрифти KaTeX її не містять, тож
    підписи рядків ідуть текстом перед таблицею.
    """
    width = max(len(r) for r in rows)
    body = "".join(" & ".join(str(c) for c in r) + r"\\\hline " for r in rows)
    return r"$$\begin{array}{|" + "c|" * width + r"}\hline " + body + r"\end{array}$$"


def _split(rng: random.Random, total: int, k: int, lo: int = 1):
    """Випадкове розбиття total на k доданків, кожен не менший за lo."""
    free = total - k * lo
    if free < 0:
        return None
    cuts = sorted(rng.randint(0, free) for _ in range(k - 1))
    parts, prev = [], 0
    for cut in [*cuts, free]:
        parts.append(lo + cut - prev)
        prev = cut
    return parts


def _spread(rng: random.Random, total: int, slots: int, cap: int = 9):
    """Розкидати total одиниць по slots кошиках, не більше cap у кожен."""
    if slots <= 0:
        return [] if total == 0 else None
    if total > slots * cap:
        return None
    parts = [0] * slots
    for _ in range(total):
        free = [j for j in range(slots) if parts[j] < cap]
        parts[rng.choice(free)] += 1
    return parts


def _expand(labels, counts):
    """Таблиця частот -> сама вибірка (перелік значень)."""
    out = []
    for lab, c in zip(labels, counts):
        out.extend([lab] * c)
    return out


def _stats(sample):
    """Розмах, середнє, медіана, мода вибірки – прямо за означеннями §15.

    Медіана повертається лише там, де вона однозначна: для парної кількості
    даних підручник дозволяє брати будь-яке з двох середніх (а для чисел – ще
    й їхню півсуму), тож усі вибірки в банку будуються так, щоб ці два числа
    збігалися. Мода – лише якщо вона одна.
    """
    s = sorted(sample)
    n = len(s)
    if n % 2:
        mid = s[n // 2]
    else:
        mid = s[n // 2] if s[n // 2 - 1] == s[n // 2] else None
    freq = {v: s.count(v) for v in set(s)}
    top = max(freq.values())
    modes = [v for v, f in freq.items() if f == top]
    return {
        "range": s[-1] - s[0],
        "mean": sp.Rational(sum(s), n),
        "median": mid,
        "mode": modes[0] if len(modes) == 1 else None,
        "n": n,
    }


def _ranked_stats(labels, counts):
    """Обсяг, мода й медіана для даних, які лише ПОРІВНЮЮТЬСЯ між собою.

    labels подані в порядку зростання; самі значення числами бути не мусять
    (розміри одягу), тож ні розмаху, ні середнього тут не існує.
    """
    n = sum(counts)
    data = _expand(labels, counts)
    median = data[n // 2] if n % 2 else None
    top = max(counts)
    modes = [lab for lab, c in zip(labels, counts) if c == top]
    return n, (modes[0] if len(modes) == 1 else None), median


def _all_different(values) -> bool:
    """Усі показники різні – інакше вгадане одне поле дає й інші."""
    vals = [v for v in values if v is not None]
    return len(vals) == len(values) == len(set(vals))


# =========================================================================
#  §14. КЛАСИЧНЕ ВИЗНАЧЕННЯ ЙМОВІРНОСТІ ВИПАДКОВОЇ ПОДІЇ
# =========================================================================

# (родовий множини – для переліку, знахідний однини – для умови,
#  родовий однини – для підпису поля)
_COLOURS = [("синіх", "синю", "синьої"), ("жовтих", "жовту", "жовтої"),
            ("червоних", "червону", "червоної"),
            ("зелених", "зелену", "зеленої"), ("білих", "білу", "білої"),
            ("чорних", "чорну", "чорної")]


@template("pb_urn")
def _urn(rng: random.Random) -> Question:
    """Означення $P = m/n$ плюс достовірна й неможлива події (вправа 14.3).

    Саме тут живуть єдині в тесті відповіді «0» і «1»: §14 означує неможливу
    й достовірну події через них, і перевірити це інакше, ніж спитавши саму
    ймовірність, не вийде. Решта двох полів – звичайні обчислення, тож стала
    відповідь бере щонайбільше одне поле з чотирьох.
    """
    present = rng.sample(_COLOURS, 3)
    absent = rng.choice([c for c in _COLOURS if c not in present])
    counts = rng.sample(range(3, 15), 3)
    total = sum(counts)
    pick = rng.randrange(3)
    chance = sp.Rational(counts[pick], total)

    listing = ", ".join(f"{name[0]} – ${c}$" for name, c in zip(present, counts))
    return Question(
        key="pb_urn",
        statement=(
            f"У коробці лежать кульки: {listing}. З коробки навмання виймають "
            "одну кульку."
            + "\n1) Скільки всього рівноможливих результатів має це випробування?"
            + f"\n2) Яка ймовірність вийняти {present[pick][1]} кульку?"
            + f"\n3) Яка ймовірність вийняти {absent[1]} кульку?"
            + "\n4) Яка ймовірність вийняти кульку одного з трьох кольорів, "
            "що є в коробці?"
            + "\n" + _HINT_P
        ),
        parts=[
            Part("total", "1) рівноможливих результатів:", sp.Integer(total),
                 points=1),
            Part("chance", f"2) ймовірність {present[pick][2]}:", chance, points=1,
                 carry=_carry_over(counts[pick], "total"), carry_from=("total",)),
            Part("never", f"3) ймовірність {absent[2]}:", sp.Integer(0), points=1),
            Part("sure", "4) ймовірність одного з трьох кольорів:",
                 sp.Integer(1), points=1),
        ],
        seconds=120,
        params={"counts": counts, "pick": pick,
                "present": [c[0] for c in present], "absent": absent[0]},
    )


@template("pb_cards")
def _cards(rng: random.Random) -> Question:
    """Подільність і заперечення на множині $1..N$ (вправи 14.6, 14.9, 14.10).

    Третій пункт – завдання 11 із «Перевірте себе»: «не ділиться ні на d, ні
    на e». Усі три кількості шаблон рахує ПЕРЕБОРОМ діапазону, а не формулою
    включень і виключень, тож помилка у формулі не може підтвердити сама себе.
    """
    while True:
        n = rng.randint(12, 25)
        d, e = rng.sample([2, 3, 4, 5, 6], 2)
        nums = range(1, n + 1)
        m_d = sum(1 for k in nums if k % d == 0)
        m_e = sum(1 for k in nums if k % e == 0)
        m_no = sum(1 for k in nums if k % d and k % e)
        probs = [sp.Rational(m_d, n), sp.Rational(n - m_e, n),
                 sp.Rational(m_no, n)]
        if all(0 < p < 1 for p in probs) and len(set(probs)) == 3:
            break

    return Question(
        key="pb_cards",
        statement=(
            rf"На ${n}$ картках записано натуральні числа від $1$ до ${n}$ "
            "(на кожній картці – одне число). Картку вибирають навмання."
            + "\n" + rf"1) Яка ймовірність того, що число на картці кратне ${d}$?"
            + "\n" + rf"2) Яка ймовірність того, що число на картці НЕ кратне ${e}$?"
            + "\n" + rf"3) Яка ймовірність того, що число на картці не ділиться "
            rf"націло ні на ${d}$, ні на ${e}$?"
            + "\n" + _HINT_P
        ),
        parts=[
            Part("mult", rf"1) кратне ${d}$:", probs[0], points=1),
            Part("notmult", rf"2) не кратне ${e}$:", probs[1], points=1),
            Part("neither", rf"3) ні на ${d}$, ні на ${e}$:", probs[2], points=1),
        ],
        seconds=160,
        params={"n": n, "d": d, "e": e},
    )


# (умова з {n} і {m}, назва предметів у множині, ознака в множині)
_ALL_KIND = [
    ("На полиці лежать зошити: усього ${n}$, з них у клітинку – ${m}$.",
     "зошити", "у клітинку"),
    ("У колекції Андрія є монети різних країн: усього ${n}$, з них "
     "українських – ${m}$.", "монети", "українські"),
    ("Для лотереї підготували білети: усього ${n}$, з них виграшних – ${m}$.",
     "білети", "виграшні"),
]


@template("pb_all_of_kind")
def _all_of_kind(rng: random.Random) -> Question:
    """Ймовірність через комбінації: ВСІ вибрані предмети – одного виду.

    Це задача 3 з §14 і вправи 14.13, 14.14, 14.16 – єдиний шлях, який
    підручник показує для вибору кількох предметів одразу: поділити кількість
    сприятливих вибірок на кількість усіх. Тому обидві кількості стоять
    окремими полями, а ймовірність переноситься як їхня частка.
    """
    while True:
        n = rng.randint(10, 18)
        m = rng.randint(4, 8)
        k = rng.choice([2, 3])
        if m + 2 > n or m < k:
            continue
        total, good = math.comb(n, k), math.comb(m, k)
        chance = sp.Rational(good, total)
        if 0 < chance < sp.Rational(1, 2):
            break
    head, plural, kind = _ALL_KIND[rng.randrange(len(_ALL_KIND))]
    head = head.format(n=n, m=m)

    return Question(
        key="pb_all_of_kind",
        statement=(
            head + rf" Навмання беруть ${k}$ з них."
            + "\n" + rf"1) Скількома способами можна вибрати ${k}$ з ${n}$?"
            + "\n" + rf"2) Скількома способами можна вибрати ${k}$ так, щоб "
            f"усі вони були {kind}?"
            + "\n" + rf"3) Яка ймовірність того, що всі ${k}$ вибрані {plural} "
            f"будуть {kind}?"
            + "\n" + _HINT_NP
        ),
        parts=[
            Part("total", rf"1) усіх способів вибрати ${k}$:", sp.Integer(total),
                 points=1),
            Part("good", f"2) з них усі {kind}:", sp.Integer(good),
                 points=1),
            Part("chance", "3) ймовірність:", chance, points=1,
                 carry=_carry_ratio("good", "total"),
                 carry_from=("total", "good")),
        ],
        seconds=150,
        params={"n": n, "m": m, "k": k, "context": kind},
    )


@template("pb_exactly")
def _exactly(rng: random.Random) -> Question:
    """РІВНО $a$ куль одного кольору серед вибраних (вправа 14.15).

    Відрізняється від pb_all_of_kind тим, що сприятливу вибірку треба
    розкласти на дві незалежні: $a$ з жовтих І решту з синіх. Хто взяв у
    сусіда готове число, не знає, звідки воно, – і на наступному кроці
    ділить не на те.
    """
    while True:
        y, b = rng.randint(4, 8), rng.randint(3, 7)
        s = rng.choice([3, 4])
        a = rng.randint(1, s - 1)
        if a > y or s - a > b:
            continue
        total = math.comb(y + b, s)
        good = math.comb(y, a) * math.comb(b, s - a)
        chance = sp.Rational(good, total)
        if 0 < chance < 1 and total > 20:
            break

    balls = _agree(s, ("кулю", "кулі", "куль"))
    yellow = _agree(a, ("жовта куля", "жовті кулі", "жовтих куль"))
    return Question(
        key="pb_exactly",
        statement=(
            rf"У ящику лежать кулі: жовтих – ${y}$, синіх – ${b}$. Навмання "
            rf"виймають ${s}$ {balls}."
            + "\n" + rf"1) Скількома способами можна вибрати ${s}$ {balls} "
            "з ящика?"
            + "\n" + rf"2) Скількома способами можна це зробити так, щоб жовтих "
            rf"серед вибраних було РІВНО ${a}$?"
            + "\n" + rf"3) Яка ймовірність того, що серед вийнятих куль буде "
            rf"рівно ${a}$ {yellow}?"
            + "\n" + _HINT_NP
        ),
        parts=[
            Part("total", rf"1) усіх способів вибрати ${s}$:", sp.Integer(total),
                 points=1),
            Part("good", rf"2) з них жовтих рівно ${a}$:", sp.Integer(good),
                 points=1),
            Part("chance", "3) ймовірність:", chance, points=1,
                 carry=_carry_ratio("good", "total"),
                 carry_from=("total", "good")),
        ],
        seconds=180,
        params={"y": y, "b": b, "s": s, "a": a},
    )


@template("pb_pair_parity")
def _pair_parity(rng: random.Random) -> Question:
    """Парність добутку й суми двох карток (завдання 12 із «Перевірте себе»).

    Обидві ймовірності шаблон рахує перебором усіх пар, а не формулою: набір
    малий, перебір миттєвий і не залежить від того, чи правильно виведено
    $C_n^2$.

    Питають то про парний, то про непарний випадок – і для добутку, і для
    суми. Самого лише $n$ було б замало: сімох значень на весь потік не
    хватає, а так варіантів учетверо більше.
    """
    while True:
        n = rng.randint(6, 20)
        prod_odd = rng.random() < 0.5         # добуток: непарний чи парний
        sum_even = rng.random() < 0.5         # сума: парна чи непарна
        pairs = list(itertools.combinations(range(1, n + 1), 2))
        total = len(pairs)
        m_prod = sum(1 for u, v in pairs if ((u * v) % 2 == 1) == prod_odd)
        m_sum = sum(1 for u, v in pairs if ((u + v) % 2 == 0) == sum_even)
        probs = [sp.Rational(m_prod, total), sp.Rational(m_sum, total)]
        if all(0 < p < 1 for p in probs) and probs[0] != probs[1]:
            break

    prod_word = "НЕПАРНИЙ" if prod_odd else "ПАРНИЙ"
    sum_word = "ПАРНА" if sum_even else "НЕПАРНА"
    return Question(
        key="pb_pair_parity",
        statement=(
            rf"На ${n}$ картках записано натуральні числа від $1$ до ${n}$. "
            "Навмання беруть дві картки (порядок не має значення)."
            + "\n" + rf"1) Скількома способами можна вибрати дві картки з ${n}$?"
            + f"\n2) Яка ймовірність того, що добуток двох вибраних чисел – "
            f"{prod_word}?"
            + f"\n3) Яка ймовірність того, що сума двох вибраних чисел – "
            f"{sum_word}?"
            + "\n" + _HINT_P
        ),
        parts=[
            Part("pairs", "1) усіх пар:", sp.Integer(total), points=1),
            Part("prod", f"2) добуток {prod_word.lower()}:", probs[0], points=1,
                 carry=_carry_over(m_prod, "pairs"), carry_from=("pairs",)),
            Part("summa", f"3) сума {sum_word.lower()}:", probs[1], points=1,
                 carry=_carry_over(m_sum, "pairs"), carry_from=("pairs",)),
        ],
        seconds=170,
        params={"n": n, "prod_odd": bool(prod_odd), "sum_even": bool(sum_even)},
    )


# (умова, предмет в однині, численніші в родовому, менш численні в родовому,
#  як спитати про загальну кількість)
_INVERSE = [
    ("У шухляді лежать лише олівці та ручки", "ручка", "ручок", "олівців",
     "предметів лежить у шухляді"),
    ("У подарунковому комплекті є лише зелені та червоні кулі",
     "зелена куля", "зелених куль", "червоних куль", "куль у комплекті"),
    ("У вазі стоять лише тюльпани та троянди", "тюльпан", "тюльпанів",
     "троянд", "квітів стоїть у вазі"),
]


@template("pb_inverse")
def _inverse(rng: random.Random) -> Question:
    """ОБЕРНЕНА задача: дано ймовірність – знайти кількості (14.17, 14.18).

    Найсильніше питання тесту на розуміння означення. Формулу $m/n$ тут не
    застосуєш «вперед»: невідомі і $m$, і $n$, а дано лише їхнє відношення та
    різницю двох частин. Переписувати з умови нічого – в умові є дріб і
    різниця, а в полях стоять три кількості.
    """
    while True:
        den = rng.randint(5, 12)
        num = rng.randint(den // 2 + 1, den - 1)   # більшість -> ймовірність > 1/2
        if math.gcd(num, den) != 1:
            continue
        t = rng.randint(1, 4)
        total = den * t
        more, less = num * t, (den - num) * t
        diff = more - less
        if less >= 2 and diff >= 2 and total <= 72:
            break
    head, one, many_more, many_less, whole = _INVERSE[rng.randrange(len(_INVERSE))]

    return Question(
        key="pb_inverse",
        statement=(
            f"{head}. {many_less.capitalize()} на ${diff}$ менше, ніж "
            f"{many_more}. Ймовірність того, що вибране навмання – "
            rf"це {one}, дорівнює $\dfrac{{{num}}}{{{den}}}$."
            + f"\n1) Скільки всього {whole}?"
            + f"\n2) Скільки {many_more}?"
            + f"\n3) Скільки {many_less}?"
            + "\n" + _HINT_N
        ),
        parts=[
            Part("total", "1) усього:", sp.Integer(total), points=1),
            Part("more", f"2) {many_more}:", sp.Integer(more), points=1,
                 carry=_carry_share(num, den, "total"), carry_from=("total",)),
            Part("less", f"3) {many_less}:", sp.Integer(less), points=1,
                 carry=_carry_diff("total", "more"),
                 carry_from=("total", "more")),
        ],
        seconds=170,
        params={"num": num, "den": den, "t": t, "diff": diff},
    )


# =========================================================================
#  §15. ЕЛЕМЕНТИ МАТЕМАТИЧНОЇ СТАТИСТИКИ
# =========================================================================

@template("st_sample")
def _sample(rng: random.Random) -> Question:
    """Чотири показники вибірки, заданої переліком (вправи 15.5, 15.6, 15.8).

    Вибірка будується так, щоб усі чотири відповіді були РІЗНИМИ числами, а
    розмах і середнє ще й не траплялися серед самих даних: інакше вгадане одне
    поле підказувало б решту, а переписане з умови число могло б випадково
    зійтися з розмахом.

    Перелік друкується ПЕРЕМІШАНИМ – упорядкувати його і є перший крок роботи.
    Два середні за порядком числа навмисне однакові, тож медіана однозначна за
    будь-яким з означень, які §15 допускає для парної кількості даних.

    Чисел саме ДВАНАДЦЯТЬ, а не десять: мода трапляється тричі, тож на десяти
    числах правило «перепиши k-те число умови» вгадувало б її в 30% варіантів
    (заміряно 42% на найкращій позиції). На дванадцяти це 25%. Сума при цьому
    кратна шести, тож середнє – «ціле з половиною», а не періодичний дріб.
    """
    for _ in range(4000):
        mo = rng.randint(3, 18)                 # мода: трапляється тричі
        me = rng.randint(3, 18)                 # медіана: двічі, посередині
        if me == mo:
            continue
        # щоб медіана стала на 6-7 місце, нижче за неї має бути рівно 5 чисел
        below = 2 if mo < me else 5
        pool_lo = [v for v in range(2, me) if v != mo]
        pool_hi = [v for v in range(me + 1, 21) if v != mo]
        if len(pool_lo) < below or len(pool_hi) < 7 - below:
            continue
        data = ([mo] * 3 + [me] * 2 + rng.sample(pool_lo, below)
                + rng.sample(pool_hi, 7 - below))
        if sum(data) % 6:
            continue
        st = _stats(data)
        if st["median"] != me or st["mode"] != mo:
            continue
        if not _all_different([st["range"], st["mean"], st["median"],
                               st["mode"]]):
            continue
        if st["range"] in data or st["mean"] in data:
            continue
        break
    else:                                       # запас: до нього не доходить
        data = [4, 4, 4, 6, 7, 9, 9, 11, 13, 14, 16, 17]
        st = _stats(data)

    shown = data[:]
    rng.shuffle(shown)
    return Question(
        key="st_sample",
        statement=(
            "Дано вибірку: $" + ",\\ ".join(str(v) for v in shown) + "$."
            + "\n1) Знайдіть розмах вибірки."
            + "\n2) Знайдіть середнє значення вибірки."
            + "\n3) Знайдіть медіану вибірки."
            + "\n4) Знайдіть моду вибірки."
            + "\n" + _HINT_M
        ),
        parts=[
            Part("range", "1) розмах:", sp.Integer(st["range"]), points=1),
            Part("mean", "2) середнє значення:", st["mean"], points=1),
            Part("median", "3) медіана:", sp.Integer(st["median"]), points=1),
            Part("mode", "4) мода:", sp.Integer(st["mode"]), points=1),
        ],
        seconds=150,
        params={"data": sorted(data), "shown": shown},
    )


# (умова, підпис осі Ox, підпис осі Oy)
_DIAGRAM = [
    ("Школярів опитали, скільки книжок кожен з них прочитав за місяць. "
     "Результати – на діаграмі.", "книжок прочитано", "школярів"),
    ("Телефонна компанія дізнавалася, скільки дзвінків людина робить за добу. "
     "Результати опитування – на діаграмі.", "дзвінків за добу", "опитаних"),
    ("Тренер записував, скільки голів команда забивала в матчі. "
     "Результати – на діаграмі.", "голів у матчі", "матчів"),
]


@template("st_diagram")
def _diagram(rng: random.Random) -> Question:
    """Ті самі показники, але дані є ЛИШЕ на стовпчиковій діаграмі (15.14, 15.15).

    Найстійкіше до списування питання тесту: в умові немає жодного числа, тож
    переписувати з тексту нічого. Обсяг вибірки теж треба знайти самому –
    додати всі стовпчики; у підручнику він надрукований, і саме тому його
    зазвичай пропускають.

    Обсяг вибірки НЕПАРНИЙ – тоді медіана однозначна без жодних домовленостей.
    Нульові стовпчики всередині лишаються навмисне: розмах рахується за
    значеннями, які СПРАВДІ трапилися, а не за краями осі.
    """
    for _ in range(4000):
        top = rng.choice([5, 6, 7])                   # значення 0..top
        labels = list(range(top + 1))
        counts = [rng.randint(0, 8) for _ in labels]
        n = sum(counts)
        if n % 2 == 0 or not 17 <= n <= 31:
            continue
        if sum(1 for c in counts if c) < 4:
            continue
        st = _stats(_expand(labels, counts))
        if st["mode"] is None:
            continue
        if not _all_different([st["range"], st["median"], st["mode"], st["n"]]):
            continue
        break
    else:
        labels, counts = [0, 1, 2, 3, 4, 5], [1, 3, 7, 4, 2, 2]
        st = _stats(_expand(labels, counts))

    head, xlabel, ylabel = _DIAGRAM[rng.randrange(len(_DIAGRAM))]
    return Question(
        key="st_diagram",
        statement=(
            head
            + "\n1) Який обсяг вибірки, тобто скільки всього даних зібрано?"
            + "\n2) Знайдіть розмах вибірки."
            + "\n3) Знайдіть моду вибірки."
            + "\n4) Знайдіть медіану вибірки."
        ),
        parts=[
            Part("n", "1) обсяг вибірки:", sp.Integer(st["n"]), points=1),
            Part("range", "2) розмах:", sp.Integer(st["range"]), points=1),
            Part("mode", "3) мода:", sp.Integer(st["mode"]), points=1),
            Part("median", "4) медіана:", sp.Integer(st["median"]), points=1),
        ],
        seconds=160,
        params={"labels": labels, "counts": counts},
        svg=bar_chart(labels, counts, xlabel=xlabel, ylabel=ylabel),
    )


# (умова з поясненням рядків таблиці, три питання, діапазон значень)
# Діапазон залежить від контексту: нуль голів у матчі – звичайна річ і навіть
# корисна (такий матч додає до обсягу вибірки, але не до суми), а оцінки «0»
# у дванадцятибальній системі не існує.
_FREQ = [
    ("Команда провела кілька матчів. У верхньому рядку таблиці – скільки "
     "голів забито в матчі, у нижньому – у скількох матчах це сталося.",
     "Скільки всього матчів провела команда?",
     "Скільки всього голів забито в цих матчах?",
     "Яка середня кількість голів за один матч?",
     range(0, 7)),
    ("Студентка отримала за семестр кілька оцінок. У верхньому рядку "
     "таблиці – оцінка, у нижньому – скільки разів вона її отримала.",
     "Скільки всього оцінок отримала студентка?",
     "Яка сума всіх її балів?",
     "Який її середній бал?",
     range(4, 13)),
]


@template("st_frequency")
def _frequency(rng: random.Random) -> Question:
    """Середнє значення за таблицею частот (вправи 15.11, 15.12).

    Головна помилка тут – поділити суму значень на кількість РІЗНИХ значень, а
    не на обсяг вибірки. Тому обсяг і сума стоять окремими полями, а середнє
    переноситься саме як частка цих двох своїх чисел: хто поділив не на те,
    втратить одне поле, а не три.

    Загальної кількості в умові НЕМА (у підручнику вона надрукована) – це
    перше, що треба обчислити. Середнє навмисне не ціле: ціле означало б, що
    його можна вгадати, дивлячись на значення.
    """
    head, ask1, ask2, ask3, scale = _FREQ[rng.randrange(len(_FREQ))]
    for _ in range(3000):
        k = rng.choice([4, 5])
        values = sorted(rng.sample(list(scale), k), reverse=True)
        freqs = [rng.randint(2, 11) for _ in values]
        n, total = sum(freqs), sum(v * f for v, f in zip(values, freqs))
        if not 14 <= n <= 36 or total == 0:
            continue
        if (100 * total) % n:                   # середнє – не більше двох знаків
            continue
        mean = sp.Rational(total, n)
        if mean == int(mean) or mean in values or mean in (n, total):
            continue
        break
    else:
        values, freqs = [5, 4, 3, 2], [2, 3, 9, 6]
        n, total = sum(freqs), sum(v * f for v, f in zip(values, freqs))
        mean = sp.Rational(total, n)
    return Question(
        key="st_frequency",
        statement=(
            head + "\n" + _table([values, freqs])
            + f"\n1) {ask1}"
            + f"\n2) {ask2}"
            + f"\n3) {ask3}"
            + "\n" + _HINT_M
        ),
        parts=[
            Part("n", "1) обсяг вибірки:", sp.Integer(n), points=1),
            Part("total", "2) сума всіх значень:", sp.Integer(total), points=1),
            Part("mean", "3) середнє значення:", mean, points=1,
                 carry=_carry_mean("total", "n"), carry_from=("n", "total")),
        ],
        seconds=140,
        params={"values": values, "freqs": freqs},
    )


_SIZES = ["XS", "S", "M", "L", "XL", "XXL", "XXXL"]


@template("st_ordered")
def _ordered(rng: random.Random) -> Question:
    """Які показники взагалі можна визначити (вправи 15.3, 15.4).

    §15 прямо каже: «середнє значення вибірки визначають лише у випадку, коли
    зібраними даними є числа», – а медіану й моду можна знайти і для даних, які
    між собою лише ПОРІВНЮЮТЬСЯ (приклад підручника – оцінки A..F).

    Половина варіантів нечислова (розміри одягу), половина числова (розміри
    взуття). Відповідь на четвертий пункт – один біт, і без цього поділу стала
    відповідь брала б його завжди; тепер – рівно в половині варіантів.
    """
    numeric = rng.random() < 0.5
    k = rng.choice([6, 7])
    if numeric:
        first = rng.choice([35, 36, 37, 38])
        labels = [first + i for i in range(k)]
    else:
        start = rng.randrange(0, len(_SIZES) - k + 1)
        labels = _SIZES[start:start + k]
    # Ранг медіани вибираємо САМІ – і то ДО циклу, щоб відкинуті спроби не
    # перетягували його назад до середини. Якщо просто кидати частоти навмання,
    # медіана тулиться до середини шкали: було заміряно 38% на найчастіший
    # ранг, тобто правило «пиши середній розмір» працювало б майже в кожному
    # третьому варіанті. Краї шкали недосяжні з іншої причини: якщо медіана –
    # перша категорія, то в ній лежить більш як половина даних, і вона ж буде
    # модою, – а мода й медіана тут мусять різнитися.
    middle = rng.randint(1, k - 2)
    # Так само наперед вибираємо й ранг моди. Інакше його тягне на краї шкали:
    # коли медіана друга з краю, уся вага одного боку лежить в одному кошику,
    # він і стає модою – заміряно 35% на перший розмір.
    mode_at = rng.choice([j for j in range(k) if j != middle])
    lo_slots, hi_slots = middle, k - 1 - middle
    for _ in range(6000):
        c_mid = rng.randint(2, 5)
        c_mode = rng.randint(c_mid + 1, 9)
        cap = c_mode - 1                        # решта мусить бути меншою за моду
        # Медіана стоїть у «middle» тоді й лише тоді, коли дані ліворуч і
        # праворуч від нього різняться менш ніж на c_mid. Той бік, де лежить
        # мода, набираємо першим, а другий підгонятимо під нього.
        if mode_at < middle:
            lo = _spread(rng, rng.randint(0, cap * (lo_slots - 1)),
                         lo_slots - 1, cap)
            if lo is None:
                continue
            lo.insert(mode_at, c_mode)
            below = sum(lo)
            above = rng.randint(max(0, below - c_mid + 1), below + c_mid - 1)
            hi = _spread(rng, above, hi_slots, cap)
        else:
            hi = _spread(rng, rng.randint(0, cap * (hi_slots - 1)),
                         hi_slots - 1, cap)
            if hi is None:
                continue
            hi.insert(mode_at - middle - 1, c_mode)
            above = sum(hi)
            below = rng.randint(max(0, above - c_mid + 1), above + c_mid - 1)
            lo = _spread(rng, below, lo_slots, cap)
        if lo is None or hi is None:
            continue
        counts = [*lo, c_mid, *hi]
        n = sum(counts)
        if n % 2 == 0 or not 13 <= n <= 35:
            continue
        if sum(1 for c in counts if c) < 5:     # суцільні нулі в таблиці дивні
            continue
        n, mode, median = _ranked_stats(labels, counts)
        if mode is None or mode == median:
            continue
        # побудова мусить збігтися з тим, що насправді вийшло
        if labels.index(median) != middle or labels.index(mode) != mode_at:
            continue
        break
    else:
        numeric, labels = True, [36, 37, 38, 39, 40, 41]
        counts = [4, 3, 9, 5, 2, 2]
        n, mode, median = _ranked_stats(labels, counts)

    if numeric:
        head = ("Магазин записав, скільки пар взуття кожного розміру продано за "
                "тиждень. У верхньому рядку таблиці – розмір, у нижньому – "
                "скільки пар продано.")
        table = _table([labels, counts])
        how = "У пунктах 2) і 3) запишіть сам розмір."
        mode_ans, median_ans = mode, median
    else:
        head = ("Ательє записало, скільки одиниць одягу кожного розміру продано "
                "за тиждень. У рядках таблиці – розмір, його номер за "
                "зростанням і скільки одиниць продано.")
        table = _table([[rf"\mathrm{{{lab}}}" for lab in labels],
                        list(range(1, len(labels) + 1)), counts])
        how = ("У пунктах 2) і 3) запишіть НОМЕР розміру з таблиці: сам розмір "
               "числом не є, нумерація потрібна лише для того, щоб записати "
               "відповідь.")
        mode_ans = labels.index(mode) + 1
        median_ans = labels.index(median) + 1

    return Question(
        key="st_ordered",
        statement=(
            head + "\n" + table
            + "\n1) Який обсяг вибірки?"
            + "\n2) Знайдіть моду вибірки."
            + "\n3) Знайдіть медіану вибірки."
            + "\n4) Чи можна для цих даних обчислити СЕРЕДНЄ значення? "
            "Запишіть $1$, якщо можна, і $0$, якщо ні."
            + "\n" + how
        ),
        parts=[
            Part("n", "1) обсяг вибірки:", sp.Integer(n), points=1),
            Part("mode", "2) мода:", sp.Integer(mode_ans), points=1),
            Part("median", "3) медіана:", sp.Integer(median_ans), points=1),
            Part("mean_ok", "4) середнє можна обчислити ($1$ / $0$):",
                 sp.Integer(1 if numeric else 0), points=1),
        ],
        seconds=150,
        params={"numeric": bool(numeric), "labels": [str(x) for x in labels],
                "counts": counts},
    )


_LETTERS = ["А", "Б", "В", "Г", "Д"]


@template("st_scores")
def _scores(rng: random.Random) -> Question:
    """Вибірка з нулів та одиниць: мода, середнє й медіана балів (вправа 15.13).

    Задача з ЗНО 2018, що стоїть у підручнику. Тут видно те, чого з означення
    не видно: середнє значення вибірки з нулів та одиниць – це просто частка
    правильних відповідей, а медіана дорівнює $0$, коли правильно відповіли
    менше за половину, і $1$, коли більше.

    Половина варіантів – з правильною відповіддю в більшості (тоді мода
    відповідей збігається з правильною, а медіана балів дорівнює $1$),
    половина – без (мода припадає на хибний варіант, медіана $0$). Тож стала
    відповідь у третьому пункті правильна рівно в половині випадків.
    """
    majority = rng.random() < 0.5
    for _ in range(3000):
        if majority:
            right = rng.randint(52, 72)
            rest = _split(rng, 100 - right, 4, lo=3)
            if rest is None or max(rest) >= right:
                continue
            percents, correct = [right, *rest], 0
        else:
            best = rng.randint(28, 44)
            right = rng.randint(8, best - 4)
            rest = _split(rng, 100 - best - right, 3, lo=3)
            if rest is None or max(rest) >= best:
                continue
            percents, correct = [best, right, *rest], 1
        order = list(range(5))
        rng.shuffle(order)
        percents = [percents[i] for i in order]
        correct = order.index(correct)
        if sorted(percents)[-1] == sorted(percents)[-2]:   # мода мусить бути одна
            continue
        break
    else:
        percents, correct, majority = [39, 31, 10, 14, 6], 1, False

    mode_idx = percents.index(max(percents)) + 1
    share = sp.Rational(percents[correct], 100)
    median = sp.Integer(1 if percents[correct] > 50 else 0)
    rows = ", ".join(f"{lab} – ${p}$ %" for lab, p in zip(_LETTERS, percents))
    return Question(
        key="st_scores",
        statement=(
            "Завдання тесту мало п'ять варіантів відповіді: А, Б, В, Г, Д. "
            f"Учні розподілилися так: {rows}. Правильна відповідь – "
            f"{_LETTERS[correct]}. За правильну відповідь нараховували $1$ бал, "
            "за неправильну – $0$ балів."
            + "\n1) Який варіант відповіді є модою? Запишіть його номер "
            "(А – $1$, Б – $2$, В – $3$, Г – $4$, Д – $5$)."
            + "\n2) Яке середнє значення набраних за це завдання балів?"
            + "\n3) Яка медіана набраних за це завдання балів?"
            + "\n" + _HINT_M
        ),
        parts=[
            Part("mode", "1) номер варіанта-моди:", sp.Integer(mode_idx),
                 points=1),
            Part("mean", "2) середнє значення балів:", share, points=1),
            Part("median", "3) медіана балів:", median, points=1),
        ],
        seconds=150,
        params={"percents": percents, "correct": correct,
                "majority": bool(majority)},
    )


@template("st_population")
def _population(rng: random.Random) -> Question:
    """Генеральна сукупність ПРОТИ вибірки (вправа 15.2).

    Те, що плутають найчастіше: обсяг генеральної сукупності – це скільки
    результатів МОЖЕ бути, а не скільки їх зібрано. Поруч стоять обсяг і
    розмах генеральної сукупності – вони відрізняються рівно на одиницю, і
    саме ця одиниця показує, чи розуміє студент, що він рахує.

    Числа вибірки різнозначні, як у підручнику, – медіану не знайдеш, не
    впорядкувавши їх, а від'ємні числа цьому найкраще й заважають.
    """
    for _ in range(3000):
        lo = rng.choice([-128, -100, -75, -50, -30, -20, -10])
        hi = rng.choice([40, 50, 64, 75, 90, 100, 128, 150, 200])
        span = hi - lo
        sample = rng.sample(range(lo, hi + 1), 5)
        mid = sorted(sample)[2]
        spread = max(sample) - min(sample)
        if spread < 20 or spread >= span:
            continue
        if not _all_different([span + 1, span, spread, mid]):
            continue
        if spread in sample:
            continue
        if min(sample) >= 0 or max(sample) <= 0:   # хай будуть обидва знаки
            continue
        break
    else:
        lo, hi, sample = -128, 128, [62, -15, 31, 103, -22]
        span, spread, mid = 256, 125, 31

    return Question(
        key="st_population",
        statement=(
            rf"Комп'ютерна програма видає випадкове ціле число від ${lo}$ до "
            rf"${hi}$ (включно). Після п'яти запусків отримано такі числа: $"
            + ",\\ ".join(str(v) for v in sample) + "$."
            + "\n1) Який обсяг генеральної сукупності, тобто скільки різних "
            "чисел узагалі може видати програма?"
            + "\n2) Чому дорівнює розмах генеральної сукупності?"
            + "\n3) Чому дорівнює розмах вибірки?"
            + "\n4) Чому дорівнює медіана вибірки?"
            + "\n" + _HINT_C
        ),
        parts=[
            Part("population", "1) обсяг генеральної сукупності:",
                 sp.Integer(span + 1), points=1),
            Part("span", "2) розмах генеральної сукупності:", sp.Integer(span),
                 points=1, carry=_carry_minus("population", 1),
                 carry_from=("population",)),
            Part("spread", "3) розмах вибірки:", sp.Integer(spread), points=1),
            Part("median", "4) медіана вибірки:", sp.Integer(mid), points=1),
        ],
        seconds=150,
        params={"lo": lo, "hi": hi, "sample": sample},
    )
