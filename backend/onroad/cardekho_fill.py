"""
Completes every car brand's line-up and prices from CarDekho where the maker's own site falls short: a model on sale
that the maker lists without a price (Maruti Eeco, Nissan X-Trail...), or a current model the maker's site doesn't
list at all. The maker's data always wins; CarDekho rows carry CarDekho's (New Delhi) ex-showroom price and its URL
as the source, so the app can say where a figure came from. Upcoming and discontinued models are never added: only the
brand page's current-models list (its "Product" entries, which carry a price) is used. robots.txt allows these pages.

    python -m onroad.cardekho_fill [brand,brand]     # dry run prints what would be added; --write to save
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
import time

import httpx

from . import db
from .brochure_specs import UA
from .ingest import slugify

BRAND_PAGE = {"maruti_suzuki": "Maruti", "tata_motors": "Tata", "mahindra": "Mahindra", "hyundai": "Hyundai", "kia": "Kia",
              "toyota": "Toyota", "honda": "Honda", "mg": "MG", "skoda": "Skoda", "volkswagen": "Volkswagen", "renault": "Renault",
              "nissan": "Nissan", "citroen": "Citroen", "jeep": "Jeep", "byd": "BYD", "force_motors": "Force-Motors",
              "isuzu": "Isuzu", "land_rover": "Land-Rover", "lexus": "Lexus", "porsche": "Porsche", "volvo": "Volvo",
              "audi": "Audi", "bmw": "BMW", "mercedes_benz": "Mercedes-Benz", "mini": "Mini", "jaguar": "Jaguar"}
FUEL = [("Electric", r"\bev\b|electric|kwh|long range|\blr\b"), ("Diesel", r"diesel|crdi|\bd\b|tdi|mhawk"),
        ("CNG", r"\bcng\b"), ("Strong Hybrid", r"strong hybrid|e-?hev|hybrid"), ("Petrol", r".")]


def _ld(html: str) -> list[dict]:
    out = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            d = json.loads(m.group(1))
        except Exception:
            continue
        out.extend(d if isinstance(d, list) else [d])
    return out


def current_models(c: httpx.Client, brand_page: str) -> list[dict]:
    """(name, url, price) of each model on sale, from the brand page's Product entries."""
    out = []
    for d in _ld(c.get(f"https://www.cardekho.com/cars/{brand_page}").text):
        if d.get("@type") != "ItemList":
            continue
        for li in d.get("itemListElement") or []:
            it = li.get("Item") or li.get("item") or {}
            if it.get("@type") == "Product" and it.get("name") and it.get("url"):
                img = it.get("image")
                out.append({"name": it["name"], "url": it["url"], "image": img[0] if isinstance(img, list) else img})
    return out


def variants(c: httpx.Client, model_url: str) -> list[dict]:
    t = c.get(model_url).text
    seen, out = set(), []
    for m in re.finditer(r'"@type":"Product","name":"([^"]+)","sku":"[^"]*","url":"(https://www\.cardekho\.com/overview/[^"]+)"'
                         r'[^}]*?"offers":\{[^}]*?"price":"?(\d+)', t):
        name, url, price = m.group(1), m.group(2), int(m.group(3))
        if url in seen or price < 100_000:
            continue
        seen.add(url)
        out.append({"name": name, "url": url, "price": price})
    return out


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", re.sub(r"^(new|the)\s+", "", (s or "").lower()))


