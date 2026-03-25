"""Tests for ``vipiski.parsers`` (sample PDF text snippets)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from vipiski.parsers import (
    parse_amount_ru,
    parse_bspb_spisanie_balance,
    parse_sber_outgoing_fixed,
    parse_tochka_outgoing,
    run_parser,
)


def test_parse_amount_ru():
    assert parse_amount_ru("672 116,05") == Decimal("672116.05")
    assert parse_amount_ru("0,00") == Decimal("0")
    assert parse_amount_ru("\xa0672\xa0116,05") == Decimal("672116.05")


def test_parse_amount_ru_empty_raises():
    from decimal import InvalidOperation

    with pytest.raises(InvalidOperation):
        parse_amount_ru("   ")


def test_parse_sber_outgoing_fixed():
    text = "Исходящий остаток 0,00 1 234 567,89\n"
    assert parse_sber_outgoing_fixed(text) == Decimal("1234567.89")


def test_parse_bspb_dot_decimal_footer():
    text = "footer\n -600 000.00300 000.0090 468.70\n"
    assert parse_bspb_spisanie_balance(text) == Decimal("90468.70")


def test_parse_bspb_исходящий_остаток_comma():
    text = (
        "\u0418\u0441\u0445\u043e\u0434\u044f\u0449\u0438\u0439 "
        "\u043e\u0441\u0442\u0430\u0442\u043e\u043a x 1 234,56\n"
    )
    assert parse_bspb_spisanie_balance(text) == Decimal("1234.56")


def test_parse_tochka_outgoing():
    text = "Исходящее сальдо: 304 067,14\n"
    assert parse_tochka_outgoing(text) == Decimal("304067.14")


def test_run_parser_unknown_returns_none(caplog):
    import logging

    with caplog.at_level(logging.ERROR):
        assert run_parser("no_such_parser", "") is None
    assert "Unknown parser" in caplog.text


def test_run_parser_dispatches_sber_fixed():
    text = (
        "\u0418\u0441\u0445\u043e\u0434\u044f\u0449\u0438\u0439 "
        "\u043e\u0441\u0442\u0430\u0442\u043e\u043a 0,00 250,00\n"
    )
    assert run_parser("sber_outgoing_balance", text) == Decimal("250")
