import base64
from datetime import datetime, timezone
from decimal import Decimal
import json
import re
import uuid
from .domain import assess_quote, money, normalize_text
from .ingest import COMPANY_ID, dumps
from .smart import (product_profile, match_profiles, price_basis, quote_order, price_range,
                    line_analysis, pack_key)


class AppError(Exception):
    def __init__(self, code, message, status=400, fields=None):
        self.code, self.message, self.status, self.fields = code, message, status, fields or {}


def now():
    return datetime.now(timezone.utc).isoformat()


def require_scenario(conn, scenario_id):
    row = conn.execute("SELECT * FROM scenario WHERE id=?", (scenario_id,)).fetchone()
    if row is None:
        raise AppError("SCENARIO_UNAVAILABLE", "Nu există date salvate pentru această zonă. Alege Slatina 5 km sau București 1 km.", 422)
    return dict(row)


def scenario_view(conn, row):
    return {k: row[k] for k in ("id", "name", "latitude", "longitude", "radius_m")} | {
        "store_count": conn.execute("SELECT COUNT(*) FROM store WHERE scenario_id=?", (row["id"],)).fetchone()[0]}


def get_scenarios(conn):
    return [scenario_view(conn, row) for row in conn.execute("SELECT * FROM scenario ORDER BY rowid")]


def descendants(conn, category_id):
    if not conn.execute("SELECT 1 FROM category WHERE id=?", (category_id,)).fetchone():
        raise AppError("CATEGORY_UNKNOWN", "Categoria nu există.", 422)
    return [r[0] for r in conn.execute("WITH RECURSIVE tree(id) AS (SELECT id FROM category WHERE id=? UNION ALL SELECT c.id FROM category c JOIN tree t ON c.parent_id=t.id) SELECT id FROM tree", (category_id,))]


def get_categories(conn):
    product_counts = {r[0]: r[1] for r in conn.execute("SELECT category_id,COUNT(*) FROM source_product WHERE name<>'' GROUP BY category_id")}
    quote_counts = {r[0]: r[1] for r in conn.execute("SELECT p.category_id,COUNT(*) FROM source_product p JOIN observation o ON o.item_id=p.id WHERE o.valid=1 GROUP BY p.category_id")}
    results = []
    for row in conn.execute("SELECT * FROM category ORDER BY rowid"):
        child_ids = descendants(conn, row["id"])
        results.append({"id": row["id"], "name": row["name"], "parent_id": row["parent_id"],
                        "product_count": sum(product_counts.get(cid, 0) for cid in child_ids),
                        "quote_count": sum(quote_counts.get(cid, 0) for cid in child_ids)})
    return results


def snapshot_view(row):
    result = dict(row)
    result.update(json.loads(result.pop("metadata")))
    return result


def capabilities(conn):
    sources = []
    for source_id, label in (("monitor", "Monitorul Prețurilor"), ("lidl", "Lidl · lista salvată")):
        sources.append({"id": source_id, "name": label,
                        "product_count": conn.execute("SELECT COUNT(*) FROM source_product WHERE source_id=?", (source_id,)).fetchone()[0],
                        "quote_count": conn.execute("SELECT COUNT(*) FROM observation o JOIN source_product p ON p.id=o.item_id WHERE p.source_id=? AND valid=1", (source_id,)).fetchone()[0]})
    return {"mode": "offline_snapshot", "network_mode": "offline",
            "features": {"ocr": False, "invoices": False, "savings": False, "supplier_recommendations": False},
            "catalog_count": sum(s["product_count"] for s in sources), "sources": sources,
            "limitations": ["Date salvate, fără actualizare live sau stoc verificat.",
                            "Comparăm cotațiile raportate, fără identitate exactă ori cost final confirmat.",
                            "Acoperire locală: scenariile probate Slatina 5 km și București 1 km.",
                            "OCR, facturile și economiile realizate sunt planificate pentru etape ulterioare."],
            "search_mode": conn.execute("SELECT value FROM app_meta WHERE key='search_mode'").fetchone()[0]}


