"""Comparații explicabile pe atribute declarate, fără confirmări prin similaritate."""
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re

from .domain import decimal_value, money, normalize_text


BRANDS = ("jacobs", "zuzu", "borsec", "pilos", "bellarom", "fairy", "ariel", "w5", "floralys", "lavazza", "dorna", "tchibo")
ATTRIBUTE_LABELS = {"brand": "marca", "kind": "tipul produsului", "pack": "ambalajul",
                    "fat_percent": "grăsimea", "form": "forma", "variant": "varianta",
                    "range": "gama", "processing": "tratamentul", "water_type": "tipul apei", "purpose": "utilizarea",
                    "concentration": "concentrația"}
VERDICT_LABELS = {"same_variant_candidate": "Aceleași caracteristici",
                  "variant_conflict": "Variantă diferită", "needs_details": "Detalii de verificat"}
KIND_LABELS = {"coffee": "cafea", "milk": "lapte", "water": "apă", "detergent": "detergent",
               "hot_drink": "băutură caldă", "coffee_additive": "adaos pentru cafea", "snack": "gustare"}


def separate_pack_brand(text):
    """Separă numai unitățile lipite de mărci cunoscute, fără similaritate fuzzy."""
    brand_pattern = "|".join(re.escape(brand) for brand in BRANDS)
    return re.sub(rf"(\d(?:[.,]\d+)?)\s*(kg|ml|g|l)(?=(?:{brand_pattern})\b)", r"\1\2 ", text, flags=re.I)


def attribute_value_label(attribute, value):
    if attribute == "pack":
        return value["label"]
    if attribute == "kind":
        return KIND_LABELS.get(value, str(value))
    if attribute == "fat_percent":
        return str(value) + "%"
    if attribute in {"brand", "variant", "range"}:
        return str(value).capitalize()
    return str(value)


def requested_attribute_label(attribute):
    return ATTRIBUTE_LABELS[attribute] + (" cerut" if attribute in {"kind", "pack", "processing", "water_type"} else " cerută")


def scalar_pack(text):
    """Gramaj normalizat; nu presupune semantica prețului."""
    text = separate_pack_brand(text.replace("×", "x"))
    pattern = r"(?:(?<![\d.,])|(?<=[a-zA-Z]\.))(\d+(?:[.,]\d+)?)\s*(kg|kilograme?|ml|mililitri|mililitru|g|grame?|gram|gr\.?|l|litri?|litru)(?=\b|x\s*\d)"
    matches = re.findall(pattern, text, re.I)
    if len(matches) != 1:
        return None
    value, unit = matches[0]
    unit = unit.lower().rstrip(".")
    unit = {"kilogram": "kg", "kilograme": "kg", "gr": "g", "gram": "g", "grame": "g",
            "mililitru": "ml", "mililitri": "ml", "litru": "l", "litri": "l"}.get(unit, unit)
    value = decimal_value(value)
    if value <= 0:
        return None
    match = re.search(pattern, text, re.I)
    preceding, following = text[:match.start()], text[match.end():]
    multi = re.search(r"(\d+)\s*x\s*$", preceding, re.I)
    suffix_multi = re.match(r"\s*x\s*(\d+)(?!\d)", following, re.I)
    if multi and suffix_multi:
        return None
    count = int((multi or suffix_multi).group(1)) if multi or suffix_multi else 1
    if count < 1 or count > 10000:
        return None
    dimension = "mass" if unit in {"kg", "g"} else "volume"
    canonical_unit = "g" if dimension == "mass" else "ml"
    canonical = value * (Decimal(1000) if unit in {"kg", "l"} else 1)
    amount = format(canonical.normalize(), "f")
    return {"dimension": dimension, "amount": amount, "unit": canonical_unit, "count": count,
            "label": (f"{count} x " if count != 1 else "") + f"{format(value.normalize(), 'f')} {unit}"}


