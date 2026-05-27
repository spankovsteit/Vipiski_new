"""
Built-in **default** account rules and company definitions.

When to edit this file vs JSON
-------------------------------
- Prefer ``config/accounts.json`` / ``config/companies.json`` (non-empty arrays)
  in production so accountants can toggle ``active`` or add rows without a dev.
- Use this module as the shipped fallback when JSON is missing, empty ``[]``,
  or invalid — see ``loaders.py``.

Account rule fields (each dict in ``DEFAULT_ACCOUNTS``)
-------------------------------------------------------
account_code
    Stable id used in Raw_balances column A and as merge key for PDF output.
company_code
    Logical grouping (not written to sheet by this pipeline); ties to companies.
display_name
    Shown in Telegram lines for that account.
bank
    Informational tag (ЮКБ/Сбер/...) for humans; not used by dispatch logic.
parser
    Key into ``parsers.PARSER_REGISTRY`` — must match exactly.
match_all
    Every string must appear as substring in PDF text for the rule to match.
    Order of rules in the list matters: first full match wins per file.
active
    If false, rule is skipped (soft-delete without losing history in git).

Company fields (each dict in ``DEFAULT_COMPANIES``)
---------------------------------------------------
company_code
    Short id.
display_name
    Section header / deposit matching (see ``report.deposits_key``).
section
    Telegram section title; also drives ``report.SECTION_ORDER`` grouping.
google_total_cell
    A1 notation cell on **Account_balances** receiving **sum** of listed accounts.
    ``null`` skips total update for that company.
accounts
    List of ``account_code`` values summed into the cell above.
deposits_key
    Optional; overrides ``display_name`` when matching deposit dict keys from sheet.
active
    If false, company omitted from Telegram and from total batch update.

Ordering note
-------------
``ankon_raiffeisen`` is intentionally **last** among accounts: substring ``АНКОН``
is broad; placing it late reduces false matches (same idea as the old ``elif``
order).
"""

from __future__ import annotations

from typing import Any, TypedDict


class AccountRuleDict(TypedDict, total=False):
    """Schema hint for optional static typing / documentation."""

    account_code: str
    company_code: str
    display_name: str
    bank: str
    parser: str
    match_all: list[str]
    active: bool


class CompanyDict(TypedDict, total=False):
    """Schema hint for company rows."""

    company_code: str
    display_name: str
    section: str
    google_total_cell: str | None
    accounts: list[str]
    deposits_key: str
    active: bool


