"""
One model, one listing. A maker's site can list a model without a price ("XSR155", "MT 15 V2") while the fallback
source lists the same model with prices under a slightly different name ("XSR 155", "MT 15 Version 2.0"). The unpriced
listing is retired when a priced listing of the same brand matches it by name or page address; the priced one stays.
Runs before every snapshot.
"""
from __future__ import annotations

import re

NOISE = r"(?:new|all ?new|the|versions?|v ?\d(?:\.\d)?|20\d\d|\d\.0)"


def _compact(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _keys(name: str, url: str | None, brand: str) -> set[str]:
    slug = re.sub(r"\.html?$", "", (url or "").rstrip("/").rsplit("/", 1)[-1].lower())
    out = set()
    for raw in (name, slug):
        k = _compact(re.sub(NOISE, " ", raw.lower().replace(brand.lower(), " ")))
        k = re.sub(r"^(?:" + "|".join(map(re.escape, (brand.lower().replace("_", ""), "yamaha", "honda", "tvs", "bajaj", "hero"))) + ")", "", k)
        if len(k) >= 3:
            out.add(k)
    return out


def _same(a: set[str], b: set[str]) -> bool:
    return bool(a & b) or any(len(x) >= 6 and len(y) >= 6 and (x in y or y in x) and abs(len(x) - len(y)) <= 6 for x in a for y in b)


def dedupe(conn, dry_run: bool = False) -> list[tuple[str, str]]:
    rows = conn.execute("""SELECT m.id, m.brand_slug, m.name, m.url,
                                  (SELECT COUNT(*) FROM variants v WHERE v.model_id = m.id AND v.active = 1
                                   AND EXISTS (SELECT 1 FROM prices p WHERE p.variant_id = v.id)) AS priced
                           FROM models m WHERE m.active = 1""").fetchall()
    by_brand: dict[str, list] = {}
    for mid, b, name, url, priced in rows:
        by_brand.setdefault(b, []).append((mid, _keys(name, url, b), priced))
    retired = []
    for b, ms in by_brand.items():
        for mid, keys, priced in ms:
            if priced:
                continue
            twin = next((m2 for m2, k2, p2 in ms if p2 and m2 != mid and _same(keys, k2)), None)
            if twin:
                retired.append((mid, twin))
                if not dry_run:
                    conn.execute("UPDATE models SET active = 0 WHERE id = ?", (mid,))
    return retired
