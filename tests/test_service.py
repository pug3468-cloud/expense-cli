from datetime import date
from decimal import Decimal

import pytest

from expense_cli.service import ValidationError, parse_amount


# ---- add ----

def test_add_defaults_to_today(service):
    e = service.add("120", "food", note="午餐")
    assert e.amount == Decimal("120")
    assert e.category == "food"
    assert e.note == "午餐"
    assert e.date == date.today()


def test_add_with_explicit_date_and_persists(service):
    service.add("45.5", "transport", on_date="2026-03-01")
    [e] = service.list()
    assert e.date == date(2026, 3, 1)
    assert e.amount == Decimal("45.5")
    assert e.note == ""


@pytest.mark.parametrize("bad", ["0", "-50", "-0.01", "0.00"])
def test_add_rejects_non_positive_amount(service, bad):
    with pytest.raises(ValidationError, match="正數"):
        service.add(bad, "food")
    assert service.list() == []  # 失敗時不寫入任何資料


@pytest.mark.parametrize("bad", ["abc", "", "12a", "nan", "inf", "-inf"])
def test_add_rejects_non_numeric_amount(service, bad):
    with pytest.raises(ValidationError, match="數字"):
        service.add(bad, "food")


@pytest.mark.parametrize("bad", ["2026/01/01", "2026-13-01", "yesterday"])
def test_add_rejects_bad_date(service, bad):
    with pytest.raises(ValidationError, match="YYYY-MM-DD"):
        service.add("10", "food", on_date=bad)


def test_add_rejects_blank_category(service):
    with pytest.raises(ValidationError, match="類別"):
        service.add("10", "   ")


def test_amount_is_exact_decimal():
    assert parse_amount("0.1") + parse_amount("0.2") == Decimal("0.3")


# ---- list ----

def test_list_empty(service):
    assert service.list() == []


def test_list_sorted_by_date_stable_within_same_day(service):
    service.add("1", "a", on_date="2026-05-03")
    service.add("2", "b", on_date="2026-05-01")
    service.add("3", "c", on_date="2026-05-03")
    service.add("4", "d", on_date="2026-05-02")
    assert [e.category for e in service.list()] == ["b", "d", "a", "c"]


# ---- summary ----

def test_summary_groups_by_category_with_total(service):
    service.add("100", "food")
    service.add("20.5", "food")
    service.add("300", "rent")
    service.add("0.1", "misc")
    service.add("0.2", "misc")
    totals, grand = service.summary()
    assert totals == {
        "rent": Decimal("300"),
        "food": Decimal("120.5"),
        "misc": Decimal("0.3"),
    }
    assert list(totals) == ["rent", "food", "misc"]  # 依金額由大到小
    assert grand == Decimal("420.8")


def test_summary_empty(service):
    assert service.summary() == ({}, Decimal("0"))