def product_profile(name, raw_pack="", raw_brand="", raw_category=""):
    text = normalize_text(separate_pack_brand(name))
    context = normalize_text(raw_category)
    brand_text = normalize_text(raw_brand)
    brand = next((brand for brand in BRANDS if re.search(rf"\b{brand}\b", text)), None)
    if brand is None:
        brand = next((brand for brand in BRANDS if re.search(rf"\b{brand}\b", brand_text)), None)
    kind = None
    # Denumirea are prioritate față de categoriile de merchandising ale sursei.
    if re.search(r"\b(crackers|biscuiti|biscuit|napolitane)\b", text):
        kind = "snack"
    elif re.search(r"\b(ciocolata calda|cappuccino|cacao plicuri)\b", text):
        kind = "hot_drink"
    elif "pudra pentru cafea" in text:
        kind = "coffee_additive"
    elif brand in {"fairy", "ariel", "w5"} and (re.search(r"\b(detergent|detergenti|solutie|curatare|degresant|dezinfectant|desfundarea|inalbitor)(?=\d|\b)", text) or "detergent" in context):
        kind = "detergent"
    elif "lapte" in text:
        kind = "milk"
    elif re.search(r"\b(apa|necarb|carbogazoasa)\b", text) or brand in {"borsec", "dorna"}:
        kind = "water"
    elif re.search(r"\b(cafea|coffee)\b", text) or (brand == "jacobs" and "kronung" in text):
        kind = "coffee"
    elif re.search(r"\b(detergent|detergenti|degresant|dezinfectant)(?=\d|\b)", text) or (
            brand in {"fairy", "ariel", "w5"} and (re.search(r"\b(solutie|curatare|desfundarea|inalbitor)\b", text) or "detergent" in context)):
        kind = "detergent"
    elif "cafea" in context:
        kind = "coffee"
    pack = scalar_pack(name)
    packed = scalar_pack(raw_pack)
    pack_conflict = bool(pack and packed and pack_key(pack) != pack_key(packed))
    if pack is None and packed:
        pack = packed
    percentages = re.findall(r"(\d+(?:[.,]\d+)?)\s*%", name)
    fat = format(decimal_value(percentages[0]).normalize(), "f") if kind == "milk" and len(percentages) == 1 else None
    form = None
    if kind == "coffee":
        if re.search(r"\b(boabe|beans)(?=\d|\b)", text):
            form = "boabe"
        elif re.search(r"\b(macinata|macin\w*|mac|ground)\b", text) or re.search(r"\br\s*&\s*g\b", name, re.I):
            form = "măcinată"
        elif re.search(r"\b(solubila|instant)(?=\d|\b)", text):
            form = "solubilă"
        elif re.search(r"\b(capsule|capsula)(?=\d|\b)", text):
            form = "capsule"
        elif re.search(r"\b(pads|paduri)\b", text):
            form = "paduri"
    elif kind == "detergent":
        form = next((word for word in ("gel", "crema", "pudra", "praf", "tablete", "capsule", "lichid") if re.search(rf"\b{word}\b", text)), None)
    variant = next((word for word in ("alintaroma", "intense", "intenso", "royal", "decaf", "decofeinizata", "crema", "gold", "origine") if re.search(rf"\b{word}(?=\d|\b)", text)), None)
    if variant in {"decaf", "decofeinizata"}:
        variant = "decofeinizată"
    if variant is None and kind == "coffee" and re.search(r"\bkronung int\b", text):
        variant = "intense"
    if variant is None and "intense" in brand_text:
        variant = "intense"
    water_type = None
    if kind == "water":
        if re.search(r"\b(plata|necarb|necarbogazoasa|still)(?=\d|\b)", text):
            water_type = "plată"
        elif re.search(r"\b(carbogazoasa|carbogazificata|sparkling)(?=\d|\b)", text):
            water_type = "carbogazoasă"
    processing = next((word.upper() for word in ("uht", "esl") if re.search(rf"\b{word}(?=\d|\b)", text)), None)
    purpose = None
    concentration = None
    if kind == "detergent":
        concentration = "ultraconcentrat" if "ultraconcentrat" in text else "concentrat" if re.search(r"\bconcentrat(?:a)?\b", text) else None
        rules = (("vase", r"\b(vase|dishwashing)\b"), ("WC", r"\b(wc|toaleta|toilet)\b"),
                 ("țevi", r"\b(tevi(?:lor)?|scurgeri(?:lor)?)\b"), ("geamuri", r"\b(geamuri|sticla)\b"),
                 ("rufe", r"\b(rufe|laundry)\b"), ("pardoseli", r"\b(pardoseli|podele)\b"),
                 ("degresare", r"\bdegresant\b"), ("dezinfectare", r"\bdezinfectant\b"))
        found = [label for label, expression in rules if re.search(expression, text)]
        purpose = " / ".join(found) if found else None
    return {"kind": kind, "brand": brand, "pack": pack, "fat_percent": fat, "form": form,
            "variant": variant, "range": "kronung" if "kronung" in text else None,
            "processing": processing, "water_type": water_type, "purpose": purpose,
            "concentration": concentration, "pack_conflict": pack_conflict}


