"""
Environment-driven configuration.

Design
------
- Secrets and machine-specific paths live in ``.env`` (not committed).
- ``python-dotenv`` loads ``ROOT/.env`` first, then ``ROOT/.env.example`` with
  ``override=False`` so real secrets in ``.env`` win. If you only edit
  ``.env.example``, variables are still picked up until you create ``.env``.
- ``TELEGRAM_BOT_TOKEN`` and ``TELEGRAM_CHAT_ID`` are required; missing → KeyError
  in ``load_settings()`` so ``main`` can print a clear hint.

Spreadsheet names default to the user's copy; override via env if needed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Repository root: directory that contains ``vipiski/``, ``config/``, ``main.py``.
ROOT = Path(__file__).resolve().parent.parent

# .env is canonical; .env.example is a fallback (e.g. dev forgot to copy the file).
# override=False on the second load: never let .env.example replace vars from .env.
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.example", override=False)


def _path(key: str, default: str) -> Path:
    """Expand env var to Path; supports ``~`` in paths."""
    return Path(os.environ.get(key, default)).expanduser()


@dataclass(frozen=True)
class Settings:
    """Immutable snapshot of all tunables for one process run."""

    base_path: Path
    src_current_dir_name: str
    log_file: Path
    telegram_token: str
    telegram_chat_id: str
    bitrix24_webhook_url: str | None
    bitrix24_dialog_id: str | None
    skip_bitrix24: bool
    bitrix24_soft_fail: bool
    google_credentials_path: Path
    google_spreadsheet_name: str
    google_worksheet_balances: str
    google_worksheet_raw: str
    accounts_config_path: Path
    companies_config_path: Path
    skip_run_on_non_business_day: bool
    skip_telegram: bool
    telegram_soft_fail: bool
    sheets_formula_locale: str
    account_balances_use_formulas: bool


def load_settings() -> Settings:
    """
    Read settings from environment.

    Raises
    ------
    KeyError
        If ``TELEGRAM_BOT_TOKEN`` or ``TELEGRAM_CHAT_ID`` is unset.
    """
    base = _path("VIPISKI_BASE_PATH", r"D:\Выписки")
    return Settings(
        base_path=base,
        src_current_dir_name=os.environ.get("VIPISKI_SRC_DIR", "Текущие"),
        log_file=_path("VIPISKI_LOG_FILE", str(base / "vipiski_log.txt")),
        telegram_token=os.environ["TELEGRAM_BOT_TOKEN"],
        telegram_chat_id=os.environ["TELEGRAM_CHAT_ID"],
        bitrix24_webhook_url=(
            os.environ.get("BITRIX24_WEBHOOK_URL", "").strip() or None
        ),
        bitrix24_dialog_id=(
            os.environ.get("BITRIX24_DIALOG_ID", "").strip() or None
        ),
        skip_bitrix24=os.environ.get("VIPISKI_SKIP_BITRIX24", "false").lower()
        in ("1", "true", "yes"),
        bitrix24_soft_fail=os.environ.get(
            "VIPISKI_BITRIX24_SOFT_FAIL", "false"
        ).lower()
        in ("1", "true", "yes"),
        google_credentials_path=_path(
            "GOOGLE_CREDENTIALS_JSON",
            str(ROOT / "credentials" / "service_account.json"),
        ),
        google_spreadsheet_name=os.environ.get(
            "GOOGLE_SPREADSHEET_NAME", "План_платежей (день)"
        ),
        google_worksheet_balances=os.environ.get(
            "GOOGLE_WORKSHEET_BALANCES", "Account_balances"
        ),
        google_worksheet_raw=os.environ.get(
            "GOOGLE_WORKSHEET_RAW", "raw_balances"
        ),
        accounts_config_path=_path(
            "VIPISKI_ACCOUNTS_JSON", str(ROOT / "config" / "accounts.json")
        ),
        companies_config_path=_path(
            "VIPISKI_COMPANIES_JSON", str(ROOT / "config" / "companies.json")
        ),
        skip_run_on_non_business_day=os.environ.get(
            "VIPISKI_SKIP_NON_BUSINESS_DAY", "false"
        ).lower()
        in ("1", "true", "yes"),
        skip_telegram=os.environ.get("VIPISKI_SKIP_TELEGRAM", "false").lower()
        in ("1", "true", "yes"),
        telegram_soft_fail=os.environ.get(
            "VIPISKI_TELEGRAM_SOFT_FAIL", "false"
        ).lower()
        in ("1", "true", "yes"),
        sheets_formula_locale=os.environ.get(
            "VIPISKI_SHEETS_FORMULA_LOCALE", "ru"
        ).strip()
        .lower()[:2]
        or "ru",
        account_balances_use_formulas=os.environ.get(
            "VIPISKI_ACCOUNT_BALANCES_USE_FORMULAS", "true"
        ).lower()
        in ("1", "true", "yes"),
    )
