#!/usr/bin/env python3
"""
Write text to **Account_balances!P1** only.

Does **not** run ``sync()``, PDF parsing, or Raw/total updates — useful to verify
Telegram outbox wiring and Google credentials without touching balances.

Usage
-----
From the repository root (where ``.env`` lives)::

    python scripts/write_p1_test.py
    python scripts/write_p1_test.py "Your test message"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from vipiski.google_sync import open_client, write_account_balances_telegram_outbox
from vipiski.settings import ROOT, load_settings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write text to Account_balances!P1 (no balance sync)."
    )
    parser.add_argument(
        "message",
        nargs="?",
        default=(
            "Проверка P1: запись из scripts/write_p1_test.py "
            "(остатки на листе не менялись)."
        ),
        help="Text to write to P1",
    )
    args = parser.parse_args()

    try:
        settings = load_settings()
    except KeyError as e:
        print(f"Missing environment variable: {e}", file=sys.stderr)
        print(f"Set it in {ROOT / '.env'} (same as for main.py).", file=sys.stderr)
        return 1

    gc = open_client(settings.google_credentials_path)
    sh = gc.open(settings.google_spreadsheet_name)
    ws = sh.worksheet(settings.google_worksheet_balances)
    write_account_balances_telegram_outbox(ws, args.message)
    print(
        f"OK: wrote {len(args.message)} character(s) to "
        f"{settings.google_worksheet_balances!r}!P1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
