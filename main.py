#!/usr/bin/env python3
"""
Vipiski pipeline — end-to-end orchestration.

Data flow (high level)
----------------------
1. **Inbox** — PDF statements land in ``<VIPISKI_BASE_PATH>/<Текущие>/`` (or custom name).
2. **Archive** — Each run copies every ``*.pdf`` from inbox into
   ``<base>/<YYYY-MM>/<ddmmyyyy>/``. The month folder is the calendar month of the
   run date, **except on the 1st of a month**, when the parent folder is the
   **previous** month (day folder still uses that day's ``ddmmyyyy``).
   Existing files in the day folder with the same name are **overwritten** (no
   ``_1`` suffix copies).
3. **Inbox cleanup** — Only successfully copied source files are deleted (never wipe
   inbox on a failed copy).
4. **Parse** — For each archived PDF, extract text, walk account ``rules`` in order;
   the first rule whose ``match_all`` substrings all appear wins (same as a long
   ``if/elif`` chain). Parser output updates ``account_code → Decimal`` for that file.
5. **Google — raw_balances** — Merge PDF balances into the **balance column only**
   (header ``balance``, usually D); other columns stay as on the sheet. New
   ``account_code`` from PDFs append one row (A + balance). Empty balance cells
   stay empty until a PDF fills them.
6. **Google — Account_balances** — ``google_total_cell`` (column **D**) gets a
   **formula**: sum from ``raw_balances`` plus the **число из G** as a literal when
   **J** (срок депозита) matches the run date (**проверка в Python**, не в формуле).
   With formulas off, the same date rule applies to the numeric total.
   Set ``VIPISKI_ACCOUNT_BALANCES_USE_FORMULAS=false`` for numeric totals.
   If Raw is empty and no PDF produced data, **totals are not touched**.
7. **Notifications** — Build human-readable lines from Raw + ``companies`` + deposits
   scraped from the same balance sheet; mirror the full text to **Account_balances!P1**;
   then send to Telegram and/or Bitrix24 (split if over ~4000 chars).

Legacy note: ``Vipiski_ostatki.py`` used Excel (xlwings) as a scratch pad; this
pipeline uses **Raw_balances** as per-account storage instead.

Exit codes: 0 OK, 1 missing env, 2 Google error, 3 notification error.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from vipiski.dates import (
    archive_month_folder_name,
    is_weekend,
    day_folder_segment,
    sber_day_tokens,
    statement_reference_date,
)
from vipiski.deposits import build_deposits_dict
from vipiski.account_sync import SyncStats, sync_accounts_from_default_excel
from vipiski.engine import parse_pdfs_with_unmatched
from vipiski.files import ingest_pdfs, remove_sources_only
from vipiski.google_sync import (
    sync,
    write_account_balances_telegram_outbox,
)
from vipiski.loaders import load_accounts, load_companies
from vipiski.report import build_telegram_text
from vipiski.settings import load_settings, ROOT
from vipiski.bitrix24_client import Bitrix24SendError, send_bitrix24_message
from vipiski.telegram_client import TelegramSendError, send_telegram_message


def setup_logging(log_file: Path) -> None:
    """Log to UTF-8 file and stdout (operators see progress in console)."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> int:
    """
    Run one full cycle. Order of steps is intentional: filesystem first, then
    Google (single source of truth for balances after merge), then notification.
    """
    try:
        settings = load_settings()
    except KeyError as e:
        print(f"Missing required environment variable: {e}", file=sys.stderr)
        print(
            f"Set it in {ROOT / '.env'} (preferred) or {ROOT / '.env.example'}.",
            file=sys.stderr,
        )
        print(
            "Note: only .env was loaded in older versions; now .env.example is also "
            "read as fallback — if this still fails, check for typos (TELEGRAM_BOT_TOKEN) "
            "and that the value is on the same line without a broken quote.",
            file=sys.stderr,
        )
        return 1

    setup_logging(settings.log_file)
    log = logging.getLogger("main")

    # Optional scheduler guard: not a full holiday calendar, only Sat/Sun.
    if settings.skip_run_on_non_business_day and is_weekend(datetime.now().date()):
        log.info("Skipping run: weekend and VIPISKI_SKIP_NON_BUSINESS_DAY is set")
        return 0

    # Rules: either JSON (non-empty array) or built-in registry — see loaders.py.
    accounts = load_accounts(settings.accounts_config_path)
    companies = load_companies(settings.companies_config_path)

    # Archive layout: base / YYYY-MM / ddmmyyyy / *.pdf (1st → month = previous)
    month_seg = archive_month_folder_name()
    day_seg = day_folder_segment()
    folder_path = settings.base_path / month_seg
    putdir = folder_path / day_seg
    folder_path.mkdir(parents=True, exist_ok=True)

    # Copy then delete sources — returned list is only successfully copied paths.
    copied_sources = ingest_pdfs(
        settings.base_path, settings.src_current_dir_name, putdir
    )
    remove_sources_only(copied_sources)

    pdf_paths = sorted(putdir.glob("*.pdf"))
    log.info("Found %d PDF(s) in %s", len(pdf_paths), putdir)

    # Sber "suffix" parser slices text using calendar day + first letter of English
    # month (legacy behaviour), tied to "yesterday" relative to run time.
    ref = statement_reference_date()
    daysbr, monthsbr = sber_day_tokens(ref)
    log.info("Sber parser tokens: day=%s month_letter=%s (ref date %s)", daysbr, monthsbr, ref)

    # One winning account per PDF file (first matching rule in list order).
    parsed_updates, unmatched_pdf_paths = parse_pdfs_with_unmatched(
        pdf_paths, accounts, daysbr=daysbr, monthsbr=monthsbr
    )
    if unmatched_pdf_paths:
        try:
            sync_stats = sync_accounts_from_default_excel(
                accounts_json_path=settings.accounts_config_path,
                companies_json_path=settings.companies_config_path,
            )
        except Exception as e:
            log.warning("Excel account sync failed (continuing): %s", e)
            sync_stats = SyncStats(0, 0, 0, dry_run=False)
        if sync_stats.added_accounts > 0:
            if sync_stats.dry_run:
                log.info(
                    "Excel sync dry-run enabled; config files were not changed, skip re-parse"
                )
            else:
                log.info(
                    "Re-loading config after Excel sync (%d new accounts)",
                    sync_stats.added_accounts,
                )
                accounts = load_accounts(settings.accounts_config_path)
                companies = load_companies(settings.companies_config_path)
                reparsed_updates, still_unmatched = parse_pdfs_with_unmatched(
                    unmatched_pdf_paths, accounts, daysbr=daysbr, monthsbr=monthsbr
                )
                parsed_updates.update(reparsed_updates)
                if still_unmatched:
                    log.info(
                        "Still unmatched after Excel sync: %d file(s)",
                        len(still_unmatched),
                    )

    active_codes = [
        a["account_code"] for a in accounts if a.get("active", True)
    ]
    account_meta = {str(a.get("account_code")): a for a in accounts if a.get("account_code")}

    try:
        result = sync(
            settings.google_credentials_path,
            settings.google_spreadsheet_name,
            settings.google_worksheet_balances,
            settings.google_worksheet_raw,
            parsed_updates,
            companies,
            formula_locale=settings.sheets_formula_locale,
            account_balances_use_formulas=settings.account_balances_use_formulas,
            account_meta=account_meta,
        )
    except Exception as e:
        log.exception("Google sync failed: %s", e)
        return 2

    # Balances are already in memory from sync — no extra API call needed.
    balances: dict[str, Decimal] = {
        k: (v if v is not None else Decimal(0))
        for k, v in result.final_balances.items()
    }

    # Avoid sending a useless "all zeros" message when nothing was ever seeded.
    if not balances and not parsed_updates:
        log.info("No Raw_balances data and no PDF parses; skip notifications")
        return 0

    # Telegram shows every active account; missing Raw row → display 0 for that line.
    for c in active_codes:
        balances.setdefault(c, Decimal(0))

    # Deposit annotations live on Account_balances (A/G/J); snapshot already in result.
    deposits = build_deposits_dict(result.balances_sheet_data)

    text = build_telegram_text(companies, accounts, balances, deposits)
    try:
        write_account_balances_telegram_outbox(result.ws_bal, text)
    except Exception as e:
        log.exception("Failed to write Telegram text to Account_balances!P1: %s", e)

    if settings.skip_telegram:
        log.info("VIPISKI_SKIP_TELEGRAM set — Telegram not sent (Google sync completed)")
    else:
        try:
            send_telegram_message(
                settings.telegram_token, settings.telegram_chat_id, text
            )
        except TelegramSendError as e:
            # Network-level Telegram failures should not roll back successful Google sync.
            if e.transient:
                log.warning(
                    "Telegram transient failure after %d attempt(s): %s. "
                    "Google sync succeeded; message remains in Account_balances!P1.",
                    e.attempts,
                    e,
                )
                return 0
            log.exception("Telegram failed (non-transient): %s", e)
            if settings.telegram_soft_fail:
                log.warning(
                    "VIPISKI_TELEGRAM_SOFT_FAIL: exiting with success despite Telegram error"
                )
                return 0
            return 3
        except Exception as e:
            log.exception("Telegram failed: %s", e)
            if settings.telegram_soft_fail:
                log.warning(
                    "VIPISKI_TELEGRAM_SOFT_FAIL: exiting with success despite Telegram error"
                )
                return 0
            return 3

    bitrix_ready = (
        settings.bitrix24_webhook_url
        and settings.bitrix24_dialog_id
        and not settings.skip_bitrix24
    )
    if not bitrix_ready:
        if settings.skip_bitrix24:
            log.info("VIPISKI_SKIP_BITRIX24 set — Bitrix24 not sent")
        elif not settings.bitrix24_webhook_url or not settings.bitrix24_dialog_id:
            log.debug("Bitrix24 not configured — skip")
    else:
        try:
            send_bitrix24_message(
                settings.bitrix24_webhook_url,
                settings.bitrix24_dialog_id,
                text,
            )
        except Bitrix24SendError as e:
            if e.transient:
                log.warning(
                    "Bitrix24 transient failure after %d attempt(s): %s. "
                    "Google sync succeeded; message remains in Account_balances!P1.",
                    e.attempts,
                    e,
                )
                return 0
            log.exception("Bitrix24 failed (non-transient): %s", e)
            if settings.bitrix24_soft_fail:
                log.warning(
                    "VIPISKI_BITRIX24_SOFT_FAIL: exiting with success despite Bitrix24 error"
                )
                return 0
            return 3
        except Exception as e:
            log.exception("Bitrix24 failed: %s", e)
            if settings.bitrix24_soft_fail:
                log.warning(
                    "VIPISKI_BITRIX24_SOFT_FAIL: exiting with success despite Bitrix24 error"
                )
                return 0
            return 3

    log.info("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
