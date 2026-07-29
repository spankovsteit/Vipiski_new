#!/usr/bin/env python3
"""One-off helper: build today's balance report and send to Bitrix24 chat."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vipiski.bitrix24_client import Bitrix24SendError, send_bitrix24_message
from vipiski.deposits import build_deposits_dict
from vipiski.google_sync import sync
from vipiski.loaders import load_accounts, load_companies
from vipiski.report import build_telegram_text
from vipiski.settings import load_settings


def main() -> int:
    settings = load_settings()
    if not settings.bitrix24_webhook_url or not settings.bitrix24_dialog_id:
        print(
            "Set BITRIX24_WEBHOOK_URL and BITRIX24_DIALOG_ID in .env",
            file=sys.stderr,
        )
        return 1

    accounts = load_accounts(settings.accounts_config_path)
    companies = load_companies(settings.companies_config_path)
    result = sync(
        settings.google_credentials_path,
        settings.google_spreadsheet_name,
        settings.google_worksheet_balances,
        settings.google_worksheet_raw,
        {},
        companies,
        formula_locale=settings.sheets_formula_locale,
        account_balances_use_formulas=settings.account_balances_use_formulas,
        account_meta={
            str(a.get("account_code")): a for a in accounts if a.get("account_code")
        },
    )
    balances = {
        k: (v if v is not None else Decimal(0))
        for k, v in result.final_balances.items()
    }
    for code in [a["account_code"] for a in accounts if a.get("active", True)]:
        balances.setdefault(code, Decimal(0))

    text = build_telegram_text(
        companies, accounts, balances, build_deposits_dict(result.balances_sheet_data)
    )
    (ROOT / "telegram_preview.txt").write_text(text, encoding="utf-8")

    try:
        send_bitrix24_message(
            settings.bitrix24_webhook_url,
            settings.bitrix24_dialog_id,
            text,
        )
    except Bitrix24SendError as e:
        print(e, file=sys.stderr)
        return 1

    print(
        f"done: {len(text)} chars -> {settings.bitrix24_dialog_id}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