def product_view(conn, row, scenario_id=None):
    values = dict(row)
    count_sql = "SELECT * FROM observation WHERE item_id=? AND valid=1"
    params = [row["id"]]
    if scenario_id:
        count_sql += " AND (scenario_id=? OR scenario_id IS NULL)"
        params.append(scenario_id)
    quotes = [quote_view(conn, observation) for observation in conn.execute(count_sql, params)]
    summary = price_range(quotes)
    summary.update({"offer_count": len(quotes), "candidate_count": sum(q["verdict"] == "same_variant_candidate" for q in quotes),
                    "conflict_count": sum(q["verdict"] == "variant_conflict" for q in quotes),
                    "needs_details_count": sum(q["verdict"] == "needs_details" for q in quotes),
                    "scope": "selected_area" if scenario_id else "all_saved_areas", "label": "Prețuri raportate"})
    return {k: values[k] for k in ("id", "source_id", "source_product_id", "name", "raw_category", "category_id", "category_reason", "raw_pack")} | {
        "record_kind": "source_only", "identity_status": "unverified",
        "quote_count": len(quotes), "price_summary": summary,
        "profile": product_profile(row["name"], row["raw_pack"], raw_category=row["raw_category"]),
        "price": money(row["raw_price"]) if row["raw_price"] else None,
        "snapshot_id": row["snapshot_id"], "locator": row["locator"]}


def get_product(conn, item_id, scenario_id=None):
    row = conn.execute("SELECT * FROM source_product WHERE id=?", (item_id,)).fetchone()
    if row is None:
        raise AppError("PRODUCT_NOT_FOUND", "Produsul nu există în catalogul salvat.", 404)
    return product_view(conn, row, scenario_id)


def search_catalog(conn, q="", category=None, source=None, scenario_id=None, cursor=None, limit=50,
                   priced_only=False, availability="all", sort="recommended"):
    if scenario_id:
        require_scenario(conn, scenario_id)
    if source and source not in {"monitor", "lidl"}:
        raise AppError("SOURCE_UNKNOWN", "Sursa nu este disponibilă.", 422)
    if availability not in {"all", "priced"} or sort not in {"recommended", "price", "name"}:
        raise AppError("FILTER_INVALID", "Filtrul de disponibilitate sau ordonarea nu este validă.", 422)
    priced_only = priced_only or availability == "priced"
    where, params, joins = ["p.name<>''"], [], ""
    normalized = normalize_text(q)
    if normalized:
        search_mode = conn.execute("SELECT value FROM app_meta WHERE key='search_mode'").fetchone()[0]
        if search_mode == "fts5":
            joins = " JOIN product_fts ON product_fts.id=p.id"
            where.append("product_fts MATCH ?")
            params.append(" AND ".join('"' + word + '"*' for word in normalized.split()))
        else:
            where.append("p.search_text >= ? AND p.search_text < ?")
            params.extend([normalized, normalized + "\uffff"])
    if category:
        ids = descendants(conn, category)
        where.append("p.category_id IN (" + ",".join("?" for _ in ids) + ")")
        params.extend(ids)
    if source:
        where.append("p.source_id=?")
        params.append(source)
    offer_scope = " AND (o.scenario_id=? OR o.scenario_id IS NULL)" if scenario_id else ""
    exists_sql = "EXISTS (SELECT 1 FROM observation o WHERE o.item_id=p.id AND o.valid=1" + offer_scope + ")"
    if priced_only:
        where.append(exists_sql)
        if scenario_id:
            params.append(scenario_id)
    offset = 0
    if cursor:
        try:
            payload = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
            if payload["context"] != [normalized, category, source, scenario_id, priced_only, sort] or not isinstance(payload["offset"], int):
                raise ValueError()
            offset = payload["offset"]
            if offset < 0 or offset > 200000:
                raise ValueError()
        except Exception:
            raise AppError("CURSOR_INVALID", "Cursorul nu corespunde acestei căutări.", 422)
    query = " FROM source_product p" + joins + " WHERE " + " AND ".join(where)
    total = conn.execute("SELECT COUNT(*)" + query, params).fetchone()[0]
    order_params = []
    if sort == "price":
        order = "CASE WHEN " + exists_sql + " THEN 0 ELSE 1 END,(SELECT MIN(CAST(o.price AS REAL)) FROM observation o WHERE o.item_id=p.id AND o.valid=1" + offer_scope + "),p.search_text,p.id"
        if scenario_id:
            order_params = [scenario_id, scenario_id]
    elif sort == "name":
        order = "p.search_text,p.id"
    else:
        order = "CASE WHEN " + exists_sql + " THEN 0 ELSE 1 END,p.editorial_rank,p.search_text,p.id"
        if scenario_id:
            order_params = [scenario_id]
    rows = conn.execute("SELECT p.*" + query + " ORDER BY " + order + " LIMIT ? OFFSET ?", [*params, *order_params, limit, offset]).fetchall()
    next_cursor = None
    if offset + limit < total:
        payload = {"offset": offset + limit, "context": [normalized, category, source, scenario_id, priced_only, sort]}
        next_cursor = base64.urlsafe_b64encode(dumps(payload).encode()).decode().rstrip("=")
    return {"items": [product_view(conn, row, scenario_id) for row in rows], "next_cursor": next_cursor, "total": total}


