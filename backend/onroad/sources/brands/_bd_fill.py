"""
Completes a two-wheeler brand's catalogue from BikeDekho when the manufacturer's site doesn't give us every model
(pages that refuse our crawler, models without a published price, brands that publish no prices at all).

The manufacturer always comes first: a BikeDekho model is added only when the official adapter has no priced model
of that name. Added variants carry BikeDekho's Delhi ex-showroom price and listed specs, each with the BikeDekho URL
as source. Upcoming, concept and discontinued models are never added (see _bikedekho.model).
"""
from __future__ import annotations

import re

from ..base import NotSupported, Spec, Variant
from . import _bikedekho

BD_BRAND = {"ather": "ather-energy", "bajaj": "bajaj", "hero": "hero", "honda_2wheelers": "honda", "tvs": "tvs",
            "royal_enfield": "royal-enfield", "suzuki_2wheelers": "suzuki", "yamaha": "yamaha", "ola_electric": "ola-electric",
            "ktm": "ktm", "kawasaki": "kawasaki", "triumph": "triumph", "harley_davidson": "harley-davidson", "aprilia": "aprilia",
            "bmw_motorrad": "bmw", "jawa": "jawa"}
SPEC = {"Engine": ("Engine", "displacement", "Displacement"), "Power": ("Engine", "max_power", "Max power"),
        "Torque": ("Engine", "max_torque", "Max torque"), "Mileage": ("Efficiency", "mileage_arai", "Mileage"),
        "Kerb Weight": ("Dimensions", "kerb_weight", "Kerb weight"), "Brakes": ("Chassis", "brakes", "Brakes"),
        "Battery Capacity": ("Battery", "battery_capacity", "Battery capacity"), "Range": ("Battery", "range", "Range (IDC)"),
        "Claimed Top Speed": ("Performance", "top_speed", "Top speed"), "Charging Time(0-80%)": ("Battery", "charging_time", "Charging time (0-80%)"),
        "Motor Power": ("Engine", "motor_power", "Motor power"), "Battery Warranty": ("Battery", "battery_warranty", "Battery warranty")}


def _n(s: str) -> str:
    """Comparable model name: "New Destini 125" and "Destini 125" are one scooter."""
    return re.sub(r"^(?:new|all ?new|the)", "", re.sub(r"[^a-z0-9]", "", (s or "").lower()))


def _body(name: str, kind: str, electric: bool, cc: int | None) -> str:
    n = name.lower()
    if kind == "scooter":
        return "Electric Scooter" if electric else "Scooter"
    if re.search(r"adv|himalayan|adventure|v-?strom|xpulse|transalp|tuareg|\bgs\b|scram|enduro|versys|tiger|pan america|nx500|kle", n):
        return "Adventure"
    if re.search(r"meteor|avenger|rebel|bobber|shotgun|eliminator|super meteor|classic|bullet|cruiser|street bob|fat boy|glide|"
                 r"heritage|breakout|sportster|nightster|speedmaster|x440|x 440|roadster", n):
        return "Cruiser"
    if re.search(r"\brc\b|rc ?\d|r15|r3\b|r7\b|yzf|ninja|cbr|\brs ?\d|daytona|apache rr|pulsar rs|karizma|gsx-?r|rr\b|fireblade|hayabusa", n):
        return "Sports"
    return "Commuter" if cc and cc <= 125 else "Street"


