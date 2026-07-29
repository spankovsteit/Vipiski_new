from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from vipiski.engine import parse_pdfs_with_unmatched
from vipiski.pdf_reader import extract_pdf_text


def test_tsn_oazis_tochka_matches_modern_tochka_pdf_format():
    pdf_path = Path(r"D:\Выписки\2026-07\06072026\оазис точка.pdf")
    if not pdf_path.is_file():
        return

    accounts = [
        {
            "account_code": "tsn_oazis_tochka",
            "company_code": "tsn_oazis",
            "display_name": "ТСН Оазис Точка",
            "bank": "tochka",
            "parser": "tochka_outgoing_balance",
            "match_all": ['ТОВАРИЩЕСТВО СОБСТВЕННИКОВ НЕДВИЖИМОСТИ "ОАЗИС"'],
            "active": True,
        }
    ]
    text = extract_pdf_text(pdf_path)
    assert "40703810220000003335" not in text
    assert 'ТОВАРИЩЕСТВО СОБСТВЕННИКОВ НЕДВИЖИМОСТИ "ОАЗИС"' in text

    updates, unmatched = parse_pdfs_with_unmatched(
        [pdf_path], accounts, daysbr="06", monthsbr="J"
    )
    assert unmatched == []
    assert updates == {"tsn_oazis_tochka": Decimal("426441.93")}
