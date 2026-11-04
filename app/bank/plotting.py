"""Побудова простих рисунків до задач як inline-SVG.

SVG генерується на сервері з числових параметрів задачі (жодного вводу ззовні),
тож його безпечно вставляти у сторінку напряму. Кольори підібрані під світлу
картку фронтенду; лінії темні, сітка світло-сіра, об'єкти – акцентні.
"""

from __future__ import annotations

# Геометрія полотна: діапазон -6..6 по обох осях, 25px на одиницю.
_UNIT = 25
_HALF = 6
_ORIGIN = 160  # центр полотна (px) – (size/2)
_SIZE = 2 * _ORIGIN


def _px(x: float) -> float:
    return round(_ORIGIN + x * _UNIT, 1)


def _py(y: float) -> float:
    return round(_ORIGIN - y * _UNIT, 1)


def region_between(upper, lower, a: float, b: float, n: int = 48):
    """Точки многокутника області між кривими y=upper(x) (згори) та y=lower(x)
    (знизу) на [a, b]. upper/lower – функції x. Придатне для `regions` нижче
    (заливка криволінійної трапеції / фігури між лініями)."""
    pts = []
    step = (b - a) / n
    # нижня межа зліва направо
    for i in range(n + 1):
        x = a + i * step
        pts.append((x, lower(x)))
    # верхня межа справа наліво (замикаємо контур)
    for i in range(n + 1):
        x = b - i * step
        pts.append((x, upper(x)))
    return pts


