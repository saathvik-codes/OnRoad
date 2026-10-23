"""
Hyundai India adapter (www.hyundai.com/in/en).

Endpoints (all public, called by the site's own jQuery components; found in data-attr-* attributes of the price and
dealer-locator pages and in /etc/designs/hyundai/in/en/components/spa/request-a-price.js and
hyundai_in.find-dealer-with-map.js):
  models  : GET https://api.hyundai.co.in/service/price/getModels                       (id, name, category, enabled)
            + header navigation of https://www.hyundai.com/in/en/click-to-buy/prices    (model page URL + thumbnail)
  prices  : GET https://api.hyundai.co.in/service/price/getStatesByModel?modelId=
            GET https://api.hyundai.co.in/service/price/getPriceCitiesByModelIdAndStateId?stateId=&modelId=
            GET https://api.hyundai.co.in/service/price/getPriceByModelAndCity?cityId=&modelId=
            -> per-city ex-showroom price of every variant (the same table the "price-in-<city>" pages render)
  dealers : GET https://api.hyundai.co.in/service/dealer/getStates?modelId=&dealerCategory=1
            GET https://api.hyundai.co.in/service/dealer/getCities?stateId=&dealerCategory=1&modelId=&variantId=
            GET https://api.hyundai.co.in/service/dealer/getDealers?dealerCategoryId=1&cityId=&modelId=&variantId=
            (dealerCategoryId 1 = Sales, as used by the "Find a Dealer" page)
  offers  : https://www.hyundai.com/in/en/click-to-buy/special-offers/overview (+ clicktobuy.hyundai.co.in)
            -> NotSupported (see below)

Verified 2026-10-19 (run from backend/):
  models()  -> 14 models (13 retail + PRIME taxi); BAYON is in the site menu but marked "Launching Soon", so excluded.
  prices('Hyderabad') -> every variant of every priced model, read live. Spot-check: Creta 1.5 MPi MT "E" Hyderabad
            = Rs 10,90,700 from getPriceByModelAndCity(cityId=1122, modelId=37); the static text of
            https://www.hyundai.com/in/en/find-a-car/creta/price-in-hyderabad says "starting ex-showroom price of
            Rs 10,90,700" - match. 223 variants for Hyderabad on 2026-10-19; 27 sales dealers.
  dealers('Hyderabad') -> sales outlets with address, pincode, phones, e-mails, lat/lng and dealer microsite.
Known gaps:
  * engine_cc: the API gives the engine as e.g. "Creta 1.5 MPi" (litres, not cc), so engine_cc is left None and the
    engine label is kept in the variant name. Seats and battery kWh are not in the price API (None).
  * offers() (re-checked 2026-10-22, festive season): /in/en/click-to-buy/special-offers/overview is a single banner
    image plus a test-drive form (APIs: service/test-drive/getModels|getStatesByModel|book only); click-to-buy
    overview, model highlight pages and the /in/en/sitemap.xml have no offer text/amount/validity; the online sales
    site clicktobuy.hyundai.co.in only shows personalised loan offers inside the booking flow and disallows /api/ in
    robots.txt. So offers() raises NotSupported rather than guessing.
  * Matte paint option (+Rs 5,000/15,000 on some trims) is stated only as a page note, not as separate variants.
"""

from __future__ import annotations

import re

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._ga_common import Polite, clean, inr, norm, transmission

API = "https://api.hyundai.co.in/service"
SITE = "https://www.hyundai.com"
NAV_PAGE = SITE + "/in/en/click-to-buy/prices"

# State to try first for common cities (saves requests); any other city falls back to scanning all states.
STATE_HINT = {
    "hyderabad": "Telangana", "secunderabad": "Telangana", "warangal": "Telangana",
    "bengaluru": "Karnataka", "bangalore": "Karnataka", "chennai": "Tamil Nadu", "mumbai": "Maharashtra",
    "pune": "Maharashtra", "delhi": "New Delhi", "new delhi": "New Delhi", "kolkata": "West Bengal",
    "ahmedabad": "Gujarat", "jaipur": "Rajasthan", "lucknow": "Uttar Pradesh", "indore": "Madhya Pradesh",
    "vijayawada": "Andhra Pradesh", "visakhapatnam": "Andhra Pradesh", "kochi": "Kerala", "chandigarh": "Chandigarh",
}

