from collections import Counter
from decimal import Decimal
from pathlib import Path
import pytest

from app.db import connect
from app.ingest import COMPANY_ID, seed_database
from app.repository import compare_list, get_evidence, get_offers, search_catalog, now
from app.settings import Settings
from app.smart import match_profiles, price_basis, product_profile, scalar_pack


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def seeded(tmp_path_factory):
    settings = Settings(ROOT, tmp_path_factory.mktemp("smart-db") / "app.sqlite3", testing=True)
    seed_database(settings)
    return settings


def compare(conn, specs):
    # Numai baza temporară a testelor; nu modifică listele utilizatorului.
    stamp = now()
    list_id = "smart-test"
    conn.execute("DELETE FROM shopping_list WHERE id=?", (list_id,))
    conn.execute("INSERT INTO shopping_list VALUES(?,?,?,?,?,?,?)", (list_id, COMPANY_ID, "Test", "slatina_5km", 1, stamp, stamp))
    for index, (item_id, quantity) in enumerate(specs):
        name = conn.execute("SELECT name FROM source_product WHERE id=?", (item_id,)).fetchone()[0]
        conn.execute("INSERT INTO list_line VALUES(?,?,?,?,?,?,?,?,?)", (f"smart-line-{index}", COMPANY_ID, list_id, item_id, name, quantity, "item", None, stamp))
    return compare_list(conn, list_id, 1, "slatina_5km")


@pytest.mark.parametrize("left,right", [("Zuzu Lapte 1.5% 1l", "LAPTE 1.5%GRS.1L ZUZU"),
                                       ("Borsec Apă Plată 2l", "APA MIN NECARB 2000ML BORSEC.")])
def test_explicit_attribute_equivalence_accepts_real_abbreviations(left, right):
    result = match_profiles(product_profile(left), product_profile(right))
    assert result["verdict"] == "same_variant_candidate"
    assert result["missing_attributes"] == []


@pytest.mark.parametrize("reference,offer,conflict", [
    ("Zuzu Lapte 1.5% 1l", "Zuzu Lapte 3.5% 1l", "Grăsimea"),
    ("Zuzu Lapte 1.5% 1l", "Zuzu Lapte 1.5% 1.8l", "Ambalajul"),
    ("Zuzu Lapte 1.5% 1l", "Pilos Lapte 1.5% ESL 1l", "Marca"),
    ("Jacobs Kronung cafea măcinată250g", "Jacobs Kronung cafea boabe250g", "Forma"),
    ("Jacobs Kronung cafea250g", "Jacobs Kronung cafea500g", "Ambalajul"),
    ("Borsec apă plată2l", "Borsec apă carbogazoasă2l", "Tipul apei"),
])
def test_critical_attribute_conflicts_are_explained(reference, offer, conflict):
    result = match_profiles(product_profile(reference), product_profile(offer))
    assert result["verdict"] == "variant_conflict"
    assert any(reason.startswith(conflict) for reason in result["attribute_conflicts"])


def test_unknown_attribute_does_not_become_equality_and_source_context_is_preserved():
    reference = product_profile("Jacobs Kronung cafea măcinată250g")
    generic = product_profile("Jacobs Kronung cafea măcinată250g")
    source = product_profile("JACOBS KRONUNG ALINTAROMA250G")
    assert match_profiles(reference, generic, source)["verdict"] == "needs_details"
    assert match_profiles(reference, generic, source)["reference_profile"]["variant"] == "alintaroma"
    intense = product_profile("JACOBS KRONUNG INT CAFEA MACIN250G", raw_brand="Jacobs Kronung Intense")
    assert match_profiles(reference, intense, source)["verdict"] == "variant_conflict"


