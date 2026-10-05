"""Комбінаторика: правила суми й добутку, перестановки, розміщення, комбінації.

Обсяг — §12 і §13 підручника Мерзляка (математика, 11 клас, 2019):
  * §12 «Комбінаторні правила суми та добутку»: факторіал, цифрові задачі
    (з повторами й без, нуль не може бути першим, парність, подільність),
    послідовності й паролі (правило суми над степенями);
  * §13 «Перестановки. Розміщення. Комбінації»: $P_n = n!$,
    $A_n^k = \\frac{n!}{(n-k)!}$, $C_n^k = \\frac{n!}{(n-k)!\\,k!}$.

Теорії ймовірностей і статистики (§14–§15) тут НЕМА — це окрема тема.

Чому це стійке до списування. У комбінаториці відповідь — число, тож звичайних
засобів тут мало і захист доводиться будувати на параметрах:
  * у кожного свої n, k і свій набір цифр, тож варіантів на шаблон 20–60
    (міряється тестом test_many_variants_per_template);
  * кожна задача на 2–3 поля: один переписаний результат нічого не дає,
    передати треба весь ланцюг;
  * у парах «розміщення / комбінації» навмисне стоять поруч два числа, які
    студенти плутають, — списаний результат без розуміння стає помилкою.

ВАЖЛИВО про цифрові задачі: різний НАБІР цифр змінює умову, але не завжди
відповідь — $m^k$ і $A_m^k$ залежать лише від РОЗМІРУ набору. Тому кожна така
задача має ще й пункт, що залежить від самих цифр (парність останньої), а там,
де це не вдавалося, задачу замінено (див. cmb_menu замість набору з повторами).

Відповіді цифрових задач ПЕРЕЛІЧУЮТЬСЯ (itertools), а не виводяться формулою:
набір цифр малий, перебір миттєвий і не залежить від правильності формули.
Задачі на сполуки, навпаки, вважаються через math.comb/perm/factorial, а тести
перевіряють їх перебором — тож кожна відповідь перевірена двома незалежними
шляхами.
"""

from __future__ import annotations

import itertools
import math
import random

import sympy as sp

from engine import Part, Question, template

# Відповіді тут — великі числа, тож зразу показуємо, що вираз теж приймається.
_HINT = ("(Відповідь — число. Можна вводити й виразом, у тому самому вигляді, "
         "як набираєте: 6*5*4 або 7^3+7^4.)")


def _digits_tex(digits) -> str:
    return "$" + ", ".join(str(d) for d in sorted(digits)) + "$"


def _agree(n: int, forms: tuple[str, str, str]) -> str:
    """Узгодження іменника з числівником: форми для 1, для 2-4 і для 5+."""
    one, few, many = forms
    n10, n100 = n % 10, n % 100
    if n10 == 1 and n100 != 11:
        return one
    if n10 in (2, 3, 4) and n100 not in (12, 13, 14):
        return few
    return many


def _count_numbers(digits, k, *, distinct=False, last_parity=None, first=None) -> int:
    """Скільки k-цифрових чисел можна скласти з набору `digits`.

    Перебір усіх k-ок: цифр не більше десяти, тож це миттєво. Запис числа не
    може починатися з нуля — це враховано тут, а не в умові задачі.
    """
    total = 0
    for tup in itertools.product(sorted(digits), repeat=k):
        if tup[0] == 0:
            continue
        if distinct and len(set(tup)) != k:
            continue
        if last_parity is not None and tup[-1] % 2 != last_parity:
            continue
        if first is not None and tup[0] != first:
            continue
        total += 1
    return total


def _num(value):
    """Числове значення попереднього кроку або None, якщо переносити нічого."""
    if value is None or getattr(value, "free_symbols", set()):
        return None
    return value


def _carry_mul(key, factor):
    """Крок «помножити попередній результат на factor»."""
    def _fn(prev):
        got = _num(prev[key])
        return None if got is None else got * factor
    return _fn


def _carry_add(key, addend):
    def _fn(prev):
        got = _num(prev[key])
        return None if got is None else got + addend
    return _fn


def _carry_product(k1, k2):
    def _fn(prev):
        a, b = _num(prev[k1]), _num(prev[k2])
        return None if a is None or b is None else a * b
    return _fn


def _carry_sum(k1, k2):
    def _fn(prev):
        a, b = _num(prev[k1]), _num(prev[k2])
        return None if a is None or b is None else a + b
    return _fn


