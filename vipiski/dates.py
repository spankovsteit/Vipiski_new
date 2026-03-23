"""
Date helpers for folder names and Sber-specific PDF parsing.

Important distinctions
----------------------
- **statement_reference_date** — calendar "yesterday" (legacy script used this for
  ``daysbr`` / ``monthsbr``). This is NOT the same as "previous business day".
- **previous_business_day** — walks backward skipping Sat/Sun only; Russian bank
  holidays are not encoded (extend if statements always align to a holiday calendar).
- **month_folder_name** — plain calendar ``YYYY-MM`` of a date.
- **archive_month_folder_name** — month segment for PDF archive paths; on the 1st
  of a month uses the **previous** month's ``YYYY-MM`` (see ``main``).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta


def previous_calendar_day(d: date) -> date:
    """Plain minus one day (used for Sber text token extraction)."""
    return d - timedelta(days=1)


def is_weekend(d: date) -> bool:
    """Saturday/Sunday in local timezone (Monday=0 .. Sunday=6)."""
    return d.weekday() >= 5


def previous_business_day(d: date) -> date:
    """
    Walk backward until a weekday is found.

    Note: no public holiday table — if you need 1 May / New Year off, add a set
    of closed dates and skip those too.
    """
    cur = d - timedelta(days=1)
    while is_weekend(cur):
        cur -= timedelta(days=1)
    return cur


def statement_reference_date(run_time: datetime | None = None) -> date:
    """
    Date driving ``sber_day_tokens``.

    Matches legacy ``yesterday = today - timedelta(days=1)`` — not business-day
    adjusted. If Sber statements should key off last banking day instead, switch
    this function to ``previous_business_day(run.date())`` after team agreement.
    """
    run = run_time or datetime.now()
    return previous_calendar_day(run.date())


def sber_day_tokens(ref: date) -> tuple[str, str]:
    """
    Build the two tokens used inside Sber PDF regex splitting.

    Returns
    -------
    (daysbr, monthsbr)
        * ``daysbr`` — day of month zero-padded (``strftime("%d")``).
        * ``monthsbr`` — **first character** of English abbreviated month
          (``strftime("%b")`` → e.g. ``"Mar"`` → ``"M"``).

    This mirrors the old script's ``daysbr`` and ``monthsbr`` variables.
    """
    day = ref.strftime("%d")
    month_en = ref.strftime("%b")
    return day, month_en[0]


def month_folder_name(run_time: datetime | None = None) -> str:
    """Segment under base path, e.g. ``2025-03`` (calendar month of ``run``)."""
    run = run_time or datetime.now()
    return run.strftime("%Y-%m")


def archive_month_folder_name(run_time: datetime | None = None) -> str:
    """
    Month segment for the archive path ``<base>/<YYYY-MM>/<ddmmyyyy>/``.

    On the **first calendar day of a month**, statements still use that day's
    ``ddmmyyyy`` folder, but the parent month folder is the **previous** month
    (legacy layout: first-of-month batch lives under the prior month's directory).
    """
    run = run_time or datetime.now()
    d = run.date() if isinstance(run, datetime) else run
    if d.day == 1:
        last_prev = d.replace(day=1) - timedelta(days=1)
        return last_prev.strftime("%Y-%m")
    return d.strftime("%Y-%m")


def day_folder_segment(run_time: datetime | None = None) -> str:
    """
    Day folder name: ``ddmmyyyy`` without separators.

    Same shape as legacy ``day1 = strftime("%d-%m-%Y").replace("-", "")``.
    """
    run = run_time or datetime.now()
    return run.strftime("%d-%m-%Y").replace("-", "")
