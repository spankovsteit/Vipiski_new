"""
Parse **deposit** annotations from the same Google sheet as balances.

Source of truth
---------------
Legacy script read ``Account_balances`` with:
- column **A** — company / counterparty label (must match Telegram deposit keys),
- column **G** (index 6) — amount string,
- column **J** (index 9) — date (plain text or Excel serial as string).

If the sheet layout changes, update indices here and in operator documentation.

Date handling
-------------
If ``deposit_date`` parses as float, it is interpreted as Excel / Google serial
days from 1899-12-30 (same as old code). Otherwise the string is passed through.
"""

from __future__ import annotations

import datetime as dt
import logging

log = logging.getLogger(__name__)


def build_deposits_dict(all_data: list[list[str]]) -> dict[str, list[str]]:
    """
    Scan all rows; collect deposit messages keyed by company name.

    Returns
    -------
    dict[str, list[str]]
        Company name → list of human-readable deposit lines (may be multiple
        deposits per company).
    """
    deposits_dict: dict[str, list[str]] = {}
    for i, row in enumerate(all_data):
        if len(row) < 10:
            continue
        company_name = row[0]
        deposit_amount = row[6]
        deposit_date = row[9]
        if not (
            deposit_amount
            and deposit_amount.strip()
            and deposit_date
            and deposit_date.strip()
        ):
            continue
        company_name = company_name.strip()
        deposit_amount = deposit_amount.strip()
        deposit_date = deposit_date.strip()
        try:
            amount_str = deposit_amount.replace(" ", "").replace(",", ".")
            clean_amount = "".join(c for c in amount_str if c.isdigit() or c == ".")
            if not clean_amount:
                continue
            amount = float(clean_amount)
            formatted_amount = f"{amount:,.0f}".replace(",", ".")
            formatted_date = deposit_date
            try:
                date_value = float(deposit_date)
                base_date = dt.datetime(1899, 12, 30)
                date_obj = base_date + dt.timedelta(days=date_value)
                formatted_date = date_obj.strftime("%d.%m.%Y")
            except (ValueError, TypeError, OverflowError):
                pass
            if company_name not in deposits_dict:
                deposits_dict[company_name] = []
            deposits_dict[company_name].append(
                f"Размещен депозит на сумму {formatted_amount} до {formatted_date}"
            )
        except ValueError as e:
            log.debug("Deposit row %d skipped: %s", i + 1, e)
    return deposits_dict