def _carry_diff(k1, k2):
    def _fn(prev):
        a, b = _num(prev[k1]), _num(prev[k2])
        return None if a is None or b is None else a - b
    return _fn


def _carry_ratio(k1, k2):
    def _fn(prev):
        a, b = _num(prev[k1]), _num(prev[k2])
        if a is None or b is None or b == 0:
            return None
        try:
            return sp.nsimplify(a / b)
        except Exception:  # noqa: BLE001
            return None
    return _fn


# =========================================================================
#  §12. КОМБІНАТОРНІ ПРАВИЛА СУМИ ТА ДОБУТКУ
# =========================================================================

@template("cmb_sum_product")
def _sum_product(rng: random.Random) -> Question:
    """Правило добутку і правило суми в одній задачі (вправи 12.1, 12.9)."""
    a = rng.choice([3, 4, 5, 6, 7])
    b = rng.choice([2, 3, 4, 5, 6])
    c = rng.choice([2, 3, 4, 5])
    via = a * b
    total = via + c
    there_back = total * (total - 1)
    return Question(
        key="cmb_sum_product",
        statement=(
            rf"З міста $A$ до міста $B$ ведуть ${a}$ "
            + _agree(a, ("різний шлях", "різні шляхи", "різних шляхів"))
            + rf", а з міста $B$ до міста $C$ — ${b}$ "
            + _agree(b, ("різний шлях", "різні шляхи", "різних шляхів"))
            + rf". Крім того, є ще ${c}$ "
            + _agree(c, ("шлях", "шляхи", "шляхів"))
            + r", що ведуть з $A$ до $C$ навпростець, не заходячи в $B$."
            + "\n1) Скількома способами можна проїхати з $A$ до $C$ через місто $B$?"
            + "\n2) Скількома способами можна проїхати з $A$ до $C$ узагалі?"
            + "\n3) Скількома способами можна проїхати з $A$ до $C$, а потім "
            "повернутися назад, якщо дорога назад має відрізнятися від дороги туди?"
            + "\n" + _HINT
        ),
        parts=[
            Part("via", "1) через $B$:", sp.Integer(via), points=1),
            Part("total", "2) усього:", sp.Integer(total), points=1,
                 carry=_carry_add("via", c), carry_from=("via",)),
            Part("there_back", "3) туди й назад:", sp.Integer(there_back), points=1,
                 carry=lambda prev: (None if _num(prev["total"]) is None
                                     else prev["total"] * (prev["total"] - 1)),
                 carry_from=("total",)),
        ],
        seconds=130,
        params={"a": a, "b": b, "c": c},
    )


@template("cmb_menu")
def _menu(rng: random.Random) -> Question:
    """Меню: добуток, сума попарних добутків, сума (вправи 12.3, 12.10).

    Усі три відповіді залежать від усіх трьох чисел умови, тож варіантів
    справді багато — на відміну від цифрових задач, де відповідь визначає
    лише РОЗМІР набору цифр, а не самі цифри.
    """
    a = rng.choice([3, 4, 5, 6, 7])
    b = rng.choice([4, 5, 6, 7, 8])
    c = rng.choice([3, 4, 5, 6, 7])
    full = a * b * c
    two = a * b + a * c + b * c
    one = a + b + c
    return Question(
        key="cmb_menu",
        statement=(
            rf"У їдальні пропонують ${a}$ "
            + _agree(a, ("різний салат", "різні салати", "різних салатів"))
            + rf", ${b}$ "
            + _agree(b, ("різна м'ясна страва", "різні м'ясні страви",
                         "різних м'ясних страв"))
            + rf" і ${c}$ "
            + _agree(c, ("різний десерт", "різні десерти", "різних десертів"))
            + "."
            + "\n1) Скількома способами можна вибрати обід із трьох страв — "
            "по одній страві кожного виду?"
            + "\n2) Скількома способами можна вибрати обід із двох страв "
            "РІЗНОГО виду?"
            + "\n3) Скількома способами можна вибрати лише одну страву?"
            + "\n" + _HINT
        ),
        parts=[
            Part("full", "1) обід із трьох страв:", sp.Integer(full), points=1),
            Part("two", "2) обід із двох страв:", sp.Integer(two), points=1),
            Part("one", "3) одна страва:", sp.Integer(one), points=1),
        ],
        seconds=110,
        params={"a": a, "b": b, "c": c},
    )