def coordinate_plane(lines=None, points=None, parabolas=None, circles=None,
                     ellipses=None, regions=None, segments=None, curves=None,
                     labeled_ticks=True) -> str:
    """Координатна площина з осями, сіткою та об'єктами.

    lines:     список прямих як (k, b) – рисуємо y = k*x + b через усе полотно.
    parabolas: список парабол як (a, h, k) – рисуємо y = a*(x-h)^2 + k.
    circles:   список кіл як (cx, cy, r).
    ellipses:  список еліпсів як (cx, cy, ra, rb) – півосі вздовж Ox і Oy.
    points:    список (x, y[, підпис]) – позначаємо кружечками.
    regions:   список заштрихованих областей; кожна – список точок (x, y)
               (напр. з region_between) – заливаємо напівпрозорим акцентом.
    segments:  список відрізків прямих як (k, b, x1, x2) – малюємо y = kx + b
               ЛИШЕ на [x1; x2]. Потрібно для кусково заданих функцій і графіків
               із розривом (повна пряма тут не годиться).
    curves:    список довільних кривих як (f, x1, x2), де f – функція однієї
               змінної. Для степеневих (y = x³, y = x⁻ⁿ), яких немає серед
               примітивів. Лінія рветься в точках розриву й за межами полотна.
    Повертає рядок <svg>…</svg>, придатний для inline-вставки.
    """
    lines = lines or []
    parabolas = parabolas or []
    circles = circles or []
    ellipses = ellipses or []
    points = points or []
    regions = regions or []
    segments = segments or []
    curves = curves or []
    el: list[str] = []

    # --- сітка ---
    for i in range(-_HALF, _HALF + 1):
        x = _px(i)
        y = _py(i)
        el.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{_SIZE}" stroke="#e6e9ee" stroke-width="1"/>')
        el.append(f'<line x1="0" y1="{y}" x2="{_SIZE}" y2="{y}" stroke="#e6e9ee" stroke-width="1"/>')

    # --- заштриховані області (під осями/кривими, над сіткою) ---
    for reg in regions:
        poly = " ".join(f"{_px(px)},{_py(py)}" for px, py in reg)
        el.append(
            f'<polygon points="{poly}" fill="#2f6df6" fill-opacity="0.15" '
            'stroke="#2f6df6" stroke-opacity="0.35" stroke-width="1"/>'
        )

    # --- осі ---
    el.append(f'<line x1="0" y1="{_ORIGIN}" x2="{_SIZE}" y2="{_ORIGIN}" stroke="#3a4553" stroke-width="1.6"/>')
    el.append(f'<line x1="{_ORIGIN}" y1="0" x2="{_ORIGIN}" y2="{_SIZE}" stroke="#3a4553" stroke-width="1.6"/>')
    # стрілки осей
    el.append(f'<polygon points="{_SIZE},{_ORIGIN} {_SIZE-9},{_ORIGIN-4} {_SIZE-9},{_ORIGIN+4}" fill="#3a4553"/>')
    el.append(f'<polygon points="{_ORIGIN},0 {_ORIGIN-4},9 {_ORIGIN+4},9" fill="#3a4553"/>')
    el.append(f'<text x="{_SIZE-6}" y="{_ORIGIN+16}" font-size="13" fill="#3a4553" text-anchor="end">x</text>')
    el.append(f'<text x="{_ORIGIN+8}" y="12" font-size="13" fill="#3a4553">y</text>')
    el.append(f'<text x="{_ORIGIN-11}" y="{_ORIGIN+15}" font-size="12" fill="#6b7684">O</text>')

    # --- поділки з числами (кожну 2, щоб не тісно) ---
    if labeled_ticks:
        for i in range(-_HALF, _HALF + 1):
            if i == 0:
                continue
            xt, yt = _px(i), _py(i)
            el.append(f'<line x1="{xt}" y1="{_ORIGIN-3}" x2="{xt}" y2="{_ORIGIN+3}" stroke="#3a4553" stroke-width="1.2"/>')
            el.append(f'<line x1="{_ORIGIN-3}" y1="{yt}" x2="{_ORIGIN+3}" y2="{yt}" stroke="#3a4553" stroke-width="1.2"/>')
            if i % 2 == 0:
                el.append(f'<text x="{xt}" y="{_ORIGIN+15}" font-size="10.5" fill="#6b7684" text-anchor="middle">{i}</text>')
                el.append(f'<text x="{_ORIGIN-6}" y="{yt+4}" font-size="10.5" fill="#6b7684" text-anchor="end">{i}</text>')

    # --- параболи (y = a*(x-h)^2 + k); polyline по точках у межах видимості ---
    for a, h, k in parabolas:
        pts = []
        x = -_HALF
        while x <= _HALF + 1e-9:
            y = a * (x - h) ** 2 + k
            if abs(y) <= _HALF + 0.5:
                pts.append(f"{_px(x)},{_py(y)}")
            x += 0.2
        if pts:
            el.append(
                f'<polyline points="{" ".join(pts)}" fill="none" '
                'stroke="#2f6df6" stroke-width="2.4"/>'
            )

    # --- кола ---
    for cx, cy, r in circles:
        el.append(
            f'<circle cx="{_px(cx)}" cy="{_py(cy)}" r="{round(r * _UNIT, 1)}" '
            'fill="none" stroke="#2f6df6" stroke-width="2.4"/>'
        )

    # --- еліпси (півосі ra вздовж Ox, rb вздовж Oy) ---
    for cx, cy, ra, rb in ellipses:
        el.append(
            f'<ellipse cx="{_px(cx)}" cy="{_py(cy)}" rx="{round(ra * _UNIT, 1)}" '
            f'ry="{round(rb * _UNIT, 1)}" fill="none" stroke="#2f6df6" stroke-width="2.4"/>'
        )

    # --- прямі (y = k*x + b); малюємо від краю до краю, svg обріже рамкою ---
    for k, b in lines:
        x1, x2 = -_HALF, _HALF
        el.append(
            f'<line x1="{_px(x1)}" y1="{_py(k*x1+b)}" x2="{_px(x2)}" y2="{_py(k*x2+b)}" '
            'stroke="#2f6df6" stroke-width="2.4"/>'
        )

    # --- довільні криві y = f(x) ---
    # Потрібні для степеневих функцій, яких немає серед примітивів: y = x³,
    # y = x⁻ⁿ тощо. Лінію розриваємо там, де функція не визначена або вийшла
    # за полотно, – інакше гілки гіперболи з'єдналися б хибною вертикаллю.
    for fn, x1, x2 in curves:
        run: list[str] = []
        steps = 240
        for i in range(steps + 1):
            xx = x1 + (x2 - x1) * i / steps
            try:
                yy = fn(xx)
            except (ZeroDivisionError, ValueError, OverflowError):
                yy = None
            if yy is None or abs(yy) > _HALF + 0.4:
                if len(run) > 1:
                    el.append(
                        f'<polyline points="{" ".join(run)}" fill="none" '
                        'stroke="#2f6df6" stroke-width="2.4"/>'
                    )
                run = []
                continue
            run.append(f"{_px(xx)},{_py(yy)}")
        if len(run) > 1:
            el.append(
                f'<polyline points="{" ".join(run)}" fill="none" '
                'stroke="#2f6df6" stroke-width="2.4"/>'
            )

    # --- відрізки прямих (y = kx + b лише на [x1; x2]) ---
    for k, b, x1, x2 in segments:
        el.append(
            f'<line x1="{_px(x1)}" y1="{_py(k*x1+b)}" x2="{_px(x2)}" y2="{_py(k*x2+b)}" '
            'stroke="#2f6df6" stroke-width="2.4"/>'
        )

    # --- точки ---
    for p in points:
        x, y = p[0], p[1]
        el.append(f'<circle cx="{_px(x)}" cy="{_py(y)}" r="4.2" fill="#d23f3f"/>')
        if len(p) > 2 and p[2]:
            el.append(f'<text x="{_px(x)+7}" y="{_py(y)-7}" font-size="12" fill="#d23f3f">{p[2]}</text>')

    return (
        f'<svg viewBox="0 0 {_SIZE} {_SIZE}" width="{_SIZE}" '
        'style="max-width:100%;height:auto;background:#fff;border-radius:8px" '
        'xmlns="http://www.w3.org/2000/svg" role="img">'
        + "".join(el)
        + "</svg>"
    )


