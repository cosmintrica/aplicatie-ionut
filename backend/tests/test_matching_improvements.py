from decimal import Decimal
from pathlib import Path

import pytest

from app.db import connect
from app.ingest import COMPANY_ID, seed_database
from app.repository import compare_list, get_evidence, get_list, get_offers, now
from app.settings import Settings
from app.smart import (match_profiles, normalized_unit_price, pack_alternative, pack_key,
                       price_basis, product_profile, scalar_pack)


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def seeded_matching(tmp_path_factory):
    settings = Settings(ROOT, tmp_path_factory.mktemp("matching-db") / "app.sqlite3", testing=True)
    seed_database(settings)
    return settings


@pytest.mark.parametrize("title,brand,amount", [
    ("Cafea Boabe Beans500gjacobs", "jacobs", "500"),
    ("Cafea macinata250gtchibo", "tchibo", "250"),
    ("Lavazza Cafea boabe Crema1kg", "lavazza", "1000"),
    ("Dorna apa minerala plata0,5l", "dorna", "500"),
])
def test_known_brands_and_attached_units_are_extracted_without_fuzzy_matching(title, brand, amount):
    profile = product_profile(title)
    assert profile["brand"] == brand
    assert profile["pack"]["amount"] == amount


@pytest.mark.parametrize("text,key", [
    ("1,8 litri", ("volume", "1800", 1)),
    ("500 mililitri", ("volume", "500", 1)),
    ("1 mililitru", ("volume", "1", 1)),
    ("250 grame", ("mass", "250", 1)),
    ("1 kilogram", ("mass", "1000", 1)),
    ("3 x 100 g", ("mass", "100", 3)),
    ("100 G X3", ("mass", "100", 3)),
])
def test_explicit_unit_aliases_and_suffix_multipacks_preserve_pack_structure(text, key):
    assert pack_key(scalar_pack(text)) == key


def test_suffix_multipack_is_not_matched_to_one_package():
    reference = product_profile("Cafea Boabe Tchibo Exclusive100 G X3")
    single = product_profile("Cafea Boabe Tchibo Exclusive100g")
    assert reference["pack"]["count"] == 3
    assert match_profiles(reference, single)["verdict"] == "variant_conflict"
    assert scalar_pack("3 x 100 g x 2") is None


@pytest.mark.parametrize("title,expected", [
    ("Crackers Cremosi200g Jacobs", "snack"),
    ("Bellarom Ciocolata calda plicuri", "hot_drink"),
    ("Bellarom Cappuccino", "hot_drink"),
    ("Pilos Lapte condensat", "milk"),
    ("W5 Lapte pentru curatare", "detergent"),
])
def test_product_name_has_priority_over_brand_and_merchandising_category(title, expected):
    assert product_profile(title, "250g", raw_category="Cafea")["kind"] == expected


@pytest.mark.parametrize("left,right", [
    ("Intenso", "Gold"), ("Intenso", "decofeinizata"), ("Royal", "Gold"),
])
def test_explicit_coffee_variants_cannot_be_joined(left, right):
    result = match_profiles(product_profile(f"Bellarom Cafea macinata {left}250g"),
                            product_profile(f"Bellarom Cafea macinata {right}250g"))
    assert result["verdict"] == "variant_conflict"
    assert any(reason.startswith("Varianta:") for reason in result["attribute_conflicts"])


@pytest.mark.parametrize("other,purpose", [
    ("W5 Solutie curatare WC cu inalbit.", "WC"),
    ("W5 Solutie pt. desfundarea tevilor", "țevi"),
    ("W5 Degresant power cleaner", "degresare"),
])
def test_cleaning_purpose_blocks_real_same_brand_same_volume_false_matches(other, purpose):
    reference = product_profile("W5 Detergent de vase concentrat", "1l", raw_category="Detergenti")
    offered = product_profile(other, "1l", raw_category="Detergenti")
    assert offered["purpose"] == purpose
    result = match_profiles(reference, offered)
    assert result["verdict"] == "variant_conflict"
    assert any(reason.startswith("Utilizarea:") for reason in result["attribute_conflicts"])
    assert pack_alternative(reference, product_profile(other, "500ml", raw_category="Detergenti")) is None


