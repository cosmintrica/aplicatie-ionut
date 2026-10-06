"""Pregătește o copie publică, fără modificarea probelor sau datelor locale."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil


DIRECTORIES = ("backend", "web", "config", "docs", "fixtures", "probe-data", "scripts", "tests", ".github")
ROOT_FILES = (".gitignore", ".gitattributes", "README.md", "CERERE_INITIALA.md", "RAPORT_TESTARE.md")
EXCLUDED = {".git", ".venv", "node_modules", "dist", "var", "tmp", "__pycache__", ".pytest_cache", ".hypothesis"}
SUFFIXES = {".pyc", ".sqlite", ".sqlite3", ".db", ".log"}


def allowed(path):
    return not (EXCLUDED.intersection(path.parts)
                or any(part.endswith(".egg-info") for part in path.parts)
                or (path.name.startswith(".env") and path.name != ".env.example")
                or path.suffix in SUFFIXES
                or ".sqlite3-" in path.name)


def relative_metadata(value):
    if isinstance(value, dict):
        return {key: relative_metadata(item) for key, item in value.items()}
    if isinstance(value, list):
        return [relative_metadata(item) for item in value]
    if isinstance(value, str) and re.match(r"^[A-Za-z]:[\\/]", value):
        name = re.split(r"[\\/]", value)[-1]
        return "probe-data/" + name
    return value


def prepare(root, output):
    root, output = root.resolve(), output.resolve()
    if not output.is_relative_to(root / "tmp") or output == root / "tmp":
        raise ValueError("Destinația trebuie să fie un subdirector nou din tmp al proiectului.")
    if output.exists():
        raise ValueError("Destinația există deja. Alege un director nou; fișierele existente nu sunt înlocuite.")
    manifest = json.loads((root / "fixtures/snapshot-manifest.json").read_text(encoding="utf-8-sig"))
    for entry in manifest["files"]:
        if hashlib.sha256((root / entry["path"]).read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("Proba locală nu corespunde manifestului: " + entry["path"])
    output.mkdir(parents=True)
    paths = [root / name for name in ROOT_FILES]
    for name in DIRECTORIES:
        paths.extend(path for path in (root / name).rglob("*") if path.is_file() and allowed(path.relative_to(root)))
    for path in paths:
        target = output / path.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    changed = []
    for name in ("lidl-parsed-2026-10-05.json", "summary.json"):
        path = output / "probe-data" / name
        original = json.loads(path.read_text(encoding="utf-8-sig"))
        sanitized = relative_metadata(original)
        if sanitized != original:
            path.write_text(json.dumps(sanitized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
            changed.append("probe-data/" + name)
    for entry in manifest["files"]:
        content = (output / entry["path"]).read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if digest != entry["sha256"]:
            entry["original_sha256"] = entry["sha256"]
            entry["sanitization"] = "absolute_local_paths_to_relative_metadata_only"
        entry["sha256"], entry["bytes"] = digest, len(content)
    if changed:
        manifest["public_export"] = {"sanitized_files": changed, "price_records_modified": False}
    (output / "fixtures/snapshot-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return len(paths), changed


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    files, changed = prepare(Path(__file__).resolve().parents[1], args.output)
    print(f"Copie publică: {args.output.resolve()} | {files} fișiere | {len(changed)} metadate JSON normalizate")