@template("cmb_digits_zero")
def _digits_zero(rng: random.Random) -> Question:
    """Те саме, але серед цифр є НУЛЬ — головна пастка (вправи 12.12, 12.19)."""
    m = rng.choice([4, 5, 6, 7, 8, 9])
    digits = sorted([0] + rng.sample(range(1, 10), m - 1))
    # потрібні і парні, і непарні цифри — інакше третій пункт вироджується
    while min(len([d for d in digits if d % 2 == 0]),
              len([d for d in digits if d % 2])) < 2:
        digits = sorted([0] + rng.sample(range(1, 10), m - 1))
    k = min(rng.choice([3, 4, 5]), m)              # для «всі різні» потрібно k ≤ m
    with_rep = _count_numbers(digits, k)
    distinct = _count_numbers(digits, k, distinct=True)
    even_last = _count_numbers(digits, k, last_parity=0)
    return Question(
        key="cmb_digits_zero",
        statement=(
            rf"Дано цифри {_digits_tex(digits)}. Зверніть увагу: серед них є нуль, "
            "а запис числа не може починатися з нуля."
            + f"\n1) Скільки ${k}$-цифрових чисел можна записати цими цифрами, "
            "якщо цифри можуть повторюватися?"
            + f"\n2) Скільки таких ${k}$-цифрових чисел, у яких усі цифри різні?"
            + "\n3) Скільки серед чисел із пункту 1) таких, що закінчуються "
            "ПАРНОЮ цифрою?"
            + "\n" + _HINT
        ),
        parts=[
            Part("rep", "1) з повторами:", sp.Integer(with_rep), points=1),
            Part("dist", "2) усі цифри різні:", sp.Integer(distinct), points=1),
            Part("even_last", "3) закінчуються парною:", sp.Integer(even_last),
                 points=1),
        ],
        seconds=140,
        params={"digits": digits, "k": k},
    )


@template("cmb_digits_parity")
def _digits_parity(rng: random.Random) -> Question:
    """Парні / непарні числа з даних цифр (вправи 12.6, 12.13, 12.17, 12.18)."""
    m = rng.choice([6, 7, 8, 9])
    digits = sorted([0] + rng.sample(range(1, 10), m - 1))
    # щоб обидва варіанти питання мали зміст, потрібні і парні, і непарні цифри
    while len([d for d in digits if d % 2 == 0]) < 2 or \
            len([d for d in digits if d % 2]) < 2:
        digits = sorted([0] + rng.sample(range(1, 10), m - 1))
    k = rng.choice([3, 4])
    even = rng.random() < 0.5
    parity = 0 if even else 1
    word = "парних" if even else "непарних"          # родовий — для підпису
    word_nom = "парні" if even else "непарні"        # називний — для умови
    tails = len([d for d in digits if d % 2 == parity])
    total = _count_numbers(digits, k, last_parity=parity)
    distinct = _count_numbers(digits, k, last_parity=parity, distinct=True)
    return Question(
        key="cmb_digits_parity",
        statement=(
            rf"Дано цифри {_digits_tex(digits)}. Розглядаємо ${k}$-цифрові "
            f"{word_nom} числа, записані цими цифрами (запис числа не може "
            "починатися з нуля)."
            + "\n1) Скільки варіантів є для ОСТАННЬОЇ цифри такого числа?"
            + f"\n2) Скільки всього існує таких ${k}$-цифрових {word} чисел, "
            "якщо цифри можуть повторюватися?"
            + "\n3) Скільки з них таких, у яких усі цифри різні?"
            + "\n" + _HINT
        ),
        parts=[
            Part("tails", "1) варіантів останньої цифри:", sp.Integer(tails),
                 points=1),
            Part("total", f"2) усього {word}:", sp.Integer(total), points=1),
            Part("dist", "3) з них усі цифри різні:", sp.Integer(distinct),
                 points=1),
        ],
        seconds=140,
        params={"digits": digits, "k": k, "even": even},
    )


