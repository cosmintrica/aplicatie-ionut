"""Regresii E0/E1a pe probe reale; nu evaluează precizia comercială a matchingului."""
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import connect
from app.domain import assess_quote, exact_quantity, money, parse_price
from app.ingest import seed_database
from app.repository import AppError, compare_list, get_evidence, get_offers
from app.settings import Settings


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "fixtures/snapshot-manifest.json").read_text(encoding="utf-8"))
SEMANTIC = json.loads((ROOT / "fixtures/semantic-regressions.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def seeded_settings(tmp_path_factory):
    settings = Settings(root_dir=ROOT, db_path=tmp_path_factory.mktemp("e1a-db") / "app.sqlite3", testing=True)
    seed_database(settings)
    return settings


def test_original_probe_hashes_and_sizes_match_recorded_manifest():
    assert len(MANIFEST["files"]) == 11
    for entry in MANIFEST["files"]:
        content = (ROOT / entry["path"]).read_bytes()
        assert len(content) == entry["bytes"], entry["path"]
        assert hashlib.sha256(content).hexdigest() == entry["sha256"], entry["path"]


def test_collection_timestamps_preserve_only_existing_request_evidence():
    requests = json.loads((ROOT / "probe-data/requests.json").read_text(encoding="utf-8-sig"))
    by_name = {row["Name"]: row["CollectedAt"] for row in requests}
    for entry in MANIFEST["files"]:
        assert entry["collected_at"] == by_name.get(Path(entry["path"]).stem)
        assert entry["source_price_validity_at"] is None
        if entry["role"].startswith("lidl_"):
            metadata = entry["file_metadata"]
            assert metadata["metadata_is_not_price_validity"] is True
            assert metadata["workbook_modified_utc"] == "2026-10-04T20:08:50Z"


def test_changed_probe_is_refused_before_import_without_touching_original(tmp_path):
    project = tmp_path / "isolated-project"
    (project / "probe-data").mkdir(parents=True)
    (project / "fixtures").mkdir()
    entry = next(row for row in MANIFEST["files"] if row["path"] == "probe-data/requests.json")
    content = (ROOT / entry["path"]).read_bytes()
    (project / entry["path"]).write_bytes(content + b"\n")
    (project / "fixtures/snapshot-manifest.json").write_text(json.dumps({"files": [entry]}), encoding="utf-8")
    settings = Settings(root_dir=project, db_path=project / "isolated.sqlite3", testing=True)
    with pytest.raises(RuntimeError, match="manifestului SHA-256"):
        seed_database(settings)
    assert (ROOT / entry["path"]).read_bytes() == content
    with connect(settings) as conn:
        assert conn.execute("SELECT COUNT(*) FROM source_product").fetchone()[0] == 0


def test_catalog_and_lidl_rows_are_preserved_and_reimport_is_idempotent(seeded_settings):
    before = seed_database(seeded_settings)
    with connect(seeded_settings) as conn:
        before_ids = [row[0] for row in conn.execute("SELECT id FROM snapshot ORDER BY id")]
        empty_names = conn.execute("SELECT COUNT(*) FROM source_product WHERE source_id='monitor' AND name='' ").fetchone()[0]
        before_observations = conn.execute("SELECT COUNT(*) FROM observation").fetchone()[0]
    after = seed_database(seeded_settings)
    assert before == after
    assert after["monitor_count"] == 104794
    assert after["lidl_count"] == 2444
    assert after["catalog_count"] == 104794 + 2444
    assert empty_names == 12
    with connect(seeded_settings) as conn:
        assert [row[0] for row in conn.execute("SELECT id FROM snapshot ORDER BY id")] == before_ids
        assert conn.execute("SELECT COUNT(*) FROM observation").fetchone()[0] == before_observations == 2703


@pytest.mark.parametrize("scenario,stores,quotes,rows", [
    ("slatina_5km", 18, 65, 126),
    ("bucharest_1km", 19, 73, 133),
])
def test_geographic_scope_counts_are_kept_separate(seeded_settings, scenario, stores, quotes, rows):
    with connect(seeded_settings) as conn:
        assert conn.execute("SELECT COUNT(*) FROM store WHERE scenario_id=?", (scenario,)).fetchone()[0] == stores
        count = conn.execute("SELECT COUNT(*),SUM(valid) FROM observation WHERE scenario_id=?", (scenario,)).fetchone()
        assert tuple(count) == (rows, quotes)
        dates = {row[0] for row in conn.execute("SELECT source_priced_at FROM observation WHERE scenario_id=? AND valid=1", (scenario,))}
    assert dates == {"05.10.2026 04:00"}


def test_zero_undated_quote_is_missing_and_does_not_borrow_related_borsec_price(seeded_settings):
    with connect(seeded_settings) as conn:
        missing = conn.execute("SELECT raw_price,price,source_priced_at,valid FROM observation WHERE scenario_id='slatina_5km' AND store_id='7520' AND item_id='monitor:1011559'").fetchone()
        available = conn.execute("SELECT price FROM observation WHERE scenario_id='slatina_5km' AND store_id='7520' AND item_id='monitor:1361463'").fetchone()
    assert tuple(missing) == ("0", None, None, 0)
    assert available["price"] == "3.78"
    assert parse_price("0") is None
    assert parse_price("") is None


def test_jacobs_common_catalog_id_is_not_verified_identity():
    records = SEMANTIC["jacobs_variant_conflict"]["records"]
    assert records[0]["catalog_id"] == records[1]["catalog_id"] == "1013048"
    decisions = [assess_quote(row["catalog_name"], row["commercial_name"], row["raw_category"], row["raw_unit"]) for row in records]
    assert decisions[0]["relation"] == "INCOMPATIBLE"
    assert decisions[0]["conflicts"]
    assert decisions[1]["relation"] == "SOURCE_ASSOCIATION"
    assert decisions[1]["unknowns"]
    assert all(decision["relation"] != "IDENTICAL_PACK" for decision in decisions)


@pytest.mark.parametrize("example", SEMANTIC["category_conflicts"], ids=["ariel_lapte", "fairy_dezinfectanti"])
def test_wrong_source_categories_detected_even_when_commercial_name_is_empty(example, seeded_settings):
    row = example["record"]
    assert row["commercial_name"] == ""
    decision = assess_quote(row["catalog_name"], row["commercial_name"], row["raw_category"], row["raw_unit"])
    assert decision["relation"] == "INCOMPATIBLE"
    assert decision["conflicts"]
    with connect(seeded_settings) as conn:
        imported = conn.execute("SELECT category_id,category_reason FROM source_product WHERE id=?", ("monitor:" + row["catalog_id"],)).fetchone()
        evidence = conn.execute("SELECT raw_category,raw_record FROM observation WHERE scenario_id='slatina_5km' AND store_id='7520' AND item_id=?", ("monitor:" + row["catalog_id"],)).fetchone()
    assert imported["category_id"] == "unclassified"
    assert imported["category_reason"] == "source_category_conflict"
    assert evidence["raw_category"] == row["raw_category"]
    assert json.loads(evidence["raw_record"])["Catprod"]["Prodcateg"]["Name"] == row["raw_category"]


@pytest.mark.parametrize("row", SEMANTIC["ambiguous_price_basis"], ids=["coffee_K", "water_L", "water_Litru", "coffee_Kg"])
def test_title_pack_quantity_does_not_confirm_raw_price_basis(row):
    decision = assess_quote(row["catalog_name"], row["commercial_name"], row["raw_category"], row["raw_unit"])
    assert any("Baza prețului" in reason for reason in decision["unknowns"])
    assert any("Unitatea brută" in reason for reason in decision["unknowns"])
    assert decision["relation"] != "IDENTICAL_PACK"


def test_lidl_duplicates_keep_all_rows_and_different_prices(seeded_settings):
    with connect(seeded_settings) as conn:
        imported = list(conn.execute("SELECT id,name,raw_pack,raw_price FROM source_product WHERE source_id='lidl'"))
        snapshot = conn.execute("SELECT retrieved_at,source_priced_at FROM snapshot WHERE source_id='lidl'").fetchone()
        assert conn.execute("SELECT COUNT(DISTINCT raw_category) FROM source_product WHERE source_id='lidl'").fetchone()[0] == 34
    keys = Counter((row["name"], row["raw_pack"]) for row in imported)
    assert sum(count - 1 for count in keys.values()) == 8
    assert tuple(snapshot) == (None, None)
    by_id = {row["id"]: row for row in imported}
    for group in SEMANTIC["lidl_exact_duplicate_groups"]:
        assert len(group["rows"]) == 2
        for original in group["rows"]:
            row = by_id[f"lidl:{original['excel_row']}"]
            assert row["name"] == original["raw_values"][0]
            assert row["raw_pack"] == original["raw_values"][1]
            assert Decimal(row["raw_price"]) == Decimal(str(original["raw_values"][3]))
    assert by_id["lidl:183"]["name"] != by_id["lidl:413"]["name"]
    assert by_id["lidl:183"]["name"].casefold() == by_id["lidl:413"]["name"].casefold()


def test_all_explicit_lidl_categories_are_mapped_provisionally_and_otc_stays_for_review(seeded_settings):
    taxonomy = json.loads((ROOT / "config/taxonomy.json").read_text(encoding="utf-8"))
    mappings = taxonomy["source_category_mappings"]["lidl"]
    with connect(seeded_settings) as conn:
        imported_groups = list(conn.execute("SELECT raw_category,category_id,COUNT(*) AS count FROM source_product WHERE source_id='lidl' GROUP BY raw_category,category_id"))
    assert len(imported_groups) == 34
    assert sum(row["count"] for row in imported_groups) == 2444
    for row in imported_groups:
        assert row["category_id"] == mappings[row["raw_category"]]["category_id"], row["raw_category"]
    assert next(row["category_id"] for row in imported_groups if row["raw_category"] == "OTC") == "unclassified"


def _real_probe_list(conn, list_id, product_ids, quantities=None):
    """Cereri de test explicite către date reale, fără prețuri sau identități fabricate."""
    conn.execute("INSERT INTO shopping_list VALUES(?,?,?,?,?,?,?)", (list_id, "local-company", "Regresie probe", "slatina_5km", 1, "2026-10-05T00:00:00+00:00", "2026-10-05T00:00:00+00:00"))
    for number, product_id in enumerate(product_ids):
        quantity = exact_quantity((quantities or ["1"] * len(product_ids))[number])
        source_product = conn.execute("SELECT id,name,category_id FROM source_product WHERE id=?", (product_id,)).fetchone()
        conn.execute("INSERT INTO list_line VALUES(?,?,?,?,?,?,?,?,?)", (f"{list_id}-line-{number}", "local-company", list_id, source_product["id"], source_product["name"], quantity, "pack", source_product["category_id"], "2026-10-05T00:00:00+00:00"))


def test_real_three_id_sums_are_reported_quotes_and_never_payable_or_savings(seeded_settings):
    with connect(seeded_settings) as conn:
        _real_probe_list(conn, "regression-three", ["monitor:1012187", "monitor:1013048", "monitor:1361463"])
        result = compare_list(conn, "regression-three", 1, "slatina_5km")
        conn.commit()
    assert result["payable_total"] is None
    assert result["savings"] is None
    assert result["data_mode"] == "offline_snapshot"
    sums = {row["store"]["id"]: row for row in result["source_quote_sums"]}
    assert sums["7520"]["reported_quote_sum"] == {"amount": "33.86", "currency": "RON"}
    assert sums["1418"]["reported_quote_sum"] == {"amount": "41.07", "currency": "RON"}
    assert len(sums) == 18
    assert sum(row["quote_coverage_count"] == 3 for row in sums.values()) == 15
    assert all(row["semantic_coverage_count"] == 0 for row in sums.values())
    assert all(row["quantity_coverage_count"] == 0 for row in sums.values())
    assert any(row["missing_lines"] for row in sums.values())
    assert any(quote["conflicts"] for row in sums.values() for quote in row["quotes"])


def test_non_unit_quantity_does_not_multiply_uncertain_quotes_into_false_total(seeded_settings):
    with connect(seeded_settings) as conn:
        _real_probe_list(conn, "regression-quantity", ["monitor:1012187", "monitor:1013048", "monitor:1361463"], ["2", "1", "0.5"])
        result = compare_list(conn, "regression-quantity", 1, "slatina_5km")
        conn.commit()
    assert result["payable_total"] is None
    assert result["savings"] is None
    assert all(row["reported_quote_sum"] is None for row in result["source_quote_sums"])
    supeco = next(row for row in result["source_quote_sums"] if row["store"]["id"] == "7520")
    assert supeco["unadjusted_quote_sum"]["amount"] == "33.86"
    assert any("nu sunt înmulțite" in reason for reason in supeco["reasons"])


def test_missing_basket_item_stays_missing_in_every_store_and_no_unsupported_zone_fallback(seeded_settings):
    with connect(seeded_settings) as conn:
        _real_probe_list(conn, "regression-missing", ["monitor:1012187", "monitor:1013048", "monitor:1361463", "monitor:1011559"])
        result = compare_list(conn, "regression-missing", 1, "slatina_5km")
        assert all(row["quote_coverage_count"] < 4 for row in result["source_quote_sums"])
        assert all(any(line["line_id"] == "regression-missing-line-3" for line in row["missing_lines"]) for row in result["source_quote_sums"])
        assert result["payable_total"] is None
        assert result["savings"] is None
        count = conn.execute("SELECT COUNT(*) FROM comparison").fetchone()[0]
        with pytest.raises(AppError) as rejected:
            compare_list(conn, "regression-missing", 1, "unprobed-city")
        assert rejected.value.code == "SCENARIO_UNAVAILABLE"
        assert conn.execute("SELECT COUNT(*) FROM comparison").fetchone()[0] == count
        conn.commit()


def test_offer_evidence_preserves_source_ids_date_and_conflict_without_confirming_identity(seeded_settings):
    with connect(seeded_settings) as conn:
        offers = get_offers(conn, "monitor:1013048", "bucharest_1km")
        intense = next(row for row in offers["quotes"] if row["store"]["id"] == "1988")
        evidence = get_evidence(conn, intense["observation_id"])
    assert intense["relation"] == "INCOMPATIBLE"
    assert evidence["source_catalog_id"] == "1013048"
    assert evidence["source_product_id"] == "10692315574"
    assert evidence["source_priced_at"] == "05.10.2026 04:00"
    assert evidence["retrieved_at"] == "2026-10-05T14:31:04.5721154+00:00"
    assert evidence["raw_record"]["Name"] == "JACOBS KRONUNG INTENSE 250G"
    assert evidence["snapshot"]["sha256"] == next(row["sha256"] for row in MANIFEST["files"] if row["path"] == "probe-data/bucharest-representative.xml")
    assert offers["item"]["record_kind"] == "source_only"
    assert offers["item"]["identity_status"] == "unverified"


def test_taxonomy_has_declared_future_domains_without_enabling_equivalence():
    taxonomy = json.loads((ROOT / "config/taxonomy.json").read_text(encoding="utf-8"))
    by_id = {row["id"]: row for row in taxonomy["categories"]}
    assert {"food", "drinks", "cleaning", "hygiene", "office", "printing", "electronics", "appliances", "furniture", "materials", "other", "unclassified"} <= by_id.keys()
    assert all(row["automatic_equivalence_enabled"] is False for row in by_id.values())
    for category in by_id.values():
        visited = {category["id"]}
        parent = category["parent_id"]
        while parent is not None:
            assert parent in by_id
            assert parent not in visited
            visited.add(parent)
            parent = by_id[parent]["parent_id"]
    raw_lidl = json.loads((ROOT / "probe-data/lidl-parsed-2026-10-05.json").read_text(encoding="utf-8"))
    labels = {row["values"][2] for row in raw_lidl["sheets"][0]["rows"] if row["excel_row"] > 1 and row["values"][0]}
    mappings = taxonomy["source_category_mappings"]["lidl"]
    assert set(mappings) == labels
    assert mappings["OTC"]["category_id"] == "unclassified"
    assert mappings["OTC"]["status"] == "requires_review"
    assert all(mapping["category_id"] in by_id for mapping in mappings.values())


def test_decimal_money_and_non_unit_quantity_are_not_float():
    assert money(Decimal("0.10") + Decimal("0.20")) == {"amount": "0.30", "currency": "RON"}
    assert money("33,86") == {"amount": "33.86", "currency": "RON"}
    assert exact_quantity("2,500000") == "2.5"
    assert exact_quantity("0.25") == "0.25"
    with pytest.raises(ValueError):
        exact_quantity("0")
    with pytest.raises(ValueError):
        exact_quantity("1,234.56")


@pytest.fixture
def api_client(seeded_settings):
    from app.main import create_app
    with TestClient(create_app(seeded_settings)) as client:
        yield client


def _local_headers(client):
    response = client.get("/api/v1/bootstrap")
    assert response.status_code == 200
    return {"Origin": "http://testserver", "X-CSRF-Token": response.json()["csrf_token"]}


def test_api_declares_actual_offline_capabilities_and_rejects_unprobed_geography(api_client):
    bootstrap = api_client.get("/api/v1/bootstrap")
    assert bootstrap.status_code == 200
    data = bootstrap.json()
    assert data["capabilities"]["mode"] == "offline_snapshot"
    assert data["capabilities"]["network_mode"] == "offline"
    assert data["capabilities"]["catalog_count"] == 107238
    assert all(value is False for value in data["capabilities"]["features"].values())
    assert {(row["id"], row["radius_m"], row["store_count"]) for row in data["scenarios"]} == {("slatina_5km", 5000, 18), ("bucharest_1km", 1000, 19)}
    future_categories = {row["id"]: row for row in data["categories"] if row["id"] in {"electronics", "printing", "office", "appliances", "furniture", "materials"}}
    assert len(future_categories) == 6
    assert all(row["quote_count"] == 0 for row in future_categories.values())
    rejected = api_client.get("/api/v1/catalog", params={"q": "lapte", "scenario": "unprobed-city"})
    assert rejected.status_code == 422
    assert rejected.json()["code"] == "SCENARIO_UNAVAILABLE"
    assert "items" not in rejected.json()


def test_api_mutations_require_local_origin_and_csrf_without_creating_a_list(api_client):
    headers = _local_headers(api_client)
    before = api_client.get("/api/v1/lists").json()
    payload = {"name": "Cerere externă respinsă", "scenario_id": "slatina_5km"}
    assert api_client.post("/api/v1/lists", json=payload).status_code == 403
    assert api_client.post("/api/v1/lists", json=payload, headers={"Origin": "http://testserver"}).status_code == 403
    assert api_client.post("/api/v1/lists", json=payload, headers={**headers, "Origin": "https://example.invalid"}).status_code == 403
    assert api_client.get("/api/v1/lists").json() == before


def test_api_quantity_validation_revision_conflict_and_restart_preserve_real_list(api_client, seeded_settings):
    from app.main import create_app
    headers = _local_headers(api_client)
    created = api_client.post("/api/v1/lists", json={"name": "Regresie API și persistență", "scenario_id": "slatina_5km"}, headers=headers)
    assert created.status_code == 201
    shopping = created.json()
    path = f"/api/v1/lists/{shopping['id']}"
    invalid = api_client.post(path + "/lines", json={"expected_revision": 1, "source_product_id": "monitor:1012187", "quantity": 2.5}, headers=headers)
    assert invalid.status_code == 422
    assert api_client.get(path).json() == shopping
    valid = api_client.post(path + "/lines", json={"expected_revision": 1, "source_product_id": "monitor:1012187", "quantity": "2,500000"}, headers=headers)
    assert valid.status_code == 201
    shopping = valid.json()
    assert shopping["lines"][0]["quantity"] == "2.5"
    stale = api_client.post(path + "/lines", json={"expected_revision": 1, "source_product_id": "monitor:1013048", "quantity": "1"}, headers=headers)
    assert stale.status_code == 409
    assert stale.json()["code"] == "REVISION_CONFLICT"
    assert api_client.get(path).json() == shopping
    comparison = api_client.post("/api/v1/comparisons", json={"list_id": shopping["id"], "expected_revision": shopping["revision"], "scenario_id": "slatina_5km"}, headers=headers)
    assert comparison.status_code == 201
    result = comparison.json()
    assert result["payable_total"] is None
    assert result["savings"] is None
    assert all(row["reported_quote_sum"] is None for row in result["source_quote_sums"])
    with TestClient(create_app(seeded_settings)) as restarted:
        assert restarted.get(path).status_code == 403
        _local_headers(restarted)
        assert restarted.get(path).json() == shopping
        saved_comparison = restarted.get(f"/api/v1/comparisons/{result['id']}")
        assert saved_comparison.status_code == 200
        assert saved_comparison.json()["is_stale_revision"] is False
        assert saved_comparison.json()["payable_total"] is None
