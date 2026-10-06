from decimal import Decimal
import pytest
from hypothesis import given, strategies as st
from app.domain import assess_quote, exact_quantity, money


@pytest.mark.parametrize("catalog,title", [
    ("Lapte 1 L", "Lapte 1000 ml"),
    ("Cafea 1 kg", "Cafea 1000 g"),
    ("Apă 1.5 L", "Apă 1500 ml"),
    ("Apă 1,5 L", "Apă 1500 ml"),
    ("Cafea 0.25 kg", "Cafea 250 g"),
])
def test_scalar_units_are_normalized_without_false_conflict(catalog, title):
    assert not assess_quote(catalog, title, "", "")['conflicts']


def test_different_explicit_pack_size_is_not_merged():
    result = assess_quote("Jacobs cafea 250g", "Jacobs cafea 500g", "Cafea", "BUC")
    assert result["relation"] == "INCOMPATIBLE"


def test_multipack_is_not_interpreted_as_single_container():
    result = assess_quote("Apă 6 x 1L", "Apă 1L", "Apă", "BUC")
    assert result["relation"] != "IDENTICAL_PACK"
    assert any("Baza prețului" in reason for reason in result["unknowns"])


@pytest.mark.parametrize("value", ["0", "-1", "1.2345678", "1000001", "1,234.56", "NaN", "Infinity", "1e4", ""])
def test_quantity_rejects_ambiguous_nonpositive_or_unbounded_values(value):
    with pytest.raises(ValueError):
        exact_quantity(value)


def test_quantity_preserves_decimal_without_float():
    assert exact_quantity("001,2500") == "1.25"
    assert money(Decimal("0.10") + Decimal("0.20"))["amount"] == "0.30"
    assert money("1.005")["amount"] == "1.01"


@given(st.integers(min_value=1, max_value=1000000000))
def test_positive_decimal_quantities_round_trip_exactly(millionths):
    quantity = Decimal(millionths) / Decimal(1000000)
    assert Decimal(exact_quantity(format(quantity, "f"))) == quantity