def company_view(conn):
    return dict(conn.execute("SELECT * FROM company WHERE id=?", (COMPANY_ID,)).fetchone())


def get_list(conn, list_id):
    row = conn.execute("SELECT * FROM shopping_list WHERE company_id=? AND id=?", (COMPANY_ID, list_id)).fetchone()
    if row is None:
        raise AppError("LIST_NOT_FOUND", "Lista nu există în firma locală.", 404)
    result = {k: row[k] for k in ("id", "name", "scenario_id", "revision")}
    result["lines"] = [{k: line[k] for k in ("id", "source_product_id", "source_product_name", "description", "quantity", "unit", "category_id")}
                       for line in conn.execute("SELECT l.*,p.name AS source_product_name FROM list_line l LEFT JOIN source_product p ON p.id=l.source_product_id WHERE l.company_id=? AND l.list_id=? ORDER BY l.created_at,l.id", (COMPANY_ID, list_id))]
    for line in result["lines"]:
        line["price_summary"] = get_product(conn, line["source_product_id"], result["scenario_id"])["price_summary"] if line["source_product_id"] else None
    return result


def check_revision(conn, list_id, expected_revision):
    result = get_list(conn, list_id)
    if result["revision"] != expected_revision:
        raise AppError("REVISION_CONFLICT", "Lista s-a schimbat. Reîncarcă lista înainte de a continua.", 409)
    return result


def bump_revision(conn, list_id):
    conn.execute("UPDATE shopping_list SET revision=revision+1,updated_at=? WHERE company_id=? AND id=?", (now(), COMPANY_ID, list_id))


def quote_view(conn, row, line_id=None, reference=None, source_context=None, reference_item_id=None):
    product = conn.execute("SELECT * FROM source_product WHERE id=?", (row["item_id"],)).fetchone()
    raw_record = json.loads(row["raw_record"])
    # La Monitor denumirea Catprod din răspunsul de magazin poate diferi de
    # catalog.xml; ambele rămân păstrate și niciuna nu se suprascrie.
    quoted_catalog_name = raw_record.get("Catprod", {}).get("Name") or product["name"]
    assessed = assess_quote(quoted_catalog_name, row["commercial_name"], row["raw_category"], row["raw_unit"])
    if not row["valid"]:
        if not assessed["conflicts"]:
            assessed["relation"] = "UNRESOLVED"
        assessed["unknowns"].append("Nu există o cotație pozitivă și datată valid în această înregistrare Monitor.")
    snapshot = conn.execute("SELECT retrieved_at FROM snapshot WHERE id=?", (row["snapshot_id"],)).fetchone()
    store = None
    if row["store_id"]:
        store_row = conn.execute("SELECT id,name,network_name,address FROM store WHERE scenario_id=? AND id=?", (row["scenario_id"], row["store_id"])).fetchone()
        store = dict(store_row) if store_row else None
    if row["scenario_id"] is None:
        assessed["unknowns"].extend(["Listă la nivel de rețea Lidl, fără stoc sau magazin individual confirmat.",
                                    "Valabilitatea individuală a prețului nu este precizată."])
    source_id = "monitor" if row["item_id"].startswith("monitor:") else "lidl"
    reference_profile = reference or product_profile(product["name"], product["raw_pack"], raw_category=product["raw_category"])
    offered_profile = product_profile(row["commercial_name"], row["raw_unit"], row["raw_brand"], row["raw_category"])
    assessed_match = match_profiles(reference_profile, offered_profile,
                                   source_context or product_profile(quoted_catalog_name, raw_category=row["raw_category"]))
    all_conflicts = list(dict.fromkeys([*assessed["conflicts"], *assessed_match["attribute_conflicts"]]))
    if all_conflicts:
        assessed_match.update(verdict="variant_conflict", verdict_label="Variantă diferită")
        assessed_match["match_reasons"] = list(dict.fromkeys(all_conflicts + assessed_match["match_reasons"]))
    if not row["valid"] and not all_conflicts:
        assessed_match.update(verdict="needs_details", verdict_label="Fără preț disponibil")
        assessed_match["match_reasons"] = ["Înregistrarea salvată nu conține un preț pozitiv valid."]
    if "\ufffd" in row["commercial_name"]:
        assessed_match["match_reasons"].append("Denumirea sursei conține un caracter ilizibil.")
    basis = price_basis(row["raw_unit"], offered_profile, source_id)
    return {"observation_id": row["id"], "line_id": line_id, "source_id": source_id,
            "source_item_id": row["item_id"],
            "reference_item_id": reference_item_id or row["item_id"],
            "source_catalog_name": quoted_catalog_name,
            "commercial_name": row["commercial_name"], "raw_brand": row["raw_brand"],
            "raw_unit": row["raw_unit"], "raw_promo": row["raw_promo"], "price": money(row["price"]) if row["price"] else None,
            "source_priced_at": row["source_priced_at"], "retrieved_at": snapshot[0],
            "store": store, "data_mode": "offline_snapshot", **assessed, **assessed_match,
            "price_basis": basis, "price_label": "Preț raportat"}


