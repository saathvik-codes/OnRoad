"""
Royal Enfield - https://www.royalenfield.com/in/en/  (robots.txt allows /in*, only /in/en/twins* disallowed;
api.royalenfield.com has no robots.txt)

Endpoints used (the site's own "Dealership pricing" page, /in/en/motorcycles/dealership-pricing/, and its
pricingAccordian.js):
  GET  /in/en/motorcycles/dealership-pricing/       attribute motorcycleJson on #selectMotorcycle:
                                                    [{motorcycleName, variantList: [{variantCode, motorcycleVariant}]}]
                                                    (variant = colour, e.g. Classic 350 "Redditch Red" = VSMZ60RY)
  POST https://api.royalenfield.com/aem-content/master-data/motorcycle-prices   form data state=<State name>
                                                    -> {"<variantCode>": {"exshowroom", "registration", "insurance",
                                                        "onroadprice", "bookingamount"}}
  GET  /in/en/motorcycles/<model>/                  JSON-LD Product "image" (colour renders under /content/dam/...,
                                                    1920x1080)
City: prices are per state; prices(city) asks for the city's state and labels the rows with the city.
Verified 2026-10-22: Telangana list has 2,703 codes; the dealership-pricing page names 70 of them
(e.g. Meteor "Stellar Black" VAHM60SK Rs 2,10,580).
Gaps: only the ~10 models the dealership-pricing page names (Super Meteor 650, Hunter 350, Classic 350, Meteor,
Scram 411, Interceptor, Continental GT, Himalayan, Bullet 350 / ES) can be priced - the API's other codes have no
published name, so they are skipped rather than guessed (no 450/650 twins other than Super Meteor, no Bear/Classic
650/Guerrilla). The city price pages (/prices-in-<city>/) render a Chennai table, so they are not used. Placeholder
prices below Rs 10,000 (e.g. "1") are dropped. Dealer locator script (dealers-around-me) is not loaded as a readable
asset -> dealers NotSupported. Engine cc not read.
"""

from __future__ import annotations

import html as _html
import json
import re

from ..base import BrandAdapter, NotSupported, Variant
from ._2w_common import Site, inr, norm, trans_2w
from ._geo import geo

BASE = "https://www.royalenfield.com"
PRICING_PAGE = "/in/en/motorcycles/dealership-pricing/"
API = "https://api.royalenfield.com/aem-content/master-data/motorcycle-prices"
SLUG = {"supermeteor650": "super-meteor-650", "hunter350": "hunter-350", "classic350": "classic-350", "meteor": "meteor",
        "scram411": "scram411", "interceptor": "interceptor", "continentalgt": "continental-gt", "himalayan": "himalayan",
        "bullet350": "bullet-350", "bullet350es": "bullet-350"}
BODY = {"hunter350": "Street", "interceptor": "Street", "continentalgt": "Sports", "scram411": "Adventure",
        "himalayan": "Adventure"}


class RoyalEnfieldAdapter(BrandAdapter):
    brand = "Royal Enfield"
    slug = "royal_enfield"
    website = BASE
    vehicle_type = "bike"

    def __init__(self):
        self._s = None
        self._catalog = None
        self._img = {}
        self._pages = {}
        self._ok = set()

    @property
    def s(self) -> Site:
        if self._s is None:
            self._s = Site(BASE)
        return self._s

    def _cat(self) -> list[dict]:
        if self._catalog is None:
            page = self.s.text(PRICING_PAGE)
            m = re.search(r'motorcycleJson="([^"]*)"', page)
            if not m:
                raise NotSupported("Royal Enfield dealership-pricing page no longer carries motorcycleJson")
            self._catalog = json.loads(_html.unescape(m.group(1)))
        return self._catalog

    def _image(self, key: str) -> str | None:
        """First full product render in the model page's JSON-LD (skipping truncated '…' URLs); a model that shares
        a page with another (Bullet 350 / Bullet 350 ES) gets the next colour so images stay unique. None when the
        page redirects to a different model (Scram 411 -> Scram 440, Himalayan -> Himalayan 450)."""
        slug = SLUG.get(key)
        if not slug:
            return None
        if slug not in self._pages:
            imgs = []
            try:
                r = self.s.get(f"/in/en/motorcycles/{slug}/")
                if f"/motorcycles/{slug}/" in str(r.url):
                    self._ok.add(slug)
                    imgs = [u.strip() for u in re.findall(r'"@type":"ImageObject","url":"([^"]+)"', r.text)
                            if "…" not in u and "…" not in u and "/content/dam/" in u]
            except Exception:
                pass
            self._pages[slug] = list(dict.fromkeys(imgs))
        if key not in self._img:
            used = set(self._img.values())
            self._img[key] = next((u for u in self._pages[slug] if u not in used), None)
        return self._img[key]

    def _url(self, key: str) -> str | None:
        self._image(key)
        return f"{BASE}/in/en/motorcycles/{SLUG[key]}/" if SLUG.get(key) in self._ok else None

    def models(self) -> list[dict]:
        out = []
        for m in self._cat():
            name = m.get("motorcycleName") or m.get("motorcycleCode")
            k = norm(name)
            out.append({"name": name, "url": self._url(k),
                        "body_type": BODY.get(k, "Cruiser"), "image_url": self._image(k)})
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        g = geo(city)
        if not g:
            raise NotSupported(f"state for {city!r} unknown")
        res = self.s.post(API, data={"state": g[0]}, headers={"Origin": BASE, "Referer": BASE + PRICING_PAGE}).json()
        data = res.get("data") or {}
        if not data:
            raise NotSupported(f"Royal Enfield publishes no price list for {g[0]}: {res.get('message')}")
        out = []
        for m in self._cat():
            name = m.get("motorcycleName") or m.get("motorcycleCode")
            k = norm(name)
            body = BODY.get(k, "Cruiser")
            for v in m.get("variantList") or []:
                row = data.get(v.get("variantCode"))
                price = inr(row.get("exshowroom")) if row else None
                if not price or price < 10000:
                    continue
                out.append(Variant(model=name, variant=v.get("motorcycleVariant", "").strip(), fuel="Petrol",
                                   transmission=trans_2w(body, "Petrol"), ex_showroom_inr=price, city=city,
                                   source_url=f"{API}#state={g[0]}&code={v.get('variantCode')}", body_type=body,
                                   model_url=self._url(k),
                                   image_url=self._image(k)))
        return out

    def dealers(self, city: str = "Hyderabad"):
        raise NotSupported("Royal Enfield locate-us page loads its dealers-around-me script dynamically; not read")

    def offers(self, city: str = "Hyderabad"):
        raise NotSupported("offers not read by this adapter")


ADAPTER = RoyalEnfieldAdapter()
