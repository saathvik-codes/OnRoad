"""
Buyer-profile recommender. Scores every priced variant against the buyer's profile using only OnRoad's own data:
on-road price for their city (onroad_calc), published mileage / range and equipment (specs, features), official crash
tests (data/research/crash_tests.json), sales rank (popularity.json). Best variant per model, ranked, with reasons
computed from those numbers. No brand gets a bonus for being a brand.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from . import db, onroad_calc

_BRAND_CAP = 2
SAFETY_KEYS = {"airbags_6": 3, "esc": 3, "adas": 3, "camera_360": 1, "isofix": 1, "tpms": 1, "hill_hold": 1, "rear_disc_brakes": 1,
               "abs_dual": 4, "abs_single": 2, "cbs": 1, "traction_control": 2}
CITY_KEYS = {"rear_camera", "camera_360", "auto_climate", "push_button_start", "keyless_entry", "rear_parking_sensors"}
HIGHWAY_KEYS = {"cruise_control", "adas", "led_headlamps", "tpms", "ventilated_seats"}


@dataclass
class Profile:
    vehicle_type: str = "car"
    city: str = "Hyderabad"
    budget: int | None = None                   # max ON-ROAD price the buyer wants to pay
    usage: str = "mixed"                         # city | highway | mixed
    monthly_km: int = 1000
    seats: int = 0                               # people to carry regularly (0 = don't care)
    fuel: str | None = None                      # Petrol | Diesel | CNG | Electric | Hybrid
    transmission: str | None = None              # Manual | Automatic
    home_charging: bool = False
    priorities: list[str] = field(default_factory=lambda: ["value", "safety"])   # value safety mileage features performance popular


def _num(text: str | None) -> float | None:
    m = re.search(r"\d+(?:\.\d+)?", text or "")
    return float(m.group()) if m else None


def _crash():
    f = db.ROOT / "data" / "research" / "crash_tests.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


def _norm(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def recommend(p: Profile, limit: int = 6) -> list[dict]:
    from .api import _engine_cc, _pick, _pop_for, _popularity, q   # reuse the API's price picking, ranks, engine-size inference
    cte, cp = _pick(p.city)
    rows = q(f"""WITH {cte}
                 SELECT v.id, v.name, v.fuel, v.transmission, v.seats, v.engine_cc, v.battery_kwh, v.image_url AS v_image,
                        m.id AS model_id, m.name AS model, m.body_type, m.image_url, b.name AS brand, b.slug AS brand_slug,
                        pk.ex_showroom_inr AS ex
                 FROM variants v JOIN models m ON m.id = v.model_id JOIN brands b ON b.slug = m.brand_slug
                 JOIN pick pk ON pk.variant_id = v.id
                 WHERE v.active = 1 AND m.active = 1 AND coalesce(b.vehicle_type, 'car') = ?""", (*cp, p.vehicle_type))
    if not rows:
        return []
    ids = [r["id"] for r in rows]
    feats: dict[str, set] = {}
    for vid, key in db.connect().execute(f"SELECT variant_id, key FROM features WHERE variant_id IN ({','.join('?' * len(ids))})", ids):
        feats.setdefault(vid, set()).add(key)
    eff: dict[str, float] = {}
    for vid, key, val in db.connect().execute(
            f"SELECT variant_id, key, value FROM specs WHERE key IN ('mileage_arai','fuel_efficiency','range') AND variant_id IN ({','.join('?' * len(ids))})", ids):
        n = _num(val)
        if n:
            eff[vid] = n
    seats_spec: dict[str, int] = {}
    for vid, val in db.connect().execute(
            f"SELECT variant_id, value FROM specs WHERE key = 'seating_capacity' AND variant_id IN ({','.join('?' * len(ids))})", ids):
        n = _num(val)
        if n:
            seats_spec[vid] = int(n)
    pop = _popularity()
    crash = _crash()

    def stars(brand, model):
        b, m = _norm(brand), _norm(model)
        best = [r.get("adult_stars") for r in crash if _norm(r.get("brand"))[:4] == b[:4] and _norm(r.get("model"))
                and (m.startswith(_norm(r.get("model"))) or _norm(r.get("model")).startswith(m)) and r.get("adult_stars") is not None]
        return max(best) if best else None

    cands = []
    for r in rows:
        if p.fuel and (r["fuel"] or "").lower() != p.fuel.lower():
            continue
        if p.transmission and ((r["transmission"] or "").lower() == "manual") != (p.transmission.lower() == "manual"):
            continue
        seats = r["seats"] or seats_spec.get(r["id"])
        if p.seats > 5 and not (seats or 0) >= p.seats and not (seats is None and (r["body_type"] or "") == "MUV"):
            continue                                  # needs 6+ seats: published seat count, else MUVs only
        if p.seats and seats and seats < p.seats:
            continue
        name_seats = re.search(r"\((\d+)\s*\+\s*D\)", r["name"] or "")     # Force-style "(12+D)" = 12 passengers + driver
        if p.vehicle_type == "car" and name_seats and int(name_seats.group(1)) + 1 > max(p.seats, 7) + 2:
            continue
        if (r["fuel"] or "").lower() == "electric" and not p.home_charging and p.vehicle_type == "car" and p.fuel != "Electric":
            continue                                  # EV without home charging: only when explicitly asked for
        b = onroad_calc.estimate(r["ex"], city=p.city, fuel=r["fuel"], engine_cc=_engine_cc(r), battery_kwh=r["battery_kwh"])
        r["onroad"] = b.total_inr - b.refundable_inr
        if p.budget and r["onroad"] > p.budget * 1.05:
            continue
        r["feats"] = feats.get(r["id"], set())
        r["eff"] = eff.get(r["id"])
        r["stars"] = stars(r["brand"], r["model"])
        pm = _pop_for(pop, _norm(r["brand"]), _norm(r["model"]), r["model"])
        r["rank"] = pm["rank"] if pm else None
        cands.append(r)
    if not cands:
        return []
    base: dict[tuple, tuple] = {}                         # (brand, rank) -> cheapest model of that family
    for c in cands:
        if c["rank"]:
            k = (c["brand_slug"], c["rank"])
            if k not in base or c["ex"] < base[k][1]:
                base[k] = (c["model_id"], c["ex"])
    for c in cands:
        if c["rank"] and base[(c["brand_slug"], c["rank"])][0] != c["model_id"]:
            c["rank"] = None

    # percentiles within the buyer's candidate pool, so scores are relative to what they can actually buy
    def pct(vals, v):
        vals = sorted(x for x in vals if x is not None)
        return None if v is None or not vals else sum(1 for x in vals if x <= v) / len(vals)
    effs = [c["eff"] for c in cands]
    # with only a handful of published figures, rewarding them would just favour the few brands that publish mileage
    use_eff = sum(1 for e in effs if e is not None) >= max(5, 0.3 * len(cands))
    use_perf = "performance" in p.priorities or p.usage == "highway"
    fcount = [len(c["feats"]) for c in cands if c["feats"]]          # brands without equipment data: unknown, not zero
    ccs = [c["engine_cc"] or c["battery_kwh"] for c in cands]
    order = {k: i for i, k in enumerate(p.priorities)}              # first priority counts most
    w = {k: (3.0 if order.get(k) == 0 else 2.0 if k in order else 1.0)
         for k in ("value", "safety", "mileage", "features", "performance", "popular")}

    for c in cands:
        parts, why = {}, []
        if p.budget:
            gap = p.budget - c["onroad"]
            ratio = c["onroad"] / p.budget
            # 70-100 % of the budget is a full-value fit; cheaper still fine (down to 0.5 at 30 %); over budget costs points
            parts["value"] = (1.0 if 0.7 <= ratio <= 1.0 else 0.5 + (ratio - 0.3) / 0.4 * 0.5 if 0.3 <= ratio < 0.7
                              else 0.5 if ratio < 0.3 else max(0.0, 1 - (ratio - 1) * 8))
            why.append(f"On-road ₹{c['onroad'] / 1e5:.2f} L in {p.city}" + (f", ₹{gap / 1e3:,.0f}k under your budget" if gap >= 1000
                       else ", right at your budget" if gap >= 0 else f", ₹{-gap / 1e3:,.0f}k over budget"))
        sp = SAFETY_KEYS and sum(v for k, v in SAFETY_KEYS.items() if k in c["feats"]) / 8
        star_part = c["stars"] / 5 if c["stars"] is not None else 0.5        # untested: neutral, not zero
        parts["safety"] = min(1.0, star_part * 0.8 + min(sp, 1) * 0.2)
        warn = []
        if c["stars"] is not None and c["stars"] >= 4:
            why.append(f"{c['stars']}★ adult crash rating (official NCAP)")
        elif c["stars"] is not None and c["stars"] <= 3:
            warn.append(f"Only {c['stars']}★ adult crash rating (official NCAP)")
        ep = pct(effs, c["eff"]) if use_eff else None
        if ep is not None:
            parts["mileage"] = ep
            if ep >= 0.7:
                unit = "km range" if (c["fuel"] or "").lower() == "electric" else "km/l"
                why.append(f"{c['eff']:g} {unit}: top {round((1 - ep) * 100) or 1}% for efficiency in your budget")
        fp = pct(fcount, len(c["feats"])) if c["feats"] else None
        if fp is not None:
            parts["features"] = fp
            if fp >= 0.75 and len(c["feats"]) >= 10:
                why.append(f"{len(c['feats'])} listed features, more than most options at this price")
        cp_ = pct(ccs, c["engine_cc"] or c["battery_kwh"])
        if cp_ is not None and use_perf:
            parts["performance"] = cp_
        if c["rank"]:
            parts["popular"] = max(0.0, 1 - c["rank"] / 60)
            if c["rank"] <= 15:
                why.append(f"#{c['rank']} best-selling in India (wide service network, strong resale)")
        # usage fit
        u = 0.5
        if p.vehicle_type == "bike":
            u = 0.5 + (0.3 * (cp_ or 0) if p.usage == "highway" else 0)
        elif p.usage == "city":
            u = 0.4 + 0.15 * len(c["feats"] & CITY_KEYS) / 3 + (0.2 if (c["transmission"] or "").lower() != "manual" else 0) \
                + (0.2 if (c["fuel"] or "").lower() in ("cng", "electric", "hybrid", "strong hybrid") else 0)
        elif p.usage == "highway":
            u = 0.4 + 0.2 * len(c["feats"] & HIGHWAY_KEYS) / 3 + (0.3 * (cp_ or 0))
        parts["usage"] = min(1.0, u)
        if p.monthly_km >= 1500 and (c["fuel"] or "").lower() in ("diesel", "cng", "electric", "hybrid", "strong hybrid"):
            why.append(f"{c['fuel']} suits your {p.monthly_km:,} km a month")
        total_w = sum(w.get(k, 1.5) for k in parts)
        c["score"] = round(100 * sum(v * w.get(k, 1.5) for k, v in parts.items()) / total_w)
        if c["stars"] is not None and c["stars"] < 4:
            # a weak official rating always counts; much more for buyers who put safety first
            c["score"] = round(c["score"] * ((0.75 if c["stars"] <= 2 else 0.85) if "safety" in p.priorities else (0.85 if c["stars"] <= 2 else 0.95)))
        c["why"] = why[:4]
        c["warn"] = warn

    best: dict[str, dict] = {}
    for c in cands:                                       # best variant per model
        if c["model_id"] not in best or c["score"] > best[c["model_id"]]["score"]:
            best[c["model_id"]] = c
    def family(c):
        first = re.sub(r"[^a-z0-9]", "", (c["model"] or "").lower().split()[0] if c["model"] else "")
        return (c["brand_slug"], re.sub(r"[a-z]+$", "", first) or first)     # "cb350c" -> "cb350", "xuv700" stays
    ranked, fams, per_brand = [], set(), {}
    for c in sorted(best.values(), key=lambda c: -c["score"]):
        f = family(c)
        if f in fams or per_brand.get(c["brand_slug"], 0) >= _BRAND_CAP:
            continue
        fams.add(f); per_brand[c["brand_slug"]] = per_brand.get(c["brand_slug"], 0) + 1
        ranked.append(c)
        if len(ranked) == limit:
            break
    return [{"model_id": c["model_id"], "brand": c["brand"], "model": c["model"], "variant": c["name"], "variant_id": c["id"],
             "fuel": c["fuel"], "transmission": c["transmission"], "onroad_inr": c["onroad"], "image_url": c["v_image"] or c["image_url"],
             "score": c["score"], "reasons": c["why"], "warnings": c["warn"], "crash_stars": c["stars"], "efficiency": c["eff"],
             "features": len(c["feats"])}
            for c in ranked]
