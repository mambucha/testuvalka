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
