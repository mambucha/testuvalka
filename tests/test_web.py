"""Шар C: фронтенд віддається, а /api/* мають пріоритет над статикою."""


def test_index_is_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Вхід у тест" in r.text


def test_pages_are_not_cached(client):
    """Сторінки віддаються з no-cache, щоб браузер не показував стару версію
    після оновлення застосунку."""
    for path in ("/", "/teacher.html"):
        r = client.get(path)
        assert r.status_code == 200
        assert "no-cache" in r.headers.get("cache-control", "")


def test_api_routes_take_priority_over_static(client):
    # /api/* не має перехоплюватись монтуванням статики на "/".
    r = client.get("/api/attempt/999999/current")
    assert r.status_code == 404
    assert r.json().get("detail")  # JSON від застосунку, не сторінка


def test_integrity_markers_present(client):
    """Маркери академічної доброчесності: декларація на вході + рядок під питанням
    (останній завжди в кадрі скріншота)."""
    html = client.get("/").text
    assert 'class="integrity"' in html  # декларація на вході
    assert 'class="integrity-line"' in html  # рядок під питанням
    assert "ШІ" in html  # згадка про ШІ-помічників
    assert "статуту коледжу" in html or "статутом коледжу" in html
    # оголошене правило про перевидання при виході/вставці
    assert "заміниться на нове з іншими числами" in html


def test_agree_checkbox_gates_start(client):
    """Кнопка старту заблокована, доки не позначено згоду; є чекбокс і обробник,
    що керує станом кнопки. Текст про академічну доброчесність."""
    html = client.get("/").text
    assert 'id="agree"' in html
    assert 'id="btn-start" disabled' in html  # стартова кнопка вимкнена
    assert '"agree").addEventListener("change"' in html
    assert '"agree").checked' in html  # doStart перевіряє згоду
    assert "академічної" in html  # honor pledge про доброчесність


def test_symbol_keyboard_present(client):
    """Опційна екранна клавіатура: панель, кнопка виклику, цифри й символи."""
    html = client.get("/").text
    assert 'id="kbd-panel"' in html
    assert 'id="kbd-toggle"' in html
    assert 'data-ins="sqrt()"' in html  # кнопка кореня
    assert 'data-ins="7"' in html  # цифровий ряд
    assert 'data-act="clear"' in html  # кнопка «стерти все»
    assert "function kbdInsert" in html
    assert "function kbdClear" in html
    # опційна: перемикач зі станом, що запам'ятовується
    assert "function kbdSetOpen" in html
    assert 'id="kbd-arrow"' in html
    assert "testuvalka:kbd" in html  # стан зберігається


def test_live_math_preview_present(client):
    """Живий математичний прев'ю введення (учень бачить формулу, не сирий текст)."""
    html = client.get("/").text
    assert "function renderExprPreview" in html
    assert "math-preview" in html  # клас прев'ю (створюється у JS)
    assert 'p.kind === "expr"' in html  # прев'ю лише для полів-виразів


def test_submit_button_is_wired(client):
    """Регрес: кнопка «Відповісти» мусить мати обробник кліку — інакше клік по
    ній нічого не робить (submit спрацьовував лише по Enter)."""
    html = client.get("/").text
    assert 'id="btn-submit"' in html
    assert '"btn-submit").addEventListener("click"' in html
    # І кнопка входу теж має бути прив'язана.
    assert '"btn-start").addEventListener("click"' in html