@template("cmb_divisible")
def _divisible(rng: random.Random) -> Question:
    """Скільки k-цифрових чисел кратні d (вправи 12.21, 12.22 — рівень ••)."""
    k = rng.choice([4, 5, 6, 7])
    d = rng.choice([2, 4, 5, 8, 25])
    tail_len = 1 if d in (2, 5) else (3 if d == 8 else 2)
    if tail_len == 1:
        tails = sum(1 for t in range(10) if t % d == 0)
        rule = (r"Число кратне $2$ тоді й лише тоді, коли його остання цифра парна."
                if d == 2 else
                r"Число кратне $5$ тоді й лише тоді, коли його остання цифра — "
                r"$0$ або $5$.")
        ask = "ОСТАННЬОЇ цифри"
        label = "1) варіантів останньої цифри:"
    else:
        tails = sum(1 for t in range(10**tail_len) if t % d == 0)
        many = "двома" if tail_len == 2 else "трьома"
        few = "двох" if tail_len == 2 else "трьох"
        rule = (rf"Число кратне ${d}$ тоді й лише тоді, коли число, записане "
                rf"{many} його останніми цифрами, кратне ${d}$ "
                r"(нуль теж кратний).")
        ask = f"{few} ОСТАННІХ цифр"
        label = f"1) варіантів {few} останніх цифр:"
    # Загальну кількість беремо прямим підрахунком кратних у діапазоні — це
    # не залежить від жодної комбінаторної формули.
    hi, lo = 10**k - 1, 10 ** (k - 1) - 1
    total = hi // d - lo // d
    return Question(
        key="cmb_divisible",
        statement=(
            rf"Скільки існує ${k}$-цифрових чисел, які діляться націло на ${d}$?"
            + "\n" + rule
            + f"\n1) Скільки різних варіантів може мати закінчення ({ask}) "
            "такого числа?"
            + f"\n2) Скільки всього існує ${k}$-цифрових чисел, кратних ${d}$?"
            + "\n" + _HINT
        ),
        parts=[
            Part("tails", label, sp.Integer(tails), points=1),
            Part("total", f"2) усього ${k}$-цифрових:", sp.Integer(total), points=1,
                 carry=_carry_mul("tails", 9 * 10 ** (k - 1 - tail_len)),
                 carry_from=("tails",)),
        ],
        seconds=130,
        params={"k": k, "d": d},
    )


@template("cmb_sequences")
def _sequences(rng: random.Random) -> Question:
    """Паролі змінної довжини: правило суми над степенями (задача 2 з §12)."""
    m = rng.choice([6, 8, 9, 10, 12, 14, 16, 18, 20, 24, 26])
    k = rng.choice([2, 3, 4])
    exact = m**k
    distinct = math.perm(m, k)
    both = m**k + m ** (k + 1)
    return Question(
        key="cmb_sequences",
        statement=(
            rf"Пароль складають із ${m}$ різних символів; символи в паролі можуть "
            r"повторюватися."
            + f"\n1) Скільки різних паролів завдовжки рівно ${k}$ "
            + _agree(k, ("символ", "символи", "символів")) + " можна утворити?"
            + f"\n2) Скільки серед них таких, у яких усі ${k}$ "
            + _agree(k, ("символ", "символи", "символи")) + " різні?"
            + f"\n3) Скільки всього паролів можна утворити, якщо довжина пароля — "
            rf"від ${k}$ до ${k + 1}$ символів?"
            + "\n" + _HINT
        ),
        parts=[
            Part("exact", rf"1) завдовжки ${k}$:", sp.Integer(exact), points=1),
            Part("dist", "2) усі символи різні:", sp.Integer(distinct), points=1),
            Part("both", rf"3) завдовжки ${k}$ або ${k + 1}$:", sp.Integer(both),
                 points=1, carry=_carry_add("exact", m ** (k + 1)),
                 carry_from=("exact",)),
        ],
        seconds=130,
        params={"m": m, "k": k},
    )


# =========================================================================
#  §13. ПЕРЕСТАНОВКИ. РОЗМІЩЕННЯ. КОМБІНАЦІЇ
# =========================================================================

@template("cmb_permutations")
def _permutations(rng: random.Random) -> Question:
    """Перестановки $P_n = n!$ з додатковою умовою (вправи 13.1, 13.6)."""
    n = rng.choice([6, 7, 8, 9, 10])     # 11! і більше руками вже не порахувати
    g = rng.choice([2, 3, 4])
    both_ends = rng.random() < 0.5
    allways = math.factorial(n)
    firstg = math.factorial(g) * math.factorial(n - g)
    if both_ends:
        third = (n - g) * (n - g - 1) * math.factorial(n - 2)
        ask3 = ("\n3) Скількома способами, якщо ні на першому, ні на останньому "
                "місці НЕ має стояти підручник?")
        label3 = "3) по краях — не підручники:"
    else:
        third = (n - g) * math.factorial(n - 1)
        ask3 = ("\n3) Скількома способами, якщо на першому місці НЕ має стояти "
                "підручник?")
        label3 = "3) першим — не підручник:"
    return Question(
        key="cmb_permutations",
        statement=(
            rf"На полиці потрібно розставити ${n}$ різних книг, серед яких "
            rf"${g}$ підручники."
            + "\n1) Скількома способами це можна зробити?"
            + "\n" + rf"2) Скількома способами, якщо всі ${g}$ підручники мають стояти "
            rf"на перших ${g}$ місцях (у будь-якому порядку між собою)?"
            + ask3
            + "\n" + _HINT
        ),
        parts=[
            Part("all", "1) усіх способів:", sp.Integer(allways), points=1),
            Part("firstg", rf"2) підручники на перших ${g}$ місцях:",
                 sp.Integer(firstg), points=1),
            Part("third", label3, sp.Integer(third), points=1),
        ],
        seconds=110,
        params={"n": n, "g": g, "both_ends": both_ends},
    )


