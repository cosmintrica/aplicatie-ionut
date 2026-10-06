"""Offline probe of the saved public Lidl XLSB price list; no network requests.

Minimal read-only MS-XLSB reader for the record types present in this source.
It reads stored cell values, not formula recalculation or Excel formatting.
Specification: https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xlsb/acc8aa92-1f02-4167-99f5-84f9f676b95a
"""
import collections
import datetime
import hashlib
import json
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


def records(data):
    pos = 0
    while pos < len(data):
        kind = 0
        for shift in (0, 7):
            byte = data[pos]
            pos += 1
            kind |= (byte & 0x7F) << shift
            if byte < 128:
                break
        size = 0
        for shift in (0, 7, 14, 21):
            byte = data[pos]
            pos += 1
            size |= (byte & 0x7F) << shift
            if byte < 128:
                break
        if pos + size > len(data):
            raise ValueError("Truncated record")
        yield kind, data[pos:pos + size]
        pos += size


def xstring(payload, offset=0):
    size = struct.unpack_from("<I", payload, offset)[0]
    if size == 0xFFFFFFFF:
        return None
    return payload[offset + 4:offset + 4 + size * 2].decode("utf-16le")


def rk(payload):
    value = struct.unpack("<I", payload)[0]
    if value & 2:
        number = struct.unpack("<i", payload)[0] >> 2
    else:
        number = struct.unpack("<d", b"\0\0\0\0" + struct.pack("<I", value & ~3))[0]
    return number / 100 if value & 1 else number


def main(path):
    with zipfile.ZipFile(path) as source:
        strings = [xstring(body, 1) for kind, body in records(source.read("xl/sharedStrings.bin")) if kind == 19]
        result = {"file": str(path.resolve()), "source_url": "https://www.lidl.ro/explore/assets/webPriceData/ro/preturiZilniceLidl.xlsb", "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "core_properties": source.read("docProps/core.xml").decode(), "sheets": [], "reader_limit": "Stored values only; no Excel formula recalculation or formatting"}
        for name in source.namelist():
            if not (name.startswith("xl/worksheets/sheet") and name.endswith(".bin")):
                continue
            rows = collections.defaultdict(dict)
            counts = collections.Counter()
            current_row = None
            unsupported_cells = []
            for kind, body in records(source.read(name)):
                counts[kind] += 1
                if kind == 0:
                    current_row = struct.unpack_from("<I", body)[0]
                elif 1 <= kind <= 11:
                    column = struct.unpack_from("<I", body)[0]
                    if kind == 1:
                        value = None
                    elif kind == 2:
                        value = rk(body[8:12])
                    elif kind in (3, 11):
                        value = {"excel_error_code": body[8]}
                    elif kind in (4, 10):
                        value = bool(body[8])
                    elif kind in (5, 9):
                        value = struct.unpack_from("<d", body, 8)[0]
                    elif kind in (6, 8):
                        value = xstring(body, 8)
                    elif kind == 7:
                        value = strings[struct.unpack_from("<I", body, 8)[0]]
                    else:
                        unsupported_cells.append({"row": current_row, "column": column, "record_kind": kind})
                        continue
                    rows[current_row][column] = value
            width = max(c for values in rows.values() for c in values) + 1
            matrix = [{"excel_row": row + 1, "values": [values.get(col) for col in range(width)]} for row, values in sorted(rows.items()) if any(v is not None for v in values.values())]
            result["sheets"].append({"part": name, "column_count": width, "nonempty_row_count": len(matrix), "record_counts": dict(counts), "unsupported_cell_records": unsupported_cells, "rows": matrix})
    capture_date_match = re.search(r"(\d{4}-\d{2}-\d{2})$", path.stem)
    capture_date = None
    if capture_date_match:
        capture_date = datetime.date.fromisoformat(capture_date_match.group(1)).isoformat()
    if path.stem.startswith("lidl-preturiZilnice"):
        parsed_stem = path.stem.replace("lidl-preturiZilnice", "lidl-parsed", 1)
        summary_stem = path.stem.replace("lidl-preturiZilnice", "lidl-summary", 1)
    else:
        parsed_stem = path.stem + "-parsed"
        summary_stem = path.stem + "-summary"
    output = path.with_name(parsed_stem + ".json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    sheet = result["sheets"][0]
    rows = sheet["rows"]
    assert rows[0]["values"][:4] == ["Denumire comerciala", "Gramaj", "Categorie", "Pret vanzare"]
    products = rows[1:]
    assert all(isinstance(row["values"][3], (int, float)) for row in products)
    core = ET.fromstring(result["core_properties"])
    summary = {
        "source_page": "https://www.lidl.ro/c/preturile-la-zi/s10019622",
        "source_file": result["source_url"],
        "capture_date_from_filename": capture_date,
        "file_bytes": path.stat().st_size,
        "sha256": result["sha256"],
        "file_created_utc": core.find("{http://purl.org/dc/terms/}created").text,
        "file_modified_utc": core.find("{http://purl.org/dc/terms/}modified").text,
        "file_date_is_not_a_price_validity_date": True,
        "product_rows": len(products),
        "populated_columns": rows[0]["values"][:4],
        "category_count": len({row["values"][2] for row in products}),
        "numeric_price_rows": sum(isinstance(row["values"][3], (int, float)) for row in products),
        "duplicate_name_pack_rows_above_unique": sum(n - 1 for n in collections.Counter((row["values"][0], row["values"][1]) for row in products).values()),
        "source_page_states": ["Same prices throughout Lidl Romania network", "Permanent assortment list published Monday-Friday", "Prices exclude SGR guarantee", "Offers within available stock"],
        "missing_structured_fields": ["GTIN/EAN", "SKU", "price validity date", "store id", "stock", "per-product SGR applicability", "VAT"],
        "examples": [row for row in products if row["excel_row"] in {1715, 589, 329, 1514, 1153}],
        "reader_limit": result["reader_limit"],
        "present_supported_cell_record_counts": {
            str(kind): sheet["record_counts"][kind]
            for kind in range(1, 12) if kind in sheet["record_counts"]
        },
        "formula_cell_record_count": sum(sheet["record_counts"].get(kind, 0) for kind in range(8, 12)),
    }
    summary_path = path.with_name(summary_stem + ".json")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(output)
    print(summary_path)


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "probe-data/lidl-preturiZilnice-2026-10-05.xlsb"))
