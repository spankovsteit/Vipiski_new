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
