"""
Refresh everything from the brand adapters (manufacturers' own sites).

    python -m onroad.ingest                 # all brands, Hyderabad
    python -m onroad.ingest hyundai kia     # some brands
    python -m onroad.ingest --city Pune

A price row is written only when the price is new or changed, so the prices table doubles as price history.
A brand that fails keeps its previous data (marked with the error), so one broken site never empties the catalogue.
"""

import os
import argparse
import datetime as dt
import importlib
import json
import logging
import pkgutil
import re
from contextlib import closing

from . import db
from .sources import brands as brand_pkg
from .sources.base import NotSupported

log = logging.getLogger("onroad.ingest")


_MARKETING = re.compile(r"^(all[- ]new|the all[- ]new|the new|new)\s+", re.I)


def display_name(name: str) -> str:
    """'All New Seltos' -> 'Seltos', 'New Amaze' -> 'Amaze' (the brand sites prefix launch years with these)."""
    name = _MARKETING.sub("", name.strip()) or name
    # 'CRETA N LINE' -> 'Creta N Line', 'SCORPIO-N' -> 'Scorpio-N'; short codes and alphanumerics (XUV 3XO, EV6, OG) stay
    return re.sub(r"[A-Z]{4,}", lambda m: m.group(0).capitalize(), name)


# Body type when a brand's feed leaves it empty or uses its own label. Categories only (never prices); keyed by model key.
_BODY_ALIASES = {"cuv": "SUV", "crossover": "SUV", "suv coupe": "SUV", "van": "MUV", "mpv": "MUV", "roadster": "Convertible",
                 "spider": "Convertible", "cabriolet": "Convertible", "pick-up": "Pickup", "pickup truck": "Pickup"}
_KNOWN_BODY = {
    "magnite": "SUV", "magnite-kuro-special-edition": "SUV", "kuro": "SUV", "x-trail": "SUV", "tekton": "SUV", "gravite": "MUV",
    "duster": "SUV", "duster-strong-hybrid-e-tech-160": "SUV", "kiger": "SUV", "triber": "MUV", "kwid": "Hatchback",
    "octavia-rs": "Sedan", "mg-majestor": "SUV", "mg-cyberster": "Convertible", "mg-m9": "MUV",
    "eletre": "SUV", "emeya": "Sedan", "emira": "Coupe", "evija": "Coupe",
    "ferrari-luce": "SUV", "ferrari-12cilindri": "Coupe", "849-testarossa": "Coupe", "ferrari-amalfi": "Coupe",
    "296-gtb": "Coupe", "296-gts": "Convertible", "luce": "SUV", "12cilindri": "Coupe", "amalfi": "Coupe",
    "majestor": "SUV", "cyberster": "Convertible", "m9": "MUV",
}


def body_type(key: str, given: str | None) -> str | None:
    if given:
        g = given.strip()
        return _BODY_ALIASES.get(g.lower(), g if g[:1].isupper() else g.title())
    return _KNOWN_BODY.get(key)


NATIONAL = "India (national)"


def national_label(city: str) -> str:
    """Adapters spell a single all-India price list differently ('India', 'All India (national ex-showroom)'); store one label."""
    return NATIONAL if (city or "").strip().lower().startswith(("india", "all india")) else city

LUXURY = {"mercedes_benz", "bmw", "audi", "volvo", "lexus", "jaguar", "land_rover", "porsche", "mini", "lamborghini",
          "ferrari", "rolls_royce", "bentley", "maserati", "aston_martin", "mclaren", "lotus"}
PREMIUM = {"skoda", "volkswagen", "jeep", "byd", "toyota", "honda", "mg", "tesla", "vinfast"}


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def model_key(brand: str, name: str) -> str:
    """One key per real model however the brand's feeds spell it: 'New Nissan Magnite' / 'Magnite', 'Kiger PH2' / 'Kiger',
    'Renault Kwid' / 'Kwid', 'The new Taigun' / 'Taigun'."""
    n = display_name(name)
    for word in brand.split():                       # drop a leading brand name ('Nissan', 'Renault', 'MG' is kept: it is part of MG's names)
        if brand.lower() != "mg" and n.lower().startswith(word.lower() + " "):
            n = n[len(word) + 1:]
    n = re.sub(r"\s+ph\s?\d$", "", n, flags=re.I)   # Renault 'PH2' = phase-2 facelift of the same model
    return slugify(n)


