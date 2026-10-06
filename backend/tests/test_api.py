from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.db import connect
from app.main import create_app
from app.settings import Settings


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def settings(tmp_path_factory):
    return Settings(ROOT, tmp_path_factory.mktemp("api-db") / "app.sqlite3", testing=True)


@pytest.fixture()
def client(settings):
    with TestClient(create_app(settings)) as current:
        yield current


def bootstrap(client):
    result = client.get("/api/v1/bootstrap")
    assert result.status_code == 200
    return result.json(), {"Origin": "http://testserver", "X-CSRF-Token": result.json()["csrf_token"]}


def build_list(client, headers, names=None):
    response = client.post("/api/v1/lists", json={"name": "Lista API", "scenario_id": "slatina_5km"}, headers=headers)
    assert response.status_code == 201
    shopping = response.json()
    for item_id in names or ["monitor:1012187", "monitor:1013048", "monitor:1361463"]:
        response = client.post(f"/api/v1/lists/{shopping['id']}/lines", json={"expected_revision": shopping["revision"], "source_product_id": item_id, "quantity": "1", "unit": "item"}, headers=headers)
        assert response.status_code == 201
        shopping = response.json()
    return shopping


def test_first_bootstrap_declares_snapshot_features_and_source_dates(client):
    data, _ = bootstrap(client)
    assert data["capabilities"]["mode"] == "offline_snapshot"
    assert data["capabilities"]["network_mode"] == "offline"
    assert data["capabilities"]["catalog_count"] == 107238
    assert not any(data["capabilities"]["features"].values())
    assert {s["id"]: s["store_count"] for s in data["scenarios"]} == {"slatina_5km": 18, "bucharest_1km": 19}
    cookie = client.cookies.get("local_session")
    assert cookie and "httponly" in client.get("/api/v1/bootstrap").headers["set-cookie"].casefold()
    monitor = next(s for s in data["snapshots"] if s["query_scope"] == "slatina_5km")
    assert monitor["retrieved_at"] == "2026-10-05T14:31:03.9187173+00:00"
    assert monitor["source_priced_at"] == "05.10.2026 04:00"


def test_complete_api_list_comparison_evidence_flow_and_reload(client):
    _, headers = bootstrap(client)
    shopping = build_list(client, headers)
    response = client.post("/api/v1/comparisons", json={"list_id": shopping["id"], "expected_revision": shopping["revision"], "scenario_id": "slatina_5km"}, headers=headers)
    assert response.status_code == 201
    result = response.json()
    supeco = next(s for s in result["source_quote_sums"] if s["store"]["id"] == "7520")
    assert supeco["reported_quote_sum"]["amount"] == "33.86"
    assert supeco["quote_coverage_count"] == 3
    assert supeco["semantic_coverage_count"] == 0
    assert result["payable_total"] is None and result["savings"] is None
    evidence = client.get(f"/api/v1/evidence/{supeco['quotes'][0]['observation_id']}").json()
    assert evidence["snapshot"]["sha256"]
    assert evidence["locator"].startswith("/RetailStores/")
    assert client.get(f"/api/v1/lists/{shopping['id']}").json() == shopping
    data, _ = bootstrap(client)
    assert data["current_list"]["id"] == shopping["id"]


def test_revision_conflict_does_not_drop_or_replace_the_users_list(client):
    _, headers = bootstrap(client)
    shopping = build_list(client, headers, ["monitor:1012187"])
    response = client.patch(f"/api/v1/lists/{shopping['id']}", json={"expected_revision": 1, "name": "Stale overwrite"}, headers=headers)
    assert response.status_code == 409
    assert response.json()["code"] == "REVISION_CONFLICT"
    assert client.get(f"/api/v1/lists/{shopping['id']}").json() == shopping


