"""
Google Sheets integration: per-account **raw_balances** + company totals on **Account_balances**.

Data flow
---------
- **raw_balances** — PDF merges **only into the balance column** (detected from the
  header, usually **D**); columns A–C, E–F are left as on the sheet. New
  ``account_code`` values from PDFs get a new row with **A** and the balance column
  filled only. Balances use RU-style text (``672 116,05``) and ``USER_ENTERED``.
- **Account_balances** — column **A** can be synced from ``account_balances_label``
  (same row as ``google_total_cell``, or ``account_balances_name_cell`` when set).
  After the Telegram body is built, ``main`` mirrors it to cell **P1** for optional
  Google Apps Script delivery (see ``write_account_balances_telegram_outbox``).
  Cell ``google_total_cell`` (column **D**) holds either a **formula**:
  sum from ``raw_balances`` **plus** a **numeric literal** (no ``G`` reference) when
  the pipeline decides the deposit counts: column **J** is parsed in Python and
  compared to the run date; if it matches **today**, **G** is read and embedded as
  the literal addend. Re-run after changing **G** or **J** so the formula updates.
  The sheet formula itself has **no** date check on **J**.

Formula locale
--------------
Russian spreadsheets use ``;`` as the argument separator and localized function
names (``СУММПРОИЗВ``, ``ПОИСКПОЗ``, …). Set ``VIPISKI_SHEETS_FORMULA_LOCALE``
to ``ru`` (default) or ``en`` to match the spreadsheet locale
(File → Settings → locale).

Safety rail
-----------
If there is **no** data in Raw and **no** PDF updates, ``sync()`` returns early
without rewriting Raw or touching company cells.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

import gspread
from gspread.exceptions import WorksheetNotFound

from vipiski.deposits import parse_deposit_amount_cell, parse_deposit_maturity_date

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class SyncResult:
    """
    Return value of :func:`sync`.

    Carries open worksheet handles and in-memory data so callers do not need to
    re-authenticate or re-read sheets after the sync run.
    """

    ws_bal: Any
    ws_raw: Any
    final_balances: dict[str, Optional[Decimal]]
    balances_sheet_data: list[list[str]]

RAW_HEADER_EXTENDED = [
    "account_code",
    "company_code",
    "bank",
    "balance",
    "business_date",
    "active",
]


def format_balance_for_ru_sheet(value: Decimal) -> str:
    """
    String for ``USER_ENTERED`` in a Russian-locale spreadsheet: thousands
    separated by spaces, comma as decimal separator (e.g. ``672 116,05``).
    """
    q = value.quantize(Decimal("0.01"))
    s = format(q, "f")
    neg = s.startswith("-")
    if neg:
        s = s[1:]
    if "." in s:
        int_part, frac = s.split(".", 1)
    else:
        int_part, frac = s, "00"
    frac = (frac + "00")[:2]
    groups: list[str] = []
    while int_part:
        groups.append(int_part[-3:])
        int_part = int_part[:-3]
    spaced = " ".join(reversed(groups)) if groups else "0"
    sign = "-" if neg else ""
    return f"{sign}{spaced},{frac}"


def open_client(credentials_path: Path):
    """Service-account client (sheet must be shared with the service email)."""
    if not credentials_path.is_file():
        raise FileNotFoundError(f"Google credentials not found: {credentials_path}")
    return gspread.service_account(filename=str(credentials_path))


def _a1_row_number(cell_ref: str) -> int:
    """Extract 1-based row index from ``D14`` or ``$D$14``."""
    t = re.sub(r"\$", "", cell_ref.strip())
    m = re.match(r"^[A-Za-z]+(\d+)$", t)
    if not m:
        raise ValueError(f"Bad cell ref: {cell_ref!r}")
    return int(m.group(1))


def _column_a_from_total_cell(total_cell: str) -> str:
    """
    Map ``D14`` → ``A14`` so the company title sits in column A of the same row.

    Accepts simple A1 notation only (optional leading ``$`` stripped).
    """
    return f"A{_a1_row_number(total_cell)}"


# Column G (6), J (9) on Account_balances — deposit amount and maturity (see deposits.py).
_ACCOUNT_BALANCES_DEPOSIT_COL = 6
_ACCOUNT_BALANCES_MATURITY_COL = 9


def _deposit_amount_if_mature_today(
    all_values: list[list[str]],
    total_cell_a1: str,
    *,
    as_of: date | None = None,
) -> Decimal:
    """
    Deposit in **G** counts only when **J** parses to the same calendar day as ``as_of``
    (default: today).
    """
    as_of = as_of or date.today()
    try:
        rn = _a1_row_number(total_cell_a1)
    except ValueError:
        return Decimal(0)
    i = rn - 1
    if i < 0 or i >= len(all_values):
        return Decimal(0)
    row = all_values[i]
    j_raw = row[_ACCOUNT_BALANCES_MATURITY_COL] if len(row) > _ACCOUNT_BALANCES_MATURITY_COL else ""
    mat = parse_deposit_maturity_date(str(j_raw))
    if mat != as_of:
        return Decimal(0)
    g_raw = row[_ACCOUNT_BALANCES_DEPOSIT_COL] if len(row) > _ACCOUNT_BALANCES_DEPOSIT_COL else ""
    return parse_deposit_amount_cell(str(g_raw))


def _decimal_abs_literal_for_formula(magnitude: Decimal, locale: str) -> str:
    """
    Positive magnitude as a constant in a Sheets formula (no thousands separators).
    RU: comma decimal; EN: dot.
    """
    q = magnitude.copy_abs().quantize(Decimal("0.01"))
    s = format(q, "f")
    if (locale or "ru").lower()[:2] == "en":
        return s
    return s.replace(".", ",")


def _deposit_formula_suffix(addend: Decimal, locale: str) -> str:
    """``+1,23`` / ``-4,56`` / empty when zero."""
    if addend == 0:
        return ""
    lit = _decimal_abs_literal_for_formula(addend, locale)
    if addend > 0:
        return f"+{lit}"
    return f"-{lit}"


def write_account_balance_labels(ws_balances, companies: list[dict[str, Any]]) -> None:
    """
    Write ``account_balances_label`` into column A (or ``account_balances_name_cell``).

    Skips companies without a label. Row is inferred from ``google_total_cell``
    unless ``account_balances_name_cell`` (e.g. ``A45``) is set explicitly.
    """
    updates: list[dict] = []
    for co in companies:
        if not co.get("active", True):
            continue
        label = (co.get("account_balances_label") or "").strip()
        if not label:
            continue
        explicit = (co.get("account_balances_name_cell") or "").strip()
        if explicit:
            a_cell = explicit
        else:
            cell = co.get("google_total_cell")
            if not cell:
                continue
            try:
                a_cell = _column_a_from_total_cell(str(cell))
            except ValueError as e:
                log.warning("Skip label for %s: %s", co.get("company_code"), e)
                continue
        updates.append({"range": a_cell, "values": [[label]]})
    if updates:
        ws_balances.batch_update(updates, value_input_option="USER_ENTERED")
        log.info("Updated %d company title cells (column A)", len(updates))


def _quote_sheet_title_for_formula(title: str) -> str:
    """Wrap sheet title in single quotes; escape embedded quotes."""
    escaped = title.replace("'", "''")
    return f"'{escaped}'"


def _balance_column_index(header_row: list[str]) -> int:
    """0-based index of the balance column (legacy: column B → index 1)."""
    if not header_row:
        return 1
    lowered = [str(c).strip().lower() for c in header_row]
    try:
        return lowered.index("balance")
    except ValueError:
        return 1


def _balance_column_letter(header_row: list[str]) -> str:
    """A1 column letter for the balance field (A–F only)."""
    idx = _balance_column_index(header_row)
    if not 0 <= idx <= 25:
        raise ValueError(f"Balance column index out of range: {idx}")
    return chr(65 + idx)


def _company_total_formula(
    raw_sheet_title: str,
    account_codes: list[str],
    *,
    locale: str,
    deposit_addend: Decimal | None = None,
) -> str:
    """
    Sum ``raw_balances`` for ``account_codes`` (column F active), then add
    ``deposit_addend`` as a **literal** (already zero when **J** ≠ today — decided
    in Python before calling this).
    """
    loc = (locale or "ru").lower()[:2]
    sep = ";" if loc != "en" else ","
    add = Decimal(0) if deposit_addend is None else deposit_addend
    dep = _deposit_formula_suffix(add, loc)

    if not account_codes:
        if add == 0:
            return "=0"
        lit = _decimal_abs_literal_for_formula(add, loc)
        if add > 0:
            return f"={lit}"
        return f"=-{lit}"

    q = _quote_sheet_title_for_formula(raw_sheet_title)
    a_range = f"{q}!A2:A"
    d_range = f"{q}!D2:D"
    f_range = f"{q}!F2:F"
    arr = "{" + ";".join(f'"{c}"' for c in account_codes) + "}"
    if loc == "en":
        core = (
            f"IFERROR(SUMPRODUCT(ISNUMBER(MATCH({a_range}, {arr}, 0))"
            f"*({f_range}<>FALSE)*({d_range})), 0)"
        )
        return f"={core}{dep}"
    return (
        f"=ЕСЛИОШИБКА(СУММПРОИЗВ(ЕЧИСЛО(ПОИСКПОЗ({a_range}{sep} {arr}{sep} 0))"
        f"*({f_range}<>ЛОЖЬ)*({d_range})){sep} 0){dep}"
    )


def ensure_worksheet(sh, title: str, rows: int = 500, cols: int = 6):
    """
    Open worksheet by title or create it.

    Raw-like sheets get the extended header row so ``read_raw_balances`` can find
    the balance column.
    """
    try:
        return sh.worksheet(title)
    except WorksheetNotFound:
        log.info("Creating worksheet %r", title)
        ws = sh.add_worksheet(title=title, rows=rows, cols=max(cols, 6))
        if title.lower().startswith("raw"):
            ws.update(
                "A1:F1",
                [RAW_HEADER_EXTENDED],
                value_input_option="USER_ENTERED",
            )
        return ws


def read_raw_balances_ordered(
    ws,
    *,
    prefetched_rows: list[list[str]] | None = None,
) -> tuple[list[str], dict[str, Optional[Decimal]], list[tuple[int, str]]]:
    """
    Read ``raw_balances`` preserving **row order** (column A top to bottom).

    Every non-empty ``account_code`` is kept. An **empty** balance cell is stored
    as ``None``. If the same code appears twice, the **last** row wins for the
    merged dict; ``row_codes`` lists **every** data row as ``(1-based row, code)``
    so the balance column can be updated per row.

    Parameters
    ----------
    prefetched_rows
        If provided, used instead of calling ``ws.get_all_values()`` (avoids an
        extra API round-trip when the caller already holds the rows).

    Returns
    -------
    order
        First-seen order of distinct codes (for merge tail logic).
    balances
        code → last balance on sheet (or ``None``).
    row_codes
        ``(sheet_row_number, account_code)`` for each non-empty column A row.
    """
    rows = prefetched_rows if prefetched_rows is not None else ws.get_all_values()
    if not rows:
        return [], {}, []
    bal_idx = _balance_column_index(rows[0])
    order: list[str] = []
    out: dict[str, Optional[Decimal]] = {}
    row_codes: list[tuple[int, str]] = []
    for i, row in enumerate(rows):
        if i == 0 and row and str(row[0]).strip().lower() == "account_code":
            continue
        if not row:
            continue
        code = str(row[0]).strip()
        if not code:
            continue
        rownum = i + 1
        row_codes.append((rownum, code))
        raw = ""
        if len(row) > bal_idx:
            raw = (
                str(row[bal_idx])
                .strip()
                .replace("\xa0", " ")
                .replace(" ", "")
                .replace(",", ".")
            )
        if raw:
            try:
                val: Optional[Decimal] = Decimal(raw)
            except Exception:
                log.debug("Bad balance for %s: %r — leaving empty", code, row[bal_idx])
                val = None
        else:
            val = None
        if code not in out:
            order.append(code)
        out[code] = val
    return order, out, row_codes


def read_raw_balances(ws) -> dict[str, Decimal]:
    """
    Parse ``account_code`` → **balance** for pipelines that need a number.

    ``None`` (empty cell) is returned as ``Decimal(0)`` for arithmetic / Telegram.
    """
    _, balances, _ = read_raw_balances_ordered(ws)
    return {k: (v if v is not None else Decimal(0)) for k, v in balances.items()}


def _batch_update_batched(
    ws, updates: list[dict[str, Any]], *, chunk_size: int = 400
) -> None:
    for i in range(0, len(updates), chunk_size):
        ws.batch_update(
            updates[i : i + chunk_size],
            value_input_option="USER_ENTERED",
        )


def apply_merged_balances_to_raw_sheet(
    ws,
    final: dict[str, Optional[Decimal]],
    row_codes: list[tuple[int, str]],
    header_row: list[str],
    new_codes_sorted: list[str],
    *,
    current_row_count: int | None = None,
) -> None:
    """
    Write merged balances **only** into the balance column for existing rows;
    append new rows with column **A** + balance column only (B,C,E,F untouched).

    Parameters
    ----------
    current_row_count
        Number of rows currently on the sheet (avoids an extra ``get_all_values``
        call when the caller already knows it).
    """
    bal_col = _balance_column_letter(header_row)
    updates: list[dict] = []
    for rownum, code in row_codes:
        bal = final.get(code)
        cell = "" if bal is None else format_balance_for_ru_sheet(bal)
        updates.append({"range": f"{bal_col}{rownum}", "values": [[cell]]})

    if current_row_count is None:
        current_row_count = len(ws.get_all_values())
    next_row = current_row_count + 1
    for code in new_codes_sorted:
        bal = final.get(code)
        if bal is None:
            continue
        updates.append({"range": f"A{next_row}", "values": [[code]]})
        updates.append(
            {
                "range": f"{bal_col}{next_row}",
                "values": [[format_balance_for_ru_sheet(bal)]],
            }
        )
        next_row += 1

    if not updates:
        return
    need = next_row - 1 + 5
    if ws.row_count < need:
        ws.resize(rows=max(ws.row_count, need), cols=max(ws.col_count, 6))
    _batch_update_batched(ws, updates)
    log.info(
        "raw_balances: updated %d balance cell(s), appended %d new row(s)",
        len(row_codes),
        len(new_codes_sorted),
    )


def write_company_totals(
    ws_balances,
    companies: list[dict[str, Any]],
    balances_by_account: dict[str, Decimal],
    *,
    prefetched_data: list[list[str]] | None = None,
) -> None:
    """
    Sum each company's ``accounts`` plus column **G** when **J** on the same row is
    today, and write the **numeric** total to ``google_total_cell`` (legacy path).
    """
    all_data = prefetched_data if prefetched_data is not None else ws_balances.get_all_values()
    updates: list[dict] = []
    for co in companies:
        if not co.get("active", True):
            continue
        cell = co.get("google_total_cell")
        if not cell:
            continue
        accs = co.get("accounts") or []
        acct_sum = sum(balances_by_account.get(a, Decimal(0)) for a in accs)
        dep = _deposit_amount_if_mature_today(all_data, str(cell))
        total = acct_sum + dep
        updates.append(
            {"range": cell, "values": [[format_balance_for_ru_sheet(total)]]}
        )
    if updates:
        ws_balances.batch_update(updates, value_input_option="USER_ENTERED")
        log.info("Updated %d company total cells (numeric)", len(updates))


def write_company_total_formulas(
    ws_balances,
    companies: list[dict[str, Any]],
    *,
    raw_sheet_title: str,
    formula_locale: str,
    prefetched_data: list[list[str]] | None = None,
) -> None:
    """
    Write one **formula** per ``google_total_cell``: raw sum plus **G** as a **literal**
    only when **J** (parsed in Python) is the run date.
    """
    all_data = prefetched_data if prefetched_data is not None else ws_balances.get_all_values()
    updates: list[dict] = []
    for co in companies:
        if not co.get("active", True):
            continue
        cell = co.get("google_total_cell")
        if not cell:
            continue
        accs = [str(a) for a in (co.get("accounts") or []) if a]
        dep = _deposit_amount_if_mature_today(all_data, str(cell))
        formula = _company_total_formula(
            raw_sheet_title,
            accs,
            locale=formula_locale,
            deposit_addend=dep,
        )
        updates.append({"range": cell, "values": [[formula]]})
    if updates:
        ws_balances.batch_update(updates, value_input_option="USER_ENTERED")
        log.info("Updated %d company total cells (formulas)", len(updates))


# Google Sheets hard limit per cell is 50k characters; stay slightly under.
_SHEETS_CELL_CHAR_SOFT_LIMIT = 50_000


def write_account_balances_telegram_outbox(ws_balances, text: str) -> None:
    """
    Write the Telegram report body to **P1** on the Account_balances worksheet
    (e.g. for a sheet-bound Apps Script that posts to Telegram and clears **P1**).
    Longer text is truncated with a log warning.
    """
    body = text or ""
    if len(body) > _SHEETS_CELL_CHAR_SOFT_LIMIT:
        log.warning(
            "Telegram outbox: truncating P1 from %d to %d characters",
            len(body),
            _SHEETS_CELL_CHAR_SOFT_LIMIT,
        )
        body = body[: _SHEETS_CELL_CHAR_SOFT_LIMIT]
    ws_balances.batch_update(
        [{"range": "P1", "values": [[body]]}],
        value_input_option="USER_ENTERED",
    )
    log.info("Account_balances!P1: wrote Telegram text (%d chars)", len(body))


def sync(
    credentials_path: Path,
    spreadsheet_name: str,
    balances_sheet: str,
    raw_sheet: str,
    pdf_updates: dict[str, Decimal],
    companies: list[dict[str, Any]],
    *,
    formula_locale: str = "ru",
    account_balances_use_formulas: bool = True,
) -> SyncResult:
    """
    Merge ``pdf_updates`` into the Raw sheet, then refresh company totals on
    ``Account_balances`` (formulas or numbers).

    Merge semantics
    ---------------
    Start from balances already on ``raw_balances`` (per ``account_code``). Then
    ``pdf_updates`` **overwrites** the **balance column only** for matching codes.
    Other columns are not modified. New codes from PDFs only: one new row each with
    column A + balance only (append at bottom, sorted by code).

    Returns
    -------
    SyncResult
        Open worksheet handles, merged balances (in-memory), and a snapshot of
        ``Account_balances`` rows — so callers need no extra API calls.
    """
    gc = open_client(credentials_path)
    sh = gc.open(spreadsheet_name)
    ws_raw = ensure_worksheet(sh, raw_sheet)
    ws_bal = sh.worksheet(balances_sheet)

    # One read of Raw sheet — reused for merge and header detection.
    raw_rows = ws_raw.get_all_values()
    _, existing, row_codes = read_raw_balances_ordered(ws_raw, prefetched_rows=raw_rows)
    final: dict[str, Optional[Decimal]] = dict(existing)
    final.update(pdf_updates)
    if not final:
        log.warning(
            "Raw_balances empty and no PDF parses — leaving company cells unchanged"
        )
        all_bal_data = ws_bal.get_all_values()
        return SyncResult(
            ws_bal=ws_bal,
            ws_raw=ws_raw,
            final_balances=final,
            balances_sheet_data=all_bal_data,
        )
    in_sheet = {c for _, c in row_codes}
    tail = sorted(k for k in pdf_updates if k not in in_sheet)
    if pdf_updates:
        header_row = raw_rows[0] if raw_rows else list(RAW_HEADER_EXTENDED)
        apply_merged_balances_to_raw_sheet(
            ws_raw, final, row_codes, header_row, tail,
            current_row_count=len(raw_rows),
        )

    # Write labels before reading Account_balances so the snapshot is up-to-date.
    write_account_balance_labels(ws_bal, companies)

    # One read of Account_balances — passed to write_company_* to avoid a second call.
    all_bal_data = ws_bal.get_all_values()

    if account_balances_use_formulas:
        write_company_total_formulas(
            ws_bal,
            companies,
            raw_sheet_title=raw_sheet,
            formula_locale=formula_locale,
            prefetched_data=all_bal_data,
        )
    else:
        write_company_totals(
            ws_bal,
            companies,
            {k: (v if v is not None else Decimal(0)) for k, v in final.items()},
            prefetched_data=all_bal_data,
        )
    return SyncResult(
        ws_bal=ws_bal,
        ws_raw=ws_raw,
        final_balances=final,
        balances_sheet_data=all_bal_data,
    )
