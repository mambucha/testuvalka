"""Час у кабінеті викладача показується в київському часі (конвертація на показі;
дані в БД лишаються наївним UTC)."""

from datetime import datetime

from app.teacher import _dt


def test_dt_empty():
    assert _dt(None) == ""


def test_dt_utc_to_kyiv_summer():
    # 2026-07-15 12:00 UTC -> Київ EEST (UTC+3) = 15:00
    assert _dt(datetime(2026, 7, 15, 12, 0, 0)) == "2026-07-15 15:00:00"


def test_dt_utc_to_kyiv_winter():
    # 2026-01-15 12:00 UTC -> Київ EET (UTC+2) = 14:00 (враховано перехід зима/літо)
    assert _dt(datetime(2026, 1, 15, 12, 0, 0)) == "2026-01-15 14:00:00"


def test_dt_crosses_midnight():
    # 2026-07-15 22:30 UTC -> Київ 01:30 наступної доби
    assert _dt(datetime(2026, 7, 15, 22, 30, 0)) == "2026-07-16 01:30:00"
