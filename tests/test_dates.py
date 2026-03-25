"""Tests for ``vipiski.dates``."""

from __future__ import annotations

from datetime import date, datetime

from vipiski.dates import (
    archive_month_folder_name,
    day_folder_segment,
    is_weekend,
    month_folder_name,
    previous_business_day,
    previous_calendar_day,
    sber_day_tokens,
    statement_reference_date,
)


def test_previous_calendar_day():
    assert previous_calendar_day(date(2026, 3, 15)) == date(2026, 3, 14)


def test_is_weekend():
    assert is_weekend(date(2026, 3, 21))  # Saturday
    assert not is_weekend(date(2026, 3, 23))  # Monday


def test_previous_business_day_skips_weekend():
    # Friday 13 -> Thursday 12
    assert previous_business_day(date(2026, 3, 13)) == date(2026, 3, 12)
    # Monday 16 -> Friday 13
    assert previous_business_day(date(2026, 3, 16)) == date(2026, 3, 13)


def test_sber_day_tokens_march():
    d = date(2026, 3, 22)
    day, letter = sber_day_tokens(d)
    assert day == "22"
    assert letter == "M"


def test_month_folder_name():
    assert month_folder_name(datetime(2026, 3, 23)) == "2026-03"


def test_archive_month_folder_name_first_of_month():
    assert archive_month_folder_name(datetime(2026, 3, 1)) == "2026-02"
    assert day_folder_segment(datetime(2026, 3, 1)) == "01032026"


def test_archive_month_folder_name_january_first():
    assert archive_month_folder_name(datetime(2026, 1, 1)) == "2025-12"
    assert day_folder_segment(datetime(2026, 1, 1)) == "01012026"


def test_archive_month_folder_name_mid_month():
    assert archive_month_folder_name(datetime(2026, 3, 23)) == "2026-03"


def test_day_folder_segment():
    assert day_folder_segment(datetime(2026, 3, 23)) == "23032026"


def test_statement_reference_date_is_yesterday_of_run_date():
    run = datetime(2026, 3, 23, 12, 0, 0)
    assert statement_reference_date(run) == date(2026, 3, 22)
