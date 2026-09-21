"""Сигнали клік-бота в панелі аномалій (webdriver + «підозріло швидко»).

Це СИГНАЛИ, не вирок: webdriver ловить незамасковану автоматизацію, «швидко» —
надлюдську швидкість на правильних пунктах. У тесті відповіді подаються миттєво,
тож усі правильні пункти автоматично «швидкі».
"""

from support import DEV_FULL_NAME, TEACHER_TOKEN, StudentClient, correct_answers

H = {"X-Teacher-Token": TEACHER_TOKEN}


def _finish_all_correct(client, webdriver=False):
    s = StudentClient(client)
    s.start()
    if webdriver:
        s.event("client_env", {"webdriver": True, "ua": "HeadlessChrome/1.0"})
    else:
        s.event("client_env", {"webdriver": False, "ua": "Mozilla/5.0"})
    while True:
        cur = s.current_json()
        if cur.get("finished"):
            break
        s.answer(correct_answers(cur["question"]["key"], reissue=cur["reissue"]))
    return s


def _row(client):
    data = client.get("/api/teacher/anomalies?test_key=demo", headers=H).json()
    return next(a for a in data["attempts"] if a["full_name"] == DEV_FULL_NAME)


def test_webdriver_signal_flagged(client):
    _finish_all_correct(client, webdriver=True)
    row = _row(client)
    assert row["webdriver"] is True
    assert "автоматизація" in row["flags"]


def test_no_webdriver_signal_when_normal(client):
    _finish_all_correct(client, webdriver=False)
    row = _row(client)
    assert row["webdriver"] is False
    assert "автоматизація" not in row["flags"]


def test_fast_signal_on_instant_correct(client):
    """Усі 3 демо-питання правильні й миттєво -> fast_correct>=3 -> прапорець."""
    _finish_all_correct(client)
    row = _row(client)
    assert row["fast_correct"] >= 3
    assert "швидко" in row["flags"]
