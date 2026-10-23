"""
Porsche India adapter (Porsche India pages live under porsche.com/middle-east/_india_/, served by Porsche's Astro site).

Endpoints used (robots.txt of porsche.com disallows /api/, /search/, /*/login/ - none of these are used):
  - https://www.porsche.com/middle-east/_india_/models/
        Astro island "ModelOverview": props.modelCards[] = every model variant Porsche India lists, with modelName,
        modelRange, bodyType, fuelTypeText, gearTypeText, price.value (INR) "From ₹x incl. VAT", image, model-page link.
  - https://www.porsche.com/in/en-IN/dealersearch/
        Astro island with initialResults[] = all Porsche India outlets (name, address, coordinates, facilityType,
        phone, e-mail, homepage).
Verified 2026-10-19/20: 20 variants in 5 model lines (911 4, Taycan 3, Panamera 1, Macan 4, Cayenne 8); Cayenne
"From ₹1,51,18,000.00 incl. VAT" identical on the overview and on /models/cayenne/cayenne-models/cayenne/; 911 Carrera
₹2,11,29,000. The per-range pages (/models/911/ etc.) show the same 20 cards, so the overview is the full published set.
Hyderabad: "Porsche Center Hyderabad" (satellite centre, Banjara Hills) and "Porsche Showroom Hyderabad".
Price semantics: Porsche India publishes a national "From ₹ ... incl. VAT" (i.e. incl. GST) starting price per variant,
no city named -> city="India", treat as national ex-showroom starting price. Options are extra.
Gaps: no offers page -> NotSupported; facilityType mapping (PORSCHE_CENTER/SATELLITE -> sales+service, SHOWROOM/STUDIO
-> sales) is our reading of Porsche's labels; the "Porsche India Headquarters" office is excluded.
"""

from __future__ import annotations

import json
import re

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._lux_common import Polite, astro_islands, city_match

MODELS_URL = "https://www.porsche.com/middle-east/_india_/models/"
DEALER_URL = "https://www.porsche.com/in/en-IN/dealersearch/"
BODY = {"coupé": "Coupe", "coupe": "Coupe", "turbo coupé": "Coupe", "gt": "Coupe", "suv": "SUV", "suv electric": "SUV",
        "macan electric": "SUV", "sport saloon": "Sedan", "cabriolet": "Convertible", "targa": "Convertible",
        "sport turismo": "Wagon"}
FUEL = {"gasoline": "Petrol", "electric": "Electric", "hybrid": "Hybrid", "e-hybrid": "Hybrid", "diesel": "Diesel"}


PORSCHE_LOCAL_IMAGES = {
    "911": "/models/porsche/911.png",
    "taycan": "/models/porsche/taycan.png",
    "panamera": "/models/porsche/panamera.png",
    "macan": "/models/porsche/macan.png",
    "cayenne": "/models/porsche/cayenne.png",
}


class PorscheAdapter(BrandAdapter):
    brand = "Porsche"
    slug = "porsche"
    website = "https://www.porsche.com/middle-east/_india_/"

    def _cards(self) -> list[dict]:
        with Polite() as p:
            page = p.text(MODELS_URL)
        for isl in astro_islands(page):
            if isinstance(isl.get("modelCards"), list) and isl["modelCards"]:
                return isl["modelCards"]
        raise RuntimeError("Porsche models page: ModelOverview island not found")

    @staticmethod
    def _link(card) -> str | None:
        m = re.search(r'"href": "(https://www\.porsche\.com/middle-east/_india_/models/[^"]+)"',
                      json.dumps(card.get("props") or {}, ensure_ascii=False))
        return m.group(1) if m else None

    def models(self) -> list[dict]:
        out, seen = [], set()
        for c in self._cards():
            m = c["model"]
            if m["modelRange"] in seen:
                continue
            seen.add(m["modelRange"])
            range_key = m.get("modelRangeId", "").lower() or m.get("modelRange", "").lower()
            img = PORSCHE_LOCAL_IMAGES.get(range_key) or ((c.get("props") or {}).get("image") or {}).get("src")
            out.append({"name": m["modelRange"], "url": f"{MODELS_URL}{m['modelRangeId'].lower()}/",
                        "body_type": BODY.get((m.get("bodyType") or "").lower(), m.get("bodyType")), "image_url": img})
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        out = []
        for c in self._cards():
            m = c["model"]
            price = (m.get("price") or {}).get("value")
            if not price:
                continue
            img = ((c.get("props") or {}).get("image") or {}).get("src")
            out.append(Variant(model=m["modelRange"], variant=f'{m["modelName"]} (MY{m.get("modelYear")})',
                               fuel=FUEL.get((m.get("fuelTypeText") or "").lower(), m.get("fuelTypeText") or ""),
                               transmission=m.get("gearTypeText") or "Automatic", ex_showroom_inr=int(price),
                               city="India", source_url=MODELS_URL,
                               body_type=BODY.get((m.get("bodyType") or "").lower(), m.get("bodyType")),
                               seats=None, model_url=self._link(c), image_url=img))
        return out

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        with Polite() as p:
            page = p.text(DEALER_URL)
        results = None
        for isl in astro_islands(page):
            if isinstance(isl.get("initialResults"), list):
                results = isl["initialResults"]
                break
        if results is None:
            raise RuntimeError("Porsche dealer search: initialResults island not found")
        out = []
        for r in results:
            d = r.get("dealer") or {}
            a = d.get("address") or {}
            if "headquarter" in (d.get("name") or "").lower() or not city_match(city, a.get("city")):
                continue
            ft = (d.get("facilityType") or "").upper()
            kind = "sales+service" if ft.endswith("PORSCHE_CENTER") else "sales"
            cd = d.get("contactDetails") or {}
            geo = d.get("coordinates") or {}
            out.append(Dealer(name=d.get("name"), address=", ".join(x for x in (a.get("street"), a.get("city"), a.get("postalCode")) if x),
                              city=a.get("city") or city, state=a.get("state") or "", pincode=a.get("postalCode"),
                              phone=cd.get("phoneNumber"), email=cd.get("emailAddress"),
                              lat=geo.get("latitude"), lng=geo.get("longitude"), kind=kind,
                              source_url=DEALER_URL, website=cd.get("homepage")))
        return out

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise NotSupported("Porsche India publishes no offers/finance-scheme page (the leasing-data API is not used "
                           "for India: leasingOption is empty on every model card)")


ADAPTER = PorscheAdapter()