# ==========================================================================
# Тригонометричне (одиничне) коло
# ==========================================================================
#
# Окреме полотно, бо на сітці coordinate_plane радіус 1 вийшов би 25 пікселів –
# на такому колі не роздивитися ні точки, ні підписів.

_CIRCLE_R = 108               # радіус кола в пікселях
_CIRCLE_PAD = 46              # поле під підписи кутів ззовні
_CIRCLE_C = _CIRCLE_R + _CIRCLE_PAD
_CIRCLE_SIZE = 2 * _CIRCLE_C

# «Гарні» кути: кратні pi/6 і pi/4. Саме їх заповнює студент у таблиці значень
# (ДЗ заняття 9), тож інші на колі й не потрібні.
_NICE = [(0, 1), (1, 6), (1, 4), (1, 3), (1, 2), (2, 3), (3, 4), (5, 6),
         (1, 1), (7, 6), (5, 4), (4, 3), (3, 2), (5, 3), (7, 4), (11, 6)]


def nice_angles() -> list[tuple[int, int]]:
    """Кути кола як пари (чисельник, знаменник) у частках pi, від 0 до 2pi."""
    return list(_NICE)


def angle_tex(num: int, den: int) -> str:
    """LaTeX кута: (0,1) -> 0, (1,1) -> \\pi, (5,6) -> \\dfrac{5\\pi}{6}."""
    if num == 0:
        return "0"
    top = r"\pi" if num == 1 else rf"{num}\pi"
    return top if den == 1 else rf"\dfrac{{{top}}}{{{den}}}"


def angle_input(num: int, den: int) -> str:
    """Той самий кут у вигляді, який розуміє парсер відповідей."""
    if num == 0:
        return "0"
    top = "pi" if num == 1 else f"{num}*pi"
    return top if den == 1 else f"{top}/{den}"


def _cx(t: float) -> float:
    import math
    return round(_CIRCLE_C + _CIRCLE_R * math.cos(t), 1)


def _cy(t: float) -> float:
    import math
    return round(_CIRCLE_C - _CIRCLE_R * math.sin(t), 1)


