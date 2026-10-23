"""
Tata Motors passenger vehicles adapter - ICE cars on https://tata.cars and Tata.ev on https://ev.tata.cars
(the official domains; TLS certificate issued to "TATA MOTORS LIMITED"). Reads ONLY those two hosts. Nothing is
hardcoded: every model, variant name, price, dealer and spec below is read live from the endpoints listed here.

Endpoints (AEM selectors the site's own clientlib calls - /etc.clientlibs/tml-framework/clientlibs/clientlib-base-min.js):
  models  : header navigation of https://tata.cars/ and https://ev.tata.cars/ -> links <host>/<slug>/<ice|ev>.html
            + each model's price page <host>/<slug>/<ice|ev>/price.html: model name (var _webengagePplName), og:image,
              modelId / pplId / brand (data-modelId, data-pplId, data-brand on #accordionExample) and the variant cards
              that page renders (data-versionType + <h5>/<h6> title). A model is "on sale" when its price page renders cards.
            body_type: the first of SUV / hatchback / sedan / MPV the model's own price page uses in its title / meta
              description / visible copy (the site publishes no body-type field).
  prices  : POST <price page>.getPriceCityList.json            -> 1,409 price cities (Hyderabad = "India-TS-HYDERABAD")
            POST <price page>.getpricefilteredresult.json  JSON {vehicleCategory, modelId, parentProductId, cityId,
                 filtersSelected:[{filterType:"price", values:["0L","1000L"]}]}
              -> variantPriceFeatures[{variantId, variantLabel "Smart P MT Standard, Petrol", priceDetails.originalPrice}]
            Only variantIds that the price page renders as cards are kept (the API also returns hidden/internal SKUs such
            as "IB Nexon K3.ev ..."). Variant name = the card's <h5> + <h6> exactly as shown ("Pure + CNG Automatic").
  specs   : <host>/<slug>/<ice|ev>/specifications.html -> data-productspecjson attribute (JSON: variantSpecFeature[
              {variantLabel, productSpecifications[{specTypeTitle, specList[{specLabel, specValue}]}], productFeatures}])
            Used for engine_cc ("Engine Capacity (cc)"), battery_kwh ("Battery Pack": "45 kWh ...") and seats.
            POST <price page>.getpricefilteroptions.json -> the model's transmission options ("5 Speed AMT").
  dealers : POST https://tata.cars/dealer-locator.dealerlist.json and https://ev.tata.cars/dealer-locator.dealerlist.json
              JSON {"locations":[{"cityName": city}]} -> outlets; kept: divType "TMPC-DLR-Sales" (dealer showrooms;
              "TMA" = Tata Motors Assured pre-owned, Parts and Sv&Pa outlets are excluded).
  offers  : POST <price page>.getproductpriceoffers.json {modelId, parentProductId, cityName, cityId}
              -> results.priceOffersDetails[].offersList[].offers[{offerTitle, offerDescription}] (no validity date is
              published, so valid_until stays None; amount = the rupee figure in the title, e.g. "Offers up to Rs 1,71,000").
  images  : Scene7 renditions (s7ap1.scene7.com/is/image/tatamotors|tatapassenger) referenced by the model's own overview
            / price page, >= 800 px wide by their preset ($BA-1920-925-D$), og:image first, unique per model.

robots.txt (both hosts) only disallows /*?modelId, /*?sku, /account/login.html, PDFs/brochures and one offer page;
none of the URLs above use those. TLS verification stays on; Polite() spaces requests 1 s apart.

Verified 2026-10-22 (run from backend/: python -m onroad.ingest tata_motors --city Hyderabad):
  * 15 models (9 ICE incl. Aeris, 6 EV), 429 priced variants; 27 Hyderabad sales outlets; 6 offers (Curvv.ev,
    Nexon.ev, Punch.ev, 3 x Tiago); ~8.2k spec values / ~34k feature rows for the matched variants.
  * getpricefilteredresult for cityId India-TS-HYDERABAD and India-DL-DELHI returned identical prices (Tata publishes
    one ex-showroom list); the Hyderabad city id is used because the site's price tool lists it.
  * Spot-checks vs the cards on the live price pages: Punch "Smart" Rs 5,74,990 (tata.cars/punch/ice/price.html),
    Nexon "Smart 1.2" Rs 7,39,990 (nexon/ice/price.html), Tiago "Smart" Rs 4,76,990 (tiago/ice/price.html),
    Harrier "Smart" (Diesel) Rs 13,99,990 (harrier/ice/price.html), Nexon.ev "Creative + MR" Rs 12,49,000.
Known gaps:
  * The price API intermittently answers HTTP 200 + {"errorData": 504}; prices() retries 4x, then raises so ingest keeps
    the previous prices rather than retiring a model.
  * engine_cc / seats: value stated by >= 90% of that model+fuel's spec-page rows (one Nexon row says 1496 cc for a
    1.2 petrol); None when they disagree (Nexon CNG cc, Safari 6/7 seats). battery_kwh: the single pack, or the pack
    whose size appears in the card name - None for Nexon.ev "MR" and one Tiago EV card.
  * specs(): Spec/Feature rows only for spec-page variants whose label matches a price-card id (~315 variants);
    features are stored with key "other" and the site's own wording.
  * Offers carry no end date on the site; "Offer may vary state to state" is kept as conditions.
  * The price page meta description can lag the live API (Punch meta "from Rs 5.69 Lakh" vs card 5,74,990); the API
    value (what the cards render) is used.
"""