def test_search_paginates_and_never_promotes_source_records(client):
    data = client.get("/api/v1/catalog", params={"q": "cafea", "limit": 3}).json()
    assert data["total"] > 3 and len(data["items"]) == 3
    assert all(item["record_kind"] == "source_only" and item["identity_status"] == "unverified" for item in data["items"])
    next_page = client.get("/api/v1/catalog", params={"q": "cafea", "limit": 3, "cursor": data["next_cursor"]}).json()
    assert not {item["id"] for item in data["items"]} & {item["id"] for item in next_page["items"]}
    mismatch = client.get("/api/v1/catalog", params={"q": "lapte", "cursor": data["next_cursor"]})
    assert mismatch.status_code == 422
    injection = client.get("/api/v1/catalog", params={"q": "' OR 1=1 --"})
    assert injection.status_code == 200
    assert client.get("/api/v1/catalog", params={"limit": 101}).status_code == 422


def test_unprobed_city_and_client_company_are_not_accepted(client):
    _, headers = bootstrap(client)
    wrong_zone = client.post("/api/v1/lists", json={"name": "Alt oraș", "scenario_id": "brasov"}, headers=headers)
    assert wrong_zone.status_code == 422
    assert wrong_zone.json()["code"] == "SCENARIO_UNAVAILABLE"
    wrong_company = client.post("/api/v1/lists", json={"name": "Altă firmă", "scenario_id": "slatina_5km", "company_id": "someone-else"}, headers=headers)
    assert wrong_company.status_code == 422


def test_csrf_origin_and_host_protect_mutations_without_side_effects(client):
    _, headers = bootstrap(client)
    before = client.get("/api/v1/lists").json()
    payload = {"name": "Must not be saved", "scenario_id": "slatina_5km"}
    no_csrf = client.post("/api/v1/lists", json=payload, headers={"Origin": "http://testserver"})
    assert no_csrf.status_code == 403
    foreign = client.post("/api/v1/lists", json=payload, headers={**headers, "Origin": "https://attacker.example"})
    assert foreign.status_code == 403
    host = client.get("/api/v1/bootstrap", headers={"Host": "attacker.example"})
    assert host.status_code == 403
    origin = client.get("/api/v1/bootstrap", headers={"Origin": "https://attacker.example"})
    assert origin.status_code == 403
    assert client.get("/api/v1/lists").json() == before


def test_private_lists_require_a_local_session(client):
    assert client.get("/api/v1/lists").status_code == 403
    bootstrap(client)
    assert client.get("/api/v1/lists").status_code == 200


def test_float_quantity_is_rejected_and_missing_source_product_is_preserved_as_free_text(client):
    _, headers = bootstrap(client)
    shopping = build_list(client, headers, ["monitor:1012187"])
    invalid = client.post(f"/api/v1/lists/{shopping['id']}/lines", json={"expected_revision": shopping["revision"], "description": "Laptop", "quantity": 1.5}, headers=headers)
    assert invalid.status_code == 422
    response = client.post(f"/api/v1/lists/{shopping['id']}/lines", json={"expected_revision": shopping["revision"], "description": "Laptop pentru birou", "quantity": "2", "category_id": "computers"}, headers=headers)
    assert response.status_code == 201
    shopping = response.json()
    result = client.post("/api/v1/comparisons", json={"list_id": shopping["id"], "expected_revision": shopping["revision"], "scenario_id": "slatina_5km"}, headers=headers).json()
    free_line_id = shopping["lines"][-1]["id"]
    assert all(row["reported_quote_sum"] is None and any(missing["line_id"] == free_line_id for missing in row["missing_lines"]) for row in result["source_quote_sums"])
    assert all(row["semantic_coverage_count"] == row["quantity_coverage_count"] == 0 for row in result["source_quote_sums"])


def test_line_delete_and_saved_comparison_revision_are_scoped(client):
    _, headers = bootstrap(client)
    first = build_list(client, headers, ["monitor:1012187"])
    second = build_list(client, headers, ["monitor:1361463"])
    result = client.post("/api/v1/comparisons", json={"list_id": first["id"], "expected_revision": first["revision"], "scenario_id": "slatina_5km"}, headers=headers).json()
    wrong_list = client.delete(f"/api/v1/lists/{second['id']}/lines/{first['lines'][0]['id']}", params={"expected_revision": second["revision"]}, headers=headers)
    assert wrong_list.status_code == 404
    updated = client.patch(f"/api/v1/lists/{first['id']}/lines/{first['lines'][0]['id']}", json={"expected_revision": first["revision"], "quantity": "2"}, headers=headers)
    assert updated.status_code == 200
    assert client.get(f"/api/v1/comparisons/{result['id']}").json()["is_stale_revision"] is True


