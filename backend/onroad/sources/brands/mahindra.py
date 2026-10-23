"""
Mahindra adapter - ICE SUVs/pik-ups on auto.mahindra.com and the electric SUVs on www.mahindraelectricsuv.com
(both Salesforce Commerce Cloud storefronts: Sites-amc-Site and Sites-esuv-Site).

Endpoints / pages (public, server-rendered or the storefront's own AJAX controllers):
  models  : https://auto.mahindra.com/  - header "Explore <MODEL>" cards (name, page URL, image, product id)
            https://www.mahindraelectricsuv.com/ - nav links /esuv/.../<PID>.html (BE 6, XEV 9e, XEV 9S)
  prices  : ICE  - the model page itself (e.g. /suv/xuv-7xo.html, /suv/scorpio-n/SCN.html) renders one card per
                   variant (variant id, name, "Rs X* Ex. showroom price", fuel, transmission, seats). The page is
                   used rather than BrandPage-VariantCardsAjax?cgid=<PID> because on 2026-10-19 the AJAX list for
                   XUV 7XO omitted all 9 AX7L variants that the page shows. The AJAX controller
                   /on/demandware.store/Sites-amc-Site/en_IN/BrandPage-VariantCardsAjax?cgid=<PID>&page=0&srule=price
                   is the fallback for model pages without cards (XUV 3XO EV).
            EV   - https://www.mahindraelectricsuv.com/on/demandware.store/Sites-esuv-Site/en_IN/
                   BrandPage-VariantCardsAjax?cgid=<PID>&page=0&srule=price (pack, battery, charger, seats, price)
            Mahindra publishes ONE national ex-showroom price per variant: no city selector exists and the price
            never names a city, so Variant.city is set to "All India (national ex-showroom)".
  dealers : https://auto.mahindra.com/on/demandware.store/Sites-amc-Site/en_IN/Stores-FindStores
                ?postalCode=<city or PIN>&radius=<km>&showMap=false
            (the dealer-locator page's own search; the server geocodes the text, e.g. "Hyderabad").
            dealerType S = sales, 2S/3S = sales + service (+ spares).
  offers  : no offers page or feed on either site (sitemaps checked) -> NotSupported.

Verified 2026-10-19/20 (run from backend/): XUV 7XO 27 variants (AX Petrol MT Rs 13,99,000 ... AX7L Diesel AWD
Rs 25,79,000), Scorpio-N 31 (Z2 Petrol (E) Rs 13,69,000; Z8L Diesel 4WD Rs 25,49,000 - equal to the page's
JSON-LD lowPrice/highPrice 1369000/2549000), XUV 3XO 31, BE 6 20, XEV 9S 20, XEV 9e 6.
Known gaps:
  * Veero's page has no cards; its rows come from the AJAX fallback (cgid=UPP).
  * engine_cc is not on the variant cards (None). battery_kwh comes from the EV card text.
  * The header range for XUV 7XO said up to Rs 25.94L while the highest variant card was Rs 25.79L; cards are used.
"""

from __future__ import annotations

import html as _html
import re
from urllib.parse import parse_qs, unquote

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._ga_common import Polite, clean, inr, make_client

AUTO = "https://auto.mahindra.com"
ESUV = "https://www.mahindraelectricsuv.com"
CARDS_ICE = AUTO + "/on/demandware.store/Sites-amc-Site/en_IN/BrandPage-VariantCardsAjax?cgid={pid}&page=0&srule=price"
CARDS_EV = ESUV + "/on/demandware.store/Sites-esuv-Site/en_IN/BrandPage-VariantCardsAjax?cgid={pid}&page=0&srule=price"
STORES = AUTO + "/on/demandware.store/Sites-amc-Site/en_IN/Stores-FindStores"
NATIONAL = "All India (national ex-showroom)"
DEALER_RADIUS_KM = 30

CARD_START = re.compile(r'data-variant="([A-Z0-9]+)"|id="check-([A-Z0-9]+)"')
TRANS = {"MANUAL": "Manual", "AUTOMATIC": "Automatic", "AUTOSHIFT+": "AMT", "AMT": "AMT"}
FUEL = {"PETROL": "Petrol", "DIESEL": "Diesel", "CNG": "CNG", "ELECTR": "Electric", "ELECTRIC": "Electric"}


