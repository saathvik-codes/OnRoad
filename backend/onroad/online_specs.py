"""
Fallback spec sheets from public spec pages (CarDekho for cars, BikeDekho for two-wheelers) for models whose
manufacturer publishes no readable spec sheet (blocked sites, image-only brochures).

Rules, so the fallback never contradicts or invents:
  * only labels a variant has no row for yet are written (manufacturer data always wins and is never replaced);
  * every value passes the same per-spec checks as brochure_specs (unit + sane range);
  * the page shows one variant's engine: engine figures go only to variants with the same fuel and, where the variant's
    engine size is known, the same displacement (+-60 cc); dimensions go to every variant of the model;
  * the page must be about this model (its title names it), and robots.txt is respected (both sites allow /specs).
Rows keep the page URL as source_url, so the app can say where they came from.

    python -m onroad.online_specs jeep,citroen          # brands
"""
from __future__ import annotations

import json
import re
import sys
import time

import httpx

from . import db
from .brochure_specs import UA, _canon_label, canon, plausible

BRAND = {"maruti_suzuki": "maruti", "tata_motors": "tata", "land_rover": "land-rover", "force_motors": "force-motors",
         "mercedes_benz": "mercedes-benz", "honda_2wheelers": "honda", "suzuki_2wheelers": "suzuki", "royal_enfield": "royal-enfield",
         "harley_davidson": "harley-davidson", "ola_electric": "ola-electric", "bmw_motorrad": "bmw", "rolls_royce": "rolls-royce",
         "aston_martin": "aston-martin"}
# a model-level page reliably gives numbers; trim-dependent or descriptive rows (drive, gearbox, suspension, brakes) are
# left to the manufacturer
KEEP = {"Length", "Width", "Height", "Wheelbase", "Ground clearance", "Seat height", "Boot space", "Fuel tank", "Kerb weight",
        "Seating capacity", "Displacement", "Max power", "Max torque", "Cylinders", "Top speed", "Range", "Battery capacity", "Tyre size"}
ENGINE = {"Displacement", "Max power", "Max torque", "Cylinders", "Transmission", "Fuel tank", "Range", "Battery capacity", "Drive type"}


def read(html: str) -> tuple[dict, str | None, str]:
    """({label: (group, value)}, fuel shown on the page, page title)."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    for t in soup(["script", "style", "noscript", "svg"]):
        t.decompose()
    nodes = [re.sub(r"\s+", " ", s).strip() for s in soup.stripped_strings]
    out, seen_twice, fuel = {}, set(), None
    for i, n in enumerate(nodes):
        if re.fullmatch(r"fuel type", n, re.I) and i + 1 < len(nodes):
            fuel = fuel or nodes[i + 1].lower()
        if len(n) > 40 or not _canon_label(n):
            continue
        v = nodes[i + 1] if i + 1 < len(nodes) else ""
        got = canon("", n, v)
        if not got:
            continue
        g, label, value = got
        if label in out and out[label][1] != value:
            seen_twice.add(label)                            # two different values on one page: keep neither
        out.setdefault(label, (g, value))
    return {k: v for k, v in out.items() if k not in seen_twice}, fuel, title


def _fuel(s: str | None) -> str:
    s = (s or "").lower()
    return "electric" if "electric" in s else "diesel" if "diesel" in s else "cng" if "cng" in s else "petrol" if "petrol" in s else s


def run_model(c: httpx.Client, conn, model_id: str, vehicle_type: str) -> dict:
    brand, slug = model_id.split("/", 1)
    name = (conn.execute("SELECT name FROM models WHERE id = ?", (model_id,)).fetchone() or [""])[0]
    site = "https://www.bikedekho.com" if vehicle_type == "bike" else "https://www.cardekho.com"
    url = f"{site}/{BRAND.get(brand, brand.replace('_', '-'))}/{slug}/{'specifications' if vehicle_type == 'bike' else 'specs'}"
    r = c.get(url)
    if r.status_code != 200:
        return {"model": model_id, "url": url, "status": r.status_code}
    specs, page_fuel, title = read(r.text)
    words = [w for w in re.findall(r"[a-z0-9]+", name.lower()) if len(w) >= 2]
    if not words or not all(re.search(r"\b" + re.escape(w) + r"\b", title.lower()) for w in words):
        return {"model": model_id, "url": url, "skipped": f"page title is not this model: {title[:60]}"}
    disp = specs.get("Displacement", (None, ""))[1]
    page_cc = int(m.group(1)) if (m := re.match(r"(\d+) cc", disp)) else None
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    n = 0
    for v in conn.execute("SELECT id, fuel, engine_cc FROM variants WHERE model_id = ? AND COALESCE(active, 1) = 1", (model_id,)).fetchall():
        have = {_canon_label(x[0]) for x in conn.execute("SELECT label FROM specs WHERE variant_id = ?", (v[0],))}
        same_engine = (not page_fuel or _fuel(v[1]) == _fuel(page_fuel)) and \
                      (not v[2] or not page_cc or abs(v[2] - page_cc) <= 60)
        ev = _fuel(v[1]) == "electric"
        for label, (grp, value) in specs.items():
            if label not in KEEP or label in have or (label in ENGINE and not same_engine) or not plausible(label, value, vehicle_type):
                continue
            if label in ("Range", "Battery capacity") and not ev or label in ("Displacement", "Fuel tank", "Cylinders") and ev:
                continue
            key = "online_" + re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
            conn.execute("INSERT OR REPLACE INTO specs VALUES (?, ?, ?, ?, ?, ?, ?)", (v[0], grp, key, label, value, url, ts))
            n += 1
    return {"model": model_id, "url": url, "specs": list(specs), "fuel": page_fuel, "written": n}


def run(brands: list[str]) -> list[dict]:
    out = []
    with db.connect() as conn, httpx.Client(headers=UA, timeout=40, follow_redirects=True) as c:
        for b in brands:
            vt = (conn.execute("SELECT vehicle_type FROM brands WHERE slug = ?", (b,)).fetchone() or ["car"])[0] or "car"
            for (mid,) in conn.execute("""SELECT m.id FROM models m WHERE m.brand_slug = ? AND EXISTS (SELECT 1 FROM variants v
                                          WHERE v.model_id = m.id AND COALESCE(v.active,1) = 1
                                          AND (SELECT COUNT(*) FROM specs s WHERE s.variant_id = v.id) < 10)""", (b,)).fetchall():
                try:
                    out.append(run_model(c, conn, mid, vt))
                except Exception as e:
                    out.append({"model": mid, "error": str(e)[:120]})
                conn.commit()
                time.sleep(2)                                    # gentle: one page every two seconds
    return out


if __name__ == "__main__":
    for r in run(sys.argv[1].split(",")):
        print(json.dumps(r, ensure_ascii=False), flush=True)