def pack_key(pack):
    return (pack["dimension"], pack["amount"], pack["count"]) if pack else None


def match_profiles(reference, offer, source_catalog=None, ignore_pack=False, offer_catalog=None):
    target = dict(reference)
    if source_catalog:
        # Contextul de magazin poate declara o variantă omisă din catalogul global.
        for attribute, value in source_catalog.items():
            if target.get(attribute) is None and value is not None:
                target[attribute] = value
    reasons, conflicts, missing, missing_details = [], [], [], []
    if offer.get("pack_conflict"):
        conflicts.append("Gramajul din denumire contrazice gramajul declarat separat de sursă.")
    for attribute in ATTRIBUTE_LABELS:
        if ignore_pack and attribute == "pack":
            continue
        expected, actual = target.get(attribute), offer.get(attribute)
        if expected is None:
            continue
        equal = pack_key(expected) == pack_key(actual) if attribute == "pack" else expected == actual
        if actual is None:
            missing.append(ATTRIBUTE_LABELS[attribute])
            missing_details.append(ATTRIBUTE_LABELS[attribute] + " " + attribute_value_label(attribute, expected))
        elif not equal:
            conflicts.append(f"{ATTRIBUTE_LABELS[attribute].capitalize()}: {attribute_value_label(attribute, actual)} în ofertă, {attribute_value_label(attribute, expected)} în cerere.")
        else:
            shown = attribute_value_label(attribute, expected)
            reasons.append(f"{ATTRIBUTE_LABELS[attribute].capitalize()}: {shown}.")
    for essential in ("kind", "brand", "pack"):
        if target.get(essential) is None:
            missing.append(requested_attribute_label(essential))
            missing_details.append(requested_attribute_label(essential))
    if target.get("kind") == "milk" and target.get("fat_percent") is None:
        missing.append("grăsimea cerută")
        missing_details.append("grăsimea cerută")
    if target.get("kind") == "water" and target.get("water_type") is None:
        missing.append("tipul apei cerut")
        missing_details.append("tipul apei cerut")
    if target.get("kind") == "detergent" and target.get("purpose") is None:
        missing.append("utilizarea cerută")
        missing_details.append("utilizarea cerută")
    critical = {"coffee": ("form", "variant"), "milk": ("processing",),
                "detergent": ("purpose", "form", "concentration")}.get(target.get("kind"), ())
    for attribute in critical:
        actual = offer.get(attribute)
        catalog_value = (offer_catalog or {}).get(attribute)
        declared = actual if actual is not None else catalog_value
        if target.get(attribute) is None and declared is not None:
            missing.append(requested_attribute_label(attribute))
            location = "oferta declară " if actual is not None else "catalogul ofertei declară "
            missing_details.append(requested_attribute_label(attribute) + "; " + location + attribute_value_label(attribute, declared))
        elif target.get(attribute) is not None and actual is None and catalog_value is not None and target[attribute] != catalog_value:
            conflicts.append(f"{ATTRIBUTE_LABELS[attribute].capitalize()}: {attribute_value_label(attribute, catalog_value)} în catalogul ofertei, {attribute_value_label(attribute, target[attribute])} în cerere.")
    missing = list(dict.fromkeys(missing))
    verdict = "variant_conflict" if conflicts else "needs_details" if missing else "same_variant_candidate"
    if missing:
        reasons.append("Lipsesc: " + ", ".join(dict.fromkeys(missing_details)) + ".")
    if verdict == "same_variant_candidate":
        reasons.append("Caracteristicile declarate corespund; codul exact al articolului nu este verificat.")
    return {"verdict": verdict, "verdict_label": VERDICT_LABELS[verdict],
            "match_reasons": conflicts + reasons, "profile": offer, "reference_profile": target,
            "attribute_conflicts": conflicts, "missing_attributes": missing}


