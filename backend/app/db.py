from contextlib import contextmanager
import sqlite3
from .settings import Settings


@contextmanager
def connect(settings: Settings):
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    try:
        yield conn
    finally:
        conn.close()


def migrate(settings: Settings):
    from pathlib import Path
    import hashlib
    with connect(settings) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migration (name TEXT PRIMARY KEY,sha256 TEXT NOT NULL)")
        for path in sorted((Path(__file__).parent / "migrations").glob("*.sql")):
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            applied = conn.execute("SELECT sha256 FROM schema_migration WHERE name=?", (path.name,)).fetchone()
            if applied:
                if applied[0] != digest:
                    raise RuntimeError(f"Migrația aplicată {path.name} a fost modificată.")
                continue
            conn.executescript("BEGIN IMMEDIATE;\n" + path.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migration VALUES(?,?)", (path.name, digest))
            conn.commit()
        if conn.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise RuntimeError("Verificarea integrității SQLite a eșuat.")
