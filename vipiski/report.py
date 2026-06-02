"""
Human-readable Telegram report from **per-account** balances + sheet deposits.

Layout
------
1. Fixed **section** order (``SECTION_ORDER``) plus any extra sections sorted
   alphabetically (so ``registry``/JSON can add a new section without code change).
2. Within each section, companies appear in the order they are listed in the
   ``companies`` config.
3. For each company, one line per **account** (``display_name`` from account rule),
   then optional deposit lines tied to ``deposits_key`` or ``display_name``.

Deposits
--------
``deposits_key`` overrides the key used to match column A on the balance sheet.
Otherwise ``account_balances_label`` (synced to column A) is used, then
``display_name``.

Trailing block **Дополнительные депозиты** lists deposit keys not attached to any
company block above (legacy behaviour).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any


def _fmt_money(d: Decimal) -> str:
    """Format for chat: thousands with space, decimal comma (RU-style)."""
    q = d.quantize(Decimal("0.01"))
    s = format(q.copy_abs(), "f")
    int_part, frac = s.split(".", 1) if "." in s else (s, "00")
    frac = (frac + "00")[:2]
    groups: list[str] = []
    while int_part:
        groups.append(int_part[-3:])
        int_part = int_part[:-3]
    spaced = " ".join(reversed(groups)) if groups else "0"
    sign = "-" if q < 0 else ""
    return f"{sign}{spaced},{frac}"


# Explicit ordering for known section titles; unknown sections append sorted.
SECTION_ORDER = [
    "Управляющие компании",
    "Балансодержатели",
    "Инвестиционные компании",
    "Ген подрядные компании",
]


def _accounts_by_code(accounts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Quick lookup for ``display_name`` while building lines."""
    return {a["account_code"]: a for a in accounts if a.get("active", True)}


def build_telegram_text(
    companies: list[dict[str, Any]],
    account_rules: list[dict[str, Any]],
    balances_by_account: dict[str, Decimal],
    deposits_dict: dict[str, list[str]],
) -> str:
    """
    Build the full message body (may exceed Telegram limit — sender splits).

    ``balances_by_account`` should already include ``Decimal(0)`` for missing
    active codes if you want every account line visible (``main`` does setdefault).
    """
    by_code = _accounts_by_code(account_rules)
    lines: list[str] = ["Остатки на счетах обновлены", ""]
    consumed_deposit_keys: set[str] = set()

    by_section: dict[str, list[dict[str, Any]]] = {}
    for co in companies:
        if not co.get("active", True):
            continue
        sec = co.get("section") or "Прочее"
        by_section.setdefault(sec, []).append(co)

    section_keys = list(SECTION_ORDER) + sorted(
        k for k in by_section if k not in SECTION_ORDER
    )

    first_section = True
    for sec in section_keys:
        cos = by_section.get(sec)
        if not cos:
            continue
        if not first_section:
            lines.append("")
        lines.append(sec + ":")
        lines.append("")
        first_section = False
        for co in cos:
            accs = co.get("accounts") or []
            for ac in accs:
                rule = by_code.get(ac)
                # Skip account codes that are absent among active account rules.
                if rule is None:
                    continue
                label = (rule or {}).get("display_name") or ac
                bal = balances_by_account.get(ac, Decimal(0))
                lines.append(f"{label} - {_fmt_money(bal)}")
            dkey = (
                co.get("deposits_key")
                or co.get("account_balances_label")
                or co.get("display_name")
                or ""
            )
            if dkey and dkey in deposits_dict:
                consumed_deposit_keys.add(dkey)
                for info in deposits_dict[dkey]:
                    lines.append(f"  {info}")
            lines.append("")

    lines.append("Дополнительные депозиты:")
    for company_name, deposit_list in deposits_dict.items():
        if company_name not in consumed_deposit_keys:
            lines.append(f"{company_name}:")
            for info in deposit_list:
                lines.append(f"  {info}")

    return "\n".join(lines).strip()