DEFAULT_ACCOUNTS: list[dict[str, Any]] = [
    {
        "account_code": "parfenenko_ukb",
        "company_code": "parfenenko",
        "display_name": 'ИП Парфененко М.А.',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ИППарфененко Мария Александровна'],
        "active": True,
    },
    {
        "account_code": "parfenenko_vtb",
        "company_code": "parfenenko",
        "display_name": "ИП Парфененко М.А. ВТБ",
        "bank": "vtb",
        "parser": "vtb_outgoing_balance",
        "match_all": [
            "Владелец счета: Индивидуальный предприниматель ПАРФЕНЕНКО МАРИЯ АЛЕКСАНДРОВНА"
        ],
        "active": True,
    },
    {
        "account_code": "manevich_ukb",
        "company_code": "manevich",
        "display_name": "ИП Маневич А.Е.",
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ["holder: ИПМАНЕВИЧ АЛЛАЕФИМОВНА"],
        "active": True,
    },
    {
        "account_code": "manevich_sber",
        "company_code": "manevich",
        "display_name": "ИП Маневич А.Е. СБЕР",
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            "ИНДИВИДУАЛЬНЫЙ ПРЕДПРИНИМАТЕЛЬ МАНЕВИЧ АЛЛА ЕФИМОВНА",
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "manevich_vtb",
        "company_code": "manevich",
        "display_name": "ИП Маневич А.Е. ВТБ",
        "bank": "vtb",
        "parser": "vtb_outgoing_balance",
        "match_all": [
            "Владелец счета: Индивидуальный предприниматель МАНЕВИЧ АЛЛА ЕФИМОВНА"
        ],
        "active": True,
    },
    {
        "account_code": "steit_sber",
        "company_code": "steit",
        "display_name": 'ООО "СТЕЙТ" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance_with_day_suffix",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СТЕЙТ"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "steit_ukb",
        "company_code": "steit",
        "display_name": 'ООО "СТЕЙТ" ЮКБ',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"СТЕЙТ"'],
        "active": True,
    },
    {
        "account_code": "metro_ukb",
        "company_code": "metro",
        "display_name": 'ООО "МЕТРО"',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"Метро"'],
        "active": True,
    },
    {
        "account_code": "metro_sber",
        "company_code": "metro",
        "display_name": 'ООО "МЕТРО" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "МЕТРО"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "tsn_repinskoe_vtb",
        "company_code": "tsn_repinskoe",
        "display_name": 'ТСН "РЕПИНСКОЕ" ВТБ',
        "bank": "vtb",
        "parser": "vtb_outgoing_balance",
        "match_all": [
            'Владелец счета: ТОВАРИЩЕСТВО СОБСТВЕННИКОВ НЕДВИЖИМОСТИ "РЕПИНСКОЕ"'
        ],
        "active": True,
    },
    {
        "account_code": "tsn_repinskoe2_tochka",
        "company_code": "tsn_repinskoe2",
        "display_name": 'ТСН "РЕПИНСКОЕ 2"',
        "bank": "tochka",
        "parser": "tochka_outgoing_balance",
        "match_all": [
            'Клиент: ТОВАРИЩЕСТВО СОБСТВЕННИКОВ НЕДВИЖИМОСТИ "РЕПИНСКОЕ 2"'
        ],
        "active": True,
    },
    {
        "account_code": "tsn_oazis_tochka",
        "company_code": "tsn_oazis",
        "display_name": 'ТСН "ОАЗИС"',
        "bank": "tochka",
        "parser": "tochka_outgoing_balance",
        "match_all": [
            'Клиент: ТОВАРИЩЕСТВО СОБСТВЕННИКОВ НЕДВИЖИМОСТИ "ОАЗИС"'
        ],
        "active": True,
    },
    {
        "account_code": "kudrovo_stroy_sber",
        "company_code": "kudrovo_stroy",
        "display_name": 'ООО "КУДРОВО-СТРОЙ"',
        "bank": "sber",
        "parser": "sber_outgoing_balance_with_day_suffix",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "КУДРОВО-СТРОЙ"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "klever_bspb_375",
        "company_code": "klever",
        "display_name": 'ООО "Клевер" 375',
        "bank": "bspb",
        "parser": "bspb_spisanie_balance",
        "match_all": ["Счёт: 40702 810 3 9027 0000375"],
        "active": True,
    },
    {
        "account_code": "klever_bspb_852",
        "company_code": "klever",
        "display_name": 'ООО "Клевер" 852',
        "bank": "bspb",
        "parser": "bspb_spisanie_balance",
        "match_all": ["Счёт: 40702 810 7 9027 0000852"],
        "active": True,
    },
    {
        "account_code": "klever_sber",
        "company_code": "klever",
        "display_name": 'ООО "Клевер" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance_with_day_suffix",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "КЛЕВЕР"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "klever_vtb",
        "company_code": "klever",
        "display_name": 'ООО "Клевер" ВТБ',
        "bank": "vtb",
        "parser": "vtb_outgoing_balance",
        "match_all": [
            'Владелец счета: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "КЛЕВЕР"'
        ],
        "active": True,
    },
    {
        "account_code": "partner_ukb",
        "company_code": "partner",
        "display_name": 'ООО "Партнер"',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"Партнер"'],
        "active": True,
    },
    {
        "account_code": "partner_vtb",
        "company_code": "partner",
        "display_name": 'ООО "Партнер" ВТБ',
        "bank": "vtb",
        "parser": "vtb_outgoing_balance",
        "match_all": [
            'Владелец счета: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ПАРТНЕР'
        ],
        "active": True,
    },
    {
        "account_code": "partner_sber",
        "company_code": "partner",
        "display_name": 'ООО "Партнер" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ПАРТНЕР"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "ohtinskaya_alleya_ukb",
        "company_code": "ohtinskaya_alleya",
        "display_name": 'ООО "Охтинская аллея"',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"Охтинская аллея"'],
        "active": True,
    },
    {
        "account_code": "ohtinskaya_alleya_vtb",
        "company_code": "ohtinskaya_alleya",
        "display_name": 'ООО "Охтинская аллея" ВТБ',
        "bank": "vtb",
        "parser": "vtb_outgoing_balance",
        "match_all": [
            'Владелец счета: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ОХТИНСКАЯ АЛЛЕЯ"'
        ],
        "active": True,
    },
    {
        "account_code": "ohtinskaya_alleya_sber",
        "company_code": "ohtinskaya_alleya",
        "display_name": 'ООО "Охтинская аллея" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ОХТИНСКАЯ АЛЛЕЯ"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "h1_sovcom",
        "company_code": "h1",
        "display_name": 'ООО "Н1"',
        "bank": "sovcom",
        "parser": "sovcom_outgoing_balance",
        "match_all": ['Общество с ограниченной ответственностью "Н1"'],
        "active": True,
    },
    {
        "account_code": "h1_sber",
        "company_code": "h1",
        "display_name": 'ООО "Н1" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "Н1"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "raduga_sber",
        "company_code": "raduga",
        "display_name": 'ООО "Радуга" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance_with_day_suffix",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "РАДУГА"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "raduga_vtb",
        "company_code": "raduga",
        "display_name": 'ООО "Радуга" ВТБ',
        "bank": "vtb",
        "parser": "vtb_outgoing_balance",
        "match_all": [
            'Владелец счета: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "РАДУГА"'
        ],
        "active": True,
    },
    {
        "account_code": "reaktiv_bspb",
        "company_code": "reaktiv",
        "display_name": 'ООО "Реактив" БСПБ',
        "bank": "bspb",
        "parser": "bspb_spisanie_balance",
        "match_all": ["Счёт: 40702 810 3 9027 0000414"],
        "active": True,
    },
    {
        "account_code": "reaktiv_sber",
        "company_code": "reaktiv",
        "display_name": 'ООО "Реактив" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "РЕАКТИВ"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "romashki_bspb",
        "company_code": "romashki",
        "display_name": 'ООО "Ромашки" БСПБ',
        "bank": "bspb",
        "parser": "bspb_spisanie_balance",
        "match_all": ["0001648"],
        "active": True,
    },
    {
        "account_code": "romashki_ukb",
        "company_code": "romashki",
        "display_name": 'ООО "Ромашки" ЮКБ',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"Ромашки"'],
        "active": True,
    },
    {
        "account_code": "romashki_sber",
        "company_code": "romashki",
        "display_name": 'ООО "Ромашки" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "РОМАШКИ"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "smart_solution_vtb",
        "company_code": "smart_solution",
        "display_name": 'ООО "Смарт Солюшн" ВТБ',
        "bank": "vtb",
        "parser": "vtb_outgoing_balance",
        "match_all": [
            'Владелец счета: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СМАРТ СОЛЮШН"'
        ],
        "active": True,
    },
    {
        "account_code": "smart_solution_sber",
        "company_code": "smart_solution",
        "display_name": 'ООО "Смарт Солюшн" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance_with_day_suffix",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СМАРТ СОЛЮШН"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "formula_ukb",
        "company_code": "formula",
        "display_name": 'ООО "Формула"',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"Формула"'],
        "active": True,
    },
    {
        "account_code": "formula_vtb",
        "company_code": "formula",
        "display_name": 'ООО "Формула" ВТБ',
        "bank": "vtb",
        "parser": "vtb_outgoing_balance",
        "match_all": [
            'Владелец счета: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ФОРМУЛА'
        ],
        "active": True,
    },
    {
        "account_code": "formula_sber",
        "company_code": "formula",
        "display_name": 'ООО "Формула" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ФОРМУЛА"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "sityinvest_ukb",
        "company_code": "sityinvest",
        "display_name": 'ООО "СитиИнвест"',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"СитиИнвест"'],
        "active": True,
    },
    {
        "account_code": "sityinvest_sber",
        "company_code": "sityinvest",
        "display_name": 'ООО "СитиИнвест" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СИТИИНВЕСТ"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "sityinvest_vtb",
        "company_code": "sityinvest",
        "display_name": 'ООО "СитиИнвест" ВТБ',
        "bank": "vtb",
        "parser": "vtb_outgoing_balance",
        "match_all": [
            'Владелец счета: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СИТИИНВЕСТ"'
        ],
        "active": True,
    },
    {
        "account_code": "sev_zvezda_ukb",
        "company_code": "sev_zvezda",
        "display_name": 'ООО "Северная звезда"',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"Северная звезда"'],
        "active": True,
    },
    {
        "account_code": "sev_zvezda_sber",
        "company_code": "sev_zvezda",
        "display_name": 'ООО "Северная звезда" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СЕВЕРНАЯ ЗВЕЗДА"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "sev_zvezda_vtb",
        "company_code": "sev_zvezda",
        "display_name": 'ООО "Северная звезда" ВТБ',
        "bank": "vtb",
        "parser": "vtb_outgoing_balance",
        "match_all": [
            'Владелец счета: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СЕВЕРНАЯ ЗВЕЗДА"'
        ],
        "active": True,
    },
    {
        "account_code": "dudergof_ukb",
        "company_code": "dudergof",
        "display_name": 'ООО "Дудергоф"',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"Дудергоф"'],
        "active": True,
    },
    {
        "account_code": "dudergof_sber",
        "company_code": "dudergof",
        "display_name": 'ООО "Дудергоф" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ДУДЕРГОФ"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "m_invest_ukb",
        "company_code": "m_invest",
        "display_name": 'ООО "М-Инвест"',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"М-Инвест"'],
        "active": True,
    },
    {
        "account_code": "m_invest_sber",
        "company_code": "m_invest",
        "display_name": 'ООО "М-Инвест" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "М-ИНВЕСТ"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "sp_impost_ukb",
        "company_code": "sp_impost",
        "display_name": 'ООО "СП-Импост"',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"СП-Импост"'],
        "active": True,
    },
    {
        "account_code": "sp_impost_sber",
        "company_code": "sp_impost",
        "display_name": 'ООО "СП-Импост" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СП-ИМПОСТ"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "praga_ukb",
        "company_code": "praga",
        "display_name": 'ООО "Прага"',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"Прага"'],
        "active": True,
    },
    {
        "account_code": "praga_vtb",
        "company_code": "praga",
        "display_name": 'ООО "Прага" ВТБ',
        "bank": "vtb",
        "parser": "vtb_outgoing_balance",
        "match_all": [
            'Владелец счета: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ПРАГА"'
        ],
        "active": True,
    },
    {
        "account_code": "praga_sber",
        "company_code": "praga",
        "display_name": 'ООО "Прага" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ПРАГА"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "frank_ukb",
        "company_code": "frank",
        "display_name": 'ООО "Франк"',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"Франк"'],
        "active": True,
    },
    {
        "account_code": "ser_ukb",
        "company_code": "ser",
        "display_name": 'ООО "СЭР"',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"СтройЭкспертРитейл"'],
        "active": True,
    },
    {
        "account_code": "ser_sber",
        "company_code": "ser",
        "display_name": 'ООО "СЭР" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СТРОЙЭКСПЕРТРИТЕЙЛ"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "murino_grad_sber",
        "company_code": "murino_grad",
        "display_name": 'ООО "Мурино-Град"',
        "bank": "sber",
        "parser": "sber_outgoing_balance_with_day_suffix",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "МУРИНО-ГРАД"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "akvitania_ukb",
        "company_code": "akvitania",
        "display_name": 'ООО "Аквитания"',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"Аквитания"'],
        "active": True,
    },
    {
        "account_code": "akvitania_sber",
        "company_code": "akvitania",
        "display_name": 'ООО "Аквитания" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "АКВИТАНИЯ"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "bergen_ukb",
        "company_code": "bergen",
        "display_name": 'ООО "Берген"',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"БЕРГЕН"'],
        "active": True,
    },
    {
        "account_code": "bergen_sber",
        "company_code": "bergen",
        "display_name": 'ООО "Берген" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "БЕРГЕН"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "immobi_ukb",
        "company_code": "immobi",
        "display_name": 'ООО "Иммоби"',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"ИММОБИ"'],
        "active": True,
    },
    {
        "account_code": "immobi_sber",
        "company_code": "immobi",
        "display_name": 'ООО "Иммоби" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ИММОБИ"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "kudrovo_invest_ukb",
        "company_code": "kudrovo_invest",
        "display_name": 'ООО "Кудрово-Инвест"',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"Кудрово-Инвест"'],
        "active": True,
    },
    {
        "account_code": "kudrovo_invest_sber",
        "company_code": "kudrovo_invest",
        "display_name": 'ООО "Кудрово-Инвест" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "КУДРОВО-ИНВЕСТ"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "proektnye_resheniya_ukb",
        "company_code": "proektnye_resheniya",
        "display_name": 'ООО "Проектные решения"',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"Проектные Решения"'],
        "active": True,
    },
    {
        "account_code": "proektnye_resheniya_sber",
        "company_code": "proektnye_resheniya",
        "display_name": 'ООО "Проектные решения" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ПРОЕКТНЫЕ РЕШЕНИЯ"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "riteil_park_ukb",
        "company_code": "riteil_park",
        "display_name": 'ООО "Ритейл Парк"',
        "bank": "ukb",
        "parser": "ukb_holder_outgoing",
        "match_all": ['holder: ООО"Ритейл Парк"'],
        "active": True,
    },
    {
        "account_code": "riteil_park_sber",
        "company_code": "riteil_park",
        "display_name": 'ООО "Ритейл Парк" СБЕР',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "РИТЕЙЛ ПАРК"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "media47_sber",
        "company_code": "media47",
        "display_name": 'ООО "Медиа 47"',
        "bank": "sber",
        "parser": "sber_outgoing_balance",
        "match_all": [
            'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "МЕДИА 47"',
            "СберБизнес",
        ],
        "active": True,
    },
    {
        "account_code": "gastropark_sovcom",
        "company_code": "gastropark",
        "display_name": 'ООО "ГАСТРОПАРК"',
        "bank": "sovcom",
        "parser": "sovcom_outgoing_balance",
        "match_all": ['Общество с ограниченной ответственностью "ГАСТРОПАРК"'],
        "active": True,
    },
    {
        "account_code": "ankon_raiffeisen",
        "company_code": "ankon",
        "display_name": 'ООО "АНКОН"',
        "bank": "raiffeisen",
        "parser": "raiffeisen_outgoing_balance",
        "match_all": ["АНКОН"],
        "active": True,
    },
]