def price_basis(raw_unit, profile, source_id):
    unit = normalize_text(raw_unit)
    pack = profile.get("pack")
    if unit in {"per kg", "pe kg"}:
        return {"status": "declared_mass_unit", "label": "Preț declarat pe kilogram; greutatea cerută nu este exprimată în kilograme", "quantity_eligible": False}
    if unit in {"buc", "bucata", "bucati", "piece", "item"} and pack and not profile.get("pack_conflict"):
        return {"status": "declared_pack", "label": "Preț declarat pe bucată/ambalaj", "quantity_eligible": True}
    if source_id == "lidl" and pack and not profile.get("pack_conflict") and normalize_text(raw_unit) not in {"per kg", "kg"}:
        return {"status": "structured_pack", "label": "Preț de vânzare asociat gramajului din lista Lidl", "quantity_eligible": True}
    # Pentru exact 1 l, preț/litru și preț/ambalaj produc aceeași estimare.
    if unit in {"l", "litru", "litri"} and pack_key(pack) == ("volume", "1000", 1) and not profile.get("pack_conflict"):
        return {"status": "equivalent_one_litre", "label": "Ambalaj de 1 l; estimarea este identică pe litru sau pe ambalaj", "quantity_eligible": True}
    return {"status": "ambiguous", "label": "Sursa nu precizează clar prețul pe ambalaj", "quantity_eligible": False}


def unit_price_value(value, unit, basis):
    """Valoare de prezentare cu șase zecimale; eticheta este calculată în backend."""
    amount = value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    label_amount = money(value)["amount"].replace(".", ",")
    if 0 < value < Decimal("0.01"):
        label_amount = "<0,01"
    return {"amount": format(amount, "f"), "currency": "RON", "unit": unit,
            "label": f"{label_amount} lei/{unit}", "basis": basis}


def normalized_unit_price(price, profile, basis):
    if price is None or profile.get("pack_conflict"):
        return None
    price = decimal_value(price) if isinstance(price, str) else price
    if price <= 0:
        return None
    if basis.get("status") == "declared_mass_unit":
        return unit_price_value(price, "kg", basis["label"])
    if not basis.get("quantity_eligible"):
        return None
    pack = profile.get("pack")
    if not pack or pack.get("dimension") not in {"mass", "volume"}:
        return None
    amount = Decimal(pack["amount"]) * Decimal(pack["count"]) / Decimal(1000)
    if amount <= 0 or price <= 0:
        return None
    unit = "kg" if pack["dimension"] == "mass" else "l"
    result = unit_price_value(price / amount, unit, basis["label"])
    return result if Decimal(result["amount"]) > 0 else None


def pack_alternative(reference, offer, context=None, offer_catalog=None):
    left, right = reference.get("pack"), offer.get("pack")
    if not left or not right or left["dimension"] != right["dimension"] or pack_key(left) == pack_key(right):
        return None
    if reference.get("brand") is None or reference.get("kind") is None or reference["brand"] != offer.get("brand") or reference["kind"] != offer.get("kind"):
        return None
    assessed = match_profiles(reference, offer, context, ignore_pack=True, offer_catalog=offer_catalog)
    if assessed["verdict"] == "variant_conflict":
        return None
    return {"kind": "different_pack",
            "status": "compatible_characteristics" if assessed["verdict"] == "same_variant_candidate" else "needs_details",
            "label": "Alt ambalaj, aceleași caracteristici declarate" if assessed["verdict"] == "same_variant_candidate" else "Alt ambalaj, detalii de verificat",
            "changes": [f"Ambalaj: {right['label']} în loc de {left['label']}."],
            "reasons": assessed["match_reasons"] + ["Ambalajul diferă; această opțiune nu înlocuiește automat produsul din coș."]}


def unit_price_groups(quotes):
    groups = defaultdict(list)
    for quote in quotes:
        unit_price = quote.get("unit_price")
        alternative = quote.get("alternative")
        eligible = (alternative and alternative["status"] == "compatible_characteristics") or (not alternative and quote["verdict"] == "same_variant_candidate")
        if not unit_price or not eligible:
            continue
        profile = {key: value for key, value in quote["profile"].items() if key not in {"pack", "pack_conflict"}}
        key = json.dumps({"profile": profile, "unit": unit_price["unit"]}, sort_keys=True, ensure_ascii=False)
        groups[key].append(quote)
    result = []
    for key, options in groups.items():
        options = sorted(options, key=lambda quote: (Decimal(quote["unit_price"]["amount"]), quote["observation_id"]))
        first, last = options[0], options[-1]
        profile = first["profile"]
        labels = [profile.get("brand"), profile.get("range"), profile.get("variant"), profile.get("form"),
                  profile.get("processing"), profile.get("water_type"), profile.get("purpose")]
        if profile.get("fat_percent"):
            labels.append(profile["fat_percent"] + "%")
        spread = Decimal(last["unit_price"]["amount"]) - Decimal(first["unit_price"]["amount"])
        result.append({"id": "unit_group_" + hashlib.sha256(key.encode()).hexdigest()[:16],
                       "label": " · ".join(label for label in labels if label), "unit": first["unit_price"]["unit"],
                       "options": options, "minimum": first["unit_price"], "maximum": last["unit_price"],
                       "spread": unit_price_value(spread, first["unit_price"]["unit"], "Diferență între prețuri normalizate"),
                       "best_option": first,
                       "explanation": "Prețul pe unitate permite evaluarea ambalajelor. Nu reprezintă totalul coșului sau economii realizate."})
    return sorted(result, key=lambda group: Decimal(group["minimum"]["amount"]))


