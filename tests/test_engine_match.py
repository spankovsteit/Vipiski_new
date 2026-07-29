from decimal import Decimal
from pathlib import Path

from vipiski.engine import _match_all_satisfied, parse_pdfs_with_unmatched


def test_match_all_ignores_extra_whitespace():
    text = 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ  "СП-ИМПОСТ"'
    needles = ['ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СП-ИМПОСТ"']
    assert _match_all_satisfied(text, needles)


def test_parse_sp_impost_sber_pdf(tmp_path: Path):
    pdf = Path(r"c:\Users\s.pankov\Desktop\сп импост сбер.pdf")
    if not pdf.is_file():
        return

    rules = [
        {
            "account_code": "sp_impost_sber",
            "display_name": 'ООО СП-Импост СБЕР',
            "parser": "sber_outgoing_balance",
            "match_all": [
                "40702810355710017205",
                'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СП-ИМПОСТ"',
                "СберБизнес",
            ],
            "active": True,
        }
    ]
    updates, unmatched = parse_pdfs_with_unmatched(
        [pdf], rules, daysbr="08", monthsbr="J"
    )
    assert unmatched == []
    assert updates["sp_impost_sber"] == Decimal("3475394.22")
