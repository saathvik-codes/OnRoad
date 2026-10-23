"""
Lamborghini adapter (Automobili Lamborghini global site; India is served through it - there is no India locale).

Endpoints used (robots.txt allows these):
  - https://www.lamborghini.com/en-en/models       __NEXT_DATA__ -> first tab of the families gallery = current range
                                                    (Revuelto, Urus, Temerario); later tabs are few-off/concept cars.
  - https://www.lamborghini.com/en-en/dealerships  __NEXT_DATA__ -> elements[0].items[] = every dealer site worldwide
                                                    (dealerIntName, country.code, siteCategory SALES/SERVICE, address,
                                                    lat/lng, siteData.contacts zipCode/phone/email)
Verified 2026-10-19/20: India has 3 dealers, each with a showroom + service site: Lamborghini Bengaluru (Hoysala
Automotive), Lamborghini Delhi (Italica Motors), Lamborghini Mumbai (Infinity Cars). None in Hyderabad -> dealers()
returns [] for Hyderabad (we do not substitute the nearest city).
Prices: Lamborghini publishes no prices on its site (configurator shows none for India) -> NotSupported("price on
request"). Offers: none published -> NotSupported.
Gaps: body_type is our classification (Urus = SUV, others = Coupe); the models list is global, not India-specific.
"""

from __future__ import annotations

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._lux_common import Polite, city_match, clean, next_data

BASE = "https://www.lamborghini.com"
MODELS_URL = BASE + "/en-en/models"
DEALER_URL = BASE + "/en-en/dealerships"


def _label(obj) -> str:
    for l in obj.get("labelsLong") or obj.get("labels") or []:
        if l.get("key") == "title_primary" and l.get("value"):
            return clean(l["value"][0])
    return ""


class LamborghiniAdapter(BrandAdapter):
    brand = "Lamborghini"
    slug = "lamborghini"
    website = BASE + "/en-en"

    def models(self) -> list[dict]:
        with Polite() as p:
            data = next_data(p.text(MODELS_URL))
        els = data["props"]["pageProps"]["data"]["elements"]
        tabs = next(e for e in els if e.get("bundle") == "wrapperWithTabs")["subElements"]
        gallery = tabs[0]["subElements"][0]                     # first tab = current range
        out = []
        for fam in gallery.get("subElements") or []:
            if fam.get("bundle") != "familiesGalleryFamilyObject":
                continue
            name = _label(fam)
            url = next((c["url"]["url"] for c in fam.get("callToActions") or []
                        if isinstance(c.get("url"), dict) and c["url"].get("url", "").startswith("/en-en/models/")), None)
            img = None
            for mo in fam.get("subElements") or []:
                for im in mo.get("image") or []:
                    img = img or (im.get("desktop") or {}).get("url")
            if not name and url:
                name = url.rsplit("/", 1)[-1].title()
            out.append({"name": name, "url": BASE + url if url else MODELS_URL,
                        "body_type": "SUV" if "urus" in name.lower() else "Coupe",
                        "image_url": BASE + img if img and img.startswith("/") else img})
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        raise NotSupported("price on request: Lamborghini publishes no prices for India (site or configurator)")

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        with Polite() as p:
            data = next_data(p.text(DEALER_URL))
        items = []
        for e in data["props"]["pageProps"]["data"]["elements"]:
            items += [i for i in e.get("items") or [] if isinstance(i, dict)]
        out = []
        for d in items:
            if (d.get("country") or {}).get("code") != "IN":
                continue
            sd = d.get("siteData") or {}
            town = ((sd.get("city") or {}).get("value") or [""])[0]
            name = d.get("dealerIntName") or d.get("dealerName") or ""
            if not city_match(city, town, name.replace("Lamborghini", "")):
                continue
            contacts = {c.get("key"): (c.get("value") or [None])[0] for c in sd.get("contacts") or []}
            cat = ((d.get("siteCategory") or {}).get("code") or "").upper()
            out.append(Dealer(name=f'{name} ({(d.get("siteCategory") or {}).get("title", "")})',
                              address=d.get("addressInt") or d.get("address") or "", city=town or city, state="",
                              pincode=contacts.get("zipCode"), phone=contacts.get("phone"), email=contacts.get("email"),
                              lat=float(d["latitude"]) if d.get("latitude") else None,
                              lng=float(d["longitude"]) if d.get("longitude") else None,
                              kind="service" if cat == "SERVICE" else "sales", source_url=DEALER_URL,
                              website=BASE + d["url"] if d.get("url") else None))
        return out

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise NotSupported("Lamborghini publishes no offers or finance schemes for India")


ADAPTER = LamborghiniAdapter()
