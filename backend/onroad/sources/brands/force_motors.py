"""
Force Motors - https://www.forcemotors.com  (passenger vehicles only)

Endpoints used (robots.txt checked 2026-10-20: forcemotors.com blocks only /wp-admin/, /demo, /blog/category/,
/wp-content/plugins/, /subscribeuser; forcegurkha.co.in and forceurbania.co.in block only /wp-admin/ and explicitly
allow /wp-admin/admin-ajax.php):
  GET  https://www.forcemotors.com/prices/            official price list: one <table class="prodct-dtl-table-data">
                                                      per model group (row "productmainname" = group heading, then
                                                      "description | Ex-showroom Price" rows)
  GET  https://www.forcemotors.com/vehicles/<model>/  spec pages ("Displacement 2596 cc") for engine_cc
  POST https://forceurbania.co.in/wp-admin/admin-ajax.php  action=get_dealer_data&city=<CITY>  (JSON the Urbania
                                                      "Find a dealer" page itself calls; html_sales / html_service)
  GET  https://forcegurkha.co.in/find-dealer/         Gurkha dealer page; all sales/service cards are server-rendered
                                                      (its own AJAX endpoint getDealersNew.php returns 404)

Passenger models emitted: Gurkha (3-door, 5-door), Urbania DX, Trax Cruiser / Toofan / Gama / Citiline
Not emitted (buses / commercial): Traveller minibuses, ambulances, delivery vans, school buses/vans, Monobus, special apps.

City: the price list is one national list that names no city or state, so prices() returns city="India (national)".
Verified 2026-10-20 (page dateModified 2026-10-14): Gurkha 3 Door 3+D 16,51,881; Gurkha 5 Door 6+D 17,83,366;
Trax Cruiser (9+D) non-AC 12,80,400; Urbania DX 3350WB 10D 29,51,433. Hyderabad: Realty Shield Services (K Motors),
LB Nagar, on both the Urbania (JSON) and Gurkha locators.
Known gaps: transmission is not stated in the list (all Force models are manual-only, so "Manual" is set);
engine_cc not published in HTML for Gurkha/Urbania (None); dealer lat/lng and e-mail not published; the main
forcemotors.com locator's script (dealer-ajax.js) returns 404, and /locations-term/<city>/ lists spare-parts
stockists, not dealers, so neither is used; no offers are published on any Force site (offers() -> NotSupported).
"""

from __future__ import annotations

import re
import time

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._ga_common import clean, inr, norm
from ._geo import geo

BASE = "https://www.forcemotors.com"
GURKHA = "https://forcegurkha.co.in"
URBANIA = "https://forceurbania.co.in"
PRICES = f"{BASE}/prices/"
DELAY = 1.0
NATIONAL = "India (national)"

# group heading prefix on /prices/ -> (model name, body type, model page). Order matters (longest first).
GROUPS = [
    ("TRAX CRUISER AMBULANCE", None, None, None),
    ("GURKHA", "Gurkha", "SUV", f"{GURKHA}/"),
    ("URBANIA", "Urbania", "MUV", f"{URBANIA}/"),
    ("TRAX GAMA", "Trax Gama", "MUV", f"{BASE}/vehicle/trax-gama/"),
    ("TRAX CRUISER", "Trax Cruiser", "MUV", f"{BASE}/vehicles/trax-cruiser/"),
    ("TRAX TOOFAN", "Trax Toofan", "MUV", f"{BASE}/vehicles/trax-toofan/"),
    ("CITILINE", "Citiline", "MUV", f"{BASE}/vehicles/citiline/"),
]
SKIP_ROW = re.compile(r"SCHOOL VAN|\bSCV\b|AMB", re.I)


def _seats(desc: str) -> int | None:
    m = re.search(r"(\d{1,2})\s*\+?\s*D\b", desc)
    return int(m.group(1)) + 1 if m else None