from __future__ import annotations

import html as _html
import json
import re
import time

from ..base import BrandAdapter, Dealer, Feature, NotSupported, Offer, Spec, Variant
from ._ga_common import Polite, clean, inr, make_client, norm, visible_text
from ._offers import amount, kind_of

SCENE7 = re.compile(r'https://s7ap1\.scene7\.com/is/image/[^"\'\s<>),]+')
PRESET_W = re.compile(r"\$[A-Za-z]+-(\d+)-(\d+)(?:-([A-Z]))?\$")

ICE = "https://tata.cars"
EV = "https://ev.tata.cars"
HOSTS = {"ice": ICE, "ev": EV}

NAV_LINK = re.compile(r'href="(https://(?:ev\.)?tata\.cars)/([a-z0-9-]+)/(ice|ev)\.html"')
CARD = re.compile(r'data-versionType="([^"]*)">\s*<div class="card-section">\s*<div class="card-title[^"]*">\s*'
                  r'<h5[^>]*>(.*?)</h5>\s*<h6[^>]*>(.*?)</h6>', re.S)
IDS = re.compile(r'id="accordionExample"\s+data-modelId="([^"]*)"\s+data-pplId="([^"]*)"\s+data-brand="([^"]*)"')
PPL_NAME = re.compile(r'_webengagePplName\s*=\s*"([^"]+)"')
OG_IMAGE = re.compile(r'<meta property="og:image" content="([^"]+)"')
META_DESC = re.compile(r'<meta name="description" content="([^"]*)"')
TITLE = re.compile(r"<title>(.*?)</title>", re.S)
SPEC_JSON = re.compile(r'data-productspecjson="([^"]*)"')

# words the site uses -> base.Variant body types
BODY_WORDS = [("suv", "SUV"), ("hatchback", "Hatchback"), ("sedan", "Sedan"), ("mpv", "MUV")]

# Indian state / UT codes the dealer API returns ("TS") -> names (standard abbreviations, not price data)
STATES = {
    "AP": "Andhra Pradesh", "AR": "Arunachal Pradesh", "AS": "Assam", "BR": "Bihar", "CG": "Chhattisgarh", "CT": "Chhattisgarh",
    "GA": "Goa", "GJ": "Gujarat", "HR": "Haryana", "HP": "Himachal Pradesh", "JH": "Jharkhand", "KA": "Karnataka",
    "KL": "Kerala", "MP": "Madhya Pradesh", "MH": "Maharashtra", "MN": "Manipur", "ML": "Meghalaya", "MZ": "Mizoram",
    "NL": "Nagaland", "OD": "Odisha", "OR": "Odisha", "PB": "Punjab", "RJ": "Rajasthan", "SK": "Sikkim", "TN": "Tamil Nadu",
    "TS": "Telangana", "TG": "Telangana", "TR": "Tripura", "UP": "Uttar Pradesh", "UK": "Uttarakhand", "UT": "Uttarakhand",
    "WB": "West Bengal", "DL": "Delhi", "CH": "Chandigarh", "JK": "Jammu and Kashmir", "LA": "Ladakh", "PY": "Puducherry",
    "AN": "Andaman and Nicobar Islands", "DN": "Dadra and Nagar Haveli and Daman and Diu", "LD": "Lakshadweep",
}