DEFAULT_COMPANIES: list[dict[str, Any]] = [
    {
        "company_code": "parfenenko",
        "display_name": "ИП Парфененко М.А.",
        "section": "Управляющие компании",
        "google_total_cell": "D2",
        "accounts": ["parfenenko_ukb", "parfenenko_vtb"],
        "active": True,
    },
    {
        "company_code": "manevich",
        "display_name": "ИП Маневич А.Е.",
        "section": "Управляющие компании",
        "google_total_cell": "D3",
        "accounts": ["manevich_ukb", "manevich_sber"],
        "active": True,
    },
    {
        "company_code": "steit",
        "display_name": 'ООО "СТЕЙТ"',
        "section": "Балансодержатели",
        "google_total_cell": "D5",
        "accounts": ["steit_sber", "steit_ukb"],
        "active": True,
    },
    {
        "company_code": "metro",
        "display_name": 'ООО "МЕТРО"',
        "section": "Балансодержатели",
        "google_total_cell": "D6",
        "accounts": ["metro_ukb", "metro_sber"],
        "active": True,
    },
    {
        "company_code": "tsn_repinskoe",
        "display_name": 'ТСН "РЕПИНСКОЕ ВТБ"',
        "section": "Управляющие компании",
        "google_total_cell": "D8",
        "accounts": ["tsn_repinskoe_vtb"],
        "active": True,
    },
    {
        "company_code": "tsn_repinskoe2",
        "display_name": 'ТСН "РЕПИНСКОЕ 2 ТОЧКА"',
        "section": "Управляющие компании",
        "google_total_cell": "D9",
        "accounts": ["tsn_repinskoe2_tochka"],
        "active": True,
    },
    {
        "company_code": "tsn_oazis",
        "display_name": 'ТСН "ОАЗИС"',
        "section": "Управляющие компании",
        "google_total_cell": "D10",
        "accounts": ["tsn_oazis_tochka"],
        "active": True,
    },
    {
        "company_code": "ankon",
        "display_name": 'ООО "АНКОН"',
        "section": "Управляющие компании",
        "google_total_cell": "D12",
        "accounts": ["ankon_raiffeisen"],
        "active": True,
    },
    {
        "company_code": "kudrovo_stroy",
        "display_name": 'ООО "КУДРОВО-СТРОЙ"',
        "section": "Управляющие компании",
        "google_total_cell": "D13",
        "accounts": ["kudrovo_stroy_sber"],
        "active": True,
    },
    {
        "company_code": "klever",
        "display_name": 'ООО "Клевер"',
        "section": "Управляющие компании",
        "google_total_cell": "D14",
        "accounts": [
            "klever_bspb_375",
            "klever_bspb_852",
            "klever_sber",
            "klever_vtb",
        ],
        "active": True,
    },
    {
        "company_code": "partner",
        "display_name": 'ООО "Партнер"',
        "section": "Управляющие компании",
        "google_total_cell": "D15",
        "accounts": ["partner_ukb", "partner_vtb", "partner_sber"],
        "active": True,
    },
    {
        "company_code": "ohtinskaya_alleya",
        "display_name": 'ООО "Охтинская аллея"',
        "section": "Управляющие компании",
        "google_total_cell": "D16",
        "accounts": [
            "ohtinskaya_alleya_ukb",
            "ohtinskaya_alleya_vtb",
            "ohtinskaya_alleya_sber",
        ],
        "active": True,
    },
    {
        "company_code": "h1",
        "display_name": 'ООО "Н1"',
        "section": "Управляющие компании",
        "google_total_cell": "D17",
        "accounts": ["h1_sovcom", "h1_sber"],
        "active": True,
    },
    {
        "company_code": "raduga",
        "display_name": 'ООО "Радуга"',
        "section": "Управляющие компании",
        "google_total_cell": "D18",
        "accounts": ["raduga_sber", "raduga_vtb"],
        "active": True,
    },
    {
        "company_code": "reaktiv",
        "display_name": 'ООО "Реактив"',
        "section": "Управляющие компании",
        "google_total_cell": "D19",
        "accounts": ["reaktiv_bspb", "reaktiv_sber"],
        "active": True,
    },
    {
        "company_code": "romashki",
        "display_name": 'ООО "Ромашки"',
        "section": "Управляющие компании",
        "google_total_cell": "D20",
        "accounts": ["romashki_bspb", "romashki_ukb", "romashki_sber"],
        "active": True,
    },
    {
        "company_code": "smart_solution",
        "display_name": 'ООО "Смарт Солюшн"',
        "section": "Управляющие компании",
        "google_total_cell": "D21",
        "accounts": ["smart_solution_vtb", "smart_solution_sber"],
        "active": True,
    },
    {
        "company_code": "formula",
        "display_name": 'ООО "Формула"',
        "section": "Управляющие компании",
        "google_total_cell": "D22",
        "accounts": ["formula_ukb", "formula_vtb", "formula_sber"],
        "active": True,
    },
    {
        "company_code": "gastropark",
        "display_name": 'ООО "ГАСТРОПАРК"',
        "section": "Управляющие компании",
        "google_total_cell": "D23",
        "accounts": ["gastropark_sovcom"],
        "active": True,
    },
    {
        "company_code": "sityinvest",
        "display_name": 'ООО "СитиИнвест"',
        "section": "Балансодержатели",
        "google_total_cell": "D24",
        "accounts": ["sityinvest_ukb", "sityinvest_sber", "sityinvest_vtb"],
        "active": True,
    },
    {
        "company_code": "sev_zvezda",
        "display_name": 'ООО "Северная звезда"',
        "section": "Балансодержатели",
        "google_total_cell": "D25",
        "accounts": ["sev_zvezda_ukb", "sev_zvezda_sber", "sev_zvezda_vtb"],
        "active": True,
    },
    {
        "company_code": "dudergof",
        "display_name": 'ООО "Дудергоф"',
        "section": "Балансодержатели",
        "google_total_cell": "D26",
        "accounts": ["dudergof_ukb", "dudergof_sber"],
        "active": True,
    },
    {
        "company_code": "m_invest",
        "display_name": 'ООО "М-Инвест"',
        "section": "Балансодержатели",
        "google_total_cell": "D27",
        "accounts": ["m_invest_ukb"],
        "active": True,
    },
    {
        "company_code": "sp_impost",
        "display_name": 'ООО "СП-Импост"',
        "section": "Балансодержатели",
        "google_total_cell": "D28",
        "accounts": ["sp_impost_ukb", "sp_impost_sber"],
        "active": True,
    },
    {
        "company_code": "praga",
        "display_name": 'ООО "Прага"',
        "section": "Балансодержатели",
        "google_total_cell": "D29",
        "accounts": ["praga_ukb", "praga_vtb", "praga_sber"],
        "active": True,
    },
    {
        "company_code": "frank",
        "display_name": 'ООО "Франк"',
        "section": "Балансодержатели",
        "google_total_cell": "D30",
        "accounts": ["frank_ukb"],
        "active": True,
    },
    {
        "company_code": "ser",
        "display_name": 'ООО "СЭР"',
        "section": "Ген подрядные компании",
        "google_total_cell": "D32",
        "accounts": ["ser_ukb", "ser_sber"],
        "active": True,
    },
    {
        "company_code": "murino_grad",
        "display_name": 'ООО "Мурино-Град"',
        "section": "Инвестиционные компании",
        "google_total_cell": "D33",
        "accounts": ["murino_grad_sber"],
        "active": True,
    },
    {
        "company_code": "akvitania",
        "display_name": 'ООО "АКВИТАНИЯ"',
        "section": "Инвестиционные компании",
        "google_total_cell": "D34",
        "accounts": ["akvitania_ukb", "akvitania_sber"],
        "active": True,
    },
    {
        "company_code": "bergen",
        "display_name": 'ООО "БЕРГЕН"',
        "section": "Инвестиционные компании",
        "google_total_cell": "D35",
        "accounts": ["bergen_ukb", "bergen_sber"],
        "active": True,
    },
    {
        "company_code": "immobi",
        "display_name": 'ООО "ИММОБИ"',
        "section": "Инвестиционные компании",
        "google_total_cell": "D37",
        "accounts": ["immobi_ukb", "immobi_sber"],
        "active": True,
    },
    {
        "company_code": "kudrovo_invest",
        "display_name": 'ООО "Кудрово-Инвест"',
        "section": "Инвестиционные компании",
        "google_total_cell": "D39",
        "accounts": ["kudrovo_invest_ukb", "kudrovo_invest_sber"],
        "active": True,
    },
    {
        "company_code": "proektnye_resheniya",
        "display_name": 'ООО "Проектные решения"',
        "section": "Инвестиционные компании",
        "google_total_cell": "D40",
        "accounts": ["proektnye_resheniya_ukb", "proektnye_resheniya_sber"],
        "active": True,
    },
    {
        "company_code": "riteil_park",
        "display_name": 'ООО "Ритейл Парк"',
        "section": "Инвестиционные компании",
        "google_total_cell": "D41",
        "accounts": ["riteil_park_ukb", "riteil_park_sber"],
        "active": True,
    },
    {
        "company_code": "media47",
        "display_name": 'ООО "Медиа 47"',
        "section": "Управляющие компании",
        "google_total_cell": "D42",
        "accounts": ["media47_sber"],
        "active": True,
    },
]
