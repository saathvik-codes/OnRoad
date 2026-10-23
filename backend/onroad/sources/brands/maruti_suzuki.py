"""
Maruti Suzuki adapter - Arena (www.marutisuzuki.com, channel NRM) and NEXA (www.nexaexperience.com, channel EXC).

Both sites are Adobe Edge Delivery pages whose blocks call these public endpoints (paths come from each site's
/placeholders.json: api-ex-showroom-detail, api-dealer-only-cities, api-nearest-dealers, get-car-list-api-endpoint):
  cities  : GET  https://www.marutisuzuki.com/dms/v1/api/common/msil/dms/dealer-only-cities
            -> cityDesc, stateDesc, forCode (pricing zone), latitude/longitude
  models  : GET  https://www.marutisuzuki.com/graphql/execute.json/msil-platform/ArenaCarList    (carModelList)
            GET  https://www.nexaexperience.com/graphql/execute.json/msil-platform/NexaCarList   (carModelList)
            -> active models with bodyTypeSegregate, image, page path and the ACTIVE variant codes/names
  prices  : GET  https://www.marutisuzuki.com/pricing/v2/common/pricing/ex-showroom-detail
                 ?forCode=<city forCode>&channel=NRM&variantInfoRequired=true
            GET  https://www.nexaexperience.com/pricing/v2/common/pricing/ex-showroom-detail?...&channel=EXC
            -> ex-showroom per variantCd and colorType (M metallic / NM non-metallic / D dual-tone). This is the
               call made by blocks/variant-carousel (masterApiUtils.updateExShowroomPrices) on /arena/<model>/price.
  dealers : GET  https://www.marutisuzuki.com/dms/v2/api/common/msil/dms/nearest-dealers
                 ?isActive=true&latitude=&longitude=&distance=<m>&channel=NRM|EXC&dealerType=S
            (exact query built by blocks/dealer-locator-filter on /arena/connect-to-dealer and NEXA connect-to-dealer)
  offers  : neither site has an offers page (checked both sitemaps and placeholders) -> NotSupported.

Price rounding: the site formats prices with utility.formatCurrency, which adds Re 1 to values ending in 9
(e.g. 648,999 is shown as 6,49,000). The same rule is applied here so numbers match what buyers see.

Verified 2026-10-19 (run from backend/): Hyderabad = forCode 10 (Telangana zone). Prices come only from the API
above (the price pages contain no server-rendered numbers, so the API is the page's own data source). Spot-check:
Dzire LXi 1.2L 5MT, Hyderabad = Rs 6,30,600; Grand Vitara Smart Hybrid Sigma 5MT = Rs 10,76,500; Swift ZXi+ AGS =
Rs 8,73,900 (dual-tone Rs 8,88,900).
Known gaps:
  * Eeco (Arena) is listed as an active model but the pricing API returns no Eeco rows for any city, so it has no
    price rows. NEXA's Ciaz and Ignis still have price rows but are not in the active car list, so they are skipped.
  * engine_cc is filled only when the model's published displacement matches the litre figure in the variant name.
  * Seats are not in either feed (None). NEXA placeholders carry a stale 'gv-metallic-prices' list that the pages do
    not use; it is ignored.
"""

from __future__ import annotations

import re

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._ga_common import Polite, clean, make_client, transmission

ARENA = "https://www.marutisuzuki.com"
NEXA = "https://www.nexaexperience.com"
CHANNELS = (
    # (label, site, channel code, car-list query)
    ("Arena", ARENA, "NRM", "/graphql/execute.json/msil-platform/ArenaCarList"),
    ("NEXA", NEXA, "EXC", "/graphql/execute.json/msil-platform/NexaCarList"),
)
CITIES = ARENA + "/dms/v1/api/common/msil/dms/dealer-only-cities"
PRICE = "/pricing/v2/common/pricing/ex-showroom-detail"
NEAREST = "/dms/v2/api/common/msil/dms/nearest-dealers"
DEALER_RADIUS_M = 50_000
TWIN_CITIES = {"HYDERABAD": ("SECUNDERABAD",)}       # Maruti lists Secunderabad outlets as a separate city
BODY = {"MPV": "MUV", "SUV": "SUV", "Hatchback": "Hatchback", "Sedan": "Sedan", "Van": "Van"}
FUEL = {"PET": "Petrol", "CNG": "CNG", "EV": "Electric", "DSL": "Diesel"}
COLOR_SUFFIX = {"M": "", "NM": "", "D": " Dual Tone"}