NAV_ITEM = re.compile(
    r'<a href="(/in/en/find-a-car/([a-z0-9-]+)/[^"]*)"[^>]*>\s*<img src="([^"]+)"[^>]*>\s*<span class="carTit">([^<]+)<')

BODY = {"Hatchback": "Hatchback", "Sedan": "Sedan", "SUV": "SUV", "Electric": "SUV"}   # both Hyundai EVs are SUVs


def _slug_from_api_name(name: str) -> str:
    s = re.sub(r"^(all\s+new|new|all)\s+", "", name.strip(), flags=re.I)
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


class HyundaiAdapter(BrandAdapter):
    brand = "Hyundai"
    slug = "hyundai"
    website = SITE + "/in/en"

    # ---------------------------------------------------------------- models
    def _api_models(self, h: Polite) -> list[dict]:
        return [m for m in h.json(API + "/price/getModels") if m.get("enabled") and m.get("price")]

    def _nav(self, h: Polite) -> dict[str, dict]:
        page = h.get(NAV_PAGE).text
        out = {}
        for href, slug, img, title in NAV_ITEM.findall(page):
            out.setdefault(slug, {"url": SITE + href, "image_url": SITE + img, "title": clean(title)})
        return out

    def models(self) -> list[dict]:
        with Polite(self.client()) as h:
            api = self._api_models(h)
            nav = self._nav(h)
        out = []
        for m in api:
            slug = _slug_from_api_name(m["description"])
            n = nav.get(slug, {})
            body = BODY.get(m.get("category") or "", None)
            if m.get("code") == "PR" or (m.get("description") or "").upper() == "PRIME":
                body = None                              # taxi line (PRIME HB / SD) - category not published
            out.append({
                "name": n.get("title") or m["description"],
                "url": n.get("url") or f"{SITE}/in/en/find-a-car/{slug}/highlights",
                "body_type": body,
                "image_url": n.get("image_url"),
                "fuel": "Electric" if m.get("electric") else None,
                "api_id": m["id"],
                "api_name": m["description"],
                "category": m.get("category"),
                "source_url": API + "/price/getModels",
            })
        return out

    # ---------------------------------------------------------------- prices
    def _price_city_id(self, h: Polite, model_id: int, city: str) -> int | None:
        states = h.json(f"{API}/price/getStatesByModel", params={"modelId": model_id})
        hint = STATE_HINT.get(city.lower())
        states.sort(key=lambda s: 0 if hint and s["description"].lower() == hint.lower() else 1)
        for st in states:
            cities = h.json(f"{API}/price/getPriceCitiesByModelIdAndStateId",
                            params={"stateId": st["id"], "modelId": model_id})
            for c in cities:
                if c["description"].strip().lower() == city.strip().lower():
                    return c["id"]
            if hint:                      # hinted state did not list the city -> give up rather than scan 35 states
                break
        return None

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        out: list[Variant] = []
        with Polite(self.client()) as h:
            api = self._api_models(h)
            nav = self._nav(h)
            city_id = None
            for m in api:
                # city ids are global (Hyderabad = 1122 for every model) but look it up per model when the first
                # lookup fails, because a model may not be priced in every city.
                cid = city_id or self._price_city_id(h, m["id"], city)
                if cid is None:
                    continue
                city_id = cid
                rows = h.json(f"{API}/price/getPriceByModelAndCity", params={"cityId": cid, "modelId": m["id"]})
                slug = _slug_from_api_name(m["description"])
                n = nav.get(slug, {})
                name = n.get("title") or m["description"]
                src = f"{API}/price/getPriceByModelAndCity?cityId={cid}&modelId={m['id']}"
                for r in rows:
                    price = inr(r.get("price"))
                    if not price:
                        continue
                    parts = [r.get("engine") or "", r.get("transmission") or "", r.get("variant") or "",
                             r.get("paintType") or "", r.get("edition") or ""]
                    label = clean(" ".join(parts))
                    eng = (r.get("engine") or "")
                    if eng.lower().startswith(name.lower()):
                        label = clean(" ".join([eng[len(name):]] + parts[1:]))
                    fuel = (r.get("fuelType") or "").strip()
                    fuel = "CNG" if "cng" in fuel.lower() else fuel.title()     # "CNG" / "Dual CNG"
                    trans_raw = (r.get("transmission") or "").strip()
                    kwh = None
                    mk = re.match(r"([\d.]+)\s*kWh", trans_raw, flags=re.I)  # Creta Electric puts the pack here
                    if mk:
                        kwh = float(mk.group(1))
                        trans_raw = "AT"                                       # single-speed EV automatic
                    if kwh is None:
                        mk = re.search(r"([\d.]+)\s*kWh", label, flags=re.I)        # e.g. IONIQ 5 "72.6 kWh"
                        kwh = float(mk.group(1)) if mk else None
                    if m.get("electric"):
                        fuel = "Electric"
                    out.append(Variant(
                        model=name, variant=label, fuel=fuel,
                        transmission=transmission(trans_raw), ex_showroom_inr=price, city=city, battery_kwh=kwh,
                        source_url=src, body_type=BODY.get(m.get("category") or ""),
                        model_url=n.get("url"), image_url=n.get("image_url")))
        if not out:
            raise NotSupported(f"Hyundai price API lists no prices for city '{city}'")
        return out

    # ---------------------------------------------------------------- dealers
    def _dealer_city_id(self, h: Polite, city: str) -> int | None:
        states = h.json(f"{API}/dealer/getStates", params={"modelId": "", "dealerCategory": 1})
        hint = STATE_HINT.get(city.lower())
        states.sort(key=lambda s: 0 if hint and s["description"].lower() == hint.lower() else 1)
        for st in states:
            cities = h.json(f"{API}/dealer/getCities",
                            params={"stateId": st["id"], "dealerCategory": 1, "modelId": "", "variantId": ""})
            for c in cities:
                if c["description"].strip().lower() == city.strip().lower():
                    return c["id"]
            if hint:
                break
        return None

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        with Polite(self.client()) as h:
            cid = self._dealer_city_id(h, city)
            if cid is None:
                raise NotSupported(f"Hyundai dealer locator has no city '{city}'")
            url = f"{API}/dealer/getDealers?dealerCategoryId=1&cityId={cid}&modelId=&variantId="
            rows = h.json(url)
        out = []
        for r in rows:
            if (r.get("dealerStatus") or "O") != "O":
                continue
            phones = [p for p in (r.get("mobile1"), r.get("mobile2"), r.get("phone1"), r.get("phone2")) if p]
            phones = list(dict.fromkeys(phones))
            emails = [e for e in (r.get("email1"), r.get("email2")) if e]
            name = clean(r.get("dealerName"))
            if r.get("location"):
                name = f"{name} - {clean(r['location'])}"
            out.append(Dealer(
                name=name, address=clean(r.get("address1") or r.get("address")), city=clean(r.get("city")) or city,
                state=clean(r.get("state")), pincode=(r.get("postCode") or None), phone=", ".join(phones) or None,
                email=", ".join(emails) or None, lat=float(r["latitude"]) if r.get("latitude") else None,
                lng=float(r["longitude"]) if r.get("longitude") else None, kind="sales", source_url=url,
                website=r.get("website") or None))
        return out

    # ---------------------------------------------------------------- offers
    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise NotSupported(
            "Hyundai India publishes no offer text/JSON (checked 2026-10-22): /in/en/click-to-buy/special-offers/overview "
            "is one banner image (newspecialoffergst-pc.jpg) + a test-drive form whose only APIs are "
            "api.hyundai.co.in/service/test-drive/*; /in/en/click-to-buy/overview and model pages (e.g. "
            "/in/en/find-a-car/creta/highlights) carry no offer amounts; the sitemap has no offer/festive page; "
            "clicktobuy.hyundai.co.in only computes personalised loan offers inside the booking flow and its "
            "robots.txt disallows /api/.")

    # ---------------------------------------------------------------- specs
    def specs(self):
        """Trim-wise standard equipment from each model's /features tables, body dimensions from the model's official
        brochure PDF, displacement from the model page's schema.org Car data (see module docstring)."""
        from ..base import Feature, Spec
        from ._spec_common import feature_keys

        priced = {(v.model, v.variant): v for v in self.prices("Hyderabad")}
        specs, feats = [], []
        with Polite(self.client()) as h:
            api = self._api_models(h)
            nav = self._nav(h)
            for m in api:
                slug = _slug_from_api_name(m["description"])
                n = nav.get(slug)
                if not n:
                    continue                                       # PRIME (taxi) has no model pages
                name = n.get("title") or m["description"]
                rows = h.json(f"{API}/price/getPriceByModelAndCity", params={"cityId": HY_CITY, "modelId": m["id"]})
                variants = []                                      # (Variant, raw price row)
                for r in rows:
                    v = priced.get((name, _hy_label(r, name)))
                    if v and all(v is not x for x, _ in variants):
                        variants.append((v, r))
                if not variants:
                    continue
                furl = f"{SITE}/in/en/find-a-car/{slug}/features"
                page = h.get(furl).text
                # --- features: one column per trim; only plain "S" (standard) cells, no footnoted/conditional ones
                for cols, items in _hy_feature_tables(page):
                    for v, r in variants:
                        ci = _hy_trim_col(r, cols)
                        if ci is None:
                            continue
                        for label, cells in items:
                            if ci < len(cells) and cells[ci] == "S":
                                for key in feature_keys(label):
                                    feats.append(Feature(v.model, v.variant, v.fuel, v.transmission, key, label, furl))
                # --- displacement from the page's schema.org Car JSON-LD, only when one engine matches unambiguously
                engines = _hy_engines(page)
                for v, r in variants:
                    e = _hy_engine_for(r, v.fuel, engines)
                    if e:
                        specs.append(Spec(v.model, v.variant, v.fuel, v.transmission, "Engine", "displacement",
                                          "Displacement", e, furl))
                # --- body dimensions + fuel tank from the official brochure (model-level table)
                pdf = re.search(r'["\'](?:https://www\.hyundai\.com)?(/content/dam/hyundai/in/en/data/brochure/'
                                + re.escape(slug.replace("creta-electric", "creta-ev")) + r'\.pdf)["\']', page, re.I)
                if pdf:
                    burl = SITE + pdf.group(1)
                    for group, key, label, value in _hy_brochure_dims(h.get(burl).content):
                        for v, _ in variants:
                            specs.append(Spec(v.model, v.variant, v.fuel, v.transmission, group, key, label, value, burl))
        if not specs and not feats:
            raise NotSupported("Hyundai India pages returned no spec/feature tables")
        return specs, feats


