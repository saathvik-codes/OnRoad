"""
Toyota Kirloskar Motor adapter (www.toyotabharat.com).

Endpoints: the price-list page https://www.toyotabharat.com/pricelist/ loads
https://static.toyotabharat.com/js/forms/api.pricelist.ob.js, which POSTs (empty body, XML response) to
API_BASEURL = https://webapi.toyotabharat.com/ :
  1.0/api/pricestates                               -> states (Id, Name)
  1.0/api/pricestates/<stateId>/pricecities         -> cities priced in that state (Id, Name, lat/lng)
  1.0/api/businesscities/<cityId>/websalesdealers   -> sales dealers of the city (address, pincode, phone, URL, lat/lng)
  1.0/api/price/models                              -> price models (Id, Name, EffectiveDate, Image, notes)
  1.0/api/price/list/<dealerId>/<priceModelId>      -> every grade with Amount (ex-showroom), FuelType, Details
The API sits behind a SafeLine WAF that rejects requests without the headers the page's jQuery sends
(Referer/Origin www.toyotabharat.com, X-Requested-With), so those same headers are sent.

Toyota prices per dealer: the page asks for state, city and the nearest dealer, then shows that dealer's list. This
adapter uses the first web-sales dealer the API lists for the city and records it in source_url.

Verified 2026-10-20 (run from backend/): Hyderabad = city 4 (Telangana 30), dealer 708 Fortune Toyota.
Urban Cruiser Hyryder "S MT 2WD NEODRIVE" = Rs 12,82,000, "V e-Drive 2WD HYBRID" = Rs 19,99,000 (27 grades incl.
dual-tone colour rows). A second Hyderabad dealer (id 41) returned identical Hyryder prices for all 27 grades,
so the first dealer's list stands for the city. Each model's EffectiveDate is kept in the source_url fragment for traceability.
Known gaps:
  * Body type is not in the API; BODY below uses Toyota's own model naming/segment and is not price data.
  * engine_cc / seats are not in the price feed (None); battery_kwh is parsed only if a grade name states kWh.
  * offers(): toyotabharat.com has no offers page or offer API (re-checked 2026-10-22: sitemap, home, model
    showroom pages, /finance/, /buynow/, /online-booking/ and its api.online-booking-pg.ob.js) -> NotSupported.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._ga_common import Polite, clean, inr, make_client

SITE = "https://www.toyotabharat.com"
API = "https://webapi.toyotabharat.com/1.0/api"
PAGE_HEADERS = {
    "Referer": SITE + "/pricelist/", "Origin": SITE, "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/xml, text/xml, */*; q=0.01",
}
FUEL = {"P": "Petrol", "D": "Diesel", "C": "CNG", "H": "Strong Hybrid", "E": "Electric", "B": "Electric"}
BODY = {
    "glanza": "Hatchback", "urban cruiser taisor": "SUV", "rumion": "MUV", "urban cruiser hyryder": "SUV",
    "urban cruiser ebella": "SUV", "innova crysta": "MUV", "innova hycross": "MUV", "fortuner": "SUV",
    "legender": "SUV", "camry": "Sedan", "vellfire": "MUV", "land cruiser 300": "SUV", "hilux": "Pickup",
}
SHOWROOM = {
    "glanza": "/showroom/glanza/", "urban cruiser taisor": "/showroom/urbancruiser-taisor/",
    "rumion": "/showroom/rumion/", "urban cruiser hyryder": "/showroom/urbancruiser-hyryder/",
    "urban cruiser ebella": "/showroom/urbancruiser-ebella/", "innova crysta": "/showroom/innova-crysta/",
    "innova hycross": "/showroom/innova/", "fortuner": "/showroom/fortuner/index-fortuner.html",
    "legender": "/showroom/fortuner/index-legender.html", "camry": "/showroom/camry/",
    "vellfire": "/showroom/vellfire/", "land cruiser 300": "/showroom/lc300/", "hilux": "/showroom/hilux/",
}


def _xml(resp) -> ET.Element:
    return ET.fromstring(resp.content)


class ToyotaAdapter(BrandAdapter):
    brand = "Toyota"
    slug = "toyota"
    website = SITE

    def client(self):
        return make_client(extra_headers=PAGE_HEADERS)

    def _post(self, h: Polite, path: str) -> ET.Element:
        return _xml(h.post(API + path, content=b""))

    def _city(self, h: Polite, city: str) -> tuple[int, str, str]:
        want = {"bengaluru": "bangalore", "gurugram": "gurgaon", "new delhi": "delhi"}.get(city.lower(), city.lower())
        states = self._post(h, "/pricestates")
        hint = {"hyderabad": "telangana", "secunderabad": "telangana"}.get(want)
        order = sorted(states, key=lambda s: 0 if hint and (s.findtext("Name") or "").lower() == hint else 1)
        for st in order:
            if (st.findtext("IsDealerState") or "true") == "false":
                continue
            for c in self._post(h, f"/pricestates/{st.findtext('Id')}/pricecities"):
                if (c.findtext("Name") or "").strip().lower() == want:
                    return int(c.findtext("Id")), c.findtext("Name"), st.findtext("Name")
            if hint:
                break
        raise NotSupported(f"Toyota price list has no city '{city}'")

    def _models(self, h: Polite) -> list[ET.Element]:
        return list(self._post(h, "/price/models"))

    def models(self) -> list[dict]:
        with Polite(self.client()) as h:
            ms = self._models(h)
        out = []
        for m in ms:
            name = clean(m.findtext("Name"))
            out.append({"name": name, "url": SITE + SHOWROOM.get(name.lower(), "/pricelist/"),
                        "body_type": BODY.get(name.lower()), "image_url": m.findtext("Image"),
                        "price_model_id": m.findtext("Id"), "price_effective": m.findtext("EffectiveDate"),
                        "source_url": API + "/price/models"})
        return out

    def _dealers_xml(self, h: Polite, city_id: int) -> list[ET.Element]:
        return [d for d in self._post(h, f"/businesscities/{city_id}/websalesdealers")
                if (d.findtext("IsDeactivateDealer") or "false") == "false"]

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        out: list[Variant] = []
        with Polite(self.client()) as h:
            cid, _, _ = self._city(h, city)
            dealers = self._dealers_xml(h, cid)
            if not dealers:
                raise NotSupported(f"Toyota lists no sales dealer for '{city}', so no price list")
            dealer_id = dealers[0].findtext("Id")
            dealer_name = clean(dealers[0].findtext("Name"))
            for m in self._models(h):
                name = clean(m.findtext("Name"))
                src = (f"{API}/price/list/{dealer_id}/{m.findtext('Id')}#dealer={dealer_name}"
                       f";effective={m.findtext('EffectiveDate')}")
                for p in self._post(h, f"/price/list/{dealer_id}/{m.findtext('Id')}"):
                    amount = inr(p.findtext("Amount"))
                    grade = clean(p.findtext("PriceGrade/Name"))
                    if not amount or not grade:
                        continue
                    fcode = (p.findtext("PriceGrade/FuelType") or "").strip().upper()
                    fuel = FUEL.get(fcode, fcode)
                    if "HYBRID" in grade.upper() and fuel == "Petrol":
                        fuel = "Strong Hybrid"
                    details = clean(p.findtext("PriceGrade/Details"))
                    trans = "Automatic" if fuel == "Electric" else _trans(grade, details)
                    kwh = re.search(r"(\d+(?:\.\d+)?)\s*kWh", grade, re.I)
                    out.append(Variant(
                        model=name, variant=grade.replace("[", " [").replace("  ", " "), fuel=fuel,
                        transmission=trans, ex_showroom_inr=amount, city=city, source_url=src,
                        body_type=BODY.get(name.lower()), battery_kwh=float(kwh.group(1)) if kwh else None,
                        model_url=SITE + SHOWROOM.get(name.lower(), "/pricelist/"), image_url=m.findtext("Image")))
        if not out:
            raise NotSupported(f"Toyota returned no prices for '{city}'")
        return out

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        with Polite(self.client()) as h:
            cid, cname, sname = self._city(h, city)
            rows = self._dealers_xml(h, cid)
        src = f"{API}/businesscities/{cid}/websalesdealers"
        out = []
        for d in rows:
            addr = ", ".join(clean(d.findtext(k)).rstrip(",") for k in ("Address1", "Address2", "Address3") if clean(d.findtext(k)))
            fac = clean(d.findtext("Facility/Value")).lower()
            lat, lng = d.findtext("Latitude"), d.findtext("Longitude")
            out.append(Dealer(
                name=clean(d.findtext("Name")) + (f" - {clean(d.findtext('Area'))}" if d.findtext("Area") else ""),
                address=addr, city=clean(d.findtext("City/Name")) or cname,
                state=clean(d.findtext("City/State/Name")) or sname, pincode=d.findtext("Pincode") or None,
                phone=clean(d.findtext("Phone")) or None, email=clean(d.findtext("Email")) or None,
                lat=float(lat) if lat else None, lng=float(lng) if lng else None,
                kind="sales+service" if "service" in fac else "sales", source_url=src,
                website=clean(d.findtext("URL")) or None))
        return out

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise NotSupported(
            "toyotabharat.com publishes no offers page or feed (checked 2026-10-22): sitemap.xml (80 URLs) has no "
            "offer page; home page, /showroom/urbancruiser-hyryder/, /showroom/glanza/, /finance/ (loan products, no "
            "amounts), /buynow/?exchange=1 (lead form) and /online-booking/ (its JS calls only states/cities/dealers/"
            "models/carbooking APIs; T&C says promotions 'will be specified separately') show no offer amounts.")


def _trans(grade: str, details: str) -> str:
    g = grade.upper()
    if "E-DRIVE" in g or "HYBRID" in g:
        return "CVT"                       # Toyota's e-Drive is a power-split e-CVT
    if re.search(r"\bCVT\b", g):
        return "CVT"
    if re.search(r"\bAT\b|\bA/T\b", g):
        return "Automatic"
    if re.search(r"\bMT\b|\bM/T\b", g):
        return "Manual"
    d = details.lower()
    if d.startswith("manual"):
        return "Manual"
    if d.startswith("auto"):
        return "Automatic"
    return details or ""


ADAPTER = ToyotaAdapter()