def quote_order(quote):
    return (Decimal(quote["price"]["amount"]) if quote.get("price") else Decimal("Infinity"), quote["observation_id"])


def price_range(quotes):
    amounts = [Decimal(quote["price"]["amount"]) for quote in quotes if quote.get("price")]
    return {"minimum": money(min(amounts)) if amounts else None,
            "maximum": money(max(amounts)) if amounts else None,
            "spread": money(max(amounts) - min(amounts)) if amounts else None}


def comparable_groups(quotes):
    groups = defaultdict(list)
    for quote in quotes:
        if not quote.get("price") or quote["verdict"] == "variant_conflict":
            continue
        profile = quote["profile"]
        basis = quote["price_basis"]
        # Ambiguele se compară doar ca valori raportate cu aceeași unitate brută.
        basis_key = "package" if basis["quantity_eligible"] else "reported:" + normalize_text(quote["raw_unit"])
        normalized_profile = {**profile, "pack": pack_key(profile.get("pack"))}
        key = json.dumps({"profile": normalized_profile, "basis": basis_key}, sort_keys=True, ensure_ascii=False)
        groups[key].append(quote)
    results = []
    for key, options in groups.items():
        options = sorted(options, key=quote_order)
        first = options[0]
        profile = first["profile"]
        labels = [profile.get("brand"), profile.get("range"), profile.get("variant"), profile.get("form"),
                  (profile.get("fat_percent") + "%") if profile.get("fat_percent") else None,
                  profile["pack"]["label"] if profile.get("pack") else None, profile.get("processing"), profile.get("water_type")]
        results.append({"id": "group_" + hashlib.sha256(key.encode()).hexdigest()[:16],
                        "label": " · ".join(label for label in labels if label) or "Detalii incomplete",
                        "profile": profile, "options": options, **price_range(options),
                        "basis_label": "Prețuri pe ambalaj, estimate" if first["price_basis"]["quantity_eligible"] else f"Unitate brută: {first['raw_unit']}. Cotații raportate; baza prețului rămâne de verificat",
                        "estimate_eligible": all(option["verdict"] == "same_variant_candidate" and option["price_basis"]["quantity_eligible"] for option in options)})
    return sorted(results, key=lambda group: Decimal(group["minimum"]["amount"]))


def line_analysis(line, quotes, reference, alternatives=None):
    options = sorted((quote for quote in quotes if quote.get("price")), key=quote_order)
    candidates = [quote for quote in options if quote["verdict"] == "same_variant_candidate"]
    eligible = [quote for quote in candidates if quote["price_basis"]["quantity_eligible"] and Decimal(line["quantity"]) == Decimal(line["quantity"]).to_integral_value()]
    # Nu compară prețurile pe kg cu prețurile pe ambalaj pentru a declara un minim.
    group_options = comparable_groups(options)
    ranges = price_range(eligible)
    return {"line_id": line["id"], "description": line["description"], "quantity": line["quantity"],
            "source_product_id": line.get("source_product_id"), "source_product_name": line.get("source_product_name"),
            "reference_profile": reference, "options": options, "comparable_options": eligible,
            "conflicting_options": [quote for quote in options if quote["verdict"] == "variant_conflict"],
            "needs_details_options": [quote for quote in options if quote["verdict"] == "needs_details"],
            "price_min": ranges["minimum"], "price_max": ranges["maximum"], "price_spread": ranges["spread"],
            "best_option": eligible[0] if eligible else None, "groups": group_options,
            "pack_alternatives": alternatives or [],
            "unit_price_groups": unit_price_groups([*options, *(alternatives or [])]),
            "warnings": (["Cantitatea de ambalaje trebuie să fie un număr întreg pentru estimare."] if Decimal(line["quantity"]) != Decimal(line["quantity"]).to_integral_value() else [])
                        + (["Nu există prețuri comparabile pe ambalaj pentru toate caracteristicile cerute."] if not eligible else [])}
