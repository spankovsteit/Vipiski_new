"""Regression tests for manevich_vtb, reaktiv_sber, sev_zvezda_vtb fixes."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from vipiski.loaders import load_accounts
from vipiski.parsers import run_parser

MANEVICH_VTB_SNIPPET = (
    'Владелец счета: Индивидуальный предприниматель МАНЕВИЧ АЛЛА ЕФИМОВНА\n'
    'ИСХОДЯЩИЙ ОСТАТОК\n34 599.76\n'
)

REAKTIV_SBER_SNIPPET = (
    'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "РЕАКТИВ"\n'
    'СберБизнес\n'
    'Исходящий остаток 0,00 3 001 097,97 07 мая 2026 г.(П)\n'
)

SEV_ZVEZDA_VTB_SNIPPET = (
    'Владелец счета: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СЕВЕРНАЯ ЗВЕЗДА"\n'
    'ИСХОДЯЩИЙ ОСТАТОК\n30 260.00\n'
)


def test_manevich_vtb_match_and_parse():
    accounts = load_accounts(Path("config/accounts.json"))
    rule = next(a for a in accounts if a["account_code"] == "manevich_vtb")
    assert all(n in MANEVICH_VTB_SNIPPET for n in rule["match_all"])
    assert run_parser(rule["parser"], MANEVICH_VTB_SNIPPET) == Decimal("34599.76")


def test_reaktiv_sber_uses_sber_parser():
    accounts = load_accounts(Path("config/accounts.json"))
    rule = next(a for a in accounts if a["account_code"] == "reaktiv_sber")
    assert rule["parser"] == "sber_outgoing_balance"
    assert run_parser(rule["parser"], REAKTIV_SBER_SNIPPET) == Decimal("3001097.97")


def test_sev_zvezda_vtb_rule_exists_and_parses():
    accounts = load_accounts(Path("config/accounts.json"))
    rule = next(a for a in accounts if a["account_code"] == "sev_zvezda_vtb")
    assert all(n in SEV_ZVEZDA_VTB_SNIPPET for n in rule["match_all"])
    assert run_parser(rule["parser"], SEV_ZVEZDA_VTB_SNIPPET) == Decimal("30260.00")
