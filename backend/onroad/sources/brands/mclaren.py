"""
McLaren Automotive adapter (www.mclaren.com/cars - a React SPA; India is served by the global gl_en site).

Endpoints used (both called by the SPA bundle /cars/assets/index-*.js; robots.txt allows everything):
  - https://mclaren-cms.production.aws.mclaren.com/api/mainnav?site=1        nav JSON, MODELS -> categories -> models
  - https://mclaren-cms.production.aws.mclaren.com/api/retailers?country=India   official retailer locator data
  The CMS answers 403 "Invalid origin" unless the request carries the Origin/Referer the site itself sends
  (https://www.mclaren.com); we send exactly those, nothing else.
Verified 2026-10-19/20: India has one retailer, McLaren Mumbai (Infinity Cars, Prabhadevi; sales +91 7208938295,
service +91 7711005551). None in Hyderabad -> [] (no nearest-city substitution).
Models: Supercars (Artura, Artura Spider, 750S, 750S Spider, 788HS, 788HS Spider), Grand Tourer (GTS), Hypercar (W1);
the Motorsport category (race cars) is excluded. Images: category image only (model tiles are videos).
Prices: none published -> NotSupported("price on request"). Offers: none -> NotSupported.
"""

from __future__ import annotations

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._lux_common import Polite, city_match, clean

CMS = "https://mclaren-cms.production.aws.mclaren.com"
HDR = {"Accept": "application/json", "Origin": "https://www.mclaren.com", "Referer": "https://www.mclaren.com/"}


def _find_models(o):
    if isinstance(o, dict):
        if str(o.get("title", "")).upper() == "MODELS" and isinstance(o.get("categories"), list):
            return o
        for v in o.values():
            r = _find_models(v)
            if r:
                return r
    elif isinstance(o, list):
        for v in o:
            r = _find_models(v)
            if r:
                return r
    return None


class McLarenAdapter(BrandAdapter):
    brand = "McLaren"
    slug = "mclaren"
    website = "https://www.mclaren.com/cars/gl_en"

    def models(self) -> list[dict]:
        with Polite(extra_headers=HDR) as p:
            nav = p.json(CMS + "/api/mainnav", params={"site": "1"})
        sec = _find_models(nav)
        if not sec:
            raise RuntimeError("McLaren nav: MODELS section not found")
        out = []
        for cat in sec["categories"]:
            if "motorsport" in (cat.get("category_name") or "").lower():
                continue
            for m in cat.get("models") or []:
                name = clean(m.get("model_title"))
                slug = m.get("primary_slug") or ""
                out.append({"name": name, "url": f"https://www.mclaren.com/{slug}" if slug else None,
                            "body_type": "Convertible" if "spider" in name.lower() else "Coupe",
                            "image_url": cat.get("category_image_url")})
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        raise NotSupported("price on request: McLaren publishes no prices for India")

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        with Polite(extra_headers=HDR) as p:
            data = p.json(CMS + "/api/retailers", params={"country": "India"})
        out = []
        for r in data.get("retailers", []):
            if r.get("country") != "India" or not city_match(city, r.get("name"), *(r.get("address") or "").split(",")):
                continue
            dep = r.get("departments") or {}
            s, v = dep.get("sales") or {}, dep.get("service") or {}
            kind = "sales+service" if s.get("available") and v.get("available") else ("sales" if s.get("available") else "service")
            a = r.get("address") or ""
            import re
            pin = re.search(r"\b(\d{6})\b", a)
            out.append(Dealer(name=f'McLaren {r.get("name")}', address=a, city=r.get("name") or city,
                              state="Maharashtra" if "Maharashtra" in a else "", pincode=pin.group(1) if pin else None,
                              phone=s.get("phone") or v.get("phone"), email=None,
                              lat=float(s["effective_latitude"]) if s.get("effective_latitude") else None,
                              lng=float(s["effective_longitude"]) if s.get("effective_longitude") else None,
                              kind=kind, source_url="https://www.mclaren.com/cars/gl_en/retailers",
                              website=r.get("retailer_page_link")))
        return out

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise NotSupported("McLaren publishes no offers or finance schemes for India")


ADAPTER = McLarenAdapter()