def adapters(only: list[str] | None = None) -> list:
    out = []
    for mod in pkgutil.iter_modules(brand_pkg.__path__):
        if only and mod.name not in only and mod.name.replace("_", "-") not in only:
            continue
        try:
            m = importlib.import_module(f"{brand_pkg.__name__}.{mod.name}")
            if hasattr(m, "ADAPTER"):
                a = m.ADAPTER
                from .sources.brands._bd_fill import BD_BRAND, WithBikeDekho
                if getattr(a, "vehicle_type", "car") == "bike" and a.slug in BD_BRAND and os.environ.get("BIKEDEKHO_FILL", "1") != "0":
                    a = WithBikeDekho(a)             # models the maker's site doesn't give us, from BikeDekho
                out.append(a)
        except Exception as e:  # a broken adapter must not stop the others
            log.warning("cannot load adapter %s: %s", mod.name, e)
    return out


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def refresh_brand(a, city: str) -> dict:
    slug = a.slug or slugify(a.brand)
    res = {"brand": slug, "models": 0, "variants": 0, "price_changes": 0, "dealers": 0, "offers": 0, "unsupported": [], "errors": []}
    now = _now()
    with closing(db.connect()) as conn, conn:
        conn.execute("""INSERT INTO brands (slug, name, website, segment, vehicle_type) VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(slug) DO UPDATE SET name = excluded.name, website = excluded.website,
                                                        vehicle_type = excluded.vehicle_type""",
                     (slug, a.brand, a.website, "luxury" if slug in LUXURY else "premium" if slug in PREMIUM else "mass",
                      getattr(a, "vehicle_type", "car")))

    def step(name, fn):
        try:
            return fn()
        except NotSupported as e:
            res["unsupported"].append(f"{name}: {e}")
        except Exception as e:
            res["errors"].append(f"{name}: {type(e).__name__}: {str(e)[:160]}")
            log.warning("%s.%s failed: %s", slug, name, e)
        return None

    models = step("models", a.models) or []
    variants = step("prices", lambda: a.prices(city)) or []
    dealers = step("dealers", lambda: a.dealers(city)) or []
    offers = step("offers", lambda: a.offers(city))
    sf = step("specs", a.specs) if city == "Hyderabad" else None

    with closing(db.connect()) as conn, conn:
        known_models, by_url = {}, {}
        for m in models:
            key = model_key(a.brand, m["name"])
            mid = f"{slug}/{key}"
            known_models[key] = mid
            if m.get("url"):
                by_url.setdefault(m["url"].rstrip("/"), mid)
            conn.execute("""INSERT INTO models (id, brand_slug, name, slug, body_type, url, image_url, active, first_seen, last_seen)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                            ON CONFLICT(id) DO UPDATE SET name = excluded.name, body_type = COALESCE(excluded.body_type, models.body_type),
                                url = COALESCE(excluded.url, models.url), image_url = COALESCE(excluded.image_url, models.image_url),
                                active = 1, last_seen = excluded.last_seen""",
                         (mid, slug, display_name(m["name"]), key, body_type(key, m.get("body_type")), m.get("url"), m.get("image_url"), now, now))
        res["models"] = len(models)
        before = conn.execute("""SELECT COUNT(*) FROM variants WHERE active = 1
                                 AND model_id IN (SELECT id FROM models WHERE brand_slug = ?)""", (slug,)).fetchone()[0]
        # launch-city read worked: retire what the site no longer lists (re-activated below). A read that suddenly lists
        # under half of what was live is a site problem (a page blocked or half-loaded), not half the lineup discontinued:
        # nothing is retired then, and the run says so.
        if variants and city == "Hyderabad" and (before < 6 or len(variants) >= before * 0.5):
            conn.execute("UPDATE variants SET active = 0 WHERE model_id IN (SELECT id FROM models WHERE brand_slug = ?)", (slug,))
        elif variants and city == "Hyderabad":
            res.setdefault("errors", []).append(f"partial read: {len(variants)} variants vs {before} live; nothing retired")
        vid_names: dict[str, str] = {}
        for v in variants:
            key = model_key(a.brand, v.model)
            mid = known_models.get(key) or (v.model_url and by_url.get(v.model_url.rstrip("/"))) or f"{slug}/{key}"
            conn.execute("""INSERT INTO models (id, brand_slug, name, slug, body_type, url, image_url, active, first_seen, last_seen)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?) ON CONFLICT(id) DO UPDATE SET last_seen = excluded.last_seen,
                            body_type = COALESCE(models.body_type, excluded.body_type), image_url = COALESCE(models.image_url, excluded.image_url)""",
                         (mid, slug, display_name(v.model), key, body_type(key, v.body_type), v.model_url, v.image_url, now, now))
            vid = f"{mid}/{slugify(v.variant + ' ' + (v.fuel or '') + ' ' + (v.transmission or ''))}"
            if vid_names.setdefault(vid, v.variant) != v.variant:   # 'Pure' vs 'Pure +' slugify alike: keep the '+'
                vid = f"{mid}/{slugify(v.variant.replace('+', ' plus ') + ' ' + (v.fuel or '') + ' ' + (v.transmission or ''))}"
                vid_names.setdefault(vid, v.variant)
            conn.execute("""INSERT INTO variants (id, model_id, name, fuel, transmission, engine_cc, battery_kwh, seats, active, first_seen, last_seen, image_url)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                            ON CONFLICT(id) DO UPDATE SET image_url = COALESCE(excluded.image_url, variants.image_url),
                                engine_cc = COALESCE(excluded.engine_cc, variants.engine_cc),
                                battery_kwh = COALESCE(excluded.battery_kwh, variants.battery_kwh),
                                seats = COALESCE(excluded.seats, variants.seats), active = 1, last_seen = excluded.last_seen""",
                         (vid, mid, v.variant, v.fuel, v.transmission, v.engine_cc, v.battery_kwh, v.seats, now, now, v.image_url))
            v.city = national_label(v.city)
            last = conn.execute("SELECT ex_showroom_inr FROM prices WHERE variant_id = ? AND city = ? ORDER BY fetched_at DESC LIMIT 1",
                                (vid, v.city)).fetchone()
            # a changed price is written only when the next refresh returns the same new figure: some makers'
            # feeds intermittently serve an older list, and a one-off reading must not move the price buyers see
            if last and last["ex_showroom_inr"] != v.ex_showroom_inr:
                conn.execute("""CREATE TABLE IF NOT EXISTS price_pending (variant_id TEXT, city TEXT, ex_showroom_inr INTEGER,
                                source_url TEXT, first_seen TEXT, PRIMARY KEY (variant_id, city))""")
                pend = conn.execute("SELECT ex_showroom_inr FROM price_pending WHERE variant_id = ? AND city = ?", (vid, v.city)).fetchone()
                if not pend or pend[0] != int(v.ex_showroom_inr):
                    conn.execute("INSERT OR REPLACE INTO price_pending VALUES (?, ?, ?, ?, ?)",
                                 (vid, v.city, int(v.ex_showroom_inr), v.source_url, v.fetched_at))
                    continue
                conn.execute("DELETE FROM price_pending WHERE variant_id = ? AND city = ?", (vid, v.city))
            elif last:
                conn.execute("DELETE FROM price_pending WHERE variant_id = ? AND city = ?", (vid, v.city))                     if conn.execute("SELECT name FROM sqlite_master WHERE name = 'price_pending'").fetchone() else None
            if not last or last["ex_showroom_inr"] != v.ex_showroom_inr:
                conn.execute("INSERT OR IGNORE INTO prices (variant_id, city, ex_showroom_inr, source_url, fetched_at) VALUES (?, ?, ?, ?, ?)",
                             (vid, v.city, int(v.ex_showroom_inr), v.source_url, v.fetched_at))
                res["price_changes"] += 1
                if last and v.ex_showroom_inr < last["ex_showroom_inr"]:       # tell buyers who saved this car
                    try:
                        from . import push
                        push.price_dropped(conn, vid, v.city, int(last["ex_showroom_inr"]), int(v.ex_showroom_inr))
                    except Exception:
                        pass
        res["variants"] = len(variants)
        if (models or variants) and city == "Hyderabad":   # models neither listed nor priced any more drop out
            listed = set(known_models.values())
            for (mid,) in conn.execute("SELECT id FROM models WHERE brand_slug = ? AND active = 1", (slug,)).fetchall():
                has = conn.execute("SELECT 1 FROM variants WHERE model_id = ? AND active = 1", (mid,)).fetchone()
                if not has and mid not in listed:
                    conn.execute("UPDATE models SET active = 0 WHERE id = ?", (mid,))
        for d in dealers:
            did = f"{slug}/{slugify(d.name)}-{d.pincode or slugify(d.address)[:20]}"
            conn.execute("""INSERT INTO dealers (id, brand_slug, name, address, city, state, pincode, phone, email, lat, lng, kind, website,
                                source_url, fetched_at, active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                            ON CONFLICT(id) DO UPDATE SET address = excluded.address, phone = COALESCE(excluded.phone, dealers.phone),
                                email = COALESCE(excluded.email, dealers.email), lat = COALESCE(excluded.lat, dealers.lat),
                                lng = COALESCE(excluded.lng, dealers.lng), fetched_at = excluded.fetched_at, active = 1""",
                         (did, slug, d.name, d.address, d.city, d.state, d.pincode, d.phone, d.email, d.lat, d.lng, d.kind,
                          d.website, d.source_url, d.fetched_at))
        res["dealers"] = len(dealers)
        if offers is not None:   # replace this brand's site offers only when the read worked
            conn.execute("UPDATE offers SET active = 0 WHERE brand_slug = ? AND source = 'brand_site' AND (city = ? OR city IS NULL)", (slug, city))
            for o in offers:
                conn.execute("""INSERT INTO offers (brand_slug, model_name, title, amount_inr, details, valid_until, city, source, source_url,
                                    fetched_at, active, kind, conditions, valid_from, variant)
                                VALUES (?, ?, ?, ?, ?, ?, ?, 'brand_site', ?, ?, 1, ?, ?, ?, ?)""",
                             (slug, o.model, o.title, o.amount_inr, o.details, o.valid_until, o.city, o.source_url, o.fetched_at,
                              getattr(o, "kind", None), getattr(o, "conditions", None), getattr(o, "valid_from", None),
                              getattr(o, "variant", None)))
            res["offers"] = len(offers)
        if sf:
            specs, feats = sf
            vid_of = {}
            for (vid, mid, name, fuel, trans) in conn.execute(
                    "SELECT v.id, v.model_id, v.name, v.fuel, v.transmission FROM variants v JOIN models m ON m.id = v.model_id WHERE m.brand_slug = ?", (slug,)):
                vid_of[(mid, name.lower(), (fuel or "").lower(), (trans or "").lower())] = vid
                vid_of.setdefault((mid, name.lower(), "", ""), vid)

            def vid_for(x):
                mid = known_models.get(model_key(a.brand, x.model)) or f"{slug}/{model_key(a.brand, x.model)}"
                fu, tr = (x.fuel or "").lower(), (x.transmission or "").lower()
                hit = vid_of.get((mid, x.variant.lower(), fu, tr)) or vid_of.get((mid, x.variant.lower(), "", ""))
                if hit:
                    return hit
                # price name = spec name + edition suffix (e.g. "PURE PAMT" -> "PURE PAMT Standard"): accept only one match
                pre = x.variant.lower() + " "
                c = {v for (m_, n, f_, t_), v in vid_of.items() if m_ == mid and n.startswith(pre) and f_ == fu and t_ == tr}
                return c.pop() if len(c) == 1 else None
            n_s = n_f = 0
            for x in specs:
                vid = vid_for(x)
                if vid:
                    conn.execute("INSERT OR REPLACE INTO specs VALUES (?, ?, ?, ?, ?, ?, ?)",
                                 (vid, x.group, x.key, x.label, x.value, x.source_url, x.fetched_at)); n_s += 1
            touched = {vid_for(x) for x in feats} - {None}
            for vid in touched:
                conn.execute("DELETE FROM features WHERE variant_id = ?", (vid,))
            for x in feats:
                vid = vid_for(x)
                if vid:
                    conn.execute("INSERT OR REPLACE INTO features VALUES (?, ?, ?, ?, ?)", (vid, x.key, x.label, x.source_url, x.fetched_at)); n_f += 1
            res["specs"], res["features"] = n_s, n_f
        conn.execute("UPDATE models SET vehicle_type = ? WHERE brand_slug = ?", (getattr(a, "vehicle_type", "car"), slug))
        conn.execute("UPDATE brands SET last_refresh = ?, refresh_note = ? WHERE slug = ?",
                     (now, json.dumps({k: res[k] for k in ("unsupported", "errors")}), slug))
    return res


def run(only: list[str] | None = None, city: str = "Hyderabad") -> list[dict]:
    db.init()
    started = _now()
    out = [refresh_brand(a, city) for a in adapters(only)]
    with closing(db.connect()) as conn, conn:
        conn.execute("INSERT INTO refresh_runs (started, finished, summary) VALUES (?, ?, ?)", (started, _now(), json.dumps(out)))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("brands", nargs="*")
    ap.add_argument("--city", default="Hyderabad")
    args = ap.parse_args()
    for r in run(args.brands or None, args.city):
        print(json.dumps(r))