def _fuel(label_suffix: str, line: str) -> str:
    f = (label_suffix or "").strip().lower()
    if line == "ev" or "electric" in f:
        return "Electric"
    if "cng" in f:
        return "CNG"
    if "diesel" in f:
        return "Diesel"
    return "Petrol"


def _transmission(text: str, line: str, options: list[str]) -> str:
    """Card id + card title ('Pure + P AMT', 'Pure X Automatic', 'Creative DCA 1.2') + the model's own transmission
    filter options ('5 Speed MT', '5 Speed AMT', '6 Speed AT', '7 Speed DCA') -> base.Variant transmission."""
    if line == "ev":
        return "Automatic"                       # single-speed EV drive
    t = " " + text.upper().replace("(", " ").replace(")", " ") + " "
    if re.search(r"DCA|DCT", t):
        return "DCT"
    if re.search(r"P?AMT\b", t):
        return "AMT"
    if re.search(r"\sAT\s|AUTOMATIC", t):
        autos = {k for o in options for k in ("AMT", "DCA", "AT") if re.search(rf"\b{k}\b", o.upper())}
        if "AUTOMATIC" in t and len(autos) == 1:
            return {"AMT": "AMT", "DCA": "DCT", "AT": "Automatic"}[autos.pop()]
        return "Automatic"
    if re.search(r"MT\s", t) or any(re.search(r"\bMT\b|MANUAL", o.upper()) for o in options):
        return "Manual"
    return ""


def _num(s: str | None) -> float | None:
    m = re.search(r"\d+(?:\.\d+)?", s or "")
    return float(m.group(0)) if m else None