def _unescape_page(text: str) -> str:
    # model pages embed part of the markup as escaped JSON strings
    return _html.unescape(text).replace('\\"', '"').replace("\\n", " ")


def _cards(text: str) -> list[dict]:
    """Parse Mahindra variant cards (ICE card layout and EV card layout)."""
    pos = [(m.start(), m.group(1) or m.group(2)) for m in CARD_START.finditer(text)]
    out, seen = [], set()
    for i, (start, vid) in enumerate(pos):
        if vid in seen or not re.search(r"M\d{4}", vid):          # skip the master product id (e.g. "X7XO")
            continue
        end = pos[i + 1][0] if i + 1 < len(pos) else start + 20000
        blk = text[start:end]
        name = re.search(r'class="variant-name">\s*([^<]+?)\s*<', blk)
        price = re.search(r'class="(?:variant-price|price showroom-price-value)">\s*([^<]+?)\s*<', blk)
        if not (name and price and inr(price.group(1))):
            continue
        seen.add(vid)
        sub = re.search(r'class="variant-name">[^<]*</h\d>\s*<p>\s*(.*?)\s*</p>', blk, re.S)
        qs = re.search(r'data-url="[^"?]*\?([^"]+)"', blk)
        params = {k.split("_")[-1]: unquote(v[0]) for k, v in parse_qs(_html.unescape(qs.group(1))).items()} if qs else {}
        out.append({"id": vid, "name": clean(name.group(1)), "price": inr(price.group(1)),
                    "values": [clean(v) for v in re.findall(r'class="section-value">\s*([^<]*?)\s*<', blk)][:3],
                    "sub": clean(sub.group(1)) if sub else "", "params": params})
    return out