def unit_circle(marked=None, pickable: bool = False,
                show_labels: bool = True, radius_to=None) -> str:
    """Тригонометричне коло.

    marked:    кути (num, den) у частках pi, які позначаємо червоною точкою
               з підписом P – для задач «прочитай координати точки».
    pickable:  чи робити точки клікабельними. Тоді кожна дістає data-ins із
               записом кута для парсера, і фронтенд вписує його в поле за
               клацанням – так само, як це робить екранна клавіатура.
               Жодного вводу ззовні в SVG не потрапляє: усе з чисел задачі.
    show_labels: підписувати кути ззовні кола.
    radius_to: кут (num, den), до якого провести радіус і намалювати дугу
               повороту – щоб було видно, звідки й куди крутимо.
    """
    import math

    marked = marked or []
    el: list[str] = []
    c, r = _CIRCLE_C, _CIRCLE_R

    # --- осі ---
    el.append(f'<line x1="{_CIRCLE_PAD - 18}" y1="{c}" x2="{_CIRCLE_SIZE - _CIRCLE_PAD + 18}" '
              f'y2="{c}" stroke="#3a4553" stroke-width="1.6"/>')
    el.append(f'<line x1="{c}" y1="{_CIRCLE_SIZE - _CIRCLE_PAD + 18}" x2="{c}" '
              f'y2="{_CIRCLE_PAD - 18}" stroke="#3a4553" stroke-width="1.6"/>')
    el.append(f'<polygon points="{_CIRCLE_SIZE - _CIRCLE_PAD + 18},{c} '
              f'{_CIRCLE_SIZE - _CIRCLE_PAD + 9},{c - 4} '
              f'{_CIRCLE_SIZE - _CIRCLE_PAD + 9},{c + 4}" fill="#3a4553"/>')
    el.append(f'<polygon points="{c},{_CIRCLE_PAD - 18} {c - 4},{_CIRCLE_PAD - 9} '
              f'{c + 4},{_CIRCLE_PAD - 9}" fill="#3a4553"/>')
    el.append(f'<text x="{_CIRCLE_SIZE - _CIRCLE_PAD + 16}" y="{c + 18}" font-size="13" '
              'fill="#3a4553" text-anchor="end">x</text>')
    el.append(f'<text x="{c - 16}" y="{_CIRCLE_PAD - 20}" font-size="13" '
              'fill="#3a4553" text-anchor="end">y</text>')

    # --- саме коло ---
    el.append(f'<circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="#2f6df6" '
              'stroke-width="2.2"/>')

    # --- радіус і дуга повороту ---
    if radius_to is not None:
        t = math.pi * radius_to[0] / radius_to[1]
        el.append(f'<line x1="{c}" y1="{c}" x2="{_cx(t)}" y2="{_cy(t)}" '
                  'stroke="#d23f3f" stroke-width="2"/>')
        big = 1 if t > math.pi else 0
        el.append(f'<path d="M {c + 34} {c} A 34 34 0 {big} 0 '
                  f'{round(c + 34 * math.cos(t), 1)} {round(c - 34 * math.sin(t), 1)}" '
                  'fill="none" stroke="#d23f3f" stroke-width="1.4" stroke-dasharray="3 2"/>')

    # --- точки кола ---
    for num, den in _NICE:
        t = math.pi * num / den
        x, y = _cx(t), _cy(t)
        is_marked = (num, den) in marked
        if pickable:
            # Клікабельна зона більша за саму точку: на телефоні в 4 пікселі
            # пальцем не влучиш.
            el.append(
                f'<circle class="uc-dot" data-ins="{angle_input(num, den)}" '
                f'cx="{x}" cy="{y}" r="13" fill="#2f6df6" fill-opacity="0.001" '
                'style="cursor:pointer"><title>'
                f'{angle_input(num, den)}</title></circle>'
            )
        el.append(
            f'<circle cx="{x}" cy="{y}" r="{4.6 if is_marked else 3.2}" '
            f'fill="{"#d23f3f" if is_marked else "#2f6df6"}" '
            f'fill-opacity="{1 if is_marked else 0.55}" pointer-events="none"/>'
        )
        if is_marked:
            # Підпис ставимо ВСЕРЕДИНІ кола, збоку від радіуса. Ззовні він
            # накладався б на підпис кута, а просто на радіусі – на сам
            # радіус.
            rr, off = r - 17, 12
            mx = rr * math.cos(t) - off * math.sin(t)
            my = rr * math.sin(t) + off * math.cos(t)
            el.append(f'<text x="{round(c + mx, 1)}" y="{round(c - my + 4, 1)}" '
                      'font-size="13" fill="#d23f3f" font-weight="600" '
                      'text-anchor="middle" pointer-events="none">P</text>')
        if show_labels:
            lx = c + (r + 20) * math.cos(t)
            ly = c - (r + 20) * math.sin(t) + 4
            # Чотири кути лежать просто на осях, де вже є стрілка й буква осі.
            # Якщо не зсунути, підписи 0, pi, pi/2 і 3pi/2 накладаються на них.
            if abs(math.sin(t)) < 0.01:                  # на осі Ox
                ly -= 13
            elif abs(math.cos(t)) < 0.01:                # на осі Oy
                lx += 17
            el.append(
                f'<text x="{round(lx, 1)}" y="{round(ly, 1)}" font-size="9.5" '
                'fill="#6b7684" text-anchor="middle" pointer-events="none">'
                f'{_label_plain(num, den)}</text>'
            )

    return (
        f'<svg viewBox="0 0 {_CIRCLE_SIZE} {_CIRCLE_SIZE}" width="{_CIRCLE_SIZE}" '
        'style="max-width:100%;height:auto;background:#fff;border-radius:8px" '
        f'class="unit-circle{" pickable" if pickable else ""}" '
        'xmlns="http://www.w3.org/2000/svg" role="img">'
        + "".join(el)
        + "</svg>"
    )


def _label_plain(num: int, den: int) -> str:
    """Підпис кута звичайним текстом – усередині SVG KaTeX не працює."""
    if num == 0:
        return "0"
    top = "π" if num == 1 else f"{num}π"
    return top if den == 1 else f"{top}/{den}"


# ==========================================================================
# Стовпчикова діаграма частот
# ==========================================================================
#
# Потрібна для §15 (математична статистика): у підручнику майже всі дані подано
# саме діаграмою, а не переліком. Заразом це найсильніший захист від списування
# в усьому тесті – в УМОВІ чисел немає взагалі, вони тільки на рисунку, тож
# переписувати з тексту нічого.

