"""
JSW MG Motor India - https://www.mgmotor.co.in (+ its premium "MG Select" channel https://www.mgselect.co.in, M9/Cyberster).

Endpoints used (all called by MG's own pages; API keys are the public x-api-key values the pages embed in their HTML,
re-read from the page on every run rather than hard-coded):
  GET  /tools/mg-cars-on-road-price-calculator     -> data-vehicles-endpoint / data-calculate-endpoint / data-*-api-key
  GET  https://dqjwojf1la.execute-api.ap-south-1.amazonaws.com/prod/models      every model + variant, fuel, transmission,
                                                                                  ex-showroom (site's default list)
  POST https://dqjwojf1la.execute-api.ap-south-1.amazonaws.com/prod/calculate   {model, variant, exShowroom, state, city,
                                                                                  modelSalesCode} -> price breakup for the
                                                                                  city (what "What You'll Actually Pay" shows)
  GET  /tools/car-dealers                          JSON-LD AutoDealer list (name, address, pincode, map lat/lng per city)
  GET  https://eeysubngbk.execute-api.ap-south-1.amazonaws.com/prod/api/dealers?latitude&longitude&type=dealer&modelLine
                                                   dealer locator API (phone, email, state, facility type, website)
  GET  /                                           footer model links; GET /vehicles/<model> -> schema.org Vehicle
                                                   bodyType, vehicleSeatingCapacity, Product image
  GET  https://www.mgselect.co.in/m9  (and /cyberster)   "Ex-showroom price: Rs X" header per MG Select model

Price note: MG publishes ONE ex-showroom price nationally. The calculator's /calculate response for Hyderabad
(state Telangana) returns the same "Ex-showroom price" component as for Delhi/Mumbai and only road tax etc. differ.
prices(city) therefore calls /calculate for the requested city and records the ex-showroom component it returns, with
city = the requested city. MG Select prices are national with no city stated -> city="India (national)".
Verified 2026-10-19: Astor VTI-TECH MT SELECT ex-showroom 12,40,100 for Hyderabad/Delhi/Mumbai (calculator),
Hyderabad on-road 15,37,724 (cross-checked against the /dealer endpoint's Telangana on-road row: identical);
MG M9 79,94,800 and Cyberster 82,49,800 from mgselect.co.in headers. 8 Hyderabad dealers in JSON-LD == 8 in API.
Offers: none published (re-checked 2026-10-22, home + every /vehicles/ page + sitemap.xml + llm.txt + corporate-sales
+ mgselect.co.in; /tools/bank-offers redirects to /) -> offers() raises NotSupported with the pages checked.
Known gaps: Hector Tomahawk is listed but only shows
"starting at" BaaS prices, so it is in models() but not prices(); engine cc / battery kWh are not in the price data;
seats come from the model page schema (model level).
"""

from __future__ import annotations

import json
import re
import time

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant

BASE = "https://www.mgmotor.co.in"
SELECT = "https://www.mgselect.co.in"
DELAY = 0.6

FUEL = {"PETROL": "Petrol", "DIESEL": "Diesel", "EV": "Electric", "CNG": "CNG", "HYBRID": "Hybrid", "PHEV": "Hybrid"}
TRANS = {"MT": "Manual", "AT": "Automatic", "CVT": "CVT", "DCT": "DCT"}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


