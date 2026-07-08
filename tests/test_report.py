from decimal import Decimal

from vipiski.report import build_telegram_text


def test_build_telegram_text_skips_inactive_account_codes():
    companies = [
        {
            "display_name": 'ООО "Реактив"',
            "section": "Управляющие компании",
            "accounts": ["reactive_active", "reactive_inactive"],
            "active": True,
        }
    ]
    account_rules = [
        {
            "account_code": "reactive_active",
            "display_name": "Реактив СБЕР",
            "active": True,
        },
        {
            "account_code": "reactive_inactive",
            "display_name": "Реактив ВТБ (архив)",
            "active": False,
        },
    ]
    balances = {
        "reactive_active": Decimal("1200.00"),
        "reactive_inactive": Decimal("9900.00"),
    }

    text = build_telegram_text(companies, account_rules, balances, {})

    assert "Реактив СБЕР - 1 200,00" in text
    assert "Реактив ВТБ (архив)" not in text


def test_build_telegram_text_aggregates_same_label_accounts():
    companies = [
        {
            "display_name": 'ООО "Смарт Солюшн"',
            "section": "Управляющие компании",
            "accounts": ["bspb_1", "bspb_2", "vtb_1"],
            "active": True,
        }
    ]
    account_rules = [
        {"account_code": "bspb_1", "display_name": 'ООО "Смарт Солюшн" BSPB', "active": True},
        {"account_code": "bspb_2", "display_name": 'ООО "Смарт Солюшн" BSPB', "active": True},
        {"account_code": "vtb_1", "display_name": 'ООО "Смарт Солюшн" VTB', "active": True},
    ]
    balances = {
        "bspb_1": Decimal("100.00"),
        "bspb_2": Decimal("250.50"),
        "vtb_1": Decimal("10.00"),
    }

    text = build_telegram_text(companies, account_rules, balances, {})

    assert 'ООО "Смарт Солюшн" BSPB - 350,50' in text
    assert text.count('ООО "Смарт Солюшн" BSPB -') == 1
    assert 'ООО "Смарт Солюшн" VTB - 10,00' in text


def test_build_telegram_text_merges_excel_suffix_into_base_label():
    companies = [
        {
            "display_name": 'ООО "Радуга"',
            "section": "Управляющие компании",
            "accounts": ["raduga_sber", "raduga_sber_5169", "raduga_vtb"],
            "active": True,
        }
    ]
    account_rules = [
        {
            "account_code": "raduga_sber",
            "company_code": "raduga",
            "display_name": "ООО Радуга СБЕР",
            "bank": "sber",
            "active": True,
        },
        {
            "account_code": "raduga_sber_5169",
            "company_code": "raduga",
            "display_name": 'ООО "Радуга" SBER',
            "bank": "sber",
            "active": True,
        },
        {
            "account_code": "raduga_vtb",
            "company_code": "raduga",
            "display_name": "ООО Радуга ВТБ",
            "bank": "vtb",
            "active": True,
        },
    ]
    balances = {
        "raduga_sber": Decimal("102825.41"),
        "raduga_sber_5169": Decimal("0"),
        "raduga_vtb": Decimal("4369.46"),
    }

    text = build_telegram_text(companies, account_rules, balances, {})

    assert "ООО Радуга СБЕР - 102 825,41" in text
    assert 'ООО "Радуга" SBER' not in text
    assert text.count("ООО Радуга СБЕР -") == 1