def test_match_explanations_localize_kind_and_name_the_missing_requested_variant():
    reference = product_profile("Jacobs Kronung cafea măcinată250g")
    result = match_profiles(reference, reference, product_profile("JACOBS KRONUNG ALINTAROMA250G"))
    assert result["profile"]["kind"] == "coffee"
    assert "Tipul produsului: cafea." in result["match_reasons"]
    assert "Lipsesc: varianta Alintaroma." in result["match_reasons"]
    assert result["missing_attributes"] == ["varianta"]
    for title, expected in [("Zuzu Lapte1.5%1l", "lapte"), ("Borsec Apa plata2l", "apă"), ("Fairy detergent500ml", "detergent")]:
        profile = product_profile(title)
        assert f"Tipul produsului: {expected}." in match_profiles(profile, profile)["match_reasons"]
    conflict = match_profiles(product_profile("Zuzu Lapte1.5%1l"), product_profile("Borsec Apa plata1l"))
    assert "Tipul produsului: apă în ofertă, lapte în cerere." in conflict["attribute_conflicts"]


def test_pack_normalization_does_not_flatten_multipacks_or_conflicting_source_columns():
    assert scalar_pack("6 x 1l")["count"] == 6
    assert match_profiles(product_profile("Borsec apa plata6x1l"), product_profile("Borsec apa plata1l"))["verdict"] == "variant_conflict"
    offered = product_profile("Jacobs cafea250g", raw_pack="500g")
    assert offered["pack_conflict"] is True
    assert match_profiles(product_profile("Jacobs cafea250g"), offered)["verdict"] == "variant_conflict"
    assert scalar_pack("per kg") is None
    assert product_profile("Pilos Lapte condensat", "340g", raw_category="Cafea")["kind"] == "milk"


def test_quantity_bases_distinguish_invariant_one_litre_and_ambiguous_units():
    milk = product_profile("Zuzu Lapte1.5%1l")
    water = product_profile("Borsec Apa plata2l")
    coffee = product_profile("Jacobs cafea250g")
    assert price_basis("Litru", milk, "monitor")["status"] == "equivalent_one_litre"
    assert price_basis("L", water, "monitor")["quantity_eligible"] is False
    assert price_basis("K", coffee, "monitor")["quantity_eligible"] is False
    assert price_basis("Kg", coffee, "monitor")["quantity_eligible"] is False
    assert price_basis("BUC", water, "monitor")["quantity_eligible"] is True
    assert price_basis("per kg", product_profile("Mere", "per kg"), "lidl")["quantity_eligible"] is False


def test_real_quotes_have_different_verdicts_and_ascending_prices(seeded):
    with connect(seeded) as conn:
        milk = get_offers(conn, "monitor:1012187", "slatina_5km")
        coffee = get_offers(conn, "monitor:1013048", "slatina_5km")
        water = get_offers(conn, "monitor:1361463", "slatina_5km")
        assert milk["price_summary"]["candidate_count"] == 16
        assert water["price_summary"]["candidate_count"] == 15
        assert milk["price_summary"]["minimum"]["amount"] == "6.09"
        assert milk["price_summary"]["maximum"]["amount"] == "7.35"
        valid = [quote for quote in coffee["quotes"] if quote["price"]]
        assert Counter(quote["verdict"] for quote in valid) == {"needs_details": 14, "variant_conflict": 3}
        assert [Decimal(quote["price"]["amount"]) for quote in valid] == sorted(Decimal(quote["price"]["amount"]) for quote in valid)


def test_zero_price_is_missing_and_old_catalog_id_gets_distinct_related_observations(seeded):
    with connect(seeded) as conn:
        old = get_offers(conn, "monitor:1011559", "slatina_5km")
        assert old["price_summary"]["minimum"] is None
        assert all(quote["price"] is None for quote in old["quotes"])
        assert len(old["related_offers"]) == 15
        assert all(quote["source_item_id"] == "monitor:1361463" and quote["price"]["amount"] != "0.00" for quote in old["related_offers"])