@pytest.mark.parametrize("reference,offer,attribute", [
    ("Jacobs Kronung cafea250g", "Jacobs Kronung cafea macinata250g", "forma cerută"),
    ("Jacobs Kronung cafea250g", "Jacobs Kronung cafea boabe250g", "forma cerută"),
    ("Pilos Lapte1.5%1l", "Pilos Lapte1.5%UHT1l", "tratamentul cerut"),
    ("Pilos Lapte1.5%1l", "Pilos Lapte1.5%ESL1l", "tratamentul cerut"),
])
def test_explicit_offer_characteristic_requires_user_choice_when_reference_is_unknown(reference, offer, attribute):
    target, offered = product_profile(reference), product_profile(offer)
    result = match_profiles(target, offered)
    assert result["verdict"] == "needs_details"
    assert attribute in result["missing_attributes"]
    # Contextul explicit al referinței poate furniza informația lipsă.
    assert match_profiles(target, offered, offered)["verdict"] == "same_variant_candidate"


def test_offer_catalog_characteristic_is_context_not_a_confirmed_commercial_attribute():
    generic = product_profile("Jacobs Kronung Cafea500g")
    offered = product_profile("Jacobs Kronung Cafea250g")
    catalog = product_profile("Jacobs Kronung Alintaroma250g")
    result = match_profiles(generic, offered, ignore_pack=True, offer_catalog=catalog)
    assert result["verdict"] == "needs_details"
    assert result["profile"]["variant"] is None
    assert any("catalogul ofertei declară Alintaroma" in reason for reason in result["match_reasons"])
    alternative = pack_alternative(generic, offered, offer_catalog=catalog)
    assert alternative["status"] == "needs_details"


@pytest.mark.parametrize("name,pack,price,unit,expected,label", [
    ("Bellarom Cafea macinata Gold", "250g", "16.49", "kg", "65.960000", "65,96 lei/kg"),
    ("Bellarom Cafea macinata Gold", "500g", "32.49", "kg", "64.980000", "64,98 lei/kg"),
    ("Zuzu Lapte1.5%", "1.8l", "13.99", "l", "7.772222", "7,77 lei/l"),
    ("Tchibo Cafea boabe100g x3", "", "10.00", "kg", "33.333333", "33,33 lei/kg"),
])
def test_unit_prices_use_backend_decimals_and_full_multipack_amount(name, pack, price, unit, expected, label):
    profile = product_profile(name, pack)
    result = normalized_unit_price(Decimal(price), profile, price_basis(pack or "BUC", profile, "lidl"))
    assert result["amount"] == expected
    assert result["label"] == label
    assert result["unit"] == unit


def test_unknown_or_contradictory_price_basis_does_not_gain_unit_price():
    coffee = product_profile("Jacobs cafea250g")
    water = product_profile("Borsec apa plata2l")
    for raw_unit, profile in [("K", coffee), ("Kg", coffee), ("L", water), ("Litru", water)]:
        assert normalized_unit_price("10.00", profile, price_basis(raw_unit, profile, "monitor")) is None
    contradicted = product_profile("Jacobs cafea250g", "500g")
    assert normalized_unit_price("10.00", contradicted, price_basis("BUC", contradicted, "monitor")) is None
    explicit_kg = product_profile("Mere", "per kg")
    basis = price_basis("per kg", explicit_kg, "lidl")
    assert basis["quantity_eligible"] is False
    assert normalized_unit_price("4.99", explicit_kg, basis)["amount"] == "4.990000"


