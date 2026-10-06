"""Import offline, atomic și idempotent. Nu conține colectare de rețea."""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from defusedxml import ElementTree as ET
from .db import connect, migrate
from .domain import normalize_text, parse_price
from .settings import Settings


COMPANY_ID = "local-company"
SCENARIOS = (
    ("slatina_5km", "Slatina · raza 5 km", "44.4281", "24.3726", 5000, "slatina-representative.xml"),
    ("bucharest_1km", "București · raza 1 km", "44.4268", "26.1025", 1000, "bucharest-representative.xml"),
)
EDITORIAL = {"1012187": ("milk", 1), "1013048": ("coffee", 2), "1361463": ("water", 3),
             "1019036": ("coffee", 4), "1011559": ("water", 5),
             "1282436": ("unclassified", 6), "1449689": ("unclassified", 7)}


def dumps(value):
    return json.dumps(value, ensure_ascii=False, default=lambda v: str(v) if isinstance(v, Decimal) else None)


def text_at(node, path: str) -> str:
    for part in path.split("/"):
        node = next((child for child in node if child.tag.rsplit("}", 1)[-1] == part), None)
        if node is None:
            return ""
    return node.text or ""


def records(path: Path, tag: str):
    for _, node in ET.iterparse(path, events=("end",)):
        if node.tag.rsplit("}", 1)[-1] == tag:
            yield node
            node.clear()


def raw_node(node):
    if len(node):
        return {child.tag.rsplit("}", 1)[-1]: raw_node(child) for child in node}
    return node.text or ""


def valid_price_date(raw: str) -> bool:
    try:
        datetime.strptime(raw.strip(), "%d.%m.%Y %H:%M")
        return True
    except ValueError:
        return False


def make_snapshot(conn, settings, source, filename, scope, retrieved=None, notes=None):
    path = settings.root_dir / "probe-data" / filename
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    # Refuză schimbarea probei din spatele unei chei logice deja importate.
    old = conn.execute("SELECT id,sha256 FROM snapshot WHERE source_id=? AND filename=? AND query_scope=?",
                       (source, filename, scope)).fetchone()
    if old and old["sha256"] != digest:
        raise RuntimeError(f"Proba {filename} diferă de importul păstrat; nu este suprascrisă.")
    sid = f"{source}:{path.stem}:{digest[:12]}"
    existed = old is not None
    metadata = {"data_mode": "offline_snapshot", "notes": notes or [],
                "missing_fields": ["GTIN", "stock", "VAT", "price_basis", "shipping", "business_eligibility"],
                "bytes": path.stat().st_size}
    conn.execute("INSERT OR IGNORE INTO snapshot(id,source_id,filename,sha256,query_scope,retrieved_at,metadata) VALUES(?,?,?,?,?,?,?)",
                 (sid, source, filename, digest, scope, retrieved, dumps(metadata)))
    return sid, existed


def load_categories(conn, settings):
    path = settings.root_dir / "config" / "taxonomy.json"
    if not path.exists():
        raise RuntimeError("Lipsește config/taxonomy.json. Rulați setup-ul proiectului.")
    taxonomy = json.loads(path.read_text(encoding="utf-8-sig"))
    for category in taxonomy["categories"]:
        conn.execute("INSERT INTO category(id,name,parent_id,metadata) VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,parent_id=excluded.parent_id,metadata=excluded.metadata",
                     (category["id"], category.get("label", category.get("name", category["id"])),
                      category.get("parent_id"), dumps(category)))
    return taxonomy


def reclassify_lidl(conn, taxonomy, settings):
    """Date derivate versionate; nu schimbă proveniența sau listele private."""
    version = hashlib.sha256((settings.root_dir / "config" / "taxonomy.json").read_bytes()).hexdigest()
    existing = conn.execute("SELECT value FROM app_meta WHERE key='classification_version'").fetchone()
    if existing and existing[0] == version:
        return
    mappings = {normalize_text(label): rule for label, rule in taxonomy.get("source_category_mappings", {}).get("lidl", {}).items()}
    for row in conn.execute("SELECT DISTINCT raw_category FROM source_product WHERE source_id='lidl'").fetchall():
        rule = mappings.get(normalize_text(row[0]), {"category_id": "unclassified", "status": "unclassified"})
        conn.execute("UPDATE source_product SET category_id=?,category_reason=? WHERE source_id='lidl' AND raw_category=?",
                     (rule["category_id"], rule["status"], row[0]))
    conn.execute("INSERT OR REPLACE INTO app_meta VALUES('classification_version',?)", (version,))