def test_priced_filter_is_applied_before_pagination_and_cursor_binds_filters(seeded):
    with connect(seeded) as conn:
        first = search_catalog(conn, scenario_id="slatina_5km", priced_only=True, limit=3)
        second = search_catalog(conn, scenario_id="slatina_5km", priced_only=True, limit=3, cursor=first["next_cursor"])
        assert first["total"] == 2448
        assert all(item["price_summary"]["minimum"] for item in first["items"] + second["items"])
        assert not {item["id"] for item in first["items"]} & {item["id"] for item in second["items"]}
        from app.repository import AppError
        with pytest.raises(AppError, match="Cursorul"):
            search_catalog(conn, scenario_id="slatina_5km", priced_only=False, limit=3, cursor=first["next_cursor"])
        cheapest = search_catalog(conn, scenario_id="slatina_5km", availability="priced", sort="price", limit=3)
        amounts = [Decimal(item["price_summary"]["minimum"]["amount"]) for item in cheapest["items"]]
        assert amounts == sorted(amounts)


def test_estimated_baskets_multiply_requested_pack_counts_and_exclude_partial_stores(seeded):
    with connect(seeded) as conn:
        result = compare(conn, [("monitor:1012187", "2"), ("monitor:1361463", "3")])
        assert len(result["estimated_baskets"]) == 2
        assert all(basket["estimated_total"]["amount"] == "26.55" and basket["eligible_line_count"] == 2 for basket in result["estimated_baskets"])
        assert all(basket["estimated_total"] is None for basket in result["incomplete_estimates"])
        assert result["payable_total"] is result["savings"] is result["estimated_savings"] is None
        water = next(line for line in result["line_comparisons"] if line["reference_profile"]["kind"] == "water")
        assert water["price_min"]["amount"] == "4.39"
        assert all(quote["price_basis"]["quantity_eligible"] for quote in water["comparable_options"])


def test_conflicting_coffee_is_not_ranked_as_a_complete_basket(seeded):
    with connect(seeded) as conn:
        result = compare(conn, [("monitor:1012187", "1"), ("monitor:1013048", "1"), ("monitor:1361463", "1")])
        assert result["estimated_baskets"] == []
        coffee = next(line for line in result["line_comparisons"] if line["reference_profile"]["kind"] == "coffee")
        assert len(coffee["conflicting_options"]) == 3
        assert coffee["best_option"] is None
        assert coffee["price_min"] is None
        assert coffee["groups"]
        assert all(not group["estimate_eligible"] for group in coffee["groups"])
        assert all(basket["estimated_total"] is None for basket in result["incomplete_estimates"])


def test_fractional_packages_are_not_multiplied_as_purchasable_units(seeded):
    with connect(seeded) as conn:
        result = compare(conn, [("monitor:1012187", "0.5")])
        assert result["estimated_baskets"] == []
        assert result["line_comparisons"][0]["comparable_options"] == []
        assert any("întreg" in warning for warning in result["line_comparisons"][0]["warnings"])


def test_single_product_estimate_spread_is_useful_without_claiming_realized_savings(seeded):
    with connect(seeded) as conn:
        result = compare(conn, [("monitor:1012187", "4")])
        assert len(result["estimated_baskets"]) == 16
        assert result["estimated_range"]["minimum"]["amount"] == "24.36"
        assert result["estimated_range"]["maximum"]["amount"] == "29.40"
        assert result["estimated_range"]["spread"]["amount"] == "5.04"
        assert result["savings"] is None


@pytest.mark.parametrize("reference_item_id,related_item_id,expected_verdict", [
    ("lidl:1721", "lidl:1740", "variant_conflict"),
    ("monitor:1013048", "lidl:615", "needs_details"),
])
def test_evidence_preserves_the_selected_product_context(seeded, reference_item_id, related_item_id, expected_verdict):
    with connect(seeded) as conn:
        offers = get_offers(conn, reference_item_id, "slatina_5km")
        option = next(quote for quote in offers["related_offers"] if quote["source_item_id"] == related_item_id)
        assert option["verdict"] == expected_verdict
        evidence = get_evidence(conn, option["observation_id"], option["reference_item_id"])
        assert evidence["verdict"] == option["verdict"]
        assert evidence["reference_profile"] == option["reference_profile"]
        assert evidence["match_reasons"] == option["match_reasons"]
        assert evidence["evaluation_scope"] == "selected_product"