def item_context(conn, item_id):
    product = conn.execute("SELECT * FROM source_product WHERE id=?", (item_id,)).fetchone()
    if product is None:
        raise AppError("PRODUCT_NOT_FOUND", "Produsul de referință nu există în catalogul salvat.", 404)
    reference = product_profile(product["name"], product["raw_pack"], raw_category=product["raw_category"])
    raw = conn.execute("SELECT raw_record FROM observation WHERE item_id=? ORDER BY valid DESC,id LIMIT 1", (item_id,)).fetchone()
    catalog_name = json.loads(raw[0]).get("Catprod", {}).get("Name", "") if raw else ""
    context = product_profile(catalog_name, raw_category=product["raw_category"]) if catalog_name else reference
    return reference, context


def related_quotes(conn, item_id, scenario_id, line_id=None, available_rows=None):
    reference, context = item_context(conn, item_id)
    if not all(reference.get(key) for key in ("kind", "brand", "pack")):
        return []
    rows = available_rows if available_rows is not None else conn.execute(
        "SELECT * FROM observation WHERE valid=1 AND (scenario_id=? OR scenario_id IS NULL)", (scenario_id,)).fetchall()
    results = []
    for row in rows:
        if row["item_id"] == item_id:
            continue
        profile = product_profile(row["commercial_name"], row["raw_unit"], row["raw_brand"], row["raw_category"])
        if profile["kind"] != reference["kind"] or profile["brand"] != reference["brand"] or pack_key(profile["pack"]) != pack_key(reference["pack"]):
            continue
        quote = quote_view(conn, row, line_id, reference, context, item_id)
        quote["association_reason"] = "Găsită în altă înregistrare după marcă, tip și ambalaj; motivele potrivirii sunt afișate separat."
        results.append(quote)
    return sorted(results, key=quote_order)


def get_offers(conn, item_id, scenario_id):
    require_scenario(conn, scenario_id)
    item = get_product(conn, item_id, scenario_id)
    rows = conn.execute("SELECT * FROM observation WHERE item_id=? AND (scenario_id=? OR scenario_id IS NULL) ORDER BY valid DESC,store_id,id", (item_id, scenario_id)).fetchall()
    quotes = sorted([quote_view(conn, row) for row in rows], key=quote_order)
    return {"item": item, "scenario": scenario_view(conn, require_scenario(conn, scenario_id)),
            "quotes": quotes, "price_summary": item["price_summary"],
            "related_offers": related_quotes(conn, item_id, scenario_id),
            "warnings": ["Prețuri din fișiere salvate. Verifică stocul, condițiile și prețul final înainte de cumpărare."]}


