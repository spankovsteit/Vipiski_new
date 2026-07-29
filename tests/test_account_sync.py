from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook

from vipiski.account_sync import sync_accounts_from_excel
from vipiski.engine import parse_pdfs_with_unmatched
from vipiski.google_sync import apply_merged_balances_to_raw_sheet


def _write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_excel(path: Path, rows: list[tuple[str, str, str]]) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Счета"
    ws.append(["Организация", "Банк", "Расчетный счет"])
    for r in rows:
        ws.append(list(r))
    wb.save(path)


def _make_1c_export_excel(path: Path, rows: list[tuple[str, str, str]]) -> None:
    """1C list export: metadata rows, then header on row 8 (0-based index 7)."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Лист_1"
    for _ in range(6):
        ws.append([None] * 8)
    ws.append(["Отбор: Владелец.Сокращенное наименование Заполнено"] + [None] * 7)
    ws.append([None] * 8)
    ws.append(
        [
            "Номер счета",
            None,
            None,
            "Владелец.Сокращенное наименование",
            None,
            None,
            "Банк.Наименование",
            "Количество записей",
        ]
    )
    for company, bank, account in rows:
        ws.append([account, None, None, company, None, None, bank, 1])
    wb.save(path)


def test_sync_accounts_from_excel_adds_accounts_and_company_links(tmp_path: Path):
    accounts_path = tmp_path / "accounts.json"
    companies_path = tmp_path / "companies.json"
    excel_path = tmp_path / "Расчетные счета.xlsx"

    _write_json(accounts_path, [])
    _write_json(
        companies_path,
        [
            {
                "company_code": "reaktiv",
                "display_name": 'ООО "Реактив"',
                "accounts": ["reaktiv_legacy"],
                "active": True,
            }
        ],
    )
    _make_excel(
        excel_path,
        [
            ('ООО "Реактив"', "Сбер", "40702810900000001234"),
            ('ООО "Реактив"', "ВТБ", "40702810900000005678"),
        ],
    )

    stats = sync_accounts_from_excel(
        excel_path=excel_path,
        accounts_json_path=accounts_path,
        companies_json_path=companies_path,
    )
    assert stats.added_accounts == 2
    assert stats.linked_company_accounts == 2

    accounts = json.loads(accounts_path.read_text(encoding="utf-8"))
    codes = {a["account_code"] for a in accounts}
    assert "reaktiv_sber_1234" in codes
    assert "reaktiv_vtb_5678" in codes
    reaktiv_sber = next(a for a in accounts if a["account_code"] == "reaktiv_sber_1234")
    assert reaktiv_sber["parser"] == "sber_outgoing_balance"
    assert "СберБизнес" in reaktiv_sber["match_all"]
    assert reaktiv_sber["active"] is True
    assert reaktiv_sber["business_date"]

    companies = json.loads(companies_path.read_text(encoding="utf-8"))
    accs = companies[0]["accounts"]
    assert "reaktiv_sber_1234" in accs
    assert "reaktiv_vtb_5678" in accs


def test_sync_accounts_from_1c_export_layout(tmp_path: Path):
    accounts_path = tmp_path / "accounts.json"
    companies_path = tmp_path / "companies.json"
    excel_path = tmp_path / "Расчетные счета.xlsx"
    _write_json(accounts_path, [])
    _write_json(
        companies_path,
        [{"company_code": "reaktiv", "display_name": 'ООО "Реактив"', "accounts": [], "active": True}],
    )
    _make_1c_export_excel(
        excel_path,
        [('ООО "Реактив"', "СЕВЕРО-ЗАПАДНЫЙ БАНК ПАО СБЕРБАНК", "40702810900000001234")],
    )
    stats = sync_accounts_from_excel(
        excel_path=excel_path,
        accounts_json_path=accounts_path,
        companies_json_path=companies_path,
    )
    assert stats.added_accounts == 1
    accounts = json.loads(accounts_path.read_text(encoding="utf-8"))
    assert accounts[0]["account_code"] == "reaktiv_sber_1234"


def test_sync_accounts_from_excel_idempotent(tmp_path: Path):
    accounts_path = tmp_path / "accounts.json"
    companies_path = tmp_path / "companies.json"
    excel_path = tmp_path / "Расчетные счета.xlsx"
    _write_json(accounts_path, [])
    _write_json(
        companies_path,
        [{"company_code": "reaktiv", "display_name": 'ООО "Реактив"', "accounts": [], "active": True}],
    )
    _make_excel(excel_path, [('ООО "Реактив"', "Сбер", "40702810900000001234")])

    first = sync_accounts_from_excel(
        excel_path=excel_path,
        accounts_json_path=accounts_path,
        companies_json_path=companies_path,
    )
    second = sync_accounts_from_excel(
        excel_path=excel_path,
        accounts_json_path=accounts_path,
        companies_json_path=companies_path,
    )
    assert first.added_accounts == 1
    assert second.added_accounts == 0

    accounts = json.loads(accounts_path.read_text(encoding="utf-8"))
    assert len(accounts) == 1


def test_sync_accounts_enriches_legacy_rule_without_duplicating(tmp_path: Path):
    accounts_path = tmp_path / "accounts.json"
    companies_path = tmp_path / "companies.json"
    excel_path = tmp_path / "Расчетные счета.xlsx"
    _write_json(
        accounts_path,
        [
            {
                "account_code": "sp_impost_sber",
                "company_code": "sp_impost",
                "display_name": 'ООО "СП-Импост" СБЕР',
                "bank": "sber",
                "parser": "sber_outgoing_balance",
                "match_all": ['ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СП-ИМПОСТ"', "СберБизнес"],
                "active": True,
            }
        ],
    )
    _write_json(
        companies_path,
        [
            {
                "company_code": "sp_impost",
                "display_name": 'ООО "СП-Импост"',
                "accounts": ["sp_impost_sber"],
                "active": True,
            }
        ],
    )
    _make_excel(excel_path, [('ООО "СП-Импост"', "Сбер", "40702810355710017205")])

    stats = sync_accounts_from_excel(
        excel_path=excel_path,
        accounts_json_path=accounts_path,
        companies_json_path=companies_path,
    )
    assert stats.added_accounts == 0

    accounts = json.loads(accounts_path.read_text(encoding="utf-8"))
    assert len(accounts) == 1
    assert "40702810355710017205" in "".join(accounts[0]["match_all"])

    companies = json.loads(companies_path.read_text(encoding="utf-8"))
    assert companies[0]["accounts"] == ["sp_impost_sber"]


def test_sync_accounts_does_not_add_account_digits_to_tochka_legacy_rule(tmp_path):
    accounts_path = tmp_path / "accounts.json"
    companies_path = tmp_path / "companies.json"
    excel_path = tmp_path / "Расчетные счета.xlsx"
    _write_json(
        accounts_path,
        [
            {
                "account_code": "tsn_oazis_tochka",
                "company_code": "tsn_oazis",
                "display_name": 'ТСН "ОАЗИС" TOCHKA',
                "bank": "tochka",
                "parser": "tochka_outgoing_balance",
                "match_all": ['ТОВАРИЩЕСТВО СОБСТВЕННИКОВ НЕДВИЖИМОСТИ "ОАЗИС"'],
                "active": True,
            }
        ],
    )
    _write_json(
        companies_path,
        [
            {
                "company_code": "tsn_oazis",
                "display_name": 'ТСН "ОАЗИС"',
                "accounts": ["tsn_oazis_tochka"],
                "active": True,
            }
        ],
    )
    _make_excel(
        excel_path,
        [('ТСН "ОАЗИС"', "Точка", "40703810220000003335")],
    )

    sync_accounts_from_excel(
        excel_path=excel_path,
        accounts_json_path=accounts_path,
        companies_json_path=companies_path,
    )
    accounts = json.loads(accounts_path.read_text(encoding="utf-8"))
    assert accounts[0]["match_all"] == [
        'ТОВАРИЩЕСТВО СОБСТВЕННИКОВ НЕДВИЖИМОСТИ "ОАЗИС"'
    ]


def test_sync_accounts_from_excel_dry_run_does_not_write_files(tmp_path: Path):
    accounts_path = tmp_path / "accounts.json"
    companies_path = tmp_path / "companies.json"
    excel_path = tmp_path / "Расчетные счета.xlsx"
    _write_json(accounts_path, [])
    _write_json(
        companies_path,
        [{"company_code": "reaktiv", "display_name": 'ООО "Реактив"', "accounts": [], "active": True}],
    )
    _make_excel(excel_path, [('ООО "Реактив"', "Сбер", "40702810900000001234")])

    stats = sync_accounts_from_excel(
        excel_path=excel_path,
        accounts_json_path=accounts_path,
        companies_json_path=companies_path,
        dry_run=True,
    )
    assert stats.added_accounts == 1
    assert stats.dry_run is True
    # Files are unchanged in dry-run mode.
    assert json.loads(accounts_path.read_text(encoding="utf-8")) == []
    assert json.loads(companies_path.read_text(encoding="utf-8"))[0]["accounts"] == []


def test_reparse_after_excel_sync_matches_previously_unmatched(tmp_path: Path, monkeypatch):
    accounts_path = tmp_path / "accounts.json"
    companies_path = tmp_path / "companies.json"
    excel_path = tmp_path / "Расчетные счета.xlsx"
    pdf_path = tmp_path / "new-sber.pdf"
    pdf_path.write_bytes(b"%PDF")

    _write_json(accounts_path, [])
    _write_json(
        companies_path,
        [{"company_code": "reaktiv", "display_name": 'ООО "Реактив"', "accounts": [], "active": True}],
    )
    _make_excel(excel_path, [('ООО "Реактив"', "Сбер", "40702810900000001234")])

    text = (
        'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "РЕАКТИВ"\n'
        "СберБизнес\n"
        "40702810900000001234\n"
        "Исходящий остаток 0,00 1 234,56\n"
    )
    monkeypatch.setattr("vipiski.engine.extract_pdf_text", lambda _: text)

    updates, unmatched = parse_pdfs_with_unmatched([pdf_path], [], daysbr="26", monthsbr="M")
    assert updates == {}
    assert unmatched == [pdf_path]

    sync_accounts_from_excel(
        excel_path=excel_path,
        accounts_json_path=accounts_path,
        companies_json_path=companies_path,
    )
    accounts = json.loads(accounts_path.read_text(encoding="utf-8"))
    updates2, unmatched2 = parse_pdfs_with_unmatched([pdf_path], accounts, daysbr="26", monthsbr="M")
    assert updates2 == {"reaktiv_sber_1234": Decimal("1234.56")}
    assert unmatched2 == []


class _FakeRawWs:
    def __init__(self) -> None:
        self.row_count = 100
        self.col_count = 6
        self.calls: list[tuple[list[dict], str | None]] = []

    def batch_update(self, updates, value_input_option=None):
        self.calls.append((updates, value_input_option))

    def resize(self, rows, cols):
        self.row_count = rows
        self.col_count = cols


def test_apply_merged_balances_appends_full_extended_row():
    ws = _FakeRawWs()
    final = {"reaktiv_sber_1234": Decimal("1234.56")}
    row_codes: list[tuple[int, str]] = []
    header = ["account_code", "company_code", "bank", "balance", "business_date", "active"]
    meta = {
        "reaktiv_sber_1234": {
            "company_code": "reaktiv",
            "bank": "sber",
            "business_date": "28.05.2026",
            "active": True,
        }
    }
    apply_merged_balances_to_raw_sheet(
        ws,
        final,
        row_codes,
        header,
        ["reaktiv_sber_1234"],
        current_row_count=1,
        account_meta=meta,
    )
    assert len(ws.calls) == 1
    updates, opt = ws.calls[0]
    assert opt == "USER_ENTERED"
    assert updates[0]["range"] == "A2:F2"
    assert updates[0]["values"][0] == [
        "reaktiv_sber_1234",
        "reaktiv",
        "sber",
        "1234,56",
        "28.05.2026",
        True,
    ]
