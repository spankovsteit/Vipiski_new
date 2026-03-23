"""
PDF batch processing: map each file to at most one **account_code**.

Rule evaluation model
---------------------
Rules are tried **in list order** (JSON array order or order in ``registry.py``).
For each PDF:

1. Extract full text (all pages concatenated).
2. Skip inactive rules (``active: false``).
3. A rule matches if **every** string in ``match_all`` is a substring of the text.
4. On first match, run the named ``parser``; if it returns a ``Decimal``, store
   it under ``account_code`` and **stop** for this PDF (equivalent to ``elif``).

Implications
------------
- Put **more specific** rules before **broader** ones (e.g. long unique holder
  strings before a short substring that might appear elsewhere).
- The same ``account_code`` can be updated by multiple PDFs in one run; the last
  file in ``pdf_paths`` order wins for that code (sorted paths → deterministic).

Context passed to parsers
-------------------------
Only ``sber_outgoing_balance_with_day_suffix`` receives ``daysbr`` / ``monthsbr``;
see ``dates.sber_day_tokens`` and ``main.py``.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from pathlib import Path

from vipiski.parsers import run_parser
from vipiski.pdf_reader import extract_pdf_text

log = logging.getLogger(__name__)


def parse_pdfs(
    pdf_paths: list[Path],
    account_rules: list[dict],
    *,
    daysbr: str,
    monthsbr: str,
) -> dict[str, Decimal]:
    """
    Parse every PDF path; return merged ``account_code -> balance`` updates.

    Parameters
    ----------
    pdf_paths
        Typically sorted glob from the day archive folder.
    account_rules
        Loaded rules (from JSON or ``registry.DEFAULT_ACCOUNTS``).
    daysbr, monthsbr
        Sber-specific tokens; unused by non-Sber parsers inside ``run_parser``.
    """
    updates: dict[str, Decimal] = {}
    for pdf_path in pdf_paths:
        if not pdf_path.is_file():
            continue
        try:
            text = extract_pdf_text(pdf_path)
        except Exception as e:
            log.error("Failed to read PDF %s: %s", pdf_path, e)
            continue
        if not text.strip():
            log.warning("Empty text from %s", pdf_path)
            continue
        matched = False
        for rule in account_rules:
            if not rule.get("active", True):
                continue
            needles = rule.get("match_all") or []
            if not all(n in text for n in needles):
                continue
            parser_name = rule["parser"]
            val = run_parser(
                parser_name, text, daysbr=daysbr, monthsbr=monthsbr
            )
            if val is None:
                log.warning(
                    "Rule matched but parse failed: %s (%s)",
                    rule.get("account_code"),
                    pdf_path.name,
                )
                continue
            code = rule["account_code"]
            updates[code] = val
            log.info("Parsed %s = %s from %s", code, val, pdf_path.name)
            matched = True
            break
        if not matched:
            log.info("No rule matched for %s", pdf_path.name)
    return updates