def test_real_pack_alternatives_have_explanations_and_backend_unit_price_spread(seeded_matching):
    with connect(seeded_matching) as conn:
        result = get_offers(conn, "lidl:598", "slatina_5km")
        assert [q["source_item_id"] for q in result["pack_alternatives"]] == ["lidl:599"]
        alternative = result["pack_alternatives"][0]
        assert alternative["alternative"]["status"] == "compatible_characteristics"
        assert alternative["verdict"] == "variant_conflict"  # Alt ambalaj, fără înlocuire automată.
        group = result["unit_price_groups"][0]
        assert group["minimum"]["amount"] == "64.980000"
        assert group["maximum"]["amount"] == "65.960000"
        assert group["spread"]["label"] == "0,98 lei/kg"
        assert group["best_option"]["source_item_id"] == "lidl:599"
        assert {q["source_item_id"] for q in group["options"]} == {"lidl:598", "lidl:599"}
        evidence = get_evidence(conn, alternative["observation_id"], alternative["reference_item_id"])
        assert evidence["alternative"] == alternative["alternative"]
        assert evidence["match_reasons"] == alternative["match_reasons"]


def test_real_cleaning_purposes_and_concentration_remain_separate(seeded_matching):
    with connect(seeded_matching) as conn:
        result = get_offers(conn, "lidl:1154", "slatina_5km")
        related = {q["source_item_id"]: q for q in result["related_offers"]}
        for item_id in ("lidl:1170", "lidl:2233", "lidl:1150"):
            assert related[item_id]["verdict"] == "variant_conflict"
        assert all(q["alternative"]["status"] == "needs_details" for q in result["pack_alternatives"])
        assert all(q["source_item_id"] == "lidl:1154" for group in result["unit_price_groups"] for q in group["options"])


def test_actual_reference_is_explicit_and_other_pack_does_not_enter_original_basket(seeded_matching):
    with connect(seeded_matching) as conn:
        stamp = now()
        list_id = "matching-reference-test"
        conn.execute("INSERT INTO shopping_list VALUES(?,?,?,?,?,?,?)", (list_id, COMPANY_ID, "Test", "slatina_5km", 1, stamp, stamp))
        conn.execute("INSERT INTO list_line VALUES(?,?,?,?,?,?,?,?,?)", ("matching-reference-line", COMPANY_ID, list_id, "lidl:598", "Cafea 500 g cerută inițial", "2", "item", None, stamp))
        shopping = get_list(conn, list_id)
        assert shopping["lines"][0]["profile"]["pack"]["amount"] == "250"
        result = compare_list(conn, list_id, 1, "slatina_5km")
        line = result["line_comparisons"][0]
        assert line["description"] == "Cafea 500 g cerută inițial"
        assert line["source_product_id"] == "lidl:598"
        assert line["source_product_name"] == shopping["lines"][0]["source_product_name"]
        assert all(q["source_item_id"] == "lidl:598" for q in line["comparable_options"])
        assert line["pack_alternatives"][0]["source_item_id"] == "lidl:599"
        assert "estimated_item_total" not in line["pack_alternatives"][0]
        assert result["estimated_baskets"][0]["estimated_total"]["amount"] == "32.98"
        assert result["payable_total"] is result["savings"] is None


def test_real_larger_milk_pack_is_visible_with_unit_price_but_is_not_same_pack(seeded_matching):
    with connect(seeded_matching) as conn:
        result = get_offers(conn, "monitor:1012187", "slatina_5km")
        alternative = next(q for q in result["pack_alternatives"] if q["source_item_id"] == "lidl:1729")
        assert alternative["profile"]["pack"]["amount"] == "1800"
        assert alternative["verdict"] == "variant_conflict"
        assert alternative["alternative"]["status"] == "compatible_characteristics"
        assert alternative["unit_price"]["label"] == "7,77 lei/l"
        assert not any(q["source_item_id"] == "lidl:1729" for q in result["related_offers"])