def test_restart_preserves_lists_company_and_requires_new_session(settings):
    with TestClient(create_app(settings)) as first:
        data, headers = bootstrap(first)
        shopping = build_list(first, headers, ["monitor:1012187"])
        company = first.patch("/api/v1/company", json={"expected_revision": data["company"]["revision"], "name": "Firma de test"}, headers=headers).json()
    with TestClient(create_app(settings)) as second:
        assert second.get("/api/v1/lists").status_code == 403
        data, _ = bootstrap(second)
        assert data["company"] == company
        assert second.get(f"/api/v1/lists/{shopping['id']}").json() == shopping


def test_free_line_can_select_catalog_on_same_line_and_failed_selection_is_atomic(client):
    _, headers = bootstrap(client)
    shopping = client.post("/api/v1/lists", json={"name": "Asociere produs", "scenario_id": "slatina_5km"}, headers=headers).json()
    path = f"/api/v1/lists/{shopping['id']}"
    response = client.post(path + "/lines", json={"expected_revision": shopping["revision"], "description": "Lapte pentru birou", "quantity": "2"}, headers=headers)
    assert response.status_code == 201
    shopping = response.json()
    original_line = shopping["lines"][0]
    line_path = path + f"/lines/{original_line['id']}"
    invalid = client.patch(line_path, json={"expected_revision": shopping["revision"], "source_product_id": "monitor:does-not-exist"}, headers=headers)
    assert invalid.status_code == 404
    assert client.get(path).json() == shopping
    invalid_category = client.patch(line_path, json={"expected_revision": shopping["revision"], "source_product_id": "monitor:1012187", "category_id": "does-not-exist"}, headers=headers)
    assert invalid_category.status_code == 422
    assert client.get(path).json() == shopping
    selected = client.patch(line_path, json={"expected_revision": shopping["revision"], "source_product_id": "monitor:1012187"}, headers=headers)
    assert selected.status_code == 200
    updated = selected.json()
    assert len(updated["lines"]) == 1
    assert updated["lines"][0]["id"] == original_line["id"]
    assert updated["lines"][0]["quantity"] == "2"
    assert updated["lines"][0]["source_product_id"] == "monitor:1012187"
    assert updated["lines"][0]["category_id"] == "milk"
    assert updated["lines"][0]["description"] == client.get("/api/v1/catalog/monitor:1012187").json()["name"]
    assert updated["lines"][0]["source_product_name"] == updated["lines"][0]["description"]
    stale = client.patch(line_path, json={"expected_revision": shopping["revision"], "source_product_id": "monitor:1361463"}, headers=headers)
    assert stale.status_code == 409
    assert client.get(path).json() == updated
    preserved = client.patch(line_path, json={"expected_revision": updated["revision"], "source_product_id": "monitor:1012187", "description": original_line["description"]}, headers=headers)
    assert preserved.status_code == 200
    updated = preserved.json()
    assert updated["lines"][0]["description"] == "Lapte pentru birou"
    assert updated["lines"][0]["source_product_name"] == client.get("/api/v1/catalog/monitor:1012187").json()["name"]
    result = client.post("/api/v1/comparisons", json={"list_id": updated["id"], "expected_revision": updated["revision"], "scenario_id": "slatina_5km"}, headers=headers).json()
    assert result["payable_total"] is None and result["savings"] is None
    assert all(row["semantic_coverage_count"] == row["quantity_coverage_count"] == 0 for row in result["source_quote_sums"])
    assert all(row["reported_quote_sum"] is None for row in result["source_quote_sums"])
