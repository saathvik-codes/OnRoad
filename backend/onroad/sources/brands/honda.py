"""
Honda Cars India - https://www.hondacarindia.com (Next.js site; all data from its own pages / same-origin /api routes).

Endpoints used (all called by the site's own JS; none disallowed by robots.txt):
  GET  /                                   JSON-LD ItemList -> model name, URL, body "category" (Sedan/SUV)
  GET  /api/getAllCarsData                 model list: id, site slug, image, starting trim
  GET  /check-price/<slug>                 __NEXT_DATA__.carPriceMainData -> fuel x transmission x variant grid
                                           (robots.txt disallows /check-price/honda-zrv, so ZR-V uses the trim from
                                           getAllCarsData instead of that page)
  POST /api/getCarPrice {carID,city,fuelType,transmission,variant}
                                           -> ex-showroom P_Price for that city (what the "Check price" city picker calls)
  GET  /<slug>/tech-specs                  engine displacement + seating capacity
  GET  /api/getStateCheck?cityName=X       city -> Honda city id
  GET  /api/getAllDealerViaTypes?cityId=N&radius=100   dealer locator (phone, email, lat/lng, website, services)
  GET  /shop/shop-offers                   __NEXT_DATA__.carShopOffersData.offersList (models with offers) + the SSR
                                           disclaimer list ("*Offers are Variant, Grade & Location specific...",
                                           "Additional Offers for selected Corporates for all models.",
                                           "All Offers valid till 31st October 2026. *T&C Apply.") -> valid_until
  GET  /api/getShopCarOffer?carName=<slug> what /shop/shop-offers/<slug> ("View Details") loads: offersList lines
                                           e.g. "Benefits upto ₹|^|170|^|900/-", offerUpto, offerDesc
  GET  /                                   __NEXT_DATA__.disclaimerData: definition of TOTAL BENEFITS ("Amount include
                                           applicable cash, exchange, corporate, extended warranty ...") -> conditions
  (robots.txt disallows /shop/new-car-booking/*/bank-offers, so bank/finance offers are not read.)

Verified 2026-10-19 from Python (httpx): getCarPrice is city-specific (Elevate ZX CVT: Hyderabad 16,89,000,
Mumbai 16,98,800, Port Blair 17,19,581; unknown city -> empty). Hyderabad Elevate SV MT = 11,80,000 and City SV MT
= 11,99,900, matching the starting prices shown on /check-price/honda-elevate and /check-price/honda-city.
Dealers: locator returns showrooms + workshops; only outlets whose services include SALES are returned.
Offers verified 2026-10-22: 3 models carry offers (New City 1,70,900; New Amaze 66,800; Amaze - 2nd Gen 57,600, all
"valid till 31st October 2026"), matching the cards on /shop/shop-offers and /shop/shop-offers/<slug>; Elevate's
details API returns {} and ZR-V has IsOfferAvailable=false. Plus one brand-wide corporate offer (no amount).
Known gaps: Honda publishes only a TOTAL "Benefits upto" per model - no cash/exchange/corporate split, no variant or
city split (kind="other", city=None = national); bank offers are robots-blocked; seats/engine are
model-level from tech-specs; prices with a null in the site grid (variant not offered) are skipped.
"""

from __future__ import annotations

import datetime as dt
import html as html_lib
import json
import re
import time

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant

BASE = "https://www.hondacarindia.com"
DELAY = 0.6
ROBOTS_BLOCKED_PRICE_PAGES = {"honda-zrv"}

FUEL = {"petrol": "Petrol", "diesel": "Diesel", "e:hev": "Strong Hybrid"}


def _next_data(html: str) -> dict:
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        raise NotSupported("Honda page layout changed: __NEXT_DATA__ not found")
    return json.loads(m.group(1))["props"]["pageProps"]


def _inr_fmt(n: int) -> str:
    """170900 -> '1,70,900' (Indian digit grouping)."""
    s = str(n)
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    return ",".join(re.findall(r"\d{1,2}(?=(?:\d{2})*$)", head)) + "," + tail


def _clean(s: str) -> str:
    s = re.sub(r"<!--.*?-->|<[^>]+>", " ", s or "", flags=re.S)
    return re.sub(r"\s+", " ", html_lib.unescape(s)).strip()


