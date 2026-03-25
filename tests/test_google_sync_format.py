"""Tests for Google Sheet formatting helpers (no API calls)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from vipiski.report import _fmt_money

from vipiski.google_sync import (
    _balance_column_index,
    _company_total_formula,
    _decimal_abs_literal_for_formula,
    _deposit_amount_if_mature_today,
    _deposit_formula_suffix,
    format_balance_for_ru_sheet,
    write_account_balances_telegram_outbox,
)


def test_format_balance_for_ru_sheet():
    assert format_balance_for_ru_sheet(Decimal("672116.05")) == "672 116,05"
    assert format_balance_for_ru_sheet(Decimal("1000")) == "1 000,00"
    assert format_balance_for_ru_sheet(Decimal("-1.5")) == "-1,50"


def test_balance_column_index_extended_header():
    header = ["account_code", "company_code", "bank", "balance", "business_date", "active"]
    assert _balance_column_index(header) == 3


def test_balance_column_index_legacy():
    assert _balance_column_index(["account_code", "balance"]) == 1


def test_company_total_formula_ru_embeds_deposit_literal_not_g_ref():
    f = _company_total_formula(
        "raw_balances",
        ["klever_sber"],
        locale="ru",
        deposit_addend=Decimal("1500000.50"),
    )
    assert "G" not in f
    assert "J" not in f
    assert "СЕГОДНЯ" not in f
    assert "1500000,50" in f
    assert "klever_sber" in f


def test_company_total_formula_en():
    f = _company_total_formula(
        "raw_balances",
        ["a"],
        locale="en",
        deposit_addend=Decimal("10"),
    )
    assert "G" not in f
    assert "TODAY()" not in f
    assert "IFERROR" in f
    assert "10.00" in f


def test_company_total_formula_no_accounts_only_deposit():
    f = _company_total_formula("raw", [], locale="ru", deposit_addend=Decimal("99"))
    assert f == "=99,00"


def test_company_total_formula_no_accounts_zero_deposit():
    assert _company_total_formula("raw", [], locale="ru", deposit_addend=Decimal(0)) == "=0"


def test_deposit_amount_if_mature_today_respects_column_j():
    today = date(2025, 6, 15)
    other = date(2025, 7, 1)
    row = [""] * 10
    row[6] = "1 000,50"
    row[9] = "15.06.2025"
    data = [row]
    assert _deposit_amount_if_mature_today(data, "D1", as_of=today) == Decimal("1000.50")
    row_bad = list(row)
    row_bad[9] = other.strftime("%d.%m.%Y")
    assert _deposit_amount_if_mature_today([row_bad], "D1", as_of=today) == Decimal(0)


class _FakeBalancesWs:
    def __init__(self) -> None:
        self.batch_calls: list[tuple[list, str | None]] = []

    def batch_update(self, updates, value_input_option=None):
        self.batch_calls.append((updates, value_input_option))


def test_write_account_balances_telegram_outbox_p1():
    ws = _FakeBalancesWs()
    write_account_balances_telegram_outbox(ws, "hello\nline2")
    assert len(ws.batch_calls) == 1
    upd, opt = ws.batch_calls[0]
    assert opt == "USER_ENTERED"
    assert upd == [{"range": "P1", "values": [["hello\nline2"]]}]


def test_write_account_balances_telegram_outbox_truncates():
    ws = _FakeBalancesWs()
    long_text = "x" * 60_000
    write_account_balances_telegram_outbox(ws, long_text)
    val = ws.batch_calls[0][0][0]["values"][0][0]
    assert len(val) == 50_000


def test_fmt_money_no_float_precision():
    assert _fmt_money(Decimal("672116.05")) == "672 116,05"
    assert _fmt_money(Decimal("1000000")) == "1 000 000,00"
    assert _fmt_money(Decimal("-1.5")) == "-1,50"
    # Large value that float would round incorrectly
    assert _fmt_money(Decimal("9999999999999.99")) == "9 999 999 999 999,99"


def test_decimal_abs_literal_and_deposit_suffix():
    assert _decimal_abs_literal_for_formula(Decimal("1.23"), "ru") == "1,23"
    assert _decimal_abs_literal_for_formula(Decimal("1.23"), "en") == "1.23"
    assert _deposit_formula_suffix(Decimal("5"), "ru") == "+5,00"
    assert _deposit_formula_suffix(Decimal("-5"), "ru") == "-5,00"
    assert _deposit_formula_suffix(Decimal(0), "ru") == ""
