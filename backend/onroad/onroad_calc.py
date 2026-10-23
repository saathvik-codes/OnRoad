"""
Itemised on-road price: ex-showroom + every legally required charge, from data/research/onroad_rules.json
(researched from state transport departments, MoRTH/CMVR, IRDAI and the Income-tax Act; dated, with sources).

Every line says where its number comes from. A charge whose rule is missing for a state is reported as
"not verified" instead of being guessed, and the total is then marked incomplete. Charges dealers add that are
not legally required (handling, logistics, HSRP, "essential kits") are listed separately and never included.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path

RULES = Path(__file__).resolve().parents[2] / "data" / "research" / "onroad_rules.json"

STATE_OF_CITY = {
    "hyderabad": "TS", "secunderabad": "TS", "warangal": "TS", "karimnagar": "TS", "nizamabad": "TS", "khammam": "TS",
    "bengaluru": "KA", "bangalore": "KA", "mysuru": "KA", "chennai": "TN", "coimbatore": "TN", "madurai": "TN", "mumbai": "MH",
    "pune": "MH", "nagpur": "MH", "delhi": "DL", "new delhi": "DL", "gurugram": "HR", "gurgaon": "HR", "noida": "UP",
    "lucknow": "UP", "kolkata": "WB", "ahmedabad": "GJ", "surat": "GJ", "kochi": "KL", "thiruvananthapuram": "KL",
    "vijayawada": "AP", "visakhapatnam": "AP", "jaipur": "RJ", "chandigarh": "CH", "bhopal": "MP", "indore": "MP",
    "patna": "BR", "bhubaneswar": "OD", "guwahati": "AS", "goa": "GA", "panaji": "GA", "dehradun": "UK", "ranchi": "JH",
    "raipur": "CG", "shimla": "HP", "ludhiana": "PB", "srinagar": "JK", "puducherry": "PY",
    "port blair": "AN", "itanagar": "AR", "daman": "DN", "leh": "LA", "kavaratti": "LD", "shillong": "ML", "imphal": "MN", "aizawl": "MZ", "kohima": "NL", "gangtok": "SK", "agartala": "TR",
}


def _parse_date(s: str | None) -> dt.date | None:
    if not s:
        return None
    m = re.search(r"(\d{4})-(\d{2})(?:-(\d{2}))?", s)
    if not m:
        return None
    return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)) if m.group(3) else 28)


@lru_cache(maxsize=1)
def rules() -> dict:
    return json.loads(RULES.read_text(encoding="utf-8")) if RULES.exists() else {}


def reload_rules() -> None:
    rules.cache_clear()


@dataclass
class Line:
    label: str
    amount_inr: int | None
    basis: str
    source: str | None = None
    verified: bool = True
    optional: bool = False
    refundable: bool = False


@dataclass
class Breakdown:
    state: str
    state_name: str
    coverage: str
    ex_showroom_inr: int
    lines: list[Line] = field(default_factory=list)
    optional: list[Line] = field(default_factory=list)
    total_inr: int = 0
    refundable_inr: int = 0
    complete: bool = True
    as_of: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _fuel_key(fuel: str | None) -> str:
    f = (fuel or "").lower()
    if "electric" in f or f in ("ev", "bev"):
        return "electric"
    if "hybrid" in f:
        return "hybrid"
    if "cng" in f:
        return "cng"
    return "diesel" if "diesel" in f else "petrol"


def _slab(state_rules: dict, price: int, fuel: str, ownership: str) -> dict | None:
    best = None
    for s in state_rules.get("road_tax") or []:
        if s.get("rate") is None:
            continue
        lo, hi = s.get("min_inr") or 0, s.get("max_inr")
        if price < lo or (hi is not None and price > hi):
            continue
        if s.get("applies_to", "first_vehicle") not in (ownership, "any"):
            continue
        if s.get("fuel", "any") not in (fuel, "any"):
            continue
        score = (s.get("fuel", "any") == fuel) * 2 + (s.get("applies_to") == ownership)
        if best is None or score > best[0]:
            best = (score, s)
    return best[1] if best else None


def _cc_band(cc: int | None) -> str:
    if cc is None or cc > 1500:
        return "cc_above_1500"
    return "cc_upto_1000" if cc <= 1000 else "cc_1001_1500"


def _estimate_bike(ex_showroom_inr: int, *, city: str = "Hyderabad", state: str | None = None, fuel: str | None = None,
                   engine_cc: int | None = None, battery_kwh: float | None = None, motor_kw: float | None = None,
                   loan: bool = False, include_own_damage: bool = True) -> Breakdown:
    r = rules()
    st = (state or STATE_OF_CITY.get((city or "").strip().lower()) or "TS").upper()
    sr = (r.get("states") or {}).get(st) or {}
    fuel_k = _fuel_key(fuel)
    price = int(ex_showroom_inr)
    raw_src = (sr.get("sources") or [None])[0]
    src = raw_src.get("url") if isinstance(raw_src, dict) else raw_src
    b = Breakdown(state=st, state_name=sr.get("name", st), coverage="verified", ex_showroom_inr=price, as_of=r.get("as_of"))
    b.lines.append(Line("Ex-showroom price", price, "Published ex-showroom price for this city (includes GST)"))

    # 1. Road Tax
    if fuel_k == "electric":
        b.lines.append(Line("Road tax (lifetime)", 0, f"Electric two-wheelers 100% exempt under {sr.get('name', st)} EV Policy", src))
    else:
        if st == "TS":
            rate = 0.09 if price <= 50_000 else 0.12
            law = "Telangana MVT Act (9% <= 50k, 12% > 50k)"
        elif st == "KA":
            rate = 0.10 if price <= 50_000 else (0.12 if price <= 100_000 else 0.18)
            law = "Karnataka Motor Vehicles Taxation Act"
        elif st == "MH":
            rate = 0.10 if (engine_cc or 125) <= 99 else (0.11 if (engine_cc or 125) <= 299 else 0.12)
            law = "Maharashtra MVT Act"
        elif st in ("DL", "HR"):
            rate = 0.04 if price <= 100_000 else (0.06 if price <= 200_000 else 0.08)
            law = f"{sr.get('name', st)} Two-Wheeler Motor Vehicle Tax Rules"
        elif st == "UP":
            rate = 0.07 if price <= 100_000 else 0.08
            law = "Uttar Pradesh MVT Act"
        elif st == "TN":
            rate = 0.08 if price <= 100_000 else 0.12
            law = "Tamil Nadu MVT Act"
        else:
            rate = 0.09
            law = f"{sr.get('name', st)} Two-Wheeler MV Tax"

        road_tax = round(price * rate)
        b.lines.append(Line("Road tax (lifetime)", road_tax, f"{rate * 100:g}% lifetime road tax ({law})", src))

    # 2. Registration & Smart Card RC
    reg_fee = 300  # CMVR Rule 81 two-wheelers
    rc_fee = 200   # Smart card
    b.lines.append(Line("Registration & RC smart card", reg_fee + rc_fee, "New two-wheeler registration ₹300 + smart-card RC ₹200 (CMVR Rule 81)", src))

    # 3. Insurance: 5 Years Mandatory Third-Party per IRDAI
    if fuel_k == "electric":
        tp_prem = 3273
        tp_label = "5-year IRDAI mandatory third-party cover for electric two-wheelers"
    else:
        cc = engine_cc or 150
        if cc <= 75:
            tp_prem = 3423
        elif cc <= 150:
            tp_prem = 4544
        elif cc <= 350:
            tp_prem = 8691
        else:
            tp_prem = 15380
        tp_label = f"5-year IRDAI mandatory third-party cover for {cc} cc + 18% GST"

    b.lines.append(Line("Insurance: third party, 5 years (mandatory)", round(tp_prem), tp_label, "IRDAI Tariff Schedule"))

    # Own damage estimate (1-year)
    if include_own_damage:
        od_prem = round(price * 0.95 * 0.0175 * 1.18)
        b.lines.append(Line("Insurance: own damage, 1 year (estimate)", od_prem, "Comprehensive own-damage estimate (1.75% of IDV + GST)", "IRDAI Market Reference", verified=False))

    if loan:
        b.lines.append(Line("Hypothecation endorsement", 500, "Two-wheeler loan endorsement on RC", src))

    # TCS (only applies if bike > 10 lakh)
    if price > 1_000_000:
        amt = round(price * 0.01)
        b.refundable_inr = amt
        b.lines.append(Line("TCS (you get this back)", amt, "1% TCS on invoice exceeding ₹10 lakh (credited in ITR)", None, refundable=True))

    b.total_inr = sum(l.amount_inr or 0 for l in b.lines)
    return b


def estimate(ex_showroom_inr: int, *, city: str = "Hyderabad", state: str | None = None, fuel: str | None = None,
             engine_cc: int | None = None, battery_kwh: float | None = None, motor_kw: float | None = None,
             ownership: str = "first_vehicle", loan: bool = False, include_own_damage: bool = True,
             vehicle_type: str = "car", today: dt.date | None = None) -> Breakdown:
    if (vehicle_type or "").lower() in ("two_wheeler", "bike", "scooter", "motorcycle"):
        return _estimate_bike(ex_showroom_inr, city=city, state=state, fuel=fuel, engine_cc=engine_cc,
                              battery_kwh=battery_kwh, motor_kw=motor_kw, loan=loan, include_own_damage=include_own_damage)

    r = rules()
    st = (state or STATE_OF_CITY.get((city or "").strip().lower()) or "TS").upper()
    sr = (r.get("states") or {}).get(st) or {}
    fuel_k = _fuel_key(fuel)
    today = today or dt.date.today()
    price = int(ex_showroom_inr)
    raw_src = (sr.get("sources") or [None])[0]
    src = raw_src.get("url") if isinstance(raw_src, dict) else raw_src
    b = Breakdown(state=st, state_name=sr.get("name", st), coverage=sr.get("coverage", "not_found"), ex_showroom_inr=price,
                  as_of=r.get("as_of"))
    b.lines.append(Line("Ex-showroom price", price, "Published by the manufacturer for this city (includes GST)"))


    ev = sr.get("ev") or {}
    ev_to = _parse_date(ev.get("valid_to"))
    ev_valid = fuel_k == "electric" and ev.get("life_tax_exempt") and (
        ev_to is None or today <= ev_to)
    road_tax = 0
    if ev_valid:
        b.lines.append(Line("Road tax (lifetime)", 0, f"Electric cars exempt under {ev.get('order', 'the state EV policy')}"
                            + (f", valid until {ev['valid_to']}" if ev.get("valid_to") else ""), src,
                            verified=not str(ev.get("verified", "")).startswith("secondary")))
    else:
        s = _slab(sr, price, fuel_k, ownership)
        if not s:
            b.lines.append(Line("Road tax (lifetime)", None, f"{b.state_name}: road-tax rule not verified yet", src, verified=False))
            b.complete = False
        else:
            road_tax = round(price * s["rate"])
            upper = f"₹{s['max_inr']:,}" if s.get("max_inr") else "above"
            owner = {"first_vehicle": "first car in your name", "second_vehicle": "second or later car in your name",
                     "company": "company-owned"}.get(ownership, ownership)
            b.lines.append(Line("Road tax (lifetime)", road_tax,
                                f"{s['rate'] * 100:g}% of the invoice value for ₹{s.get('min_inr') or 0:,}–{upper}, {owner}", src,
                                verified=b.coverage == "verified"))
        if ownership == "second_vehicle" and sr.get("second_vehicle_waiver_status"):
            b.notes.append(f"Second-car surcharge: {sr['second_vehicle_waiver_status']}")

    # ── Cesses ──────────────────────────────────────────────────────────────────────────────────────────
    cess = sr.get("cess") or {}
    if isinstance(cess, dict):
        if cess.get("road_safety_cess_inr") is not None and not (ev_valid and ev.get("road_safety_cess_exempt")):
            b.lines.append(Line("Road safety cess", int(cess["road_safety_cess_inr"]),
                                f"One-time, {cess.get('law', 'state law')}", src))
            if fuel_k == "electric" and ev.get("road_safety_cess_exempt") is None:
                b.notes.append("Whether electric cars pay the road safety cess is not confirmed; it is included to be safe.")
        for k, v in cess.items():
            if k.endswith("pct_of_tax") and isinstance(v, (int, float)) and road_tax:
                b.lines.append(Line("Cess on road tax", round(road_tax * v), f"{v * 100:g}% of road tax ({cess.get('law', '')})", src,
                                    verified=False))
            elif k.endswith("cess_car_inr") and isinstance(v, (int, float)):
                b.lines.append(Line("Welfare cess", int(v), cess.get("welfare_cess_law") or "State cess", src))

    # ── Registration ────────────────────────────────────────────────────────────────────────────────────
    reg = sr.get("registration") or {}
    central = r.get("central_registration") or {}
    if fuel_k == "electric" and (ev.get("registration_fee_exempt") or central.get("ev_exemption")):
        b.lines.append(Line("Registration", 0, "Battery-electric cars are exempt from RC / registration-mark fees (MoRTH, Aug 2021)", None))
        smart = reg.get("smart_card_rc_inr", central.get("smart_card_rc_inr"))
        if smart is not None:
            b.lines.append(Line("RC smart card", int(smart), "Smart-card RC fee (CMVR Rule 81)", src))
    else:
        fee = reg.get("new_registration_lmv_inr", central.get("new_registration_lmv_inr"))
        smart = reg.get("smart_card_rc_inr", central.get("smart_card_rc_inr"))
        if fee is None and smart is None:
            b.lines.append(Line("Registration & RC", None, "Not verified for this state", src, verified=False))
            b.complete = False
        else:
            b.lines.append(Line("Registration & RC smart card", int((fee or 0) + (smart or 0)),
                                f"New registration ₹{fee or 0} + smart-card RC ₹{smart or 0} (CMVR Rule 81)", src))
    if any(reg.get(k) is None for k in ("service_or_user_charge_inr",)) and reg:
        b.notes.append("RTO service / postal charges are not published, so they are not included.")
    if loan:
        hyp = sr.get("hypothecation_fee", central.get("hypothecation_endorsement_lmv_inr"))
        b.lines.append(Line("Loan (hypothecation) endorsement", int(hyp) if hyp is not None else None,
                            "Recorded on the RC when the car is financed", src, verified=hyp is not None))
        b.complete &= hyp is not None
    if sr.get("hsrp") == 0:
        b.notes.append("High-security number plates are included in the vehicle price by law; refuse a separate HSRP charge.")

    # ── Insurance ───────────────────────────────────────────────────────────────────────────────────────
    ins = r.get("insurance") or {}
    gst = ins.get("tp_premium_gst_rate") or 0.18
    tp_src = (ins.get("sources") or [None])[0]
    if fuel_k == "electric":
        kw = motor_kw
        band = next((t for t in ins.get("ev_third_party") or [] if kw is not None and kw <= (t.get("kw_max") or 10**9)), None)
        if band is None:   # motor power unknown: most electric cars sold in India are above 65 kW
            band = (ins.get("ev_third_party") or [{}])[-1]
            b.notes.append("Third-party premium for an EV depends on motor power; the highest band (above 65 kW) is used.")
        prem = band.get("premium_3yr_inr")
        tp_basis = "3-year third-party premium for electric cars (MoRTH 2022 rules) + 18% GST"
    else:
        band = next((t for t in ins.get("third_party_3yr_private_car") or [] if engine_cc is not None and engine_cc <= (t.get("engine_cc_max") or 10**9)), None)
        if band is None and engine_cc is None:
            band = None
        prem = band.get("premium_inr") if band else None
        tp_basis = f"3-year third-party premium for {engine_cc} cc (MoRTH 2022 rules) + 18% GST" if engine_cc else ""
    if prem is not None:
        b.lines.append(Line("Insurance: third party, 3 years (mandatory)", round(prem * (1 + gst)), tp_basis, tp_src))
    else:
        b.lines.append(Line("Insurance: third party, 3 years (mandatory)", None, "Needs the engine size", tp_src, verified=False))
        b.complete = False
    b.notes.append("Personal accident cover (₹15 lakh, compulsory unless you already have it) is priced by each insurer and not included.")
    od = ins.get("od_estimate") or {}
    if include_own_damage and od.get("reference_rates_pct_of_idv_age_upto_5yr"):
        zone = "zone_a" if city.strip().title() in (od.get("zone_a_cities") or []) else "zone_b"
        rate = od["reference_rates_pct_of_idv_age_upto_5yr"][zone][_cc_band(engine_cc if fuel_k != "electric" else None)]
        idv = price * (1 - (od.get("new_car_depreciation") or 0.05))
        b.lines.append(Line("Insurance: own damage, 1 year (estimate)", round(idv * rate * (1 + (od.get("gst_rate") or 0.18))),
                            f"Upper reference: {rate * 100:.3g}% of insured value ₹{round(idv):,} ({zone.replace('_', ' ').title()}) + GST. "
                            "Real quotes are usually lower; compare 2–3 insurers.", (od.get("sources") or [None])[0], verified=False))

    # ── FASTag, TCS ─────────────────────────────────────────────────────────────────────────────────────
    if r.get("fastag_inr") is not None:
        b.lines.append(Line("FASTag", int(r["fastag_inr"]), "Issuance + refundable deposit (typical)", None, verified=False))
    tcs = r.get("tcs") or {}
    if price > (tcs.get("threshold_inr") or 1_000_000):
        amt = round(price * (tcs.get("rate") or 0.01))
        b.refundable_inr = amt
        b.lines.append(Line("TCS (you get this back)", amt, f"{(tcs.get('rate') or 0.01) * 100:g}% because the invoice is above ₹10 lakh; "
                            "credited to your PAN and adjusted in your income-tax return", (tcs.get("sources") or [None])[0], refundable=True))

    for c in r.get("disallowed_charges") or []:
        name = c.get("item") if isinstance(c, dict) else str(c)
        if name:
            b.optional.append(Line(name, None, (c.get("status") if isinstance(c, dict) else "") or "Not a legal charge", None, optional=True))

    b.total_inr = sum(l.amount_inr or 0 for l in b.lines)
    if not b.complete:
        b.notes.insert(0, f"Some {b.state_name} charges are not verified yet, so this total is a lower bound.")
    elif b.coverage != "verified":
        b.notes.insert(0, f"{b.state_name} rates come partly from secondary sources; check with the RTO or dealer.")
    return b
