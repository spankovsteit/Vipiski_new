"""Tests for deposit parsing helpers."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

from vipiski.deposits import build_deposits_dict, parse_deposit_amount_cell, parse_deposit_maturity_date


def _serial_for_date(d: dt.date) -> str:
    base = dt.datetime(1899, 12, 30).date()
    return str((d - base).days)


def test_parse_deposit_maturity_date_text():
    assert parse_deposit_maturity_date("15.06.2025") == dt.date(2025, 6, 15)
    assert parse_deposit_maturity_date("2025-06-15") == dt.date(2025, 6, 15)


def test_parse_deposit_maturity_date_excel_serial_roundtrip():
    d = dt.date(2025, 3, 22)
    assert parse_deposit_maturity_date(_serial_for_date(d)) == d


def test_parse_deposit_maturity_date_empty():
    assert parse_deposit_maturity_date("") is None
    assert parse_deposit_maturity_date("   ") is None


def test_parse_deposit_amount_cell():
    assert parse_deposit_amount_cell("1 000,50") == Decimal("1000.50")
    assert parse_deposit_amount_cell("") == Decimal(0)


def _make_row(company: str, amount: str, date_str: str) -> list[str]:
    row = [""] * 10
    row[0] = company
    row[6] = amount
    row[9] = date_str
    return row


def test_build_deposits_dict_basic():
    data = [_make_row("ООО Ромашка", "1 500 000", "15.06.2025")]
    d = build_deposits_dict(data)
    assert "ООО Ромашка" in d
    assert "1.500.000" in d["ООО Ромашка"][0]
    assert "15.06.2025" in d["ООО Ромашка"][0]


def test_build_deposits_dict_skips_zero_amount():
    data = [_make_row("ООО Ромашка", "", "15.06.2025")]
    assert build_deposits_dict(data) == {}


def test_build_deposits_dict_skips_empty_date():
    data = [_make_row("ООО Ромашка", "100000", "")]
    assert build_deposits_dict(data) == {}


def test_build_deposits_dict_excel_serial_date():
    d = dt.date(2025, 6, 15)
    base = dt.datetime(1899, 12, 30).date()
    serial = str((d - base).days)
    data = [_make_row("ООО Тест", "500000", serial)]
    result = build_deposits_dict(data)
    assert "15.06.2025" in result["ООО Тест"][0]
