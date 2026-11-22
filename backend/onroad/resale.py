"""
Resale value from today's used-car market, not a fixed depreciation table.

For a model and city it reads the live used listings on CarDekho (robots.txt allows /used-<brand>-<model>+cars+in+<city>
without a query string), takes each listing's asking price, model year and kilometres from the page's schema.org data,
and turns them into "share of today's new price kept after N years". The curve is a least-squares fit of
log(retention) against age, so a few odd listings don't swing it. Results are cached for a day per model and city.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import math
import re
import statistics

import httpx

from . import db
from .brochure_specs import UA

log = logging.getLogger("onroad.resale")
CACHE_HOURS = 24
BRAND_SLUG = {"maruti_suzuki": "maruti", "tata_motors": "tata", "mercedes_benz": "mercedes-benz", "land_rover": "land-rover",
              "mini": "mini", "bmw": "bmw", "mg": "mg"}


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def listing_urls(brand_slug: str, model_name: str, city: str) -> list[str]:
    b = BRAND_SLUG.get(brand_slug, _slug(brand_slug.replace("_", " ")))
    m = _slug(model_name)
    return [f"https://www.cardekho.com/used-{b}-{m}+cars+in+{_slug(city)}", f"https://www.cardekho.com/used-{b}-{m}+cars"]


def parse_listings(html: str, model_name: str) -> list[dict]:
    """schema.org Car entries -> [{year, km, price}] for this model only."""
    out, want = [], model_name.lower()
    for block in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html, re.S):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        stack = data if isinstance(data, list) else [data]
        while stack:
            d = stack.pop()
            if isinstance(d, list):
                stack.extend(d); continue
            if not isinstance(d, dict):
                continue
            if d.get("@type") == "Car":
                offer = d.get("offers") or {}
                offer = offer[0] if isinstance(offer, list) and offer else offer
                try:
                    price = int(float(offer.get("price")))
                    year = int(d.get("vehicleModelDate") or d.get("modelDate") or d.get("productionDate"))
                except (TypeError, ValueError, AttributeError):
                    continue
                km = (d.get("mileageFromOdometer") or {}).get("value") if isinstance(d.get("mileageFromOdometer"), dict) else None
                if want in str(d.get("name", "")).lower() and 20_000 < price < 50_000_000 and 1990 < year <= dt.date.today().year:
                    out.append({"year": year, "km": int(km) if str(km or "").isdigit() else None, "price": price})
            for v in d.values():
                if isinstance(v, (dict, list)):
                    stack.append(v)
    return out


def fit_curve(listings: list[dict], new_price: int, today: dt.date | None = None) -> dict | None:
    """Least-squares fit of ln(price / new price) = a + b * age. Needs two or more model years."""
    year_now = (today or dt.date.today()).year
    pts = [(max(year_now - l["year"], 0) + 0.5, l["price"] / new_price) for l in listings if new_price > 0]
    pts = [(a, r) for a, r in pts if 0.05 < r < 1.5]
    if len({round(a) for a, _ in pts}) < 2:
        return None
    # intercept pinned at the drive-off drop (a car is worth ~92% of ex-showroom once registered), slope fitted to the
    # market: listings mix base and top variants, so a free intercept drifts above 100% for young cars
    a = math.log(0.92)
    xs, ys = [x for x, _ in pts], [math.log(r) - a for _, r in pts]
    b = sum(x * y for x, y in zip(xs, ys)) / sum(x * x for x in xs)
    b = max(min(b, -0.03), -0.35)                   # every car loses value yearly; clamp a thin, odd sample
    keep = lambda yrs: math.exp(a + b * yrs)
    return {"keep": {str(y): round(keep(y), 3) for y in (1, 2, 3, 4, 5, 7)}, "per_year_loss_pct": round((1 - math.exp(b)) * 100, 1)}


def _model_new_price(conn, model_id: str, city: str) -> int | None:
    """Median of today's ex-showroom prices across the model's variants (city first, else any city)."""
    q = """SELECT p.ex_showroom_inr FROM variants v JOIN prices p ON p.variant_id = v.id
           WHERE v.model_id = ? AND v.active = 1 {city}
             AND p.fetched_at = (SELECT max(fetched_at) FROM prices WHERE variant_id = v.id AND city = p.city)"""
    for clause, args in (("AND lower(p.city) = lower(?)", (model_id, city)), ("", (model_id,))):
        vals = [r[0] for r in conn.execute(q.format(city=clause), args) if r[0]]
        if vals:
            return int(statistics.median(vals))
    return None


def market(model_id: str, city: str, fetch=None) -> dict:
    """Live used-market picture for one model in one city (cached a day)."""
    conn = db.connect()
    row = conn.execute("SELECT fetched_at, payload FROM resale_cache WHERE model_id = ? AND lower(city) = lower(?)", (model_id, city)).fetchone()
    if row and dt.datetime.fromisoformat(row[0]) > dt.datetime.utcnow() - dt.timedelta(hours=CACHE_HOURS):
        return json.loads(row[1])
    m = conn.execute("SELECT m.name, m.brand_slug FROM models m WHERE m.id = ?", (model_id,)).fetchone()
    if not m:
        return {"available": False, "reason": "Unknown model"}
    fetch = fetch or (lambda u: httpx.get(u, headers=UA, timeout=20, follow_redirects=True))
    listings, source = [], None
    for url in listing_urls(m[1], m[0], city):
        try:
            r = fetch(url)
            if r.status_code == 200:
                listings = parse_listings(r.text, m[0])
        except Exception as e:                                 # network trouble: say so, never invent numbers
            log.warning("resale fetch failed for %s: %s", url, type(e).__name__)
        if len(listings) >= 4:
            source = url
            break
    new_price = _model_new_price(conn, model_id, city)
    curve = fit_curve(listings, new_price) if new_price and listings else None
    by_year = {}
    for l in listings:
        by_year.setdefault(l["year"], []).append(l["price"])
    out = {"available": bool(curve), "model_id": model_id, "city": city, "listings": len(listings), "source_url": source,
           "fetched_at": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z", "new_price_inr": new_price,
           "by_year": [{"year": y, "median_inr": int(statistics.median(p)), "count": len(p)} for y, p in sorted(by_year.items(), reverse=True)],
           **(curve or {"reason": "Not enough live used listings for this model yet"})}
    conn.execute("INSERT OR REPLACE INTO resale_cache (model_id, city, fetched_at, payload) VALUES (?, ?, ?, ?)",
                 (model_id, city, dt.datetime.utcnow().isoformat(), json.dumps(out)))
    conn.commit()
    return out


def for_variant(variant_id: str, city: str, years: int = 3) -> dict:
    """Resale estimate for a specific variant after `years`, from the model's live market curve."""
    conn = db.connect()
    v = conn.execute("""SELECT v.model_id, p.ex_showroom_inr FROM variants v LEFT JOIN prices p ON p.variant_id = v.id
                        WHERE v.id = ? ORDER BY (lower(p.city) = lower(?)) DESC, p.fetched_at DESC LIMIT 1""", (variant_id, city)).fetchone()
    if not v:
        return {"available": False, "reason": "Unknown variant"}
    mk = market(v[0], city)
    if not mk.get("available") or not v[1]:
        return {**mk, "variant_id": variant_id}
    keep = {y: int(v[1] * k) for y, k in mk["keep"].items()}
    return {**mk, "variant_id": variant_id, "ex_showroom_inr": v[1], "years": years,
            "estimate_inr": keep.get(str(years)) or int(v[1] * math.exp(math.log(mk["keep"]["5"]) * years / 5.5)),
            "estimates": [{"years": int(y), "value_inr": val} for y, val in keep.items()]}