class ForceMotorsAdapter(BrandAdapter):
    brand = "Force Motors"
    slug = "force_motors"
    website = BASE

    def __init__(self):
        self._c = None
        self._last = 0.0
        self._cc: dict[str, int | None] = {}

    def _req(self, method, url, **kw):
        if self._c is None:
            self._c = self.client()
        gap = time.monotonic() - self._last
        if self._last and gap < DELAY:
            time.sleep(DELAY - gap)
        self._last = time.monotonic()
        r = self._c.request(method, url, **kw)
        r.raise_for_status()
        return r

    def _engine_cc(self, url: str | None) -> int | None:
        if not url or not url.startswith(BASE):
            return None
        if url not in self._cc:
            try:
                m = re.search(r"Displacement\s*([\d,]{3,5})\s*cc", clean(self._req("GET", url).text))
                self._cc[url] = int(m.group(1).replace(",", "")) if m else None
            except Exception:
                self._cc[url] = None
        return self._cc[url]

    # ---------------------------------------------------------------- price list
    def _tables(self):
        page = self._req("GET", PRICES).text
        for m in re.finditer(r'<table>(.*?)</table>', page, re.S):
            body = m.group(1)
            head = re.search(r'class="productmainname"><td[^>]*>(.*?)</td>', body, re.S)
            if not head:
                continue
            rows = []
            for tr in re.findall(r"<tr>(.*?)</tr>", body, re.S):
                cells = [clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
                if len(cells) == 2 and inr(cells[1]):
                    rows.append((cells[0], inr(cells[1])))
            img = re.search(r'<img[^>]+src="(https://www\.forcemotors\.com/wp-content/uploads/[^"]+)"',
                            page[m.end():m.end() + 2500])
            yield clean(head.group(1)).upper(), rows, img.group(1) if img else None

    def _group(self, heading: str):
        for prefix, model, body, url in GROUPS:
            if heading.startswith(prefix):
                return model, body, url
        return None, None, None

    def models(self) -> list[dict]:
        out, seen = [], set()
        for heading, _rows, img in self._tables():
            model, body, url = self._group(heading)
            if model and model not in seen:
                seen.add(model)
                out.append({"name": model, "url": url or f"{BASE}/vehicles-category/traveller/", "body_type": body,
                            "image_url": img})
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        out, seen = [], set()
        for heading, rows, img in list(self._tables()):
            model, body, url = self._group(heading)
            if not model:
                continue
            if model == "Traveller":
                wb = re.search(r"(\d{4})\s*MM", heading)
                url = f"{BASE}/vehicles/traveller-{wb.group(1)}wb/" if wb else f"{BASE}/vehicles-category/traveller/"
            for desc, price in rows:
                if SKIP_ROW.search(desc) or (desc, price) in seen:
                    continue
                seen.add((desc, price))
                cng = "CNG" in desc.upper()
                out.append(Variant(model=model, variant=desc, fuel="CNG" if cng else "Diesel", transmission="Manual",
                                   ex_showroom_inr=price, city=NATIONAL, source_url=PRICES, body_type=body,
                                   engine_cc=None if cng else self._engine_cc(url), seats=_seats(desc),
                                   model_url=url, image_url=img))
        if not out:
            raise NotSupported("Force Motors /prices/ table layout changed (no passenger rows found)")
        return out

    # ---------------------------------------------------------------- specs
    def specs(self):
        """forcemotors.com/vehicles/<model>/ "Technical Specifications" accordion: one tab per group (Engine, Gearbox,
        Dimensions (mm) ...) of <li><span>label</span><span>value</span></li> pairs. Force publishes one sheet per model
        (no per-variant split), so the sheet is attached to each priced variant of that model; a value listing several
        seat layouts ("9+D/10+D/12+D") is not attached. Gurkha / Urbania live on their own microsites (not covered)."""
        from bs4 import BeautifulSoup
        from ._spec_kit import SpecSink
        priced = self.prices("Hyderabad")
        specs = []
        for url in dict.fromkeys(v.model_url for v in priced if v.model_url and v.model_url.startswith(BASE)):
            try:
                soup = BeautifulSoup(self._req("GET", url).text, "html.parser")
            except Exception:
                continue
            rows = []
            for title in soup.select(".products-technical-specification .product-accordian-title"):
                pane = soup.find(id=title.get("data-tag") or "")
                if not pane:
                    continue
                for li in pane.select("li"):
                    sp = li.find_all("span")
                    if len(sp) >= 2:
                        rows.append((clean(title.get_text(" ")), clean(sp[0].get_text(" ")), clean(sp[1].get_text(" "))))
            for v in (x for x in priced if x.model_url == url):
                sink = SpecSink(v.model, v.variant, v.fuel, v.transmission)
                for sec, lab, val in rows:
                    if "/" in val and re.search(r"\+\s*D", val):
                        continue
                    sink.row(sec, lab, val, url, "spec")
                specs += sink.out()[0]
        if not specs:
            raise NotSupported("forcemotors.com model pages carried no Technical Specifications accordion")
        return specs, []

    # ---------------------------------------------------------------- dealers
    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        g = geo(city)
        state = g[0] if g else ""
        found: dict[str, Dealer] = {}

        def add(name, addr, phone, kind, src, site):
            addr = re.sub(r"\s*,\s*", ", ", addr).strip(" ,")
            pin = re.search(r"(\d{6})\s*$", addr)
            key = norm(addr)[:40]
            d = found.get(key)
            if d:
                if d.kind != kind:
                    d.kind = "sales+service"
                if kind == "sales" and phone:
                    d.phone = phone
                return
            found[key] = Dealer(name=name, address=addr, city=city, state=state, pincode=pin.group(1) if pin else None,
                                phone=phone, email=None, lat=None, lng=None, kind=kind, source_url=src, website=site)

        # Urbania locator JSON
        ajax = f"{URBANIA}/wp-admin/admin-ajax.php"
        try:
            data = self._req("POST", ajax, data={"action": "get_dealer_data", "city": city.upper()}).json()
        except Exception:
            data = {}
        for key, kind in (("html_sales", "sales"), ("html_service", "service")):
            for card in (data.get(key) or "").split('class="card-body"')[1:]:
                name = re.search(r"<h2>(.*?)</h2>", card, re.S)
                paras = [clean(p) for p in re.findall(r"<p>(.*?)</p>", card, re.S)]
                addr = next((p for p in paras if len(p) > 25), "")
                tel = re.search(r'href="tel:([^"]+)"', card)
                if name and city.lower() in addr.lower():
                    add(clean(name.group(1)), addr, tel.group(1) if tel else None, kind, ajax, URBANIA)

        # Gurkha locator (server-rendered list of every outlet)
        url = f"{GURKHA}/find-dealer/"
        page = self._req("GET", url).text
        svc_at = page.find('id="addlistservice"')
        for m in re.finditer(r'<div class="storeAddress">(.*?)<div class="shareBtn">', page, re.S):
            card = m.group(1)
            name = re.search(r"<h3>(.*?)</h3>", card, re.S)
            addr = [clean(p) for p in re.findall(r"<p>(.*?)</p>", card, re.S)]   # skips the display:none <p style=..>
            tel = re.search(r'href="tel:([^"]+)"', card)
            if name and addr and city.lower() in addr[0].lower():
                add(clean(name.group(1)), addr[0], tel.group(1) if tel else None,
                    "service" if svc_at != -1 and m.start() > svc_at else "sales", url, GURKHA)
        if not found:
            raise NotSupported(f"no Force Motors outlet listed for {city!r} on the Urbania/Gurkha locators")
        return list(found.values())

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise NotSupported("Force Motors publishes no offers on forcemotors.com, forcegurkha.co.in or forceurbania.co.in")


ADAPTER = ForceMotorsAdapter()
