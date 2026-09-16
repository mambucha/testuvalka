"""Шар C: фронтенд віддається, а /api/* мають пріоритет над статикою."""


def test_index_is_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Вхід у тест" in r.text


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


def test_agree_checkbox_gates_start(client):
    """Кнопка старту заблокована, доки не позначено ознайомлення; є чекбокс і
    обробник, що керує станом кнопки."""
    html = client.get("/").text
    assert 'id="agree"' in html
    assert 'id="btn-start" disabled' in html  # стартова кнопка вимкнена
    assert '"agree").addEventListener("change"' in html
    assert '"agree").checked' in html  # doStart перевіряє згоду


def test_submit_button_is_wired(client):
    """Регрес: кнопка «Відповісти» мусить мати обробник кліку — інакше клік по
    ній нічого не робить (submit спрацьовував лише по Enter)."""
    html = client.get("/").text
    assert 'id="btn-submit"' in html
    assert '"btn-submit").addEventListener("click"' in html
    # І кнопка входу теж має бути прив'язана.
    assert '"btn-start").addEventListener("click"' in html