HY_CITY = 1122            # Hyderabad in the price API (city ids are global; spec data is not city-specific)
_HY_DIMS = [("Dimensions", "length", "Overall length", r"(?:Overall\s*)?length\s*\(mm\)", "mm"),
            ("Dimensions", "width", "Overall width", r"(?:Overall\s*)?width\s*\(mm\)", "mm"),
            ("Dimensions", "height", "Overall height", r"(?:Overall\s*)?height\s*\(mm\)", "mm"),
            ("Dimensions", "wheelbase", "Wheelbase", r"Wheelbase\s*\(mm\)", "mm"),
            ("Capacity", "fuel_tank", "Fuel tank capacity", r"Fuel\s*tank\s*capacity\s*\(l\)", "l")]


def _hy_label(r: dict, name: str) -> str:
    """Same variant label prices() builds from one getPriceByModelAndCity row."""
    parts = [r.get("engine") or "", r.get("transmission") or "", r.get("variant") or "",
             r.get("paintType") or "", r.get("edition") or ""]
    label = clean(" ".join(parts))
    eng = r.get("engine") or ""
    if eng.lower().startswith(name.lower()):
        label = clean(" ".join([eng[len(name):]] + parts[1:]))
    return label


def _hy_cells(tr: str) -> list[tuple[str, str]]:
    return [(attrs, clean(c)) for attrs, c in re.findall(r"<t[hd]([^>]*)>(.*?)</t[hd]>", tr, re.S)]