def import_catalog(conn, settings, sid):
    batch, count = [], 0
    for node in records(settings.root_dir / "probe-data" / "catalog.xml", "CatalogProduct"):
        product_id, name = text_at(node, "Id").strip(), text_at(node, "Name").strip()
        if not product_id:
            raise RuntimeError("Catalogul conține un ID lipsă; importul este anulat.")
        category, rank = EDITORIAL.get(product_id, ("unclassified", 999))
        reason = "editorial_candidate" if product_id in EDITORIAL else "unclassified"
        if product_id in {"1282436", "1449689"}:
            reason = "source_category_conflict"
        count += 1
        batch.append((f"monitor:{product_id}", "monitor", product_id, name,
                      text_at(node, "Prodcateg/Name"), category, reason, "", None, sid,
                      f"/CatalogProducts/Items/CatalogProduct[{count}]", normalize_text(name), rank, dumps(raw_node(node))))
        if len(batch) == 1000:
            conn.executemany("INSERT INTO source_product VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
            batch.clear()
    if batch:
        conn.executemany("INSERT INTO source_product VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
    if count != 104794:
        raise RuntimeError(f"Catalogul așteptat are 104794 rânduri; proba conține {count}.")
    conn.execute("UPDATE snapshot SET row_count=? WHERE id=?", (count, sid))


def import_monitor(conn, settings, scenario, sid, networks):
    scenario_id, label, latitude, longitude, radius, filename = scenario
    conn.execute("INSERT INTO scenario VALUES(?,?,?,?,?,?)", (scenario_id, label, latitude, longitude, radius, sid))
    observations, valid, rows = [], 0, 0
    for store_number, node in enumerate(records(settings.root_dir / "probe-data" / filename, "RetailStore"), 1):
        store_id = text_at(node, "Id").strip()
        network_id = text_at(node, "Retailnetwork/Id").strip()
        conn.execute("INSERT INTO store VALUES(?,?,?,?,?,?)", (store_id, scenario_id, text_at(node, "Name").strip(),
                     network_id, networks.get(network_id, text_at(node, "Retailnetwork/Name").strip()), text_at(node, "Addr/Addrstring").strip()))
        products = next((child for child in node if child.tag.rsplit("}", 1)[-1] == "Products"), [])
        for product_number, product in enumerate(products, 1):
            catalog_id = text_at(product, "Catprod/Id").strip()
            if not conn.execute("SELECT 1 FROM source_product WHERE id=?", (f"monitor:{catalog_id}",)).fetchone():
                raise RuntimeError(f"Catalogue ID {catalog_id} absent; import annulé.")
            locator = f"/RetailStores/Items/RetailStore[{store_number}]/Products/Product[{product_number}]"
            oid = "obs_" + hashlib.sha256(f"{sid}|{locator}".encode()).hexdigest()[:24]
            raw_price, raw_date = text_at(product, "Price"), text_at(product, "Pricedate")
            price = parse_price(raw_price)
            is_valid = int(price is not None and valid_price_date(raw_date))
            valid += is_valid
            rows += 1
            observations.append((oid, f"monitor:{catalog_id}", sid, scenario_id, store_id,
                                  text_at(product, "Id"), text_at(product, "Name").strip(), text_at(product, "Brand"),
                                  text_at(product, "Unit"), text_at(product, "Promo"), text_at(product, "Catprod/Prodcateg/Name"),
                                  raw_price, price if is_valid else None, raw_date or None, is_valid, locator, dumps(raw_node(product))))
    conn.executemany("INSERT INTO observation VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", observations)
    conn.execute("UPDATE snapshot SET row_count=?,quote_count=?,source_priced_at=? WHERE id=?",
                 (rows, valid, "05.10.2026 04:00", sid))


def lidl_category(raw):
    normalized = normalize_text(raw)
    return {"cafea": "coffee", "lactate": "dairy", "bauturi": "drinks", "detergenti": "detergents",
            "hartie igienica si servetele": "paper"}.get(normalized, "unclassified")


def import_lidl(conn, settings, sid):
    path = settings.root_dir / "probe-data" / "lidl-parsed-2026-10-05.json"
    document = json.loads(path.read_text(encoding="utf-8-sig"), parse_float=Decimal)
    rows, quotes = [], []
    for sheet in document["sheets"]:
        for row in sheet["rows"]:
            values = row["values"]
            if row["excel_row"] == 1 or not values[0]:
                continue
            name, raw_pack, raw_category = map(lambda v: str(v or ""), values[:3])
            raw_price = str(values[3])
            price = parse_price(raw_price)
            excel_row = row["excel_row"]
            item_id = f"lidl:{excel_row}"
            locator = f"{sheet['part']}!row[{excel_row}]"
            category = lidl_category(raw_category)
            rows.append((item_id, "lidl", str(excel_row), name, raw_category, category,
                         "source_category_candidate" if category != "unclassified" else "unclassified",
                         raw_pack, price, sid, locator, normalize_text(name + " " + raw_pack), 999, dumps(row)))
            oid = "obs_" + hashlib.sha256(f"{sid}|{locator}".encode()).hexdigest()[:24]
            quotes.append((oid, item_id, sid, None, None, str(excel_row), name, "", raw_pack, "", raw_category,
                           raw_price, price, None, int(price is not None), locator, dumps(row)))
    if len(rows) != 2444:
        raise RuntimeError(f"Proba Lidl așteptată are 2444 rânduri; găsite {len(rows)}.")
    conn.executemany("INSERT INTO source_product VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    conn.executemany("INSERT INTO observation VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", quotes)
    conn.execute("UPDATE snapshot SET row_count=?,quote_count=? WHERE id=?", (len(rows), sum(q[14] for q in quotes), sid))


def seed_database(settings: Settings) -> dict:
    migrate(settings)
    request_path = settings.root_dir / "probe-data" / "requests.json"
    requests = json.loads(request_path.read_text(encoding="utf-8-sig"))
    collected = {row["Name"]: row.get("CollectedAt") for row in requests}
    manifest_path = settings.root_dir / "fixtures" / "snapshot-manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        for entry in manifest.get("files", []):
            path = settings.root_dir / entry["path"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                raise RuntimeError(f"Proba {entry['path']} nu corespunde manifestului SHA-256.")
    with connect(settings) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            taxonomy = load_categories(conn, settings)
            sid, existed = make_snapshot(conn, settings, "monitor", "catalog.xml", "catalog",
                                        notes=["Catalogul conține 12 denumiri goale, excluse din căutare.", "Identități de sursă, fără GTIN verificat."])
            if not existed:
                import_catalog(conn, settings, sid)
            networks = {text_at(n, "Id").strip(): text_at(n, "Name").strip()
                        for n in records(settings.root_dir / "probe-data" / "networks.xml", "RetailNetwork")}
            for scenario in SCENARIOS:
                sid, existed = make_snapshot(conn, settings, "monitor", scenario[5], scenario[0],
                                            collected.get(Path(scenario[5]).stem),
                                            notes=["Zonă fixă probată; nu reprezintă toate magazinele localității.", "Data prețului are fus orar nedeclarat de sursă."])
                if not existed:
                    import_monitor(conn, settings, scenario, sid, networks)
            sid, existed = make_snapshot(conn, settings, "lidl", "lidl-parsed-2026-10-05.json", "network_list",
                                        notes=["Listă Lidl la nivel de rețea; magazinul și stocul individual sunt necunoscute.",
                                               "Data din numele fișierului nu este data de valabilitate a fiecărui preț.",
                                               "Sursa declară prețuri fără SGR; aplicabilitatea per produs nu este confirmată."])
            if not existed:
                import_lidl(conn, settings, sid)
            reclassify_lidl(conn, taxonomy, settings)
            fts_exists = conn.execute("SELECT 1 FROM sqlite_master WHERE name='product_fts'").fetchone()
            if not fts_exists:
                try:
                    conn.execute("CREATE VIRTUAL TABLE product_fts USING fts5(id UNINDEXED,search_text)")
                    conn.execute("INSERT INTO product_fts SELECT id,search_text FROM source_product WHERE name<>''")
                    search_mode = "fts5"
                except Exception as exc:
                    if "no such module" not in str(exc):
                        raise
                    search_mode = "indexed_prefix"
                conn.execute("INSERT OR REPLACE INTO app_meta VALUES('search_mode',?)", (search_mode,))
            now = datetime.now(timezone.utc).isoformat()
            conn.execute("INSERT OR IGNORE INTO company VALUES(?,?,1)", (COMPANY_ID, "Firma mea"))
            if not conn.execute("SELECT 1 FROM shopping_list WHERE company_id=?", (COMPANY_ID,)).fetchone():
                conn.execute("INSERT INTO shopping_list VALUES(?,?,?,?,?,?,?)",
                             ("list-local", COMPANY_ID, "Lista mea de cumpărături", "slatina_5km", 1, now, now))
            conn.execute("INSERT OR REPLACE INTO app_meta VALUES('seed_version','e1a-1')")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return {"catalog_count": conn.execute("SELECT COUNT(*) FROM source_product").fetchone()[0],
                "monitor_count": conn.execute("SELECT COUNT(*) FROM source_product WHERE source_id='monitor'").fetchone()[0],
                "lidl_count": conn.execute("SELECT COUNT(*) FROM source_product WHERE source_id='lidl'").fetchone()[0],
                "quote_count": conn.execute("SELECT COUNT(*) FROM observation WHERE valid=1").fetchone()[0],
                "search_mode": conn.execute("SELECT value FROM app_meta WHERE key='search_mode'").fetchone()[0]}
