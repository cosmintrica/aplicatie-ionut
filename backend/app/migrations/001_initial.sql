CREATE TABLE IF NOT EXISTS company (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS category (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, parent_id TEXT, metadata TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS snapshot (
 id TEXT PRIMARY KEY, source_id TEXT NOT NULL, filename TEXT NOT NULL, sha256 TEXT NOT NULL,
 query_scope TEXT NOT NULL, retrieved_at TEXT, source_priced_at TEXT,
 row_count INTEGER NOT NULL DEFAULT 0, quote_count INTEGER NOT NULL DEFAULT 0,
 metadata TEXT NOT NULL, UNIQUE(source_id,sha256,query_scope)
);
CREATE TABLE IF NOT EXISTS source_product (
 id TEXT PRIMARY KEY, source_id TEXT NOT NULL, source_product_id TEXT NOT NULL,
 name TEXT NOT NULL, raw_category TEXT NOT NULL DEFAULT '', category_id TEXT NOT NULL,
 category_reason TEXT NOT NULL, raw_pack TEXT NOT NULL DEFAULT '', raw_price TEXT,
 snapshot_id TEXT NOT NULL REFERENCES snapshot(id), locator TEXT NOT NULL,
 search_text TEXT NOT NULL, editorial_rank INTEGER NOT NULL DEFAULT 999,
 raw_record TEXT NOT NULL, UNIQUE(snapshot_id,locator)
);
CREATE INDEX IF NOT EXISTS product_category ON source_product(category_id);
CREATE INDEX IF NOT EXISTS product_source ON source_product(source_id);
CREATE INDEX IF NOT EXISTS product_search ON source_product(search_text);
CREATE TABLE IF NOT EXISTS scenario (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, latitude TEXT NOT NULL, longitude TEXT NOT NULL,
 radius_m INTEGER NOT NULL, snapshot_id TEXT NOT NULL REFERENCES snapshot(id)
);
CREATE TABLE IF NOT EXISTS store (
 id TEXT NOT NULL, scenario_id TEXT NOT NULL REFERENCES scenario(id), name TEXT NOT NULL,
 network_id TEXT NOT NULL, network_name TEXT NOT NULL, address TEXT NOT NULL,
 PRIMARY KEY (scenario_id,id)
);
CREATE TABLE IF NOT EXISTS observation (
 id TEXT PRIMARY KEY, item_id TEXT NOT NULL REFERENCES source_product(id),
 snapshot_id TEXT NOT NULL REFERENCES snapshot(id), scenario_id TEXT,
 store_id TEXT, source_product_id TEXT NOT NULL, commercial_name TEXT NOT NULL,
 raw_brand TEXT NOT NULL, raw_unit TEXT NOT NULL, raw_promo TEXT NOT NULL,
 raw_category TEXT NOT NULL, raw_price TEXT NOT NULL, price TEXT,
 source_priced_at TEXT, valid INTEGER NOT NULL, locator TEXT NOT NULL,
 raw_record TEXT NOT NULL, UNIQUE(snapshot_id,locator)
);
CREATE INDEX IF NOT EXISTS observation_lookup ON observation(item_id,scenario_id,valid);
CREATE TABLE IF NOT EXISTS shopping_list (
 id TEXT NOT NULL, company_id TEXT NOT NULL REFERENCES company(id), name TEXT NOT NULL,
 scenario_id TEXT NOT NULL REFERENCES scenario(id), revision INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 PRIMARY KEY(company_id,id), UNIQUE(id)
);
CREATE TABLE IF NOT EXISTS list_line (
 id TEXT NOT NULL, company_id TEXT NOT NULL, list_id TEXT NOT NULL,
 source_product_id TEXT REFERENCES source_product(id), description TEXT NOT NULL,
 quantity TEXT NOT NULL, unit TEXT NOT NULL, category_id TEXT,
 created_at TEXT NOT NULL,
 PRIMARY KEY(company_id,id),
 FOREIGN KEY(company_id,list_id) REFERENCES shopping_list(company_id,id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS comparison (
 id TEXT NOT NULL, company_id TEXT NOT NULL, list_id TEXT NOT NULL,
 list_revision INTEGER NOT NULL, result TEXT NOT NULL, created_at TEXT NOT NULL,
 PRIMARY KEY(company_id,id),
 FOREIGN KEY(company_id,list_id) REFERENCES shopping_list(company_id,id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY,value TEXT NOT NULL);