def site_price(value) -> int | None:
    """Mirror of the site's utility.formatCurrency: int(price), +1 when the last digit is 9."""
    if value in (None, ""):
        return None
    v = int(float(value))
    return v + 1 if v % 10 == 9 else v


def _page_url(site: str, path: str | None) -> str | None:
    if not path:
        return None
    # /content/arena-eds/com/in/en/arena/swift -> /arena/swift ; /content/nexa-eds/com/in/en/baleno -> /baleno
    return site + re.sub(r"^/content/[a-z-]+/com/in/en", "", path)


def _trans(desc: str) -> str:
    d = desc.upper().replace(" ", "")
    if "AGS" in d or "AMT" in d:
        return "AMT"
    if "ECVT" in d or "E-CVT" in d:
        return "CVT"
    if "CVT" in d:
        return "CVT"
    if re.search(r"\dAT|(?<![A-Z])AT(?![A-Z])", d) or desc.upper().endswith(" AT"):
        return "Automatic"
    if re.search(r"\dMT|(?<![A-Z])MT", d):
        return "Manual"
    if "KWH" in d or "EV" in d.split():
        return "Automatic"
    return ""


class MarutiSuzukiAdapter(BrandAdapter):
    brand = "Maruti Suzuki"
    slug = "maruti_suzuki"
    website = ARENA

    def client(self):
        # Akamai on both sites stalls requests without an Accept header.
        return make_client(extra_headers={"Accept": "application/json, text/html;q=0.9, */*;q=0.8"})

    def _city(self, h: Polite, city: str) -> dict:
        rows = h.json(CITIES)["data"]
        want = city.strip().upper()
        want = {"BENGALURU": "BANGALORE", "GURUGRAM": "GURGAON", "NEW DELHI": "DELHI"}.get(want, want)
        for r in rows:
            if (r.get("cityDesc") or "").strip().upper() == want and r.get("forCode"):
                return r
        raise NotSupported(f"Maruti Suzuki city master has no city '{city}'")

    def _cars(self, h: Polite):
        for label, site, ch, q in CHANNELS:
            items = h.json(site + q)["data"]["carModelList"]["items"]
            yield label, site, ch, items, site + q

    # ------------------------------------------------------------------ models
    def models(self) -> list[dict]:
        out = []
        with Polite(self.client()) as h:
            for label, site, ch, items, src in self._cars(h):
                for m in items:
                    out.append({
                        "name": clean(m.get("modelDesc")), "channel": label,
                        "url": _page_url(site, (m.get("carDetailsPagePath") or {}).get("_path")),
                        "body_type": BODY.get(m.get("bodyTypeSegregate") or "", m.get("bodyTypeSegregate")),
                        "image_url": (m.get("carImage") or {}).get("_publishUrl"),
                        "fuel": m.get("fuelType"), "model_code": m.get("modelCd"), "source_url": src,
                    })
        return out

    # ------------------------------------------------------------------ prices
    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        out: list[Variant] = []
        with Polite(self.client()) as h:
            c = self._city(h, city)
            for label, site, ch, items, src in self._cars(h):
                url = f"{site}{PRICE}?forCode={c['forCode']}&channel={ch}&variantInfoRequired=true"
                data = h.json(url)
                prices: dict[str, dict[str, dict]] = {}
                for pm in (data.get("data") or {}).get("models", []):
                    for r in pm.get("exShowroomDetailResponseDTOList") or []:
                        if r.get("salesType", "IND") == "IND":
                            prices.setdefault(r["variantCd"], {})[r.get("colorType") or "M"] = r
                for m in items:
                    model = clean(m.get("modelDesc"))
                    body = BODY.get(m.get("bodyTypeSegregate") or "", m.get("bodyTypeSegregate"))
                    page = _page_url(site, (m.get("carDetailsPagePath") or {}).get("_path"))
                    img = (m.get("carImage") or {}).get("_publishUrl")
                    disp = {"": _cc(m.get("maxDisplacement")), "CNG": _cc(m.get("cngMaxDisplacement"))}
                    # maxDisplacement is a per-model maximum; when a model also has a strong hybrid (1490 cc vs
                    # 1462 cc, both "1.5L") the figure cannot be tied to a variant, so leave engine_cc empty.
                    raws = " ".join((r.get("variantDesc") or "").upper()
                                    for v in m.get("variants") or [] for r in prices.get(v["variantCd"], {}).values())
                    if "STGHYBRID" in raws or "STRONG HYBRID" in raws or "Strong Hybrid" in (m.get("fuelType") or []):
                        disp = {"": None, "CNG": None}
                    for v in m.get("variants") or []:
                        rows = prices.get(v["variantCd"])
                        if not rows:
                            continue
                        name = clean(v.get("variantDesc"))
                        if name.upper().startswith(model.upper() + " "):
                            name = name[len(model) + 1:]
                        name = re.sub(r"^MARUTI\s+" + re.escape(model.upper()) + r"\s+", "", name)
                        kwh = _spec(v, "batteryCapacity")
                        seen = set()
                        for ctype in ("M", "NM", "D"):
                            r = rows.get(ctype)
                            if not r:
                                continue
                            price = site_price(r.get("exShowroomPrice"))
                            key = (COLOR_SUFFIX.get(ctype, ""), price)
                            if not price or key in seen or (ctype == "NM" and ("", price) in seen):
                                continue
                            seen.add(key)
                            fuel = FUEL.get(r.get("fuelTypeCd") or "", r.get("fuelTypeCd") or "")
                            raw = r.get("variantDesc") or ""
                            if fuel == "Petrol" and re.search(r"STGHYBRID|STRONG HYBRID", raw.upper()):
                                fuel = "Strong Hybrid"
                            label_ = name + COLOR_SUFFIX.get(ctype, "")
                            if ctype == "NM" and rows.get("M") and site_price(rows["M"].get("exShowroomPrice")) != price:
                                label_ = name + " Non-metallic"
                            lit = re.search(r"(\d\.\d)\s*L", raw.upper())
                            cc = disp["CNG" if fuel == "CNG" else ""]
                            engine_cc = cc if (cc and lit and round(cc / 1000, 1) == float(lit.group(1))) else None
                            out.append(Variant(
                                model=model, variant=label_, fuel=fuel, transmission=_trans(raw) or _trans(name),
                                ex_showroom_inr=price, city=city, source_url=url, body_type=body,
                                engine_cc=None if fuel == "Electric" else engine_cc,
                                battery_kwh=kwh, model_url=page, image_url=img))
        if not out:
            raise NotSupported(f"Maruti Suzuki pricing API returned nothing for '{city}'")
        return out

    # ------------------------------------------------------------------ dealers
    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        out: list[Dealer] = []
        with Polite(self.client()) as h:
            c = self._city(h, city)
            want = (c["cityDesc"].upper(),) + TWIN_CITIES.get(c["cityDesc"].upper(), ())
            for label, site, ch, _ in CHANNELS:
                url = (f"{site}{NEAREST}?isActive=true&latitude={c['latitude']}&longitude={c['longitude']}"
                       f"&distance={DEALER_RADIUS_M}&channel={ch}&dealerType=S")
                for r in h.json(url).get("data") or []:
                    cd = (r.get("cityDesc") or "").upper()
                    if r.get("channel") != ch or not any(cd.startswith(w) for w in want):
                        continue
                    if r.get("isNonFunctional") or r.get("msilTerminatedDate"):
                        continue
                    alt = r.get("altDealerAddress") or {}
                    addr = ", ".join(x for x in (alt.get("addressLine1") or r.get("addr1"),
                                                  alt.get("addressLine2") or r.get("addr2"),
                                                  alt.get("addressLine3") or r.get("addr3")) if x)
                    phones = [p for p in (r.get("contactPhone"), r.get("dealerPhoneNumber3"), r.get("dealerPhoneNumber2"),
                                          r.get("altPhoneNumber")) if p]
                    email = next((e for e in (r.get("email"), r.get("altEmail")) if e and "@" in e), None)
                    name = clean(r.get("dealerDisplayName") or r.get("name"))
                    loc = clean(r.get("location"))
                    out.append(Dealer(
                        name=f"{name} ({label}{', ' + loc.title() if loc else ''})", address=clean(addr),
                        city=cd.title(), state=clean(r.get("stateDesc")),
                        pincode=alt.get("pinCode") or r.get("pin"), phone=", ".join(dict.fromkeys(phones)) or None,
                        email=email, lat=float(r["latitude"]) if r.get("latitude") else None,
                        lng=float(r["longitude"]) if r.get("longitude") else None, kind="sales", source_url=url,
                        website=r.get("websiteLink") or None))
        return out

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise NotSupported("Neither marutisuzuki.com (Arena) nor nexaexperience.com publishes an offers page or "
                           "offers feed (checked sitemaps and placeholders on 2026-10-19); offers are dealer-level.")

    # ------------------------------------------------------------------ specs
    def specs(self):
        """Per-variant tech specs + equipment from each site's compare-cars GraphQL (see module docstring)."""
        from ..base import Feature, Spec
        from ._spec_common import absent, feature_keys, feature_label, humanize, outlier_dimensions

        priced = self.prices("Hyderabad")          # exact (model, variant, fuel, transmission) the ingest joins on
        by_name: dict[tuple[str, str], list[Variant]] = {}
        for v in priced:
            base = re.sub(r" (Dual Tone|Non-metallic)$", "", v.variant)
            by_name.setdefault((v.model, base), []).append(v)
        rows = []                                  # (variant objs, field, value, label, src, fuel)
        feats: list[Feature] = []
        with Polite(self.client()) as h:
            for label, site, ch, items, _ in self._cars(h):
                cq = MS_COMPARE[ch]
                pairs = []
                for m in items:
                    model = clean(m.get("modelDesc"))
                    for v in m.get("variants") or []:
                        name = clean(v.get("variantDesc"))
                        if name.upper().startswith(model.upper() + " "):
                            name = name[len(model) + 1:]
                        name = re.sub(r"^MARUTI\s+" + re.escape(model.upper()) + r"\s+", "", name)
                        targets = by_name.get((model, name))
                        if targets:
                            pairs.append((m["modelCd"], v["variantCd"], model, targets))
                for i in range(0, len(pairs), 3):          # the compare page takes exactly three cars per call
                    chunk = pairs[i:i + 3]
                    pad = chunk + [chunk[-1]] * (3 - len(chunk))
                    url = (site + cq + "".join(f"variant{j + 1}={p[1]};" for j, p in enumerate(pad))
                           + "".join(f"model{j + 1}={p[0]};" for j, p in enumerate(pad)) + f"locale=en;channel={ch};")
                    data = h.json(url).get("data") or {}
                    labels = ((data.get("variantSpecificationsLabelsList") or {}).get("items") or [{}])[0] or {}
                    got = {x.get("variantCd"): x for x in (data.get("carVariantList") or {}).get("items") or []}
                    for mcd, vcd, model, targets in chunk:
                        x = got.get(vcd)
                        if not x:
                            continue
                        for cat in x.get("specificationCategory") or []:
                            for asp in cat.get("specificationAspect") or []:
                                for k, val in (asp or {}).items():
                                    if k in ("categoryLabel", "_model") or absent(val) or isinstance(val, (dict, list)):
                                        continue
                                    lab = labels.get(f"{k}_label") or humanize(k)
                                    if cat.get("categoryName") == "Features":
                                        for t in targets:
                                            for key in feature_keys(lab, str(val)):
                                                feats.append(Feature(t.model, t.variant, t.fuel, t.transmission, key,
                                                                     feature_label(lab, val), url))
                                    elif (asp.get("categoryLabel"), k) in MS_SPEC or k in MS_SPEC:
                                        rows.append((model, vcd, targets, asp.get("categoryLabel"), k, clean(str(val)), lab, url))
        # drop lone CMS slips in body dimensions (e.g. one Alto K10 variant carrying Dzire dimensions)
        bad = set()
        for k in ("length", "width", "height", "wheelBase"):
            bad |= {(m, vc, k) for m, vc in outlier_dimensions([(r[0], r[1], r[5]) for r in rows if r[4] == k])}
        specs: list[Spec] = []
        for model, vcd, targets, cat, k, val, lab, url in rows:
            if (model, vcd, k) in bad:
                continue
            group, key, unit = MS_SPEC.get((cat, k)) or MS_SPEC[k]
            for t in targets:
                value = _ms_value(k, val, unit, t.fuel)
                if value:
                    specs.append(Spec(t.model, t.variant, t.fuel, t.transmission, group, key, clean(lab), value, url))
        if not specs:
            raise NotSupported("Maruti Suzuki compare-cars API returned no specifications")
        return specs, feats