class MGAdapter(BrandAdapter):
    brand = "MG Motor"
    slug = "mg"
    website = BASE

    def __init__(self):
        self._c = None
        self._cfg = None

    def _client(self):
        if self._c is None:
            self._c = self.client()
        return self._c

    def _get(self, url, **kw):
        time.sleep(DELAY)
        r = self._client().get(url, **kw)
        r.raise_for_status()
        return r

    # ------------------------------------------------------------ config read from the calculator page
    def _config(self) -> dict:
        if self._cfg is None:
            html = self._get(f"{BASE}/tools/mg-cars-on-road-price-calculator").text
            cfg = dict(re.findall(r'data-((?:calculate|vehicles|dealer)-(?:endpoint|api-key))="([^"]+)"', html))
            loc = re.search(r'id="locateDealerEndpoint"[^>]*value="([^"]+)"', html)
            key = re.search(r'id="locateDealerkey"[^>]*value="([^"]+)"', html)
            if not cfg.get("vehicles-endpoint") or not cfg.get("calculate-endpoint"):
                raise NotSupported("MG price calculator layout changed (endpoints not found)")
            cfg["locate-endpoint"] = loc.group(1) if loc else None
            cfg["locate-key"] = key.group(1) if key else cfg.get("vehicles-api-key")
            self._cfg = cfg
        return self._cfg

    def _api_models(self) -> list[dict]:
        cfg = self._config()
        d = self._get(cfg["vehicles-endpoint"], headers={"x-api-key": cfg.get("vehicles-api-key", "")}).json()
        return d.get("models") or []

    # ------------------------------------------------------------ models
    def _footer_links(self) -> dict:
        html = self._get(BASE + "/").text
        links = {}
        for href, name in re.findall(r'<a class="cmp-footer-component__col-list-item--link" href="(/vehicles/[a-z0-9\-]+)">\s*([^<]+?)\s*<', html):
            links[name.strip()] = BASE + href
        for href in re.findall(r'href="(/vehicles/[a-z0-9\-]+)"', html):
            links.setdefault("#" + href, BASE + href)  # non-footer model pages (e.g. Windsor Pro)
        return links

    def _url_for(self, name: str, links: dict) -> str | None:
        if name in links:
            return links[name]
        toks = [t for t in re.split(r"\s+", name.lower()) if t not in ("mg",)]
        for k, u in links.items():
            if k.startswith("#") and all(t in u for t in toks):
                return u
        return None

    def _page_meta(self, url: str | None) -> dict:
        if not url:
            return {}
        try:
            html = self._get(url).text
        except Exception:
            return {}
        bt = re.search(r'"bodyType"\s*:\s*"([^"]+)"', html)
        seats = (re.search(r'"vehicleSeatingCapacity"\s*:\s*\{[^}]*"value"\s*:\s*"(\d+)', html)
                 or re.search(r'"(?:vehicleS|s)eatingCapacity"\s*:\s*"?(\d+)', html))
        img = re.search(r'"@type"\s*:\s*"Product".{0,800}?"image"\s*:\s*"([^"]+)"', html, re.S)
        return {"body_type": bt.group(1) if bt else None, "seats": int(seats.group(1)) if seats else None,
                "image_url": img.group(1) if img else None}

    def _select_models(self) -> list[dict]:
        """MG Select (premium channel run by JSW MG Motor India): one national ex-showroom price per model."""
        out = []
        html = self._get(SELECT + "/m9").text   # header lists every MG Select model with its price
        for name, price in re.findall(r'>\s*([A-Z0-9][A-Z0-9 \-]{1,30}?)\s*</[^>]+>\s*<p[^>]*>\s*Ex-showroom price:\s*₹\s*([\d,]+)', html):
            out.append({"name": "MG " + name.strip().title().replace("M9", "M9"), "price": int(price.replace(",", "")),
                        "url": f"{SELECT}/{name.strip().lower()}"})
        return out

    MODEL_IMAGES = {
        "MG Hector": "https://mgmotor.scene7.com/is/image/mgmotor/mgi-hector-thm-img-0001?fmt=png-alpha",
        "MG Hector Plus": "https://mgmotor.scene7.com/is/image/mgmotor/mgi-hector-thm-img-0001?fmt=png-alpha",
        "MG Gloster": "https://mgmotor.scene7.com/is/image/mgmotor/004-khaki-green-s-black-image?wid=1600&fmt=webp-alpha&resMode=bisharp&fit=constrain&qlt=80",
        "MG Cyberster": "https://mgmotor.scene7.com/is/image/mgmotor/Cyberster_4?fmt=webp-alpha&resMode=bisharp&fit=constrain&qlt=85&wid=1080",
        "MG M9": "https://mgmotor.scene7.com/is/image/mgmotor/m9_5?fmt=webp-alpha&resMode=bisharp&fit=constrain&qlt=85&wid=720",
        "MG Majestor": "https://mgmotor.scene7.com/is/image/mgmotor/004-khaki-green-s-black-image?wid=1600&fmt=webp-alpha&resMode=bisharp&fit=constrain&qlt=80",
    }

    def models(self) -> list[dict]:
        links = self._footer_links()
        out, seen = [], set()
        for m in self._api_models():
            url = self._url_for(m["carName"], links)
            meta = self._page_meta(url)
            img = meta.get("image_url") or self.MODEL_IMAGES.get(m["carName"])
            out.append({"name": m["carName"], "url": url, "body_type": meta.get("body_type"),
                        "image_url": img, "seats": meta.get("seats")})
            seen.add(m["carName"])
        for name, url in links.items():
            if not name.startswith("#") and name not in seen:      # listed on the site but not in the price API
                meta = self._page_meta(url)
                img = meta.get("image_url") or self.MODEL_IMAGES.get(name)
                out.append({"name": name, "url": url, "body_type": meta.get("body_type"),
                            "image_url": img, "seats": meta.get("seats"), "priced": False})
        for s in self._select_models():
            img = self.MODEL_IMAGES.get(s["name"])
            out.append({"name": s["name"], "url": s["url"], "body_type": "Convertible" if "Cyberster" in s["name"] else "MUV", "image_url": img})
        return out

    # ------------------------------------------------------------ city helpers
    def _city_dealers_ld(self, city: str) -> list[dict]:
        html = self._get(f"{BASE}/tools/car-dealers").text
        for blob in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
            if "AutoDealer" not in blob:
                continue
            items = [e["item"] for e in json.loads(blob).get("itemListElement", [])]
            return [i for i in items if (i.get("address") or {}).get("addressLocality", "").strip().lower() == city.lower()]
        return []

    def _locate(self, city: str) -> tuple[list[dict], list[dict]]:
        """(JSON-LD dealers in city, locator-API dealers around the city's dealers)."""
        ld = self._city_dealers_ld(city)
        if not ld:
            raise NotSupported(f"MG lists no dealer in {city!r}; cannot resolve the city/state")
        pts = []
        for i in ld:
            m = re.search(r"daddr=([\d.]+),([\d.]+)", i.get("hasMap", ""))
            if m:
                pts.append((float(m.group(1)), float(m.group(2))))
        cfg = self._config()
        api = []
        if cfg.get("locate-endpoint") and pts:
            seen = set()
            # centroid first; then each listed outlet's own coordinates until every JSON-LD outlet is covered
            queries = [(sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))] + pts
            for lat, lng in queries:
                d = self._get(cfg["locate-endpoint"], params={"latitude": lat, "longitude": lng, "type": "dealer",
                                                              "modelLine": "HECTOR"},
                              headers={"x-api-key": cfg["locate-key"]}).json()
                for x in d.get("DealerList") or []:
                    if x["DealerCode"] not in seen and (x.get("City") or "").strip().lower() == city.lower():
                        seen.add(x["DealerCode"]); api.append(x)
                if len(api) >= len(ld):
                    break
        return ld, api

    # ------------------------------------------------------------ prices
    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        ld, api = self._locate(city)
        state = next((x.get("State") for x in api if x.get("State")), None)
        if not state:
            raise NotSupported(f"Could not resolve the state for {city!r} from MG's dealer locator")
        cfg = self._config()
        links = self._footer_links()
        out = []
        for m in self._api_models():
            url = self._url_for(m["carName"], links)
            meta = self._page_meta(url)
            for v in m.get("variants", []):
                time.sleep(DELAY)
                body = {"model": m["modelLine"], "variant": v["variantName"], "exShowroom": v["exShowroomPrice"],
                        "state": state, "pincode": "", "city": city, "modelSalesCode": v["modelSalesCode"]}
                r = self._client().post(cfg["calculate-endpoint"], json=body, headers={"x-api-key": cfg.get("calculate-api-key", "")})
                d = r.json() if r.status_code == 200 else {}
                if d.get("statusCode") != 200:
                    continue
                ex = next((c["amount"] for c in d.get("components", []) if c.get("name", "").lower().startswith("ex-showroom")),
                          d.get("exShowroom"))
                seats = re.search(r"(\d)\s*STR", v["variantName"])
                out.append(Variant(
                    model=m["carName"], variant=v["variantName"], fuel=FUEL.get(v["fuelType"].upper(), v["fuelType"].title()),
                    transmission=TRANS.get(v["transmission"].upper(), v["transmission"]), ex_showroom_inr=int(ex),
                    city=city, source_url=f"{BASE}/tools/mg-cars-on-road-price-calculator", body_type=meta.get("body_type"),
                    seats=int(seats.group(1)) if seats else meta.get("seats"), model_url=url, image_url=meta.get("image_url")))
        for s in self._select_models():
            out.append(Variant(model=s["name"], variant=s["name"].replace("MG ", ""), fuel="Electric", transmission="Automatic",
                               ex_showroom_inr=s["price"], city="India (national)", source_url=s["url"], model_url=s["url"]))
        return out

    # ------------------------------------------------------------ dealers
    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        ld, api = self._locate(city)
        out, names = [], set()
        for x in api:
            ft = (x.get("Facility_Type") or "").upper()
            name = re.sub(r"\s+", " ", x["DealerName"]).strip()
            # Facility_Type: 1S = sales, 3S = sales+service+spares, EC = experience centre (sells); 2S = service only
            if "SALES" not in name.upper() and "1S" not in ft and "3S" not in ft and ft != "EC":
                continue
            names.add(_norm(name))
            out.append(Dealer(
                name=name, address=(x.get("Street") or "").strip(" ,"), city=x.get("City") or city, state=x.get("State") or "",
                pincode=x.get("Postal_Code"), phone=x.get("Mobile") or x.get("Telephone"), email=x.get("Sales_Manager_Email"),
                lat=float(x["Lattitude"]) if x.get("Lattitude") else None, lng=float(x["Longitude"]) if x.get("Longitude") else None,
                kind="sales+service" if "3S" in ft or "SERVICE" in name.upper() else "sales",
                source_url=f"{BASE}/tools/car-dealers", website=x.get("WebSite") or None))
        for i in ld:                                       # outlets on the page the API did not return
            if _norm(i["name"]) in names:
                continue
            m = re.search(r"daddr=([\d.]+),([\d.]+)", i.get("hasMap", ""))
            a = i.get("address") or {}
            out.append(Dealer(name=i["name"], address=(a.get("streetAddress") or "").strip(" ,"), city=city, state="",
                              pincode=a.get("postalCode"), phone=None, email=None,
                              lat=float(m.group(1)) if m else None, lng=float(m.group(2)) if m else None,
                              kind="sales+service" if "SERVICE" in i["name"].upper() else "sales",
                              source_url=f"{BASE}/tools/car-dealers"))
        return out

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise NotSupported(
            "JSW MG publishes no current purchase offers on its own sites (re-checked 2026-10-22): mgmotor.co.in "
            "sitemap.xml and llm.txt list no offers page; /tools/bank-offers (named in llm.txt) redirects to the home "
            "page; home, /vehicles/{mghector,mgastor,windsor-ev-electric-car-in-india,windsor-ev-pro,"
            "comet-ev-electric-car-in-india,mgzsev-electric-car-in-india,hector-tomahawk,mg-majestor-biggest-suv-india}, "
            "/vehicles/mghector-campaign and /tools/corporate-sales carry no discount/benefit/validity text; "
            "mgselect.co.in sitemap and /m9 have none either. BaaS per-km pricing is a price plan, not an offer.")

    def specs(self):
        raise NotSupported('mgmotor.co.in publishes specs/equipment only inside brochure PDFs whose tables lose their row/column structure in text extraction (ticks are graphics), so no value can be read without guessing (checked 2026-10-23)')


ADAPTER = MGAdapter()
