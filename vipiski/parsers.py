"""
Bank-specific parsers: each function turns statement **text** into one ``Decimal``.

Conventions
-----------
- Amounts in PDFs often use comma as decimal separator and spaces as thousands
  separators; ``parse_amount_ru`` normalizes to ``Decimal``.
- Functions return ``None`` on any mismatch (regex miss, split failure, bad number)
  so ``engine`` can try the next rule or log "parse failed".
- Parser **names** (strings) are stored in JSON / registry and resolved via
  ``PARSER_REGISTRY`` in ``run_parser``.

Legacy mapping
--------------
These implementations mirror ``Vipiski_ostatki.py`` branches (ЮКБ, Сбер, ВТБ,
БСПБ, Райффайзен, Точка, Совкомбанк) as closely as possible so behaviour stays
familiar during migration.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Callable

import regex

log = logging.getLogger(__name__)


def parse_amount_ru(s: str) -> Decimal:
    """
    Normalize a Russian-style numeric string to ``Decimal``.

    Strips NBSP/spaces, converts comma decimal to dot. Empty after strip raises
    ``InvalidOperation`` (caller catches).
    """
    s = s.strip().replace("\xa0", " ").replace(" ", "").replace(",", ".")
    if not s:
        raise InvalidOperation
    return Decimal(s)


def parse_ukb_holder_outgoing(text: str) -> Decimal | None:
    """
    ЮКБ-style: line ending with ``Исходящий ...`` then split `` / `` for amount.

    Thousands dots are stripped before split (legacy ``replace('.', '')`` on chunk).
    """
    try:
        m = regex.search(r"(Исходящий .+?)$", text, regex.MULTILINE)
        if not m:
            return None
        chunk = m.group(1).replace(".", "").split(" /")
        if len(chunk) < 2:
            return None
        return parse_amount_ru(chunk[1])
    except (InvalidOperation, IndexError, AttributeError) as e:
        log.debug("ukb parse failed: %s", e)
        return None


def _sber_try_suffix_for_date(text: str, ref: date) -> Decimal | None:
    """Single attempt: split outgoing line using ``dd`` + first letter of English month."""
    daysbr = ref.strftime("%d")
    monthsbr = ref.strftime("%b")[0]
    m = regex.search(r"(Исходящий .+?)\n", text)
    if not m:
        return None
    part = (
        m.group(1).replace(" ", "").split("0,00")[1].split(daysbr + monthsbr)[0]
    )
    return parse_amount_ru(part)


def parse_sber_outgoing_with_day_suffix(
    text: str, daysbr: str, monthsbr: str
) -> Decimal | None:
    """
    Sber variant that cuts the outgoing line using ``0,00`` and ``day+monthLetter``.

    The legacy script used **one** reference day (calendar yesterday). Real PDFs may
    carry the **statement** date (often "today" or another day), so the suffix
    ``22M`` vs ``23M`` breaks the split. We try **engine-provided** tokens first,
    then several calendar dates, then ``Исходящий остаток 0,00 …``.
    """
    try:
        m = regex.search(r"(Исходящий .+?)\n", text)
        if m:
            part = (
                m.group(1)
                .replace(" ", "")
                .split("0,00")[1]
                .split(daysbr + monthsbr)[0]
            )
            return parse_amount_ru(part)
    except (InvalidOperation, IndexError, AttributeError) as e:
        log.debug("sber suffix (passed tokens) failed: %s", e)

    today = datetime.now().date()
    try_order = [today - timedelta(days=1), today, today - timedelta(days=2)]

    for ref in try_order:
        try:
            val = _sber_try_suffix_for_date(text, ref)
            if val is not None:
                if ref != try_order[0]:
                    log.debug(
                        "sber suffix succeeded with ref date %s (not default yesterday)",
                        ref,
                    )
                return val
        except (InvalidOperation, IndexError, AttributeError, ValueError) as e:
            log.debug("sber suffix attempt %s: %s", ref, e)
            continue

    fixed = parse_sber_outgoing_fixed(text)
    if fixed is not None:
        log.debug("sber suffix: using fixed-pattern fallback")
    return fixed


def parse_sber_outgoing_fixed(text: str) -> Decimal | None:
    """
    Sber variant with fixed pattern ``Исходящий остаток 0,00 <amount>``.

    Used where the suffix split is not applied in the legacy code.
    """
    try:
        m = regex.search(r"Исходящий остаток 0,00 ([\d\s]+,\d{2})", text)
        if not m:
            return None
        return parse_amount_ru(m.group(1))
    except (InvalidOperation, AttributeError) as e:
        log.debug("sber fixed parse failed: %s", e)
        return None


def parse_vtb_outgoing_balance(text: str) -> Decimal | None:
    """
    ВТБ: block ``ИСХОДЯЩИЙ ОСТАТОК ...`` then take **second line** as amount.

    NBSP and dot/comma handling follows the original float conversion path.
    """
    try:
        m = regex.search(r"(ИСХОДЯЩИЙ ОСТАТОК\s*\d[\d\s]*.\d{2})", text)
        if not m:
            return None
        lines = m.group(1).split("\n")
        if len(lines) < 2:
            return None
        val = lines[1].replace("\xa0", "").replace(".", ",")
        return parse_amount_ru(val.replace(",", "."))
    except (InvalidOperation, IndexError, AttributeError) as e:
        log.debug("vtb parse failed: %s", e)
        return None


def _bspb_from_spisanie_line(line_compact: str) -> Decimal | None:
    """Original BSPB split logic on a compact (no spaces) line."""
    p2 = regex.split(r",\.\.", line_compact)
    if len(p2) < 3:
        return None
    pcomma = regex.split(",", line_compact)
    if len(pcomma) < 4:
        return None
    combined = p2[2] + "," + pcomma[3]
    return parse_amount_ru(combined.replace(",", "."))


def _bspb_last_amount_on_line(raw_line: str) -> Decimal | None:
    """Take the last ``digits,kopecks`` token (NBSP-aware) from a single line."""
    normalized = raw_line.replace("\xa0", " ").replace(".", ",")
    found = regex.findall(r"([\d\s]+,\d{2})", normalized)
    if not found:
        return None
    try:
        return parse_amount_ru(found[-1])
    except InvalidOperation:
        return None


# BSPB "итого" row: three money tokens glued (``-600 000.00300 000.0090 468.70``).
# Requires space-separated thousands + dot decimals so ``20.03`` dates are not matched.
_BSPB_DOT_MONEY = regex.compile(r"-?(?:\d{1,3}(?:\s\d{3})+\.\d{2})")


def _bspb_outgoing_from_dot_decimal_footer(text: str) -> Decimal | None:
    """
    Newer BSPB PDFs use dot decimals and a single footer line with debit / credit /
    outgoing (often concatenated without spaces). PyPDF2 may destroy Cyrillic labels
    on that row, so we detect it only by numeric shape.
    """
    for line in reversed(text.splitlines()):
        toks = _BSPB_DOT_MONEY.findall(line)
        if len(toks) >= 3:
            try:
                val = parse_amount_ru(toks[-1])
                log.debug(
                    "bspb footer: last of %d dot-decimal tokens -> %s",
                    len(toks),
                    val,
                )
                return val
            except InvalidOperation:
                continue
    return None


def parse_bspb_spisanie_balance(text: str) -> Decimal | None:
    """
    Банк Санкт-Петербург: line with ``Списание`` then legacy split.

    PyPDF2 sometimes omits ``\\n`` after the line or uses ``\\r\\n``; we try several
    patterns. OCR/PDF may use Latin ``C`` instead of Cyrillic ``С`` in ``Списание``.
    If the legacy ``,..`` split fails or returns ``None``, use the **last** amount
    token on that line.

    Some BSPB layouts expose the balance only on ``Исходящий остаток`` — handled as
    a fallback on the full text (comma decimals).

    **Dot-decimal** statements often end with a glued three-amount footer; labels may
    be unreadable after PDF extraction — see ``_bspb_outgoing_from_dot_decimal_footer``.
    """
    # Cyrillic С and Latin C (common PDF extraction glitch)
    spisanie = r"(?:[СC]писание|Списано) .+?"
    patterns = [
        rf"({spisanie})\n",
        rf"({spisanie})\r\n",
        rf"({spisanie}[^\n]+)",
    ]
    for pat in patterns:
        m = regex.search(pat, text)
        if not m:
            continue
        raw_line = m.group(1)
        line = raw_line.replace(" ", "").replace(".", ",")
        try:
            primary = _bspb_from_spisanie_line(line)
            if primary is not None:
                return primary
        except (InvalidOperation, IndexError, AttributeError) as e:
            log.debug("bspb primary split raised (%s): %s", pat, e)
        fallback = _bspb_last_amount_on_line(raw_line)
        if fallback is not None:
            log.debug("bspb used amount fallback on line (%s)", pat)
            return fallback

    # Outgoing balance line (newer / alternate BSPB PDFs)
    for m in regex.finditer(
        r"Исходящий\s+остаток[^\d\n]{0,60}([\d\s\xa0]+,\d{2})",
        text,
        regex.IGNORECASE,
    ):
        try:
            return parse_amount_ru(m.group(1))
        except InvalidOperation:
            continue

    return _bspb_outgoing_from_dot_decimal_footer(text)


def parse_raiffeisen_outgoing(text: str) -> Decimal | None:
    """Райффайзен: ``Исходящий`` line, strip to lowercase ``balance`` split."""
    try:
        m = regex.search(r"(Исходящий .+?)\n", text)
        if not m:
            return None
        part = (
            m.group(1).replace(" ", "").replace(".", ",").split("balance")[1]
        )
        return parse_amount_ru(part.replace(",", "."))
    except (InvalidOperation, IndexError, AttributeError) as e:
        log.debug("raiffeisen parse failed: %s", e)
        return None


def parse_tochka_outgoing(text: str) -> Decimal | None:
    """Точка: outgoing balance can be labelled as сальдо or остаток."""
    try:
        m = regex.search(
            r"(?:Исходящее сальдо|Исходящий остаток):\s*([\d\s\xa0,.]+)",
            text,
        )
        if not m:
            return None
        raw = m.group(1).replace(".", ",")
        return parse_amount_ru(raw.replace(",", "."))
    except (InvalidOperation, AttributeError) as e:
        log.debug("tochka parse failed: %s", e)
        return None


def parse_sovcom_outgoing(text: str) -> Decimal | None:
    """Совкомбанк: ``Исходящий остаток:`` optional ``Пассив`` then amount."""
    try:
        m = regex.search(
            r"Исходящий остаток:\s*\n?\s*(?:Пассив\s*)?([\d\s,.]+)", text
        )
        if not m:
            return None
        raw = m.group(1).replace(" ", "").replace(".", ",")
        return parse_amount_ru(raw.replace(",", "."))
    except (InvalidOperation, AttributeError) as e:
        log.debug("sovcom parse failed: %s", e)
        return None


ParserFn = Callable[..., Decimal | None]

# String keys must match ``parser`` field in account rules JSON / registry.
PARSER_REGISTRY: dict[str, ParserFn] = {
    "ukb_holder_outgoing": parse_ukb_holder_outgoing,
    "sber_outgoing_balance": parse_sber_outgoing_fixed,
    "sber_outgoing_balance_with_day_suffix": parse_sber_outgoing_with_day_suffix,
    "vtb_outgoing_balance": parse_vtb_outgoing_balance,
    "bspb_spisanie_balance": parse_bspb_spisanie_balance,
    "raiffeisen_outgoing_balance": parse_raiffeisen_outgoing,
    "tochka_outgoing_balance": parse_tochka_outgoing,
    "sovcom_outgoing_balance": parse_sovcom_outgoing,
}


def run_parser(
    name: str, text: str, *, daysbr: str = "", monthsbr: str = ""
) -> Decimal | None:
    """
    Dispatch by parser name. Unknown name → ERROR log and ``None``.

    Only the Sber suffix parser receives ``daysbr``/``monthsbr``; others ignore them.
    """
    fn = PARSER_REGISTRY.get(name)
    if not fn:
        log.error("Unknown parser: %s", name)
        return None
    if name == "sber_outgoing_balance_with_day_suffix":
        return fn(text, daysbr, monthsbr)
    return fn(text)