# compare-cars persisted queries (placeholders.json -> compare-all-cars-specifications-endpoint on each site)
MS_COMPARE = {"NRM": "/graphql/execute.json/msil-platform/ArenaCompareAllCarsSpecifications;",
              "EXC": "/graphql/execute.json/msil-platform/compareAllCarsSpecifications;"}
# field (or (categoryLabel, field)) -> (group, key, unit named by the site's own field label)
MS_SPEC = {
    "engineType": ("Engine", "engine_type", None), "displacement": ("Engine", "displacement", "cc"),
    "noofCylinders": ("Engine", "cylinders", None),
    "maximumPower": ("Performance", "max_power", "kW"), "maxTorque": ("Performance", "max_torque", "Nm"),
    ("Motor", "maxPowerKw"): ("Performance", "max_power", "kW"), ("Motor", "maxTorqueNm"): ("Performance", "max_torque", "Nm"),
    ("Motor", "type"): ("Engine", "motor_type", None),
    "fuelEfficiency": ("Efficiency", "mileage_arai", "km/l"), "range": ("Efficiency", "range", "km"),
    "batteryCapacity": ("Battery", "battery_capacity", "kWh"), "batteryType": ("Battery", "battery_type", None),
    "acChargingTime": ("Battery", "charging_time", None), "dcChargingTime": ("Battery", "charging_time_dc", None),
    "batteryWarranty": ("Battery", "battery_warranty", None),
    "fuelTankCapacityDimension": ("Capacity", "fuel_tank", "L"), "fuelTankCapacity": ("Capacity", "fuel_tank", "L"),
    "bootSpace": ("Capacity", "boot_space", "L"), "seatingCapacity": ("Capacity", "seating_capacity", None),
    "length": ("Dimensions", "length", "mm"), "width": ("Dimensions", "width", "mm"),
    "height": ("Dimensions", "height", "mm"), "wheelBase": ("Dimensions", "wheelbase", "mm"),
    "kerbWeight": ("Dimensions", "kerb_weight", "kg"), "grossVehicleWeight": ("Dimensions", "gross_weight", "kg"),
    "turningRadius": ("Dimensions", "turning_radius", "m"),
    "frontBrake": ("Chassis", "front_brakes", None), "backBrake": ("Chassis", "rear_brakes", None),
    "frontSuspension": ("Chassis", "front_suspension", None), "rearSuspension": ("Chassis", "rear_suspension", None),
    "tyre": ("Chassis", "tyre_size", None), "wheel": ("Chassis", "wheel_type", None),
    "transmissionType": ("Chassis", "gearbox", None), "driveType": ("Chassis", "drivetrain", None),
}


def _ms_value(field: str, val: str, unit: str | None, fuel: str | None) -> str | None:
    from ._spec_common import with_rpm_unit, with_unit
    if field in ("maximumPower", "maxTorque"):
        return with_rpm_unit(val, unit)
    if field == "fuelEfficiency" and fuel == "CNG":
        # Arena labels the column "km/l" even for CNG (km/kg); keep only cells that state their own unit.
        return val if re.search(r"[a-z]", val, re.I) else None
    return with_unit(val, unit)


def _cc(text) -> int | None:
    m = re.search(r"(\d{3,4})\s*cc", str(text or ""), re.I)
    return int(m.group(1)) if m else None


def _spec(variant: dict, key: str) -> float | None:
    for cat in variant.get("specificationCategory") or []:
        for asp in cat.get("specificationAspect") or []:
            val = (asp or {}).get(key)
            if val:
                m = re.search(r"(\d+(?:\.\d+)?)", str(val))
                if m:
                    return float(m.group(1))
    return None


ADAPTER = MarutiSuzukiAdapter()
