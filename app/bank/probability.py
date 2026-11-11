"""Ймовірність: §14 підручника Мерзляка (математика, 11 клас).

Обсяг – «Класичне визначення ймовірності випадкової події» повністю:
  * означення $P(A) = m/n$ над рівноможливими результатами, достовірна
    ($P = 1$) і неможлива ($P = 0$) події (задача 1, вправа 14.3);
  * вибір числа зі скінченної множини: подільність і заперечення (14.6,
    14.9, завдання 11 із «Перевірте себе»), просте / складене / двоцифрове
    (14.9, 14.10), кратність серед усіх k-цифрових чисел (14.8);
  * задачі, де рівноможливі результати спершу треба порахувати: числа з
    даних цифр (14.4), забуті цифри коду (завдання 9), пара з групи
    (задача 2), парність добутку й суми двох карток (завдання 12);
  * ймовірність через комбінації: усі вибрані одного виду (задача 3, вправи
    14.13, 14.14, 14.16) і рівно $a$ одного виду (14.15);
  * межі означення: найменша кількість, за якої ймовірність дорівнює $1$
    (завдання 6), і обернена задача «дано ймовірність – знайти кількість»
    (14.17, 14.18).

Комбінаторика (§12–§13) – окрема тема, вона в app/bank/combinatorics.py. Тут
сполуки вживаються як ІНСТРУМЕНТ, а не як предмет: власних питань на
перестановки й розміщення немає, і скрізь, де потрібна кількість способів,
вона стоїть окремим пунктом – щоб видно було, де комбінаторика скінчилася
й почалася ймовірність.

Статистика (§15) – теж окрема тема, вона в app/bank/statistics.py і поки що
не входить до жодного тесту.

Питань з відповіддю «так / ні» тут немає взагалі: один біт коштував би
стільки ж, скільки обчислена ймовірність, а вгадується наполовину.

ЧОМУ ЦЕ СТІЙКЕ ДО СПИСУВАННЯ. Відповідь тут – число, тож захист тримається на
параметрах і на тому, що в полі має стояти не переписане з умови:
  * у кожного свої кількості, свої дільники, свої цифри – на шаблон
    щонайменше 15 різних наборів відповідей (міряє
    test_many_variants_per_template);
  * кожна задача на 3–4 поля: один переписаний результат нічого не дає,
    передати треба весь ланцюг;
  * у половині задач знаменник ймовірності В УМОВІ НЕ НАДРУКОВАНИЙ – його
    спершу треба порахувати, і саме це питає перший пункт;
  * ймовірності в межах одного питання навмисне різні, тож одне вгадане
    поле не підказує решти.

Нуль і одиниця як відповідь є лише в pb_urn – це саме та пара, якою §14
означує неможливу й достовірну події, і перевірити її інакше, ніж спитавши
саму ймовірність, не вийде. Стала «0» в усіх полях бере там одне поле
з чотирьох, стала «1» – теж одне.

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

# Ймовірність – дріб, і зводити його до нескоротного ми не вимагаємо.
_HINT_P = ("(Ймовірність можна записати звичайним дробом 5/12, десятковим 0,25 "
           "або нескороченим виразом 10/24 – усе одно зарахується. Лише не "
           "округлюйте: 1/3 вводьте дробом, а не 0,33.)")
_HINT_N = ("(Відповідь – число. Можна й виразом, як набираєте: 6*5/2, "
           "12!/(9!*3!). Знак факторіала є на клавіатурі.)")
_HINT_NP = ("(Кількість можна писати виразом: 6*5/2, 12!/(9!*3!). Ймовірність – "
            "дробом 5/12 або 0,25; скорочувати не обов'язково, округлювати "
            "не можна: 1/3 вводьте дробом.)")


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


def _carry_diff(whole_key, part_key):
    def _fn(prev):
        whole, part = _count(prev.get(whole_key)), _count(prev.get(part_key))
        if whole is None or part is None or whole == part:
            return None
        return _whole(whole - part)
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


def _is_prime(value: int) -> bool:
    """Просте число – пробним діленням, без sympy.

    Числа тут не більші за кілька десятків, тож швидкість ні до чого; важливо
    інше – еталон і перевірка в тестах мають рахуватися РІЗНИМИ способами,
    а в тесті стоїть sp.isprime.
    """
    if value < 2:
        return False
    d = 2
    while d * d <= value:
        if value % d == 0:
            return False
        d += 1
    return True


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


@template("pb_number_kind")
def _number_kind(rng: random.Random) -> Question:
    """Просте, складене, двоцифрове (вправи 14.9, 14.10).

    Пастка тут навмисна і класична: одиниця не є ні простим числом, ні
    складеним, тож дві перші ймовірності НЕ дають у сумі одиницю. Хто
    порахував другу як «одиниця мінус перша», це й покаже.

    Усі три кількості шаблон рахує перебором діапазону, а не формулами.
    """
    while True:
        n = rng.randint(14, 40)
        two = rng.random() < 0.5          # двоцифрове чи одноцифрове
        nums = range(1, n + 1)
        primes = sum(1 for k in nums if _is_prime(k))
        composite = sum(1 for k in nums if k > 1 and not _is_prime(k))
        digits = sum(1 for k in nums if (k >= 10) == two)
        probs = [sp.Rational(primes, n), sp.Rational(composite, n),
                 sp.Rational(digits, n)]
        if all(0 < p < 1 for p in probs) and len(set(probs)) == 3:
            break

    word = "ДВОЦИФРОВЕ" if two else "ОДНОЦИФРОВЕ"
    return Question(
        key="pb_number_kind",
        statement=(
            rf"На ${n}$ картках записано натуральні числа від $1$ до ${n}$ "
            "(на кожній картці – одне число). Картку вибирають навмання."
            + "\n1) Яка ймовірність того, що число на картці – ПРОСТЕ?"
            + "\n2) Яка ймовірність того, що число на картці – СКЛАДЕНЕ?"
            + f"\n3) Яка ймовірність того, що число на картці – {word}?"
            + "\n" + _HINT_P
        ),
        parts=[
            Part("prime", "1) просте:", probs[0], points=1),
            Part("composite", "2) складене:", probs[1], points=1),
            Part("digits", f"3) {word.lower()}:", probs[2], points=1),
        ],
        seconds=170,
        params={"n": n, "two": bool(two)},
    )


@template("pb_multiples")
def _multiples(rng: random.Random) -> Question:
    """Навмання вибране k-цифрове число кратне d (вправа 14.8).

    Відрізняється від pb_cards тим, що знаменник не надрукований в умові:
    скільки взагалі існує k-цифрових чисел, треба порахувати самому. Саме
    про це й питає перший пункт – і саме його зазвичай пропускають.

    Обидві кількості шаблон рахує ПРЯМИМ підрахунком у діапазоні, а не
    формулою $9\\cdot10^{k-1}$.
    """
    while True:
        k = rng.choice([2, 3])
        d = rng.choice([3, 4, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 18, 20, 25])
        lo, hi = 10 ** (k - 1), 10**k - 1
        total = hi - lo + 1
        good = sum(1 for v in range(lo, hi + 1) if v % d == 0)
        chance = sp.Rational(good, total)
        if 0 < chance < sp.Rational(1, 2):
            break

    return Question(
        key="pb_multiples",
        statement=(
            rf"Навмання вибирають одне ${k}$-цифрове число."
            + "\n" + rf"1) Скільки всього існує ${k}$-цифрових чисел?"
            + "\n" + rf"2) Скільки серед них кратних ${d}$?"
            + "\n" + rf"3) Яка ймовірність того, що вибране число кратне ${d}$?"
            + "\n" + _HINT_NP
        ),
        parts=[
            Part("total", rf"1) усього ${k}$-цифрових:", sp.Integer(total),
                 points=1),
            Part("good", rf"2) з них кратних ${d}$:", sp.Integer(good), points=1),
            Part("chance", "3) ймовірність:", chance, points=1,
                 carry=_carry_ratio("good", "total"),
                 carry_from=("total", "good")),
        ],
        seconds=150,
        params={"k": k, "d": d},
    )


@template("pb_digits")
def _digits(rng: random.Random) -> Question:
    """Числа, складені з даних цифр (вправа 14.4).

    Тут рівноможливих результатів не видно з умови – їх спершу треба
    порахувати (правило добутку з §12), і аж потім ділити. Третій пункт
    навмисно не зводиться до «скільки цифр підходить»: однакові цифри в
    усьому записі – це вже не одна позиція, а всі.

    Нуля серед цифр немає: запис числа не може з нього починатися, і ця
    пастка належить комбінаториці, а не §14.
    """
    while True:
        m = rng.choice([4, 5, 6, 7])
        digits = sorted(rng.sample(range(1, 10), m))
        k = rng.choice([2, 3, 4])
        evens = len([v for v in digits if v % 2 == 0])
        total = m**k
        even_chance = sp.Rational(evens, m)
        same_chance = sp.Rational(1, m ** (k - 1))
        if evens < 2 or m - evens < 2:
            continue
        if 0 < even_chance < 1 and even_chance != same_chance:
            break

    listing = "$" + ",\\ ".join(str(v) for v in digits) + "$"
    return Question(
        key="pb_digits",
        statement=(
            rf"Дано цифри {listing}. З них складають ${k}$-цифрове число; "
            "цифри можуть повторюватися. Одне з таких чисел вибирають навмання."
            + "\n" + rf"1) Скільки всього ${k}$-цифрових чисел можна скласти "
            "з цих цифр?"
            + "\n2) Яка ймовірність того, що вибране число ПАРНЕ?"
            + "\n3) Яка ймовірність того, що всі цифри вибраного числа "
            "ОДНАКОВІ?"
            + "\n" + _HINT_NP
        ),
        parts=[
            Part("total", "1) усього чисел:", sp.Integer(total), points=1),
            Part("even", "2) число парне:", even_chance, points=1),
            Part("same", "3) усі цифри однакові:", same_chance, points=1,
                 carry=_carry_over(m, "total"), carry_from=("total",)),
        ],
        seconds=160,
        params={"digits": digits, "k": k},
    )


@template("pb_code")
def _code(rng: random.Random) -> Question:
    """Забуті цифри номера (завдання 9 із «Перевірте себе»).

    Показує те, заради чого класичне означення й існує: скільки саме є
    рівноможливих спроб. Третій пункт додає єдине, що з означення прямо
    випливає, – кілька різних спроб складаються, бо це різні сприятливі
    результати того самого випробування.
    """
    while True:
        k = rng.choice([2, 3])
        distinct = rng.random() < 0.5
        total = (10 * 9 if k == 2 else 10 * 9 * 8) if distinct else 10**k
        tries = rng.randint(2, 9)
        if tries < total // 4:
            break

    how = ("пам'ятає лише, що всі вони РІЗНІ" if distinct
           else "про самі цифри не пам'ятає нічого")
    return Question(
        key="pb_code",
        statement=(
            rf"Набираючи код замка, людина забула останні ${k}$ цифри і "
            f"{how}. Решту коду вона набирає правильно."
            + "\n1) Скільки різних варіантів коду їй доводиться перебирати?"
            + "\n2) Яка ймовірність набрати правильний код з першої спроби?"
            + "\n" + rf"3) Яка ймовірність набрати правильний код не більш ніж "
            rf"за ${tries}$ спроб, якщо вже набрані варіанти вона не повторює?"
            + "\n" + _HINT_P
        ),
        parts=[
            Part("total", "1) різних варіантів:", sp.Integer(total), points=1),
            Part("first", "2) з першої спроби:", sp.Rational(1, total), points=1,
                 carry=_carry_over(1, "total"), carry_from=("total",)),
            Part("tries", rf"3) не більш ніж за ${tries}$ спроб:",
                 sp.Rational(tries, total), points=1,
                 carry=_carry_over(tries, "total"), carry_from=("total",)),
        ],
        seconds=150,
        params={"k": k, "distinct": bool(distinct), "tries": tries},
    )


# (умова, хлопці в родовому, дівчата в родовому)
_PAIR = [
    ("Переможцями шкільного конкурсу талантів стали кілька учнів і учениць. "
     "На районний конкурс треба відправити двох із них, і вибирають їх "
     "жеребкуванням."),
    ("До складу команди на олімпіаду треба вибрати двох із переможців "
     "шкільного етапу. Вибір роблять жеребкуванням."),
]


@template("pb_pair_mixed")
def _pair_mixed(rng: random.Random) -> Question:
    """Пара з двох: хлопець і дівчина (задача 2 з §14).

    Приклад, розібраний у підручнику. Група мала навмисно – усі пари можна
    виписати руками, як це й зроблено в задачі 2, а не лише порахувати
    формулою. Через те ж саме третій пункт питає про двох хлопців, а не про
    «не змішану пару»: інакше його брали б як «одиниця мінус попереднє», не
    розуміючи, звідки взялося попереднє.
    """
    while True:
        boys = rng.randint(2, 7)
        girls = rng.randint(2, 7)
        n = boys + girls
        total = math.comb(n, 2)
        mixed = boys * girls
        both_boys = math.comb(boys, 2)
        probs = [sp.Rational(mixed, total), sp.Rational(both_boys, total)]
        if 5 <= n <= 9 and all(0 < p < 1 for p in probs) and probs[0] != probs[1]:
            break
    head = _PAIR[rng.randrange(len(_PAIR))]

    return Question(
        key="pb_pair_mixed",
        statement=(
            head + rf" Усього переможців ${n}$: хлопців – ${boys}$, "
            rf"дівчат – ${girls}$."
            + "\n1) Скільки всього різних пар можна скласти з переможців?"
            + "\n2) Яка ймовірність того, що поїдуть хлопець і дівчина?"
            + "\n3) Яка ймовірність того, що поїдуть двоє хлопців?"
            + "\n" + _HINT_NP
        ),
        parts=[
            Part("pairs", "1) усіх пар:", sp.Integer(total), points=1),
            Part("mixed", "2) хлопець і дівчина:", probs[0], points=1,
                 carry=_carry_over(mixed, "pairs"), carry_from=("pairs",)),
            Part("both_boys", "3) двоє хлопців:", probs[1], points=1,
                 carry=_carry_over(both_boys, "pairs"), carry_from=("pairs",)),
        ],
        seconds=160,
        params={"boys": boys, "girls": girls},
    )


@template("pb_guaranteed")
def _guaranteed(rng: random.Random) -> Question:
    """Скільки треба вийняти, щоб ймовірність дорівнювала одиниці.

    Завдання 6 із «Перевірте себе». Єдине питання тесту, де рахувати
    доводиться не сприятливі результати, а найгірший випадок: ймовірність
    дорівнює $1$ тоді й лише тоді, коли подія відбувається в КОЖНОМУ
    результаті, тобто навіть тоді, коли всі «не ті» кулі вийнято першими.

    Третій пункт повертає до звичайного означення – щоб питання не
    перетворилося на головоломку без ймовірності.
    """
    while True:
        white = rng.randint(4, 12)
        red = rng.randint(3, 10)
        need = rng.randint(2, 4)
        if need > white:
            continue
        enough_white = red + need          # усі червоні могли піти першими
        enough_red = white + 1             # і навпаки
        chance = sp.Rational(white, white + red)
        if enough_white != enough_red and chance != sp.Rational(1, 2):
            break

    whites = _agree(need, ("біла куля", "білі кулі", "білих куль"))
    return Question(
        key="pb_guaranteed",
        statement=(
            rf"У коробці лежать кулі: білих – ${white}$, червоних – ${red}$. "
            "Кулі виймають навмання одну за одною й назад не кладуть."
            + "\n" + rf"1) Яку найменшу кількість куль треба вийняти, щоб "
            rf"ймовірність того, що серед них буде ${need}$ {whites}, "
            r"дорівнювала $1$?"
            + "\n2) Яку найменшу кількість куль треба вийняти, щоб "
            r"ймовірність того, що серед них буде хоча б одна червона, "
            r"дорівнювала $1$?"
            + "\n3) Яка ймовірність того, що ПЕРША вийнята куля – біла?"
            + "\n" + _HINT_P
        ),
        parts=[
            Part("white_sure", rf"1) щоб точно було ${need}$ {whites}:",
                 sp.Integer(enough_white), points=1),
            Part("red_sure", "2) щоб точно була червона:",
                 sp.Integer(enough_red), points=1),
            Part("first", "3) перша куля біла:", chance, points=1),
        ],
        seconds=170,
        params={"white": white, "red": red, "need": need},
    )
