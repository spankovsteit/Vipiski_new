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