class MahindraAdapter(BrandAdapter):
    brand = "Mahindra"
    slug = "mahindra"
    website = AUTO

    def client(self):
        return make_client(extra_headers={"Accept": "text/html,application/json;q=0.9,*/*;q=0.8"})

    # ------------------------------------------------------------------ models
    def _ice_models(self, h: Polite) -> list[dict]:
        page = h.get(AUTO + "/").text
        out, seen = [], set()
        for part in page.split('<a title="Explore ')[1:]:
            name = clean(part.split('"')[0])
            href = re.search(r'href="([^"]+)"', part)
            if not href or not href.group(1).startswith(("/suv/", "/pick-up-trucks/")):
                continue
            url = AUTO + href.group(1)
            if url in seen:
                continue
            seen.add(url)
            img = re.search(r'<img[^>]*src="([^"]+)"', part)
            code = re.search(r"/([A-Z0-9]{3,5})\.html$", href.group(1))
            pid = re.search(r"variant-selection\?pid=([A-Z0-9]+)", part)
            out.append({"name": name, "url": url, "pid": (code and code.group(1)) or (pid and pid.group(1)),
                        "body_type": "Pickup" if "/pick-up-trucks/" in url else "SUV",
                        "image_url": _html.unescape(img.group(1)) if img else None, "fuel": None,
                        "source_url": AUTO + "/"})
        return out

    EV_IMAGES = {
        "MBE6": "https://www.mahindraelectricsuv.com/on/demandware.static/-/Sites-esuv-product-catalog/default/dwf99df80b/images/BE6/large/Pack_One/Pack_One_DesertMyst_588x330.png",
        "BE6": "https://www.mahindraelectricsuv.com/on/demandware.static/-/Sites-esuv-product-catalog/default/dwf99df80b/images/BE6/large/Pack_One/Pack_One_DesertMyst_588x330.png",
        "MXV9": "https://www.mahindraelectricsuv.com/dw/image/v2/BKRC_PRD/on/demandware.static/-/Sites-esuv-product-catalog/default/dw777b2d40/images/XEV9E/large/packthree/XEV9E_EverestWhite_588x330.png",
        "XEV9": "https://www.mahindraelectricsuv.com/dw/image/v2/BKRC_PRD/on/demandware.static/-/Sites-esuv-product-catalog/default/dwc464ce55/images/XEV9/large/PackThreeTech_Everest_White_588x330.png",
    }

    def _ev_models(self, h: Polite) -> list[dict]:
        page = h.get(ESUV + "/").text
        out, seen = [], set()
        for href, pid, text in re.findall(r'href="(https://www\.mahindraelectricsuv\.com/esuv/(?:[a-z0-9-]+/)?([A-Z0-9]{3,5})\.html)"[^>]*>([^<]+)</a>', page):
            if pid in seen:
                continue
            seen.add(pid)
            img = self.EV_IMAGES.get(pid)
            out.append({"name": clean(text), "url": href, "pid": pid, "body_type": "SUV", "image_url": img,
                        "fuel": "Electric", "source_url": ESUV + "/"})
        return out

    def models(self) -> list[dict]:
        with Polite(self.client()) as h:
            return self._ice_models(h) + self._ev_models(h)

    # ------------------------------------------------------------------ prices
    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        out: list[Variant] = []
        with Polite(self.client()) as h:
            for m in self._ice_models(h):
                cards = _cards(_unescape_page(h.get(m["url"]).text))
                src = m["url"]
                if not cards and m["pid"]:
                    src = CARDS_ICE.format(pid=m["pid"])
                    cards = _cards(_unescape_page(h.get(src).json().get("html", "")))
                for c in cards:
                    fuel_raw, trans_raw, seats_raw = (c["values"] + ["", "", ""])[:3]
                    fuel = FUEL.get(fuel_raw.upper(), fuel_raw.title())
                    trans = TRANS.get(trans_raw.upper().replace(" ", ""), trans_raw.title())
                    seats = int(seats_raw) if seats_raw.isdigit() else None
                    label = c["name"]
                    if trans and trans.upper() not in label.upper():
                        label += f" {trans}"
                    if seats:
                        label += f" {seats}-seater"
                    out.append(Variant(model=_disp(m["name"]),
                                       variant=label, fuel=fuel, transmission=trans, ex_showroom_inr=c["price"],
                                       city=NATIONAL, source_url=src, body_type=m["body_type"], seats=seats,
                                       battery_kwh=_kwh(c["name"] + " " + c["sub"]) if fuel == "Electric" else None,
                                       model_url=m["url"], image_url=m["image_url"]))
            for m in self._ev_models(h):
                src = CARDS_EV.format(pid=m["pid"])
                for c in _cards(_unescape_page(h.get(src).json().get("html", ""))):
                    seats = c["params"].get("seatingCapacity")
                    seats = int(seats) if seats and seats.isdigit() else None
                    label = c["name"]
                    charger = c["params"].get("charger") or (c["sub"].split("|")[-1].strip() if "|" in c["sub"] else "")
                    if charger:
                        label += f" ({charger}{'' if 'charger' in charger.lower() else ' charger'})"
                    if seats:
                        label += f" {seats}-seater"
                    out.append(Variant(model=m["name"], variant=label, fuel="Electric", transmission="Automatic",
                                       ex_showroom_inr=c["price"], city=NATIONAL, source_url=src, body_type="SUV",
                                       seats=seats, battery_kwh=_kwh(c["params"].get("batteryCapacity") or c["sub"]),
                                       model_url=m["url"]))
        if not out:
            raise NotSupported("Mahindra pages returned no variant price cards")
        return out

    # ------------------------------------------------------------------ dealers
    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        url = f"{STORES}?postalCode={city}&radius={DEALER_RADIUS_KM}&showMap=false"
        with Polite(self.client()) as h:
            data = h.json(STORES, params={"postalCode": city, "radius": DEALER_RADIUS_KM, "showMap": "false"})
        key = data.get("searchKey") or {}
        if (key.get("city") or "").lower() != city.lower() and not city.isdigit():
            raise NotSupported(f"Mahindra dealer search could not place '{city}' (geocoded to {key})")
        state = key.get("stateName") or ""
        out = []
        for s in data.get("stores") or []:
            dtype = (s.get("dealerType") or "").upper()
            if dtype not in ("S", "2S", "3S"):
                continue
            addr = ", ".join(x for x in (s.get("address1"), s.get("address2"), s.get("locationName"), s.get("city")) if x)
            out.append(Dealer(
                name=clean(s.get("name")) + (f" - {clean(s['locationName']).title()}" if s.get("locationName") else ""),
                address=clean(addr), city=clean(s.get("city")).title() or city, state=state,
                pincode=s.get("postalCode") or None, phone=s.get("phone") or None, email=s.get("email") or None,
                lat=s.get("latitude"), lng=s.get("longitude"),
                kind="sales" if dtype == "S" else "sales+service", source_url=url))
        return out

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise NotSupported("auto.mahindra.com and mahindraelectricsuv.com publish no offers page or offers feed "
                           "(checked sitemaps on 2026-10-19).")

    # ------------------------------------------------------------------ specs
    def specs(self):
        """ICE: each variant card on the model page links ("View all specifications") to the variant's own page
        /suv/<model>/<slug>/<VARIANT_ID>.html, whose Specifications / Features tabs are 'spec-grid' rows comparing that
        variant (first column) with the top variant (second column); only the first column is used.
        EV (mahindraelectricsuv.com): the variant links served a PDF, not a spec page on 2026-10-23 -> not covered."""
        from ._spec_kit import SpecSink
        specs, feats = [], []
        with Polite(self.client()) as h:
            for m in self._ice_models(h):
                page = _unescape_page(h.get(m["url"]).text)
                links = {vid: AUTO + path for path, vid in re.findall(
                    r'href="(?:https?://auto\.mahindra\.com)?(/[^"]*/([A-Z0-9]+)\.html)"[^>]*class="specification-button', page)}
                for c in _cards(page):
                    url = links.get(c["id"])
                    if not url:
                        continue
                    fuel_raw, trans_raw, seats_raw = (c["values"] + ["", "", ""])[:3]
                    fuel = FUEL.get(fuel_raw.upper(), fuel_raw.title())
                    trans = TRANS.get(trans_raw.upper().replace(" ", ""), trans_raw.title())
                    label = c["name"]
                    if trans and trans.upper() not in label.upper():
                        label += f" {trans}"
                    if seats_raw.isdigit():
                        label += f" {int(seats_raw)}-seater"
                    sink = SpecSink(_disp(m["name"]), label, fuel, trans)
                    try:
                        r = h.get(url)
                    except Exception:
                        continue                 # some "specifications" links point at a brochure PDF that 404s
                    if "html" not in r.headers.get("content-type", ""):
                        continue
                    for sec, lab, val, kind in _mahindra_spec_rows(r.text):
                        sink.row(sec, lab, val, url, kind)
                    s, f = sink.out()
                    specs += s
                    feats += f
        if not specs and not feats:
            raise NotSupported("Mahindra variant pages exposed no spec-grid rows")
        return specs, feats