def run(brands: list[str] | None = None, write: bool = False) -> list[dict]:
    db.init()
    log = []
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    with db.connect() as conn, httpx.Client(headers=UA, timeout=40, follow_redirects=True) as c:
        for slug, page in BRAND_PAGE.items():
            if brands and slug not in brands:
                continue
            bname = (conn.execute("SELECT name FROM brands WHERE slug = ?", (slug,)).fetchone() or [None])[0]
            if not bname:
                continue
            # "priced" counts only the maker's own prices: models we priced from CarDekho are refreshed on every run
            ours = {r["id"]: r for r in conn.execute("""SELECT m.id, m.name, m.active, (SELECT COUNT(*) FROM variants v JOIN prices p ON p.variant_id = v.id
                                                         WHERE v.model_id = m.id AND v.active = 1 AND p.source_url NOT LIKE 'https://www.cardekho.com/%') AS priced
                                                         FROM models m WHERE m.brand_slug = ?""", (slug,))}
            try:
                cur = current_models(c, page)
            except Exception as e:
                log.append({"brand": slug, "error": str(e)[:80]}); continue
            from .model_dedupe import _keys, _same
            for cm in cur:
                short = re.sub(rf"^{re.escape(bname)}\s+|^{re.escape(bname.split()[0])}\s+", "", cm["name"], flags=re.I).strip()
                cd_slug = cm["url"].rstrip("/").rsplit("/", 1)[-1].lower()
                ck = _keys(short, cm["url"], slug)
                match = next((r for r in ours.values() if r["id"].split("/", 1)[1] == cd_slug
                              or _norm(r["name"]) in (_norm(short), _norm(bname + short))), None)                     or next((r for r in ours.values() if _same(ck, _keys(r["name"], r["id"].split("/", 1)[1], slug))), None)
                if re.search(r"\btour\b|xpres|\bprime\b|yodha|pick-?up|s-?cab|\bd-?max\b|\bcargo\b|ambulance", short, re.I):
                    continue                                   # taxi, fleet and commercial vehicles are out of scope
                words = lambda x: {w for w in re.findall(r"[a-z0-9]+", x.lower()) if w not in ("ev", "electric", "new", "the")}
                if not match:                                  # "Taisor" is our "Urban Cruiser Taisor", "LX" our "LX 500d"
                    cw = words(short)
                    match = next((r for r in ours.values() if cw and (cw <= words(r["name"]) or words(r["name"]) <= cw)), None)
                if match and not match["active"]:
                    continue                                   # the maker has retired it: theirs wins
                if match and match["priced"]:
                    continue                                   # the maker's prices are there: nothing to do
                time.sleep(1.2)
                vs = variants(c, cm["url"])
                if not vs:
                    log.append({"brand": slug, "model": short, "skipped": "no priced variants on CarDekho"}); continue
                mid = match["id"] if match else f"{slug}/{slugify(short)}"
                log.append({"brand": slug, "model": short, "id": mid, "new_model": not match, "variants": len(vs)})
                if not write:
                    continue
                conn.execute("""INSERT INTO models (id, brand_slug, name, slug, url, image_url, active, first_seen, last_seen)
                                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?) ON CONFLICT(id) DO UPDATE SET active = 1, last_seen = excluded.last_seen,
                                image_url = COALESCE(models.image_url, excluded.image_url)""",
                             (mid, slug, short if not match else match["name"], mid.split("/", 1)[1], cm["url"], cm.get("image"), now, now))
                for v in vs:
                    vname = re.sub(rf"^{re.escape(cm['name'])}\s*|^{re.escape(bname)}\s+{re.escape(short)}\s*", "", v["name"], flags=re.I).strip() or "Standard"
                    fuel = next(f for f, rx in FUEL if re.search(rx, v["name"], re.I))
                    trans = "Automatic" if re.search(r"\b(at|amt|ags|cvt|dct|dsg|ivt|automatic|tc)\b", v["name"], re.I) or fuel == "Electric" else "Manual"
                    vid = f"{mid}/{slugify(vname + ' ' + fuel + ' ' + trans)}"
                    conn.execute("""INSERT INTO variants (id, model_id, name, fuel, transmission, active, first_seen, last_seen)
                                    VALUES (?, ?, ?, ?, ?, 1, ?, ?) ON CONFLICT(id) DO UPDATE SET active = 1, last_seen = excluded.last_seen""",
                                 (vid, mid, vname, fuel, trans, now, now))
                    last = conn.execute("SELECT ex_showroom_inr FROM prices WHERE variant_id = ? AND city = 'Delhi' ORDER BY fetched_at DESC LIMIT 1",
                                        (vid,)).fetchone()
                    if not last or last[0] != v["price"]:
                        conn.execute("INSERT OR IGNORE INTO prices (variant_id, city, ex_showroom_inr, source_url, fetched_at) VALUES (?, 'Delhi', ?, ?, ?)",
                                     (vid, v["price"], v["url"], now))
                conn.commit()
    return log


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    for r in run(args[0].split(",") if args else None, write="--write" in sys.argv):
        print(json.dumps(r))