def _trans(t: str) -> str:
    t = (t or "").upper()
    if "CVT" in t:
        return "CVT"
    if "MT" in t or "MANUAL" in t:
        return "Manual"
    return "Automatic"


class HondaAdapter(BrandAdapter):
    brand = "Honda"
    slug = "honda"
    website = BASE

    def __init__(self):
        self._c = None

    def _client(self):
        if self._c is None:
            self._c = self.client()
        return self._c

    def _get(self, path, **kw):
        time.sleep(DELAY)
        r = self._client().get(BASE + path, **kw)
        r.raise_for_status()
        return r

    def _post(self, path, payload):
        time.sleep(DELAY)
        r = self._client().post(BASE + path, json=payload)
        r.raise_for_status()
        return r.json()

    # ---------------------------------------------------------------- models
    def _categories(self) -> dict:
        html = self._get("/").text
        cats = {}
        for blob in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
            try:
                d = json.loads(blob)
            except ValueError:
                continue
            for el in d.get("itemListElement", []) if isinstance(d, dict) else []:
                it = el.get("item") or {}
                if it.get("url") and it.get("category"):
                    cat = it["category"]          # site says "Sedan", "SUV", "Hybrid SUV"
                    cats[it["url"].rstrip("/").rsplit("/", 1)[-1]] = "SUV" if "SUV" in cat.upper() else cat
        return cats

    def _cars(self) -> list[dict]:
        d = self._get("/api/getAllCarsData").json()
        if d.get("code") != 200:
            raise NotSupported("Honda /api/getAllCarsData did not return data")
        return d["data"]

    def models(self) -> list[dict]:
        cats = self._categories()
        out = []
        for c in self._cars():
            s = c["carModelSiteUrl"]
            out.append({"name": c["carModelName"], "url": f"{BASE}/{s}", "body_type": cats.get(s),
                        "image_url": (c.get("webUrlLink") or [None])[0], "id": c["carModelId"], "slug": s})
        return out

    # ---------------------------------------------------------------- prices
    def _specs(self, slug: str) -> tuple[int | None, int | None]:
        try:
            html = self._get(f"/{slug}/tech-specs").text
        except Exception:
            return None, None
        cc = re.search(r'"Displacement[^"]*","TnSPopData":\[[^\]]*\],"TnSDataArr":\[\{[^}]*?"TnSItemVal":"([\d ,]+)"', html)
        st = re.search(r'"Seating Capacity[^"]*","TnSPopData":\[[^\]]*\],"TnSDataArr":\[\{[^}]*?"TnSItemVal":"(\d+)"', html)
        cc_v = int(re.sub(r"\D", "", cc.group(1))) if cc else None
        return cc_v, (int(st.group(1)) if st else None)

    def _grid(self, car: dict) -> list[tuple[str, str, str]]:
        """(fuelType, transmission, variant) combinations exactly as the site's price picker sends them."""
        slug = car["carModelSiteUrl"]
        if slug in ROBOTS_BLOCKED_PRICE_PAGES:
            return [(car["carModelFuelType"], car["carModelTransmissionType"], car["carModelVarient"])]
        pp = _next_data(self._get(f"/check-price/{slug}").text)
        combos = []
        for block in pp.get("carPriceMainData", []):
            if "grade" not in block:
                continue
            fuel = block["resourceFuelType"]
            for g in block["grade"]:
                for v, p in zip(g["variants"], g["price"]):
                    if v and p:
                        combos.append((fuel, g["transType"], v))
        return combos

    def _city_known(self, city: str) -> str:
        d = self._get("/api/getStateCheck", params={"cityName": city}).json()
        if d.get("code") != 200 or not d.get("data"):
            raise NotSupported(f"Honda does not list the city {city!r}")
        return d["data"][0]["cd_Name"]

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        self._city_known(city)
        cats = self._categories()
        out = []
        for car in self._cars():
            slug = car["carModelSiteUrl"]
            cc, seats = self._specs(slug)
            src = f"{BASE}/check-price/{slug}"
            for fuel, trans, var in self._grid(car):
                d = self._post("/api/getCarPrice", {"carID": car["carModelId"], "city": city, "fuelType": fuel,
                                                     "transmission": trans, "variant": var})
                rows = d.get("data") or []
                if not rows or not int(float(rows[0].get("P_Price") or 0)):
                    continue
                f = FUEL.get(fuel.lower(), fuel)
                out.append(Variant(
                    model=car["carModelName"], variant=f"{var} {trans.split(' ')[0]}",
                    fuel=f, transmission="e-CVT" if f == "Strong Hybrid" else _trans(trans),
                    ex_showroom_inr=int(float(rows[0]["P_Price"])), city=city, source_url=src,
                    body_type=cats.get(slug), engine_cc=cc, seats=seats, model_url=f"{BASE}/{slug}",
                    image_url=(car.get("webUrlLink") or [None])[0]))
        return out

    # ---------------------------------------------------------------- dealers
    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        d = self._get("/api/getStateCheck", params={"cityName": city}).json()
        if not d.get("data"):
            raise NotSupported(f"Honda dealer locator has no city {city!r}")
        row = d["data"][0]
        cid, state = row["cd_ID_pk"], row.get("stateName", "")
        data = self._get("/api/getAllDealerViaTypes", params={"cityId": cid, "radius": 100}).json().get("data") or []
        out = []
        for x in data:
            services = (x.get("dealerServices") or "").upper()
            if "SALES" not in services:
                continue
            out.append(Dealer(
                name=f'{x.get("dealerTitle")} ({x.get("DD_companyName")})' if x.get("DD_companyName") else x.get("dealerTitle"),
                address=x.get("DD_address") or "", city=city, state=state, pincode=x.get("DD_pincode"),
                phone=x.get("DD_telephone"), email=x.get("DD_email"), lat=x.get("latitude"), lng=x.get("longitude"),
                kind="sales+service" if "SERVICE" in services else "sales",
                source_url=f"{BASE}/honda-dealership", website=x.get("DealerWebsite")))
        return out

    # ---------------------------------------------------------------- offers
    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        # Honda publishes one national "Benefits upto Rs X" per model (no city split, no component breakup), so the
        # offers are returned with city=None (valid for every city, including the one asked for).
        page_url = f"{BASE}/shop/shop-offers"
        html = self._get("/shop/shop-offers").text
        pp = _next_data(html)
        lst = (pp.get("carShopOffersData") or {}).get("offersList") or []
        disc = [_clean(x) for x in re.findall(r'<li class="cpBuyingDesclaimer_desc[^"]*">(.*?)</li>', html, re.S)]
        valid = None
        for line in disc:
            m = re.search(r"valid till\s+(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})", line)
            if m:
                valid = dt.datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%d %B %Y").date().isoformat()
        # Home-page disclaimer defines what "TOTAL BENEFITS" consists of.
        home = _next_data(self._get("/").text)
        total_def = _clean(((home.get("disclaimerData") or {}).get("text")) or "")
        total_def = " ".join(s.strip() for s in re.split(r"(?<=\.)\s+", total_def) if "BENEFIT" in s.upper()
                             or "Stock without" in s or "select cities" in s)
        names = {c["carModelSiteUrl"]: c["carModelName"] for c in self._cars()}
        out = []
        for o in lst:
            slug = o.get("prodSiteName")
            d = self._get("/api/getShopCarOffer", params={"carName": slug}).json()
            det = (d.get("data") or {}) if d.get("code") == 200 else {}
            lines = [x.replace("|^|", ",").replace("₹,", "₹ ") for x in (det.get("offersList") or [])]
            amount = det.get("offerUpto") or o.get("offerUpto")
            out.append(Offer(
                model=names.get(slug, o["prodName"]), kind="other",
                title=f"Total benefits up to ₹{_inr_fmt(int(amount))}" if amount else "Benefits",
                amount_inr=int(amount) if amount else None,
                details=" | ".join(lines + ([det["offerDesc"]] if det.get("offerDesc") else []) + disc),
                conditions=" ".join(x for x in [total_def] + [x for x in disc if "valid till" not in x] if x) or None,
                valid_until=valid, city=None,
                source_url=f"{BASE}/shop/shop-offers/{slug} (API {BASE}/api/getShopCarOffer?carName={slug})"))
        corp = next((x for x in disc if "Corporate" in x), None)
        if corp:
            out.append(Offer(model=None, kind="corporate", title="Additional offers for selected corporates",
                             amount_inr=None, details=" | ".join(disc), conditions=corp, valid_until=valid, city=None,
                             source_url=page_url))
        return out


ADAPTER = HondaAdapter()
