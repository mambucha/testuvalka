"""Побудова простих рисунків до задач як inline-SVG.

SVG генерується на сервері з числових параметрів задачі (жодного вводу ззовні),
тож його безпечно вставляти у сторінку напряму. Кольори підібрані під світлу
картку фронтенду; лінії темні, сітка світло-сіра, об'єкти — акцентні.
"""

from __future__ import annotations

# Геометрія полотна: діапазон -6..6 по обох осях, 25px на одиницю.
_UNIT = 25
_HALF = 6
_ORIGIN = 160  # центр полотна (px) — (size/2)
_SIZE = 2 * _ORIGIN


def _px(x: float) -> float:
    return round(_ORIGIN + x * _UNIT, 1)


def _py(y: float) -> float:
    return round(_ORIGIN - y * _UNIT, 1)


def region_between(upper, lower, a: float, b: float, n: int = 48):
    """Точки многокутника області між кривими y=upper(x) (згори) та y=lower(x)
    (знизу) на [a, b]. upper/lower — функції x. Придатне для `regions` нижче
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
                     ellipses=None, regions=None, labeled_ticks=True) -> str:
    """Координатна площина з осями, сіткою та об'єктами.

    lines:     список прямих як (k, b) — рисуємо y = k*x + b через усе полотно.
    parabolas: список парабол як (a, h, k) — рисуємо y = a*(x-h)^2 + k.
    circles:   список кіл як (cx, cy, r).
    ellipses:  список еліпсів як (cx, cy, ra, rb) — півосі вздовж Ox і Oy.
    points:    список (x, y[, підпис]) — позначаємо кружечками.
    regions:   список заштрихованих областей; кожна — список точок (x, y)
               (напр. з region_between) — заливаємо напівпрозорим акцентом.
    Повертає рядок <svg>…</svg>, придатний для inline-вставки.
    """
    lines = lines or []
    parabolas = parabolas or []
    circles = circles or []
    ellipses = ellipses or []
    points = points or []
    regions = regions or []
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