def get_evidence(conn, observation_id, reference_item_id=None):
    row = conn.execute("SELECT * FROM observation WHERE id=?", (observation_id,)).fetchone()
    if row is None:
        raise AppError("EVIDENCE_NOT_FOUND", "Dovada nu există.", 404)
    snap = conn.execute("SELECT * FROM snapshot WHERE id=?", (row["snapshot_id"],)).fetchone()
    reference, context = item_context(conn, reference_item_id) if reference_item_id else (None, None)
    return quote_view(conn, row, reference=reference, source_context=context, reference_item_id=reference_item_id) | {
                                    "evaluation_scope": "selected_product" if reference_item_id else "source_product",
                                    "snapshot": snapshot_view(snap), "source_catalog_id": row["item_id"].split(":", 1)[1],
                                    "source_product_id": row["source_product_id"], "raw_category": row["raw_category"],
                                    "raw_price": row["raw_price"], "locator": row["locator"], "raw_record": json.loads(row["raw_record"])}


def compare_list(conn, list_id, expected_revision, scenario_id):
    shopping = check_revision(conn, list_id, expected_revision)
    scenario = scenario_view(conn, require_scenario(conn, scenario_id))
    if not shopping["lines"]:
        raise AppError("LIST_EMPTY", "Adaugă cel puțin un articol în listă.", 422)
    stores = [dict(row) for row in conn.execute("SELECT id,name,network_name,address FROM store WHERE scenario_id=? ORDER BY network_name,name,id", (scenario_id,))]
    if any(line["source_product_id"] and line["source_product_id"].startswith("lidl:") for line in shopping["lines"]):
        stores.append({"id": "lidl_network", "name": "Lidl · listă la nivel de rețea", "network_name": "Lidl", "address": ""})
    items = shopping["lines"]
    rows_by_item = {}
    for line in items:
        if line["source_product_id"]:
            rows_by_item[line["source_product_id"]] = conn.execute("SELECT * FROM observation WHERE item_id=? AND (scenario_id=? OR scenario_id IS NULL)", (line["source_product_id"], scenario_id)).fetchall()
    quote_sums, snapshot_ids = [], set()
    for store in stores:
        quotes, missing, reasons, amounts = [], [], [], []
        quantity_is_one = True
        for line in items:
            quantity_is_one &= Decimal(line["quantity"]) == Decimal(1)
            observations = [r for r in rows_by_item.get(line["source_product_id"], [])
                            if r["valid"] and (r["store_id"] == store["id"] or (r["scenario_id"] is None and store["id"] == "lidl_network"))]
            if len(observations) != 1:
                reason = "Articol introdus liber: nu există asociere confirmată cu o sursă." if not line["source_product_id"] else "Nu există cotație validă pentru acest articol în această sursă."
                if len(observations) > 1:
                    reason = "Mai multe cotații pentru aceeași poziție; selecția necesită verificare."
                missing.append({"line_id": line["id"], "description": line["description"], "reason": reason})
                continue
            row = observations[0]
            quote = quote_view(conn, row, line["id"])
            quotes.append(quote)
            amounts.append(Decimal(row["price"]))
            snapshot_ids.add(row["snapshot_id"])
            reasons.extend(quote["conflicts"])
        raw_sum = money(sum(amounts, Decimal(0))) if amounts else None
        # Numai suma neajustată a cotelor, nu subtotal plătibil/costul cererii.
        reported_sum = raw_sum if quantity_is_one else None
        if not quantity_is_one:
            reasons.append("Cantitățile cerute diferă de o unitate; cotațiile nu sunt înmulțite fără o bază a prețului confirmată.")
        reasons.append("Identitatea, cantitatea ofertată și costul final rămân neconfirmate.")
        if store["id"] == "lidl_network":
            reasons.append("Listă de rețea distinctă de magazinele geografice; disponibilitatea locală nu este confirmată.")
        quote_sums.append({"store": store, "source_scope": "network_list" if store["id"] == "lidl_network" else "geographic_store",
                           "quote_coverage_count": len(quotes), "semantic_coverage_count": 0, "quantity_coverage_count": 0,
                           "total_line_count": len(items), "reported_quote_sum": reported_sum,
                           "unadjusted_quote_sum": raw_sum if not quantity_is_one else None,
                           "quotes": quotes, "missing_lines": missing, "reasons": list(dict.fromkeys(reasons))})
    available_rows = conn.execute("SELECT * FROM observation WHERE valid=1 AND (scenario_id=? OR scenario_id IS NULL)", (scenario_id,)).fetchall()
    analyses = []
    for line in items:
        item_id = line["source_product_id"]
        if item_id:
            reference, context = item_context(conn, item_id)
            options = [quote_view(conn, row, line["id"], reference, context)
                       for row in rows_by_item.get(item_id, []) if row["valid"]]
            options.extend(related_quotes(conn, item_id, scenario_id, line["id"], available_rows))
        else:
            reference = product_profile(line["description"])
            options = []
        analysis = line_analysis(line, options, reference)
        for quote in analysis["comparable_options"]:
            quote["estimated_item_total"] = money(Decimal(quote["price"]["amount"]) * Decimal(line["quantity"]))
        analyses.append(analysis)
    estimated, incomplete = [], []
    eligible_stores = {"lidl_network": {"id": "lidl_network", "name": "Lidl · lista de rețea", "network_name": "Lidl", "address": ""}}
    eligible_stores.update({store["id"]: store for store in stores})
    for store in eligible_stores.values():
        picked = []
        missing_ids = []
        for analysis in analyses:
            choices = [quote for quote in analysis["comparable_options"]
                       if (quote.get("store") or {}).get("id", "lidl_network") == store["id"]]
            if choices:
                picked.append(min(choices, key=quote_order))
            else:
                missing_ids.append(analysis["line_id"])
        value = {"store": store, "eligible_line_count": len(picked), "total_line_count": len(items),
                 "quotes": picked, "missing_line_ids": missing_ids,
                 "assumptions": ["Estimare pentru ambalajele cerute, pe caracteristicile declarate.",
                                 "Stocul, transportul, condițiile comerciale și costul final nu sunt verificate.",
                                 "Diferența între estimări nu reprezintă economii realizate."]}
        if not missing_ids:
            value["estimated_total"] = money(sum((Decimal(quote["estimated_item_total"]["amount"]) for quote in picked), Decimal(0)))
            estimated.append(value)
        elif picked:
            value["estimated_total"] = None
            incomplete.append(value)
    estimated.sort(key=lambda basket: (Decimal(basket["estimated_total"]["amount"]), basket["store"]["id"]))
    for basket in estimated:
        basket["difference_from_best"] = money(Decimal(basket["estimated_total"]["amount"]) - Decimal(estimated[0]["estimated_total"]["amount"]))
    estimate_range = {"minimum": estimated[0]["estimated_total"] if estimated else None,
                      "maximum": estimated[-1]["estimated_total"] if estimated else None,
                      "spread": money(Decimal(estimated[-1]["estimated_total"]["amount"]) - Decimal(estimated[0]["estimated_total"]["amount"])) if len(estimated) > 1 else None}
    result = {"id": "comparison_" + uuid.uuid4().hex, "data_mode": "offline_snapshot", "network_mode": "offline",
              "list_id": list_id, "list_revision": expected_revision, "scenario": scenario,
              "source_snapshot_ids": sorted(snapshot_ids | {row["snapshot_id"] for row in available_rows if any(quote["observation_id"] == row["id"] for analysis in analyses for quote in analysis["options"])}), "algorithm_version": "attributes-explainable-2",
              "currency": "RON", "source_quote_sums": quote_sums,
              "line_comparisons": analyses, "estimated_baskets": estimated, "incomplete_estimates": incomplete,
              "estimated_range": estimate_range, "estimated_savings": None,
              "payable_total": None, "savings": None, "rank_basis": "reported_quotes_only",
              "warnings": ["Sumele cotelor pot include variante diferite și poziții lipsă; nu sunt totaluri de plată.",
                           "Prețurile sunt probe salvate, fără stoc, TVA, SGR, transport și eligibilitate confirmate.",
                           "Estimările se ordonează numai pentru coșuri complete cu aceleași cerințe. Diferențele nu sunt economii realizate."],
              "as_of": "05.10.2026 04:00 · dată raportată de Monitor; Lidl are valabilitate individuală necunoscută",
              "created_at": now()}
    conn.execute("INSERT INTO comparison VALUES(?,?,?,?,?,?)", (result["id"], COMPANY_ID, list_id, expected_revision, dumps(result), result["created_at"]))
    return result
