"""Reguli conservative; afișarea unei cotații nu confirmă identitatea."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
import unicodedata


UNKNOWN_CONDITIONS = [
    "Identitatea exactă a produsului nu este confirmată.",
    "Baza prețului (pe ambalaj sau pe unitate) nu este confirmată.",
    "TVA nu este precizat în înregistrare.",
    "Disponibilitatea în stoc nu este verificată.",
    "Costul transportului și eligibilitatea firmei nu sunt cunoscute.",
    "SGR și condițiile de promoție/card nu sunt confirmate per produs.",
]


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.replace("kroenung", "kronung").replace("kronüng", "kronung")
    return " ".join(re.findall(r"[a-z0-9]+", value))


def decimal_value(value: str) -> Decimal:
    if not isinstance(value, str) or not re.fullmatch(r"-?\d+(?:[.,]\d+)?", value.strip()):
        raise ValueError("Este necesar un șir numeric zecimal, fără separatori de mii.")
    parsed = Decimal(value.strip().replace(",", "."))
    if not parsed.is_finite():
        raise ValueError("Valoarea trebuie să fie finită.")
    return parsed


def exact_quantity(value: str) -> str:
    parsed = decimal_value(value)
    if parsed <= 0 or parsed > Decimal("1000000") or -parsed.as_tuple().exponent > 6:
        raise ValueError("Cantitatea trebuie să fie pozitivă, maximum 1.000.000, cu cel mult șase zecimale.")
    return format(parsed.normalize(), "f")


def money(value: str | Decimal) -> dict:
    parsed = decimal_value(value) if isinstance(value, str) else value
    if not parsed.is_finite():
        raise ValueError("Suma trebuie să fie finită.")
    # Numai la prezentarea unei sume finale, niciodată float.
    return {"amount": format(parsed.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f"), "currency": "RON"}


def parse_price(value: str) -> str | None:
    try:
        result = decimal_value(value)
        return format(result, "f") if result > 0 else None
    except (ValueError, InvalidOperation):
        return None


def assess_quote(catalog_name: str, commercial_name: str, raw_category: str, raw_unit: str) -> dict:
    catalog, title, category = map(normalize_text, (catalog_name, commercial_name or catalog_name, raw_category))
    conflicts = []
    if "alintaroma" in catalog and ("intense" in title or re.search(r"\bkronung int\b", title)):
        conflicts.append("Varianta Intense diferă de Alintaroma cerută în catalog.")
    if "intense" in catalog and "alintaroma" in title:
        conflicts.append("Varianta Alintaroma diferă de Intense cerută în catalog.")
    if ("ariel" in title or "detergent" in title) and category in {"lapte", "lactate"}:
        conflicts.append("Categoria sursei (lapte) contrazice denumirea detergentului.")
    if "fairy" in title and "dezinfect" in category:
        conflicts.append("Categoria sursei (dezinfectanți) nu confirmă utilizarea detergentului Fairy.")
    # Gramajul din titlu nu stabilește baza prețului; doar contradicțiile explicite.
    def scalar_pack(original):
        # Un scalar explicit; multipack-urile și textele cu mai multe cantități
        # necesită o schemă proprie și nu produc verdict automat în E1a.
        if re.search(r"\d\s*[x×]\s*\d", original, re.IGNORECASE):
            return None
        found = re.findall(r"(?<![\w.,])(\d+(?:[.,]\d+)?)\s*(kg|ml|g|l)\b", original, re.IGNORECASE)
        if len(found) != 1:
            return None
        number, unit = found[0]
        unit = unit.casefold()
        scale = {"kg": Decimal(1000), "g": Decimal(1), "l": Decimal(1000), "ml": Decimal(1)}[unit]
        return ("mass" if unit in {"kg", "g"} else "volume", decimal_value(number) * scale)
    left, right = scalar_pack(catalog_name), scalar_pack(commercial_name)
    if left is not None and right is not None and left != right:
        conflicts.append("Cantitatea explicită a ambalajului diferă de catalog.")
    unknowns = list(UNKNOWN_CONDITIONS)
    if raw_unit in {"K", "Kg", "L", "Litru"}:
        unknowns.append(f"Unitatea brută «{raw_unit}» nu stabilește dacă prețul este pe pachet sau pe kg/l.")
    if "kronung" in catalog and not any(word in title for word in ("intense", "alintaroma")):
        unknowns.append("Varianta cafelei nu este explicită în denumirea comercială.")
    return {"relation": "INCOMPATIBLE" if conflicts else "SOURCE_ASSOCIATION", "conflicts": conflicts, "unknowns": unknowns}