class WithBikeDekho:
    """Wraps an official two-wheeler adapter; every other attribute is the adapter's own."""

    def __init__(self, adapter):
        self._a = adapter
        self._bd_brand = BD_BRAND[adapter.slug]
        self._extra: dict[str, dict] | None = None
        self._official: set[str] | None = None

    def __getattr__(self, k):
        return getattr(self._a, k)

    def _official_priced(self, city: str) -> list[Variant]:
        try:
            return list(self._a.prices(city))
        except NotSupported:
            return []

    def _load(self):
        if self._extra is not None:
            return
        bn = _n(getattr(self._a, "brand", ""))
        # "Harley-Davidson X 440" and "X440" are one model: drop the brand from official names before comparing
        have = {re.sub("^" + re.escape(bn), "", _n(v.model)) or _n(v.model) for v in self._official_priced("Hyderabad")}
        have |= {re.sub(r"^(?:harleydavidson|royalenfield|ktm|tvs|hero|bajaj|honda|suzuki|yamaha)", "", h) for h in have}
        self._official = have
        self._extra = {}
        try:
            slugs = _bikedekho.brand_slugs(self._bd_brand)
        except Exception:
            slugs = []
        for slug in slugs:
            try:
                m = _bikedekho.model(self._bd_brand, slug)
            except Exception:
                m = None
            if not m or not m["variants"]:
                continue
            name = re.sub(r"^" + re.escape(m["brand"]) + r"\s+", "", m["name"] or "", flags=re.I).strip() or m["name"]
            k = _n(name)
            # the manufacturer has this model (or a same-named one) priced: theirs is kept
            if not k or any(k == h or k.startswith(h) or h.startswith(k) for h in have) or name in self._extra:
                continue
            self._extra[name] = m

    def models(self):
        try:
            out = list(self._a.models())
        except NotSupported:
            out = []
        self._load()
        known = {_n(m.get("name", "")) for m in out}
        for name, m in self._extra.items():
            if _n(name) not in known:
                out.append({"name": name, "url": m["url"], "image_url": m["image"],
                            "body_type": _body(name, m["kind"], self._ev(m), self._cc(m["variants"][0]))})
        if not out:
            raise NotSupported("no models from the manufacturer or BikeDekho")
        return out

    @staticmethod
    def _ev(m) -> bool:
        return any("Battery Capacity" in v["props"] or "Range" in v["props"] for v in m["variants"])

    @staticmethod
    def _cc(v) -> int | None:
        x = re.match(r"(\d+(?:\.\d+)?)\s*cc", v["props"].get("Engine", ""))
        return round(float(x.group(1))) if x else None

    def _vname(self, m, name, v) -> str:
        s = re.sub(r"^" + re.escape(m["brand"]) + r"\s+", "", v["name"], flags=re.I)
        s = re.sub(r"^" + re.escape(name) + r"\s*", "", s, flags=re.I).strip(" -")
        return s or "Standard"

    def prices(self, city: str = "Hyderabad"):
        out = self._official_priced(city)
        self._load()
        for name, m in self._extra.items():
            ev = self._ev(m)
            for v in m["variants"]:
                kwh = re.match(r"([\d.]+)", v["props"].get("Battery Capacity", ""))
                fuel = "Electric" if ev else "CNG" if "cng" in v["name"].lower() else "Petrol"
                out.append(Variant(model=name, variant=self._vname(m, name, v), fuel=fuel,
                                   transmission="Automatic" if ev or m["kind"] == "scooter" else "Manual",
                                   ex_showroom_inr=v["price"], city="Delhi", source_url=v["url"],
                                   body_type=_body(name, m["kind"], ev, self._cc(v)), model_url=m["url"], image_url=v["image"] or m["image"],
                                   engine_cc=self._cc(v), battery_kwh=float(kwh.group(1)) if kwh else None))
        if not out:
            raise NotSupported(f"no prices for {city!r} from the manufacturer or BikeDekho")
        return out

    def specs(self):
        try:
            specs, feats = self._a.specs()
            specs, feats = list(specs), list(feats)
        except NotSupported:
            specs, feats = [], []
        self._load()
        for name, m in self._extra.items():
            ev = self._ev(m)
            for v in m["variants"]:
                fuel = "Electric" if ev else "CNG" if "cng" in v["name"].lower() else "Petrol"
                trans = "Automatic" if ev or m["kind"] == "scooter" else "Manual"
                for k, (grp, key, label) in SPEC.items():
                    val = v["props"].get(k)
                    if val:
                        val = val.replace("Kwh", "kWh").replace("km/Hr", "km/h")
                        specs.append(Spec(name, self._vname(m, name, v), fuel, trans, grp, key, label, val, v["url"]))
        if not specs and not feats:
            raise NotSupported("no specs from the manufacturer or BikeDekho")
        return specs, feats
