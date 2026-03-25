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
from decimal import Decimal

log = logging.getLogger(__name__)

_EXCEL_SERIAL_ORIGIN = dt.datetime(1899, 12, 30)


def parse_deposit_amount_cell(raw: str) -> Decimal:
    """Parse column **G** amount (spaces, NBSP, comma decimal) to ``Decimal``."""
    s = (
        str(raw or "")
        .strip()
        .replace("\xa0", " ")
        .replace(" ", "")
        .replace(",", ".")
    )
    if not s:
        return Decimal(0)
    try:
        return Decimal(s)
    except Exception:
        return Decimal(0)


def parse_deposit_maturity_date(raw: str) -> dt.date | None:
    """
    Parse column **J** maturity date: Excel / Google serial (days since 1899-12-30)
    or text ``dd.mm.yyyy`` / ``dd/mm/yyyy`` / ``yyyy-mm-dd``.
    """
    s = (raw or "").strip().replace("\xa0", " ")
    if not s:
        return None
    try:
        serial = float(s.replace(" ", "").replace(",", "."))
    except ValueError:
        for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                return dt.datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        return None
    try:
        d = _EXCEL_SERIAL_ORIGIN + dt.timedelta(days=serial)
        return d.date()
    except (OverflowError, ValueError):
        return None


def _fmt_deposit_amount(amount: Decimal) -> str:
    """Format deposit amount as integer with dot thousands separator (``1.500.000``)."""
    s = format(int(amount), ",")
    return s.replace(",", ".")


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
        company_name = row[0].strip()
        if not company_name:
            continue
        amount = parse_deposit_amount_cell(row[6])
        if amount == 0:
            log.debug("Deposit row %d skipped: empty or zero amount", i + 1)
            continue
        raw_date = row[9].strip()
        if not raw_date:
            log.debug("Deposit row %d skipped: empty date", i + 1)
            continue
        mat = parse_deposit_maturity_date(raw_date)
        formatted_date = mat.strftime("%d.%m.%Y") if mat is not None else raw_date
        deposits_dict.setdefault(company_name, []).append(
            f"Размещен депозит на сумму {_fmt_deposit_amount(amount)} до {formatted_date}"
        )
    return deposits_dict