class TataMotorsAdapter(BrandAdapter):
    brand = "Tata Motors"
    slug = "tata_motors"
    website = ICE

    def __init__(self):
        self._pages: dict[str, str] = {}
        self._catalog: list[dict] | None = None
        self._specjson: dict[str, list] = {}

    def client(self):
        return make_client()

    # ---------------------------------------------------------------- helpers
    def _page(self, h: Polite, url: str) -> str | None:
        if url not in self._pages:
            h._wait()
            r = h.c.get(url)
            self._pages[url] = r.text if r.status_code == 200 else None
        return self._pages[url]

    def _nav(self, h: Polite) -> list[tuple[str, str, str]]:
        seen, out = set(), []
        for home in (ICE + "/", EV + "/"):
            page = self._page(h, home) or ""
            for host, slug, line in NAV_LINK.findall(page):
                if (slug, line) not in seen:
                    seen.add((slug, line))
                    out.append((host, slug, line))
        return out

    @staticmethod
    def _body(page: str) -> str | None:
        head = " ".join(TITLE.findall(page)[:1] + META_DESC.findall(page)[:1]).lower()
        for w, b in BODY_WORDS:
            if re.search(rf"\b{w}", head):
                return b
        text = visible_text(page).lower()
        counts = {b: len(re.findall(rf"\b{w}", text)) for w, b in BODY_WORDS}
        best = max(counts, key=counts.get)
        return best if counts[best] else None

    def _models(self, h: Polite) -> list[dict]:
        if self._catalog is not None:
            return self._catalog
        out = []
        for host, slug, line in self._nav(h):
            price_url = f"{host}/{slug}/{line}/price.html"
            page = self._page(h, price_url)
            if not page:
                continue
            ids = IDS.search(page)
            cards = [(vid, clean(t5), clean(t6)) for vid, t5, t6 in CARD.findall(page)]
            if not ids or not cards:
                continue
            name = _html.unescape(PPL_NAME.search(page).group(1)) if PPL_NAME.search(page) else slug.title()
            title = TITLE.search(page)
            tname = re.search(r"Tata\s+(.+?)\s+Price", clean(title.group(1))) if title else None
            if line == "ev" and "ev" not in name.lower() and tname and "ev" in tname.group(1).lower():
                name = tname.group(1)              # 'Tiago' -> 'Tiago EV' as the EV price page titles it
            overview = self._page(h, f"{host}/{slug}/{line}.html") or ""
            og = [_html.unescape(u) for p_ in (overview, page) for u in OG_IMAGE.findall(p_)]
            cands = og + [_html.unescape(u) for u in SCENE7.findall(overview + page)]
            out.append({
                "name": name,
                "url": f"{host}/{slug}/{line}.html",
                "body_type": self._body(page) or (self._body(overview) if overview else None),
                "image_url": None, "_images": cands,
                "fuel": "Electric" if line == "ev" else None,
                "line": line, "slug": slug, "host": host,
                "price_page": price_url, "api": price_url[:-len(".html")],
                "modelId": ids.group(1), "pplId": ids.group(2), "vehicleCategory": ids.group(3),
                "cards": cards,
                "source_url": price_url,
            })
        used: set[str] = set()
        for m in out:
            m["image_url"] = self._pick_image(m.pop("_images"), m["slug"], used)
            if m["image_url"]:
                used.add(m["image_url"].split("?")[0])
        for m in out:                              # e.g. Tiago ICE page names no body type; its EV sibling does
            if not m["body_type"]:
                m["body_type"] = next((o["body_type"] for o in out if o["slug"] == m["slug"] and o["body_type"]), None)
        self._catalog = out
        return out

    @staticmethod
    def _pick_image(urls: list[str], slug: str, used: set[str]) -> str | None:
        """Hero image from the model's own pages: a Scene7 rendition >= 800 px wide (preset '$BA-1920-925-D$'),
        preferring the page's og:image, then assets named after the model, desktop renditions; never an asset another
        model already uses, never the logo / generic price banner."""
        # 1st choice: a transparent colour cutout = frame 0 of the page's 360-degree colour viewer ("BengalRogue-0",
        # "Oxide-0-2"): a clean side view on no background, which renders far better on cards than a banner photo.
        for u in dict.fromkeys(urls):
            asset = u.split("?")[0]
            if asset not in used and re.fullmatch(r"[A-Za-z]+-0(?:-\d+)?", asset.rsplit("/", 1)[-1]):
                return asset + "?fmt=webp-alpha&wid=1200"
        best, best_score = None, None
        for i, u in enumerate(dict.fromkeys(urls)):
            asset = u.split("?")[0]
            name = asset.rsplit("/", 1)[-1].lower()
            w = PRESET_W.search(u)
            if not w or int(w.group(1)) < 800 or asset in used or re.search(r"logo|price-banner|placeholder|icon", name):
                continue
            score = (i >= 0 and u in urls[:2],  # og:image of overview / price page
                     slug in name, (w.group(3) or "S") in "DS", "banner" in name or "-d" in name, -i)
            if best_score is None or score > best_score:
                best, best_score = u, score
        return best

    def _spec_rows(self, h: Polite, m: dict) -> list:
        url = f"{m['host']}/{m['slug']}/{m['line']}/specifications.html"
        if url not in self._specjson:
            page = self._page(h, url)
            rows = []
            if page:
                sj = SPEC_JSON.search(page)
                if sj:
                    try:
                        rows = json.loads(_html.unescape(sj.group(1)))["results"]["variantSpecFeature"]
                    except (ValueError, KeyError, TypeError):
                        rows = []
            self._specjson[url] = rows
        return self._specjson[url]

    @staticmethod
    def _spec_value(row: dict, label_rx: str) -> str | None:
        for g in row.get("productSpecifications") or []:
            for s in g.get("specList") or []:
                if re.search(label_rx, s.get("specLabel") or "", re.I) and s.get("specValue"):
                    return s["specValue"]
        return None

    def _values(self, rows: list, line: str, label_rx: str) -> list[tuple[str, str, float]]:
        """[(fuel, spec-page variant label, number)] for one spec label."""
        out = []
        for r in rows:
            label = r.get("variantLabel") or ""
            v = _num(self._spec_value(r, label_rx))
            if v is not None:
                out.append((_fuel(label.rsplit(",", 1)[-1], line), label, v))
        return out

    @staticmethod
    def _agreed(vals: list[float]) -> float | None:
        """The value at least 90% of the spec-page rows state (one stray row on the site must not blank the field)."""
        if not vals:
            return None
        best = max(set(vals), key=vals.count)
        return best if vals.count(best) >= 0.9 * len(vals) else None

    def _engine_cc(self, vals, fuel: str, name: str) -> int | None:
        same = [(lab, v) for f, lab, v in vals if f == fuel]
        disp = re.search(r"\b(\d\.\d)\b", name)
        if disp:                                   # '1.2' in the card name -> spec rows of the same displacement
            same = [(lab, v) for lab, v in same if disp.group(1) in lab] or same
        v = self._agreed([v for _, v in same])
        return int(v) if v else None

    @staticmethod
    def _battery(vals, name: str) -> float | None:
        packs = sorted({v for _, _, v in vals})
        if len(packs) == 1:
            return packs[0]
        toks = set(re.findall(r"\d+", name))
        hit = [p for p in packs if str(int(p)) in toks]
        return hit[0] if len(hit) == 1 else None

    def _transmission_options(self, h: Polite, m: dict) -> list[str]:
        if "tx_options" not in m:
            r = h.post(m["api"] + ".getpricefilteroptions.json",
                       data={"vehicleCategory": m["vehicleCategory"], "modelId": m["modelId"], "parentProductId": m["pplId"],
                             "cityId": getattr(self, "_cid", None) or "India-TS-HYDERABAD"})
            try:
                lists = (r.json().get("results") or {}).get("filterOptionsList") or []
            except ValueError:
                lists = []
            m["tx_options"] = [o.get("optionValue") or "" for f in lists if f.get("filterType") == "transmission_type"
                               for o in f.get("filterOption") or []]
        return m["tx_options"]

    # ---------------------------------------------------------------- models
    def models(self) -> list[dict]:
        with Polite(self.client()) as h:
            cat = self._models(h)
        if not cat:
            raise NotSupported("no tata.cars / ev.tata.cars price page rendered any variant")
        return [{k: m[k] for k in ("name", "url", "body_type", "image_url", "fuel", "source_url")} for m in cat]

    # ---------------------------------------------------------------- prices
    def _city_id(self, h: Polite, m: dict, city: str) -> tuple[str | None, str | None]:
        r = h.post(m["api"] + ".getPriceCityList.json", data={"vehicleCategory": "", "serviceCategory": "", "vehicleType": ""})
        want = city.strip().upper()
        for c in r.json().get("results", {}).get("cityList", []):
            if isinstance(c, dict) and (c.get("city") or "").upper() == want:
                return c["cityId"], c["cityName"]
        return None, None

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        out: list[Variant] = []
        with Polite(self.client()) as h:
            cat = self._models(h)
            if not cat:
                raise NotSupported("no tata.cars / ev.tata.cars price page rendered any variant")
            city_id, _ = self._city_id(h, cat[0], city)
            self._cid = city_id
            label_city = city if city_id else "India (national)"
            if not city_id:   # not a price city: the national list (any listed city - prices are identical nationwide)
                city_id = "India-DL-DELHI"
            for m in cat:
                body = {"vehicleCategory": m["vehicleCategory"], "modelId": m["modelId"], "parentProductId": m["pplId"],
                        "cityId": city_id, "filtersSelected": [{"filterType": "price", "values": ["0L", "1000L"]}]}
                rows = []
                for attempt in range(4):           # the price API intermittently answers {"errorData": 504 timed out}
                    r = h.post(m["api"] + ".getpricefilteredresult.json", content=json.dumps(body),
                               headers={"Content-Type": "application/json"})
                    rows = (r.json().get("results") or {}).get("variantPriceFeatures") or []
                    if rows:
                        break
                    time.sleep(5 * (attempt + 1))
                if not rows:   # fail the whole read so ingest keeps the previous prices instead of retiring this model
                    raise RuntimeError(f"tata.cars price API returned no variants for {m['name']}: {r.text[:160]}")
                by_id = {x.get("variantId"): x for x in rows}
                spec_rows = self._spec_rows(h, m)
                cc = self._values(spec_rows, m["line"], r"engine capacity|displacement")
                kwh = self._values(spec_rows, m["line"], r"battery (pack|capacity)")
                seat_vals = self._values(spec_rows, m["line"], r"seating capacity")
                opts = self._transmission_options(h, m)
                names_seen: dict[str, int] = {}
                for vid, t5, t6 in m["cards"]:
                    x = by_id.get(vid)
                    price = inr(((x or {}).get("priceDetails") or {}).get("originalPrice"))
                    if not x or not price:
                        continue
                    base = vid.split("_", 1)[0]
                    fuel = _fuel((x.get("variantLabel") or "").rsplit(",", 1)[-1] if "," in (x.get("variantLabel") or "") else "", m["line"])
                    name = clean(f"{t5} {t6}")
                    names_seen[name] = names_seen.get(name, 0) + 1
                    if names_seen[name] > 1:          # two cards with the same title: keep the API label to tell them apart
                        name = clean((x.get("variantLabel") or base).rsplit(",", 1)[0])
                    self.__dict__.setdefault("_card_names", {})[vid] = (name, _transmission(f"{base} {name}", m["line"], opts))
                    out.append(Variant(
                        model=m["name"], variant=name, fuel=fuel, transmission=_transmission(f"{base} {name}", m["line"], opts),
                        ex_showroom_inr=price, city=label_city, source_url=m["price_page"],
                        body_type=m["body_type"],
                        engine_cc=self._engine_cc(cc, fuel, name) if fuel != "Electric" else None,
                        battery_kwh=self._battery(kwh, name) if fuel == "Electric" else None,
                        seats=int(st) if (st := self._agreed([v for f, _, v in seat_vals if f == fuel])) else None,
                        model_url=m["url"], image_url=m["image_url"]))
        return out

    # ---------------------------------------------------------------- dealers
    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        out, seen = [], set()
        with Polite(self.client()) as h:
            for host in (ICE, EV):
                url = host + "/dealer-locator.dealerlist.json"
                r = h.post(url, content=json.dumps({"locations": [{"cityName": city}]}),
                           headers={"Content-Type": "application/json"})
                try:
                    rows = r.json()
                except ValueError:
                    continue
                for d in rows if isinstance(rows, list) else []:
                    if d.get("divType") != "TMPC-DLR-Sales":
                        continue
                    area = (d.get("dealerDivision") or "").split("-")
                    area = area[2] if len(area) > 3 else ""
                    name = clean(d.get("dealerNameLabel") or d.get("dealerName"))
                    name = f"{name} - {area}" if area else name
                    a1, a2 = clean(d.get("dealerAddress1Label")), clean(d.get("dealerAddress2Label"))
                    addr = a1 if not a2 or a2 == a1 else f"{a1}, {a2}"
                    key = (norm(name), norm(addr))
                    if key in seen:
                        continue
                    seen.add(key)
                    st = d.get("dealerStateLabel") or d.get("dealerState") or ""
                    lat, lng = _num(d.get("dealerLatitude")), _num(d.get("dealerLongitude"))
                    out.append(Dealer(
                        name=name + (" (Tata.ev)" if host == EV else ""), address=addr,
                        city=(d.get("dealerCityLabel") or city).title(), state=STATES.get(st.upper(), st),
                        pincode=d.get("dealerPinCode"), phone=d.get("dealerMobileLabel") or d.get("dealerMobileNumber"),
                        email=d.get("dealerEmailLabel") or d.get("dealerEmailId"), lat=lat, lng=lng, kind="sales",
                        source_url=host + "/dealer-locator.html"))
        if not out:
            raise NotSupported(f"Tata dealer locator lists no sales outlets for {city!r}")
        return out

    # ---------------------------------------------------------------- offers
    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        with Polite(self.client()) as h:
            cat = self._models(h)
            city_id, city_name = self._city_id(h, cat[0], city) if cat else (None, None)
            found = []
            for m in cat:
                r = h.post(m["api"] + ".getproductpriceoffers.json",
                           data={"modelId": m["modelId"], "parentProductId": m["pplId"],
                                 "cityName": city_name or "", "cityId": city_id or ""})
                det = (r.json().get("results") or {}).get("priceOffersDetails") or []
                if det:
                    found.append((m, det))
        if not found:
            raise NotSupported("tata.cars / ev.tata.cars publish no offers: the price pages' getproductpriceoffers.json "
                               "returns an empty priceOffersDetails list for every model")
        out = []
        for m, det in found:
            for block in det:
                for grp in block.get("offersList") or []:
                    for o in grp.get("offers") or []:
                        title = clean(o.get("offerTitle"))
                        desc = clean(o.get("offerDescription"))
                        if not title:
                            continue
                        text = f"{title} {desc}"
                        out.append(Offer(
                            model=m["name"], title=title, amount_inr=amount(title), details=desc or title,
                            valid_until=None, city=city if city_id else None, source_url=m["price_page"],
                            kind=kind_of(text),
                            conditions=desc if desc and desc != title else (grp.get("offerTypeLabel") or None)))
        return out

    # ---------------------------------------------------------------- specs
    def specs(self) -> tuple[list[Spec], list[Feature]]:
        specs: list[Spec] = []
        feats: list[Feature] = []
        with Polite(self.client()) as h:
            cat = self._models(h)
            for m in cat:
                rows = self._spec_rows(h, m)
                if not rows:
                    continue
                src = f"{m['host']}/{m['slug']}/{m['line']}/specifications.html"
                opts = self._transmission_options(h, m)
                # price-card variants of this model: (card name, fuel, transmission) keyed by the card's id base
                cards = {}
                labels = {norm(r.get("variantLabel", "").rpartition(",")[0]): r.get("variantLabel", "") for r in rows}
                seen_nm: dict[str, int] = {}
                for vid, t5, t6 in m["cards"]:
                    base = vid.split("_", 1)[0]
                    nm = clean(f"{t5} {t6}")
                    seen_nm[nm] = seen_nm.get(nm, 0) + 1
                    if seen_nm[nm] > 1:          # same renaming rule as prices(): repeated card titles use the API label
                        nm = clean((labels.get(norm(base)) or base).rsplit(",", 1)[0])
                        if t6 and not nm.lower().endswith(t6.lower()):
                            nm = clean(f"{nm} {t6}")       # the price API's label carries the edition ("Standard")
                    # same name the price read gave this card (it renames repeated card titles), else the card title
                    hit = self.__dict__.get("_card_names", {}).get(vid) or (nm, _transmission(f"{base} {nm}", m["line"], opts))
                    if hit not in cards.setdefault(norm(base), []):
                        cards[norm(base)].append(hit)        # one spec row can serve several cards (Standard / Dark editions)
                for r in rows:
                    label = (r.get("variantLabel") or "")
                    vname, _, fuel_s = label.rpartition(",")
                    fuel = _fuel(fuel_s, m["line"])
                    for name, trans in cards.get(norm(vname), []):
                      for g in r.get("productSpecifications") or []:
                        grp = g.get("specTypeTitle") or ""
                        if grp.lower() == "price":
                            continue
                        for s in g.get("specList") or []:
                            if s.get("specValue"):
                                specs.append(Spec(m["name"], name, fuel, trans, grp,
                                                  re.sub(r"[^a-z0-9]+", "_", (s.get("specLabel") or "").lower()).strip("_"),
                                                  s.get("specLabel") or "", clean(s["specValue"]), src))
                      for g in r.get("productFeatures") or []:
                        for f in g.get("featureList") or []:
                            val = clean(f.get("featureValue"))
                            if not val or val.lower() in ("no", "na", "-"):
                                continue
                            lab = clean(f.get("featureLabel"))
                            feats.append(Feature(m["name"], name, fuel, trans, "other",
                                                 lab if val.lower() == "yes" else f"{lab}: {val}", src))
        if not specs and not feats:
            raise NotSupported("spec-page variant labels could not be matched to price-page variants")
        return specs, feats


ADAPTER = TataMotorsAdapter()