def _hy_feature_tables(page: str):
    """Yield (trim column names, [(feature label, [cell per trim])]) for each 'Feature' table on a /features page."""
    for t in re.findall(r"<table.*?</table>", page, re.S):
        trs = re.findall(r"<tr.*?</tr>", t, re.S)
        if not trs:
            continue
        head = [c for _, c in _hy_cells(trs[0])]
        if not head or head[0] != "Feature":
            continue
        cols = head[1:]
        group, left, items = "", 0, []
        for tr in trs[1:]:
            cells = _hy_cells(tr)
            vals = [c for _, c in cells[-len(cols):]]
            lead = cells[:-len(cols)]
            if len(lead) == 2:                    # "Airbag" (rowspan) + "Driver & passenger"
                rs = re.search(r'rowspan="(\d+)"', lead[0][0])
                group, left = lead[0][1], (int(rs.group(1)) if rs else 1) - 1
                label = f"{group}: {lead[1][1]}" if lead[1][1] else group
            elif len(lead) == 1:
                if left > 0:
                    label, left = f"{group}: {lead[0][1]}", left - 1
                else:
                    label, group = lead[0][1], ""
            else:
                continue
            if label and len(vals) == len(cols):
                items.append((label, vals))
        yield cols, items


def _hy_trim_col(r: dict, cols: list[str]) -> int | None:
    """Column of this price row's trim. Paint (DT / Dual Tone), seat count and DSL prefixes are not separate columns;
    CNG trims have no column on the features page and are left without features."""
    trim = clean(r.get("variant") or "")
    if re.search(r"\bCNG\b", trim, re.I):
        return None
    trim = re.sub(r"^DSL\s+", "", trim, flags=re.I)
    trim = re.sub(r"\s*(\bDT\b|Dual\s*Tone|\b[67]S\b|\(\s*HC\s*\)|\[\s*HC\s*\])", " ", trim, flags=re.I)
    trim = clean(trim)
    knight = "knight" in (r.get("edition") or "").lower()
    cands = [trim + " Knight"] if knight else [trim]
    if re.search(r"\bLounge\b", trim, re.I) and not knight:
        cands += ["Lounge Edition", "Lounge"]
    want = [norm(c) for c in cands]
    for i, c in enumerate(cols):
        if norm(c) in want:
            return i
    return None