@template("cmb_arrangements_vs_combinations")
def _arrangements_vs_combinations(rng: random.Random) -> Question:
    """Розміщення ПРОТИ комбінацій — те, що плутають найчастіше (13.4, 13.5, 13.9).

    Два числа стоять поруч навмисне: списаний результат без розуміння, де
    порядок важливий, а де ні, перетворюється на помилку.
    """
    n = rng.choice(list(range(8, 21)))
    k = rng.choice([2, 3, 4])
    posts = {2: "голову та секретаря",
             3: "голову, заступника та секретаря",
             4: "голову, заступника, секретаря та скарбника"}[k]
    ordered = math.perm(n, k)
    unordered = math.comb(n, k)
    times = math.factorial(k)
    return Question(
        key="cmb_arrangements_vs_combinations",
        statement=(
            rf"У комісії працюють ${n}$ осіб."
            + f"\n1) Скількома способами з них можна вибрати {posts}?"
            + "\n" + rf"2) Скількома способами з них можна вибрати ${k}$ делегатів на "
            "конференцію (без розподілу обов'язків)?"
            + "\n3) У скільки разів перша кількість більша за другу?"
            + "\n" + _HINT
        ),
        parts=[
            Part("ordered", "1) з розподілом обов'язків:", sp.Integer(ordered),
                 points=1),
            Part("unordered", rf"2) ${k}$ делегатів:", sp.Integer(unordered),
                 points=1),
            Part("times", "3) у скільки разів більше:", sp.Integer(times), points=1,
                 carry=_carry_ratio("ordered", "unordered"),
                 carry_from=("ordered", "unordered")),
        ],
        seconds=120,
        params={"n": n, "k": k},
    )


@template("cmb_team_with_fixed")
def _team_with_fixed(rng: random.Random) -> Question:
    """Комбінації з умовою «входить / не входить» (вправа 13.9).

    Третій крок дорівнює різниці перших двох — тож перевіряється не лише
    арифметика, а й розуміння, що ці дві множини разом дають усі команди.
    """
    n = rng.choice([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])
    k = rng.choice([3, 4, 5])
    allways = math.comb(n, k)
    with_head = math.comb(n - 1, k - 1)
    without = math.comb(n - 1, k)
    return Question(
        key="cmb_team_with_fixed",
        statement=(
            rf"У класі ${n}$ учнів та учениць, один із них — староста класу. "
            rf"Треба сформувати команду з ${k}$ осіб для участі в олімпіаді."
            + "\n1) Скількома способами це можна зробити?"
            + "\n2) Скількома способами, якщо староста обов'язково входить "
            "до команди?"
            + "\n3) Скількома способами, якщо староста до команди не входить?"
            + "\n" + _HINT
        ),
        parts=[
            Part("all", "1) усіх команд:", sp.Integer(allways), points=1),
            Part("with_head", "2) зі старостою:", sp.Integer(with_head), points=1),
            Part("without", "3) без старости:", sp.Integer(without), points=1,
                 carry=_carry_diff("all", "with_head"),
                 carry_from=("all", "with_head")),
        ],
        seconds=130,
        params={"n": n, "k": k},
    )


