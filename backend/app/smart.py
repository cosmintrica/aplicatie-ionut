"""Comparații explicabile pe atribute declarate, fără confirmări prin similaritate."""
from collections import defaultdict
from decimal import Decimal
import hashlib
import json
import re

from .domain import decimal_value, money, normalize_text


BRANDS = ("jacobs", "zuzu", "borsec", "pilos", "bellarom", "fairy", "ariel", "w5", "floralys")
ATTRIBUTE_LABELS = {"brand": "marca", "kind": "tipul produsului", "pack": "ambalajul",
                    "fat_percent": "grăsimea", "form": "forma", "variant": "varianta",
                    "range": "gama", "processing": "tratamentul", "water_type": "tipul apei"}
VERDICT_LABELS = {"same_variant_candidate": "Aceleași caracteristici",
                  "variant_conflict": "Variantă diferită", "needs_details": "Detalii de verificat"}
KIND_LABELS = {"coffee": "cafea", "milk": "lapte", "water": "apă", "detergent": "detergent"}


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


def scalar_pack(text):
    """Gramaj normalizat; nu presupune semantica prețului."""
    text = text.replace("×", "x")
    pattern = r"(?:(?<![\d.,])|(?<=[a-zA-Z]\.))(\d+(?:[.,]\d+)?)\s*(kg|ml|g|l)\b"
    matches = re.findall(pattern, text, re.I)
    if len(matches) != 1:
        return None
    value, unit = matches[0]
    unit = unit.lower()
    value = decimal_value(value)
    if value <= 0:
        return None
    preceding = text[:re.search(pattern, text, re.I).start()]
    multi = re.search(r"(\d+)\s*x\s*$", preceding, re.I)
    count = int(multi.group(1)) if multi else 1
    if count < 1 or count > 10000:
        return None
    dimension = "mass" if unit in {"kg", "g"} else "volume"
    canonical_unit = "g" if dimension == "mass" else "ml"
    canonical = value * (Decimal(1000) if unit in {"kg", "l"} else 1)
    amount = format(canonical.normalize(), "f")
    return {"dimension": dimension, "amount": amount, "unit": canonical_unit, "count": count,
            "label": (f"{count} x " if count != 1 else "") + f"{format(value.normalize(), 'f')} {unit}"}


def product_profile(name, raw_pack="", raw_brand="", raw_category=""):
    text = normalize_text(name)
    context = normalize_text(raw_category)
    brand_text = normalize_text(raw_brand)
    brand = next((brand for brand in BRANDS if re.search(rf"\b{brand}\b", text)), None)
    if brand is None:
        brand = next((brand for brand in BRANDS if re.search(rf"\b{brand}\b", brand_text)), None)
    kind = None
    # Denumirea are prioritate față de categoriile de merchandising ale sursei.
    if "lapte" in text:
        kind = "milk"
    elif re.search(r"\b(apa|necarb|carbogazoasa)\b", text) or brand == "borsec":
        kind = "water"
    elif re.search(r"\b(cafea|coffee)\b", text) or brand in {"jacobs", "bellarom"}:
        kind = "coffee"
    elif re.search(r"\b(detergent|detergenti)\b", text) or brand in {"fairy", "ariel", "w5"}:
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
    variant = next((word for word in ("alintaroma", "intense", "decaf", "decofeinizata", "crema", "gold") if word in text), None)
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
    processing = next((word.upper() for word in ("uht", "esl") if re.search(rf"\b{word}\b", text)), None)
    return {"kind": kind, "brand": brand, "pack": pack, "fat_percent": fat, "form": form,
            "variant": variant, "range": "kronung" if "kronung" in text else None,
            "processing": processing, "water_type": water_type, "pack_conflict": pack_conflict}


def pack_key(pack):
    return (pack["dimension"], pack["amount"], pack["count"]) if pack else None


def match_profiles(reference, offer, source_catalog=None):
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
            missing.append(ATTRIBUTE_LABELS[essential] + " cerută")
            missing_details.append(ATTRIBUTE_LABELS[essential] + " cerută")
    if target.get("kind") == "milk" and target.get("fat_percent") is None:
        missing.append("grăsimea cerută")
        missing_details.append("grăsimea cerută")
    if target.get("kind") == "water" and target.get("water_type") is None:
        missing.append("tipul apei cerut")
        missing_details.append("tipul apei cerut")
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
    if unit in {"buc", "bucata", "bucati", "piece", "item"} and pack:
        return {"status": "declared_pack", "label": "Preț declarat pe bucată/ambalaj", "quantity_eligible": True}
    if source_id == "lidl" and pack and normalize_text(raw_unit) not in {"per kg", "kg"}:
        return {"status": "structured_pack", "label": "Preț de vânzare asociat gramajului din lista Lidl", "quantity_eligible": True}
    # Pentru exact 1 l, preț/litru și preț/ambalaj produc aceeași estimare.
    if unit in {"l", "litru"} and pack_key(pack) == ("volume", "1000", 1):
        return {"status": "equivalent_one_litre", "label": "Ambalaj de 1 l; estimarea este identică pe litru sau pe ambalaj", "quantity_eligible": True}
    return {"status": "ambiguous", "label": "Sursa nu precizează clar prețul pe ambalaj", "quantity_eligible": False}


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


def line_analysis(line, quotes, reference):
    options = sorted((quote for quote in quotes if quote.get("price")), key=quote_order)
    candidates = [quote for quote in options if quote["verdict"] == "same_variant_candidate"]
    eligible = [quote for quote in candidates if quote["price_basis"]["quantity_eligible"] and Decimal(line["quantity"]) == Decimal(line["quantity"]).to_integral_value()]
    # Nu compară prețurile pe kg cu prețurile pe ambalaj pentru a declara un minim.
    group_options = comparable_groups(options)
    ranges = price_range(eligible)
    return {"line_id": line["id"], "description": line["description"], "quantity": line["quantity"],
            "reference_profile": reference, "options": options, "comparable_options": eligible,
            "conflicting_options": [quote for quote in options if quote["verdict"] == "variant_conflict"],
            "needs_details_options": [quote for quote in options if quote["verdict"] == "needs_details"],
            "price_min": ranges["minimum"], "price_max": ranges["maximum"], "price_spread": ranges["spread"],
            "best_option": eligible[0] if eligible else None, "groups": group_options,
            "warnings": (["Cantitatea de ambalaje trebuie să fie un număr întreg pentru estimare."] if Decimal(line["quantity"]) != Decimal(line["quantity"]).to_integral_value() else [])
                        + (["Nu există prețuri comparabile pe ambalaj pentru toate caracteristicile cerute."] if not eligible else [])}
