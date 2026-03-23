"""
Load **account rules** and **company** definitions from JSON with fallback to code.

File contract
-------------
- ``config/accounts.json`` and ``config/companies.json`` must be JSON **arrays**
  of objects if present.
- An empty array ``[]`` is treated as "use built-in defaults" (returns ``None``
  from ``_load_json_list``) so operators can clear JSON to revert quickly.
- Malformed JSON or wrong type → warning log + defaults (fail-soft).

Built-in defaults live in ``vipiski.registry`` (large static lists). Editing JSON
is preferred for production so you can add accounts without redeploying code.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from vipiski.registry import DEFAULT_ACCOUNTS, DEFAULT_COMPANIES

log = logging.getLogger(__name__)


def _load_json_list(path: Path) -> list[dict[str, Any]] | None:
    """
    Return a non-empty list of dicts, or ``None`` to signal "fall back to defaults".

    Returns
    -------
    None
        If file missing, invalid JSON, not a list, or list length 0.
    """
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        log.warning("Could not read %s: %s — using defaults", path, e)
        return None
    if not isinstance(data, list):
        log.warning("%s must be a JSON array — using defaults", path)
        return None
    if len(data) == 0:
        return None
    return data


def load_accounts(path: Path) -> list[dict[str, Any]]:
    """Account rules: ``account_code``, ``parser``, ``match_all``, ``active``, ..."""
    loaded = _load_json_list(path)
    if loaded is not None:
        log.info("Loaded %d account rules from %s", len(loaded), path)
        return loaded
    log.info("Using built-in default account rules")
    return list(DEFAULT_ACCOUNTS)


def load_companies(path: Path) -> list[dict[str, Any]]:
    """Company groups: ``accounts`` list, ``google_total_cell``, ``section``, ..."""
    loaded = _load_json_list(path)
    if loaded is not None:
        log.info("Loaded %d companies from %s", len(loaded), path)
        return loaded
    log.info("Using built-in default companies")
    return list(DEFAULT_COMPANIES)