def _hy_engines(page: str) -> list[tuple[str, str, str]]:
    """[(engine name, fuel, '1497 cc')] from the page's schema.org Car JSON-LD."""
    import json
    out = []
    for blob in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', page, re.S):
        try:
            d = json.loads(blob)
        except ValueError:
            continue
        eng = (d.get("vehicleEngine") or []) if isinstance(d, dict) else []
        for e in (eng if isinstance(eng, list) else [eng]):
            if not isinstance(e, dict):
                continue
            disp = e.get("engineDisplacement") or {}
            if disp.get("value") and (disp.get("unitCode") or "").upper() in ("CC", "CMQ"):
                out.append((e.get("name") or "", e.get("fuelType") or "", f"{disp['value']} cc"))
    return out


def _hy_engine_for(r: dict, fuel: str, engines) -> str | None:
    eng = (r.get("engine") or "").lower()
    lit = re.search(r"(\d\.\d)", eng)
    if not lit or fuel not in ("Petrol", "Diesel"):
        return None
    turbo = bool(re.search(r"turbo|\d\.\dt\b|gdi", eng))
    hits = {d for n, f, d in engines
            if f.lower() == fuel.lower() and lit.group(1) in n and bool(re.search(r"turbo|gdi", n.lower())) == turbo}
    return hits.pop() if len(hits) == 1 else None


def _hy_brochure_dims(pdf: bytes):
    import io
    from pypdf import PdfReader
    text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(pdf)).pages)
    for group, key, label, rx, unit in _HY_DIMS:
        m = re.search(rx + r"\s*(\d[\d ]{0,5}\d|\d)\s*([*^@#~]*)", text, re.I)
        if m:
            num = m.group(1).replace(" ", "")
            note = ""
            if m.group(2):
                fn = re.search(r"(?<![*^@#~])" + re.escape(m.group(2)) + r"(?![*^@#~])\s*([A-Za-z][^\n*^@#~]{3,60})",
                               text[m.end():])
                note = f" ({fn.group(1).strip().rstrip('.')})" if fn else ""
            yield group, key, label, f"{num} {unit}{note}"


ADAPTER = HyundaiAdapter()