_BAR_SLOT = 38                # ширина «місця» під один стовпчик
_BAR_W = 26                   # ширина самого стовпчика
_BAR_H = 150                  # висота поля під стовпчики
_BAR_LEFT = 46                # поле ліворуч під підписи осі Oy
_BAR_TOP = 26                 # місце під підпис осі Oy над верхньою поділкою
_BAR_BOTTOM = 42


def bar_chart(labels, counts, *, xlabel: str = "", ylabel: str = "") -> str:
    """Стовпчикова діаграма: під кожним значенням стовпчик висотою в його частоту.

    labels: підписи під стовпчиками (числа або короткі рядки на кшталт XL);
    counts: висоти стовпчиків (цілі невід'ємні);
    xlabel / ylabel: підписи осей.

    Частоти підписані над стовпчиками, як у Мерзляка (рис. 15.5, 15.7, 15.8):
    завдання тут – обчислити показники вибірки, а не вгадати висоту на око.
    Нульовий стовпчик не малюємо, але підпис значення лишаємо – інакше
    зникало б саме те значення, якого у вибірці немає.
    """
    counts = [int(c) for c in counts]
    top = max(counts) if counts else 1
    step = 1 if top <= 10 else (2 if top <= 20 else 5)
    axis_top = max(step, -(-top // step) * step)      # округлення вгору до кроку
    scale = _BAR_H / axis_top
    width = _BAR_LEFT + len(labels) * _BAR_SLOT + 18
    height = _BAR_TOP + _BAR_H + _BAR_BOTTOM
    base = _BAR_TOP + _BAR_H
    el: list[str] = []

    # --- сітка з підписами по Oy ---
    for v in range(0, axis_top + 1, step):
        y = round(base - v * scale, 1)
        el.append(
            f'<line x1="{_BAR_LEFT}" y1="{y}" x2="{width - 12}" y2="{y}" '
            'stroke="#e6e9ee" stroke-width="1"/>'
        )
        el.append(
            f'<text x="{_BAR_LEFT - 7}" y="{y + 4}" font-size="10.5" '
            f'fill="#6b7684" text-anchor="end">{v}</text>'
        )

    # --- стовпчики ---
    for i, (lab, c) in enumerate(zip(labels, counts)):
        cx = _BAR_LEFT + i * _BAR_SLOT + _BAR_SLOT / 2
        h = round(c * scale, 1)
        if c:
            el.append(
                f'<rect x="{round(cx - _BAR_W / 2, 1)}" y="{round(base - h, 1)}" '
                f'width="{_BAR_W}" height="{h}" rx="2" fill="#2f6df6" '
                'fill-opacity="0.75" stroke="#2f6df6" stroke-width="1"/>'
            )
            el.append(
                f'<text x="{round(cx, 1)}" y="{round(base - h - 5, 1)}" '
                'font-size="10.5" fill="#3a4553" text-anchor="middle">'
                f'{c}</text>'
            )
        el.append(
            f'<text x="{round(cx, 1)}" y="{base + 16}" font-size="11.5" '
            f'fill="#3a4553" text-anchor="middle">{lab}</text>'
        )

    # --- осі ---
    el.append(
        f'<line x1="{_BAR_LEFT}" y1="{base}" x2="{width - 12}" y2="{base}" '
        'stroke="#3a4553" stroke-width="1.6"/>'
    )
    el.append(
        f'<line x1="{_BAR_LEFT}" y1="{_BAR_TOP - 8}" x2="{_BAR_LEFT}" y2="{base}" '
        'stroke="#3a4553" stroke-width="1.6"/>'
    )
    if xlabel:
        el.append(
            f'<text x="{width - 12}" y="{base + 34}" font-size="11" '
            f'fill="#6b7684" text-anchor="end">{xlabel}</text>'
        )
    if ylabel:
        # Праворуч від осі й вище за верхню поділку: ліворуч стоять числа
        # поділок, і підпис налазив би саме на найбільше з них.
        el.append(
            f'<text x="{_BAR_LEFT + 4}" y="{_BAR_TOP - 10}" font-size="11" '
            f'fill="#6b7684">{ylabel}</text>'
        )

    return (
        f'<svg viewBox="0 0 {width} {height}" width="{width}" '
        'style="max-width:100%;height:auto;background:#fff;border-radius:8px" '
        'xmlns="http://www.w3.org/2000/svg" role="img">'
        + "".join(el)
        + "</svg>"
    )