@template("cmb_polygon")
def _polygon(rng: random.Random) -> Question:
    """Комбінації в геометрії: фігури з вершин n-кутника (13.10, 13.11)."""
    n = rng.choice([7, 8, 9, 10, 11, 12, 13, 14, 15])
    r = rng.choice([4, 5])
    rname = "чотирикутників" if r == 4 else "п'ятикутників"
    diagonals = rng.random() < 0.5
    tri = math.comb(n, 3)
    poly = math.comb(n, r)
    if diagonals:
        third = math.comb(n, 2) - n
        ask3 = ("\n3) Скільки діагоналей має цей багатокутник? "
                "(діагональ сполучає дві вершини, які не є сусідніми)")
        label3 = "3) діагоналей:"
    else:
        third = math.comb(n, 2)
        ask3 = ("\n3) Скільки всього відрізків сполучають пари вершин цього "
                "багатокутника (і сторони, і діагоналі)?")
        label3 = "3) відрізків:"
    return Question(
        key="cmb_polygon",
        statement=(
            rf"Дано правильний ${n}$-кутник."
            + "\n1) Скільки існує трикутників, усі вершини яких є вершинами "
            "цього багатокутника?"
            + f"\n2) Скільки існує {rname} з вершинами у вершинах цього "
            "багатокутника?"
            + ask3
            + "\n" + _HINT
        ),
        parts=[
            Part("tri", "1) трикутників:", sp.Integer(tri), points=1),
            Part("poly", f"2) {rname}:", sp.Integer(poly), points=1),
            Part("third", label3, sp.Integer(third), points=1),
        ],
        seconds=130,
        params={"n": n, "r": r, "diagonals": diagonals},
    )


@template("cmb_exactly_k")
def _exactly_k(rng: random.Random) -> Question:
    """«Рівно a елементів одного виду» — добуток двох комбінацій (вправа 13.13)."""
    n = rng.choice([18, 20, 22, 24])
    m = rng.choice([6, 7, 8, 9])
    s = rng.choice([5, 6])
    a = rng.choice([2, 3])
    masons = math.comb(m, a)
    others = math.comb(n - m, s - a)
    total = masons * others
    return Question(
        key="cmb_exactly_k",
        statement=(
            rf"Серед ${n}$ робітників бригади є ${m}$ мулярів. Треба скласти "
            rf"ланку з ${s}$ робітників так, щоб мулярів у ній було "
            rf"РІВНО ${a}$."
            + "\n" + rf"1) Скількома способами можна вибрати ${a}$ мулярів?"
            + "\n" + rf"2) Скількома способами можна вибрати решту ${s - a}$ "
            "робітників (не мулярів)?"
            + "\n3) Скількома способами можна скласти таку ланку?"
            + "\n" + _HINT
        ),
        parts=[
            Part("masons", rf"1) ${a}$ мулярів:", sp.Integer(masons), points=1),
            Part("others", rf"2) ${s - a}$ не мулярів:", sp.Integer(others),
                 points=1),
            Part("total", "3) усієї ланки:", sp.Integer(total), points=1,
                 carry=_carry_product("masons", "others"),
                 carry_from=("masons", "others")),
        ],
        seconds=150,
        params={"n": n, "m": m, "s": s, "a": a},
    )


@template("cmb_two_lines")
def _two_lines(rng: random.Random) -> Question:
    """Трикутники з точок на двох паралельних прямих (вправа 13.15, рівень ••)."""
    p = rng.choice([6, 7, 8, 9, 10, 11, 12, 13, 14])
    q = rng.choice([4, 5, 6, 7, 8, 9])
    on_a = math.comb(p, 2) * q
    on_b = math.comb(q, 2) * p
    return Question(
        key="cmb_two_lines",
        statement=(
            rf"На прямій $a$ позначено ${p}$ "
            + _agree(p, ("точку", "точки", "точок"))
            + rf", а на паралельній їй прямій $b$ — ${q}$ "
            + _agree(q, ("точку", "точки", "точок")) + "."
            + "\n1) Скільки існує трикутників, у яких дві вершини лежать на "
            "прямій $a$, а третя — на прямій $b$?"
            + "\n2) Скільки існує трикутників, у яких дві вершини лежать на "
            "прямій $b$, а третя — на прямій $a$?"
            + "\n3) Скільки всього існує трикутників з вершинами в цих точках? "
            "(три точки однієї прямої трикутника не утворюють)"
            + "\n" + _HINT
        ),
        parts=[
            Part("on_a", "1) дві вершини на $a$:", sp.Integer(on_a), points=1),
            Part("on_b", "2) дві вершини на $b$:", sp.Integer(on_b), points=1),
            Part("total", "3) усього трикутників:", sp.Integer(on_a + on_b),
                 points=1, carry=_carry_sum("on_a", "on_b"),
                 carry_from=("on_a", "on_b")),
        ],
        seconds=150,
        params={"p": p, "q": q},
    )
