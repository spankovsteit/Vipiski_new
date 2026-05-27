"""Regression: Sber match_all must match PDF holder line spacing."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from vipiski.engine import parse_pdfs
from vipiski.loaders import load_accounts
from vipiski.parsers import parse_sber_outgoing_fixed

M_INVEST_SBER_SNIPPET = (
    'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "М-ИНВЕСТ"\n'
    "СберБизнес\n"
    "Исходящий остаток 0,00 394 009,83 25 мая 2026 г.\t(П)\n"
)


def test_m_invest_sber_match_all_matches_pdf_holder_line():
    accounts = load_accounts(Path("config/accounts.json"))
    rule = next(a for a in accounts if a["account_code"] == "m_invest_sber")
    needles = rule["match_all"]
    assert all(n in M_INVEST_SBER_SNIPPET for n in needles)


def test_m_invest_sber_outgoing_balance_from_statement_snippet():
    assert parse_sber_outgoing_fixed(M_INVEST_SBER_SNIPPET) == Decimal("394009.83")


def test_m_invest_sber_pdf_parses_via_engine(tmp_path, monkeypatch):
    pdf_path = tmp_path / "m-invest-sber.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    accounts = load_accounts(Path("config/accounts.json"))

    def fake_extract(_path):
        return M_INVEST_SBER_SNIPPET

    monkeypatch.setattr("vipiski.engine.extract_pdf_text", fake_extract)

    updates = parse_pdfs([pdf_path], accounts, daysbr="26", monthsbr="M")
    assert updates == {"m_invest_sber": Decimal("394009.83")}