def _mahindra_spec_rows(text: str) -> list[tuple[str, str, str, str]]:
    """(section id, label, value of this variant's column, kind) from a variant page's spec-grid rows."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(text, "html.parser")
    out = []
    for tab, kind in (("Specifications-tab", "spec"), ("Features-tab", "feature")):
        pane = soup.find(id=tab)
        if not pane:
            continue
        for body in pane.select(".spec-accordion-body"):
            for g in body.select("div.spec-grid"):
                label = g.get("data-grid-feature")
                items = g.select(".spec-grid-item")
                if not label or not items:
                    continue
                it = items[0]
                use = it.select_one("use")
                if use is not None:
                    ref = use.get("xlink:href") or use.get("href") or ""
                    value = "✓" if ref.endswith("checktrue") else ""
                else:
                    for lab in it.select("label"):
                        lab.extract()
                    value = clean(it.get_text(" ", strip=True))
                if value and not (kind == "spec" and value == "✓"):
                    # section ids ("engineAndTransmission") would mis-key every row of the section, so none is passed
                    out.append(("", clean(label), value, kind))
    return out


def _disp(name: str) -> str:
    """'SCORPIO-N' -> 'Scorpio-N', 'XUV 7XO' stays, 'THAR OG' -> 'Thar OG'."""
    if not name.isupper():
        return name
    keep = {"XUV", "XEV", "BE", "OG", "EV", "HD", "ROXX"}
    return " ".join(w if (w in keep or any(ch.isdigit() for ch in w)) else w.title() for w in name.split())


def _kwh(text: str | None) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)\s*kWh", text or "", re.I)
    return float(m.group(1)) if m else None


ADAPTER = MahindraAdapter()
