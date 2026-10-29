"""
After-the-price help for one variant in one city: insurance, registration (RTA), accessories, and what changed.
Everything here is either computed from the verified rules file (data/research/onroad_rules.json), read from our own
catalogue, or a link to an official / regulated source. No partner claims, no invented ratings or discounts.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from . import db, onroad_calc

ACCESSORIES = Path(__file__).resolve().parents[2] / "data" / "research" / "accessories.json"

# official car / two-wheeler insurance quote pages (checked 2026-10-29). Listed alphabetically, no ranking, no
# commission: OnRoad has no tie-up with any of them.
# Official car / two-wheeler insurance pages, logos from each insurer's own site and the cashless-garage count each
# states there (checked 2026-10-29). Listed alphabetically, no ranking, no commission: OnRoad has no tie-up with any.
INSURERS = {
    "car": [
        {"name": "Acko", "url": "https://www.acko.com/car-insurance/", "logo": "ins_acko", "logo_dark": True,
         "garages": "4,000+", "stated_on": "https://www.acko.com/car-insurance/"},
        {"name": "Bajaj General", "url": "https://www.bajajgeneralinsurance.com/motor-insurance/car-insurance-online.html", "logo": "ins_bajaj_general",
         "garages": "10,000+", "stated_on": "https://www.bajajgeneralinsurance.com/motor-insurance/car-insurance-online.html"},
        {"name": "Digit", "url": "https://www.godigit.com/motor-insurance/car-insurance", "logo": "ins_digit",
         "garages": "10,000+", "stated_on": "https://www.godigit.com/motor-insurance/car-insurance"},
        {"name": "HDFC ERGO", "url": "https://www.hdfcergo.com/car-insurance", "logo": "ins_hdfc_ergo",
         "garages": "8,500+", "stated_on": "https://www.hdfcergo.com/car-insurance"},
        {"name": "ICICI Lombard", "url": "https://www.icicilombard.com/motor-insurance/car-insurance", "logo": None, "garages": None, "stated_on": None},
        {"name": "Tata AIG", "url": "https://www.tataaig.com/motor-insurance/car-insurance", "logo": "ins_tata_aig",
         "garages": "5,700+", "stated_on": "https://www.tataaig.com/motor-insurance/car-insurance"},
    ],
    "bike": [
        {"name": "Acko", "url": "https://www.acko.com/two-wheeler-insurance/", "logo": "ins_acko", "logo_dark": True, "garages": None, "stated_on": None},
        {"name": "Digit", "url": "https://www.godigit.com/motor-insurance/two-wheeler-insurance", "logo": "ins_digit", "garages": None, "stated_on": None},
        {"name": "Tata AIG", "url": "https://www.tataaig.com/motor-insurance/two-wheeler-insurance", "logo": "ins_tata_aig", "garages": None, "stated_on": None},
    ],
}
COMPARE = {
    "car": [("InsuranceDekho", "https://www.insurancedekho.com/car-insurance"),
            ("Policybazaar", "https://www.policybazaar.com/motor-insurance/car-insurance/")],
    "bike": [("Policybazaar", "https://www.policybazaar.com/motor-insurance/two-wheeler-insurance/")],
}
INSURANCE_TIPS = [
    "You can buy the policy yourself; a dealer cannot make its own insurance a condition of sale. Ask for the dealer's "
    "quote, then compare it with two or three insurers for the same IDV and add-ons.",
    "Compare like for like: the same IDV (insured value), zero-depreciation and engine-protect add-ons, and the same "
    "deductible. A lower premium with a lower IDV pays out less after an accident.",
    "Selling or replacing an older vehicle? Your no-claim bonus belongs to you, not the car. Ask your insurer for an "
    "NCB certificate and carry it to the new policy.",
    "Third-party cover for a new car is fixed by the government for every insurer; only the own-damage part differs.",
]


def stable(rows: list[dict]) -> list[dict]:
    """Price readings for one (variant, city), oldest first, without flip-flops: a reading the maker's feed later
    reverses (A -> B -> A) was a glitch, not a price change, so it is dropped; consecutive repeats merge."""
    vals = [r["ex_showroom_inr"] for r in rows]
    out: list[dict] = []
    for i, r in enumerate(rows):
        if out and r["ex_showroom_inr"] == out[-1]["ex_showroom_inr"]:
            continue
        if out and out[-1]["ex_showroom_inr"] in vals[i + 1:]:     # the earlier value comes back: not a real change
            continue
        if out and r["ex_showroom_inr"] in vals[:i]:              # swinging back to a value already seen: a flip-flop
            continue
        out.append(r)
    return out


def _q(sql: str, params: tuple = ()) -> list[dict]:
    with db.connect() as conn:
        return [dict(r) for r in conn.execute(sql, params)]


def _accessories(brand_slug: str) -> dict | None:
    try:
        a = json.loads(ACCESSORIES.read_text(encoding="utf-8")).get(brand_slug) or {}
    except Exception:
        return None
    return {"url": a.get("url"), "checked": a.get("checked")} if a.get("url") else None


def _items(model_id: str) -> list[dict]:
    from contextlib import closing
    from . import accessories
    with closing(db.connect()) as conn:
        return accessories.for_model(conn, model_id)


def _rta(state: str, breakdown: dict, vehicle_type: str) -> dict:
    r = onroad_calc.rules()
    sr = (r.get("states") or {}).get(state) or {}
    tax = [l for l in breakdown["lines"] if "tax" in l["label"].lower() or "cess" in l["label"].lower()]
    reg = [l for l in breakdown["lines"] if any(w in l["label"].lower() for w in ("registration", "smart card", "hypothecation", "rc "))]
    ev = sr.get("ev") if isinstance(sr.get("ev"), dict) else None
    steps = [
        "The dealer applies for registration online through Vahan before delivery and must hand you a temporary "
        "registration (TR) if the vehicle leaves the showroom unregistered.",
        "Keep these ready: Aadhaar or other address proof, PAN (or Form 60), passport photos, and, for a loan, the "
        "lender's Form 34 for the hypothecation entry.",
        "Road tax is paid once, at registration, to the state; ask for the Vahan receipt, not a dealer slip.",
        "The high-security number plate (HSRP) is fitted by the dealer and its cost is already in the vehicle price.",
        "Your RC arrives as a smart card by post; you can track the application on Parivahan with the application number.",
    ]
    return {
        "state": sr.get("name", state), "coverage": sr.get("coverage", "not_found"),
        "road_tax_basis": sr.get("road_tax_basis"), "fuel_differential": sr.get("fuel_differential"),
        "second_vehicle_rule": sr.get("second_vehicle_rule"),
        "ev": {k: ev.get(k) for k in ("life_tax_exempt", "registration_fee_exempt", "order", "valid_to", "conditions") if k in ev} if ev else None,
        "charges": [{"label": l["label"], "amount_inr": l["amount_inr"], "basis": l["basis"]} for l in tax + reg],
        "steps": steps,
        "not_allowed": [d for d in (r.get("disallowed_charges") or []) if d.get("allowed") is False],
        "optional": [d for d in (r.get("disallowed_charges") or []) if d.get("allowed") == "optional"],
        "sources": [s for s in (sr.get("sources") or []) if isinstance(s, dict)][:4],
        "links": [{"title": "Parivahan: registration status and services", "url": "https://parivahan.gov.in/"},
                  {"title": "Book or track an HSRP plate", "url": "https://bookmyhsrp.com/"}],
        "as_of": r.get("as_of"),
    }


def ownership(variant: dict, model: dict, city: str, breakdown: dict) -> dict:
    vt = "bike" if (model.get("vehicle_type") or "car") in ("bike", "two_wheeler") else "car"
    ins = [l for l in breakdown["lines"] if l["label"].lower().startswith("insurance")]
    state = breakdown.get("state") or "TS"
    return {
        "insurance": {
            "lines": [{"label": l["label"], "amount_inr": l["amount_inr"], "basis": l["basis"], "verified": l["verified"]} for l in ins],
            "tips": INSURANCE_TIPS,
            "insurers": [{**i, "logo_url": f"/api/logos/{i['logo']}" if i.get("logo") else None} for i in INSURERS[vt]],
            "compare": [{"name": n, "url": u} for n, u in COMPARE[vt]],
            "regulator": {"name": "IRDAI", "url": "https://irdai.gov.in/"},
            "disclosure": "OnRoad has no tie-up with these insurers and earns nothing from them. Listed alphabetically.",
        },
        "rta": _rta(state, breakdown, vt),
        "accessories": {
            "items": _items(model["id"]),
            "official": _accessories(model["brand_slug"]),
            "advice": [
                "Genuine accessories fitted at the dealer keep the warranty intact; ask for the itemised price list "
                "and buy only what you want. An accessory pack cannot be made a condition of sale.",
                "Ask the dealer to note fitted accessories on the invoice so they are covered by insurance.",
            ],
        },
        "updates": updates(model_id=model["id"], limit=8),
    }


def updates(vehicle_type: str | None = None, model_id: str | None = None, limit: int = 40, days: int = 120) -> list[dict]:
    """What changed, from our own records: price revisions, new models, and offers that started recently."""
    since = (dt.datetime.utcnow() - dt.timedelta(days=days)).strftime("%Y-%m-%d")
    out: list[dict] = []
    cond, params = "", ()
    if model_id:
        cond, params = " AND m.id = ?", (model_id,)
    elif vehicle_type:
        cond, params = " AND coalesce(m.vehicle_type, 'car') = ?", ("bike" if vehicle_type in ("bike", "two_wheeler") else "car",)
    # price revisions: consecutive different Hyderabad (or national) prices for a variant
    rows = _q(f"""SELECT p.variant_id, p.ex_showroom_inr, p.fetched_at, p.source_url, p.city, v.name AS variant, m.id AS model_id,
                         m.name AS model, b.name AS brand, m.image_url
                  FROM prices p JOIN variants v ON v.id = p.variant_id JOIN models m ON m.id = v.model_id JOIN brands b ON b.slug = m.brand_slug
                  WHERE v.active = 1 AND m.active = 1 AND p.city IN ('Hyderabad', 'India (national)') {cond}
                  ORDER BY p.variant_id, p.city, p.fetched_at""", params)
    seqs: dict = {}
    for r in rows:
        seqs.setdefault((r["variant_id"], r["city"]), []).append(r)
    by_model: dict = {}
    for seq in seqs.values():
        clean = stable(seq)
        for prev, r in zip(clean, clean[1:]):
            if r["ex_showroom_inr"] and prev["ex_showroom_inr"] and r["fetched_at"][:10] >= since:
                g = by_model.setdefault((r["model_id"], r["fetched_at"][:10]), {"r": r, "changes": []})
                g["changes"].append((r["variant"], prev["ex_showroom_inr"], r["ex_showroom_inr"]))
    for (mid, day), g in by_model.items():
        r, ch = g["r"], g["changes"]
        ups = sum(1 for _, a, b in ch if b > a)
        downs = len(ch) - ups
        biggest = max(ch, key=lambda x: abs(x[2] - x[1]))
        verb = "up" if ups and not downs else "down" if downs and not ups else "revised"
        out.append({"kind": "price", "date": day, "model_id": mid, "title": f"{r['brand']} {r['model']} prices {verb}",
                    "brand": r["brand"], "model": r["model"], "variants_changed": len(ch), "direction": verb,
                    "example_variant": biggest[0], "old_inr": biggest[1], "new_inr": biggest[2],
                    "detail": f"{len(ch)} variant{'s' if len(ch) > 1 else ''} revised; {biggest[0]}: "
                              f"₹{biggest[1]:,} → ₹{biggest[2]:,}", "source_url": r["source_url"], "image_url": r["image_url"]})
    # models that appeared after the first catalogue load
    first = (_q("SELECT MIN(first_seen) AS t FROM models")[0]["t"] or "")[:10]
    for m in _q(f"""SELECT m.id, m.name, m.first_seen, m.url, m.image_url, b.name AS brand,
                           EXISTS (SELECT 1 FROM variants v JOIN prices p ON p.variant_id = v.id WHERE v.model_id = m.id) AS priced
                    FROM models m JOIN brands b ON b.slug = m.brand_slug
                    WHERE m.active = 1 AND substr(m.first_seen, 1, 10) >= ? {cond}
                    AND m.first_seen > datetime((SELECT MIN(m3.first_seen) FROM models m3 WHERE m3.brand_slug = m.brand_slug), '+3 day')
                    AND m.url NOT LIKE '%cardekho.com%' AND m.url NOT LIKE '%bikedekho.com%'""",
                (since, *params)):
        out.append({"kind": "new", "date": m["first_seen"][:10], "model_id": m["id"], "title": f"New: {m['brand']} {m['name']}",
                    "brand": m["brand"], "model": m["name"],
                    "detail": "Newly listed on the maker's website" + (", with prices." if m["priced"] else "; price on request."), "source_url": m["url"], "image_url": m["image_url"]})
    # offers that started recently
    ocond = cond.replace("m.id", "m2.id").replace("m.vehicle_type", "m2.vehicle_type") if cond else ""
    for o in _q(f"""SELECT o.title, o.amount_inr, o.valid_from, o.valid_until, o.source_url, b.name AS brand, o.model_name,
                           (SELECT m2.id FROM models m2 WHERE m2.brand_slug = o.brand_slug AND lower(m2.name) = lower(o.model_name)) AS model_id
                    FROM offers o JOIN brands b ON b.slug = o.brand_slug
                    WHERE o.active = 1 AND o.valid_from >= ? AND (o.valid_until IS NULL OR o.valid_until >= date('now'))""", (since,)):
        if model_id and o["model_id"] != model_id:
            continue
        out.append({"kind": "offer", "date": o["valid_from"][:10], "model_id": o["model_id"],
                    "title": f"{o['brand']} {o['model_name'] or ''}: {o['title']}".replace("  ", " "),
                    "detail": (f"Benefits up to ₹{o['amount_inr']:,}" if o["amount_inr"] else "Manufacturer offer")
                              + (f", until {o['valid_until']}" if o["valid_until"] else ""), "source_url": o["source_url"]})
    out.sort(key=lambda x: x["date"], reverse=True)
    return out[:limit]
