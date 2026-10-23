"""
Ola Electric - https://www.olaelectric.com  (robots.txt: Allow /)

Endpoints used:
  GET /electric-scooter-price/<state>/<city>   (listed in /sitemap_city_pages.xml)
        - price cards (div.dpbc_product_card, preceded by an HTML comment naming the variant, e.g.
          "<!-- S1 Pro+ 5.2kWh -->") with span#..._EX_SHOWROOM_PRICE, battery kWh, and the product cut-out on Ola's
          CDN (cdn.olaelectric.com/sites/evdp/pages/pricing/ev_scooter_product_*_web_image.webp, 1206x1176 RGBA)
        - #current_city_data JSON: the city's Ola stores (name, address, pincode, lat/lng, type)
City: the card prices carry national ids (..._EN_IN_EX_SHOWROOM_PRICE) and were identical on the Hyderabad and
Bangalore pages on 2026-10-23, so prices() returns city="India (national)"; dealers are per city.
Verified 2026-10-23: S1 Pro+ 5.2kWh Rs 1,74,999; S1 X 2kWh Rs 89,999; 19 Hyderabad stores.
Gaps: only the S1 3rd-gen scooters have variant cards; Roadster motorcycles, S1 Z and Gig show only
"starts at" figures in the menu (not stored); offers/specs not read.
"""

from __future__ import annotations

import json
import re

from ..base import BrandAdapter, Dealer, NotSupported, Variant
from ._2w_common import NATIONAL, Site, clean, inr
from ._geo import geo

BASE = "https://www.olaelectric.com"


class OlaElectricAdapter(BrandAdapter):
    brand = "Ola Electric"
    slug = "ola_electric"
    website = BASE
    vehicle_type = "bike"

    def __init__(self):
        self._s = None
        self._pages = {}

    @property
    def s(self) -> Site:
        if self._s is None:
            self._s = Site(BASE)
        return self._s

    def _url(self, city: str) -> str:
        g = geo(city)
        if not g:
            raise NotSupported(f"state for {city!r} unknown")
        return f"{BASE}/electric-scooter-price/{g[0].lower().replace(' ', '-')}/{city.lower().replace(' ', '-')}"

    def _page(self, city: str) -> tuple[str, str]:
        url = self._url(city)
        if url not in self._pages:
            r = self.s.get(url, ok=(200, 404))
            if r.status_code == 404 or "/404" in str(r.url):
                raise NotSupported(f"Ola has no price page for {city!r}")
            self._pages[url] = r.text
        return url, self._pages[url]

    def _cards(self, city: str = "Hyderabad"):
        url, page = self._page(city)
        out = []
        for name, card in re.findall(r"<!--\s*([^>]*?)\s*-->\s*<div class=\"dpbc_product_card\">(.*?)(?=<!--[^>]*-->\s*<div class=\"dpbc_product_card\">|</section>)", page, re.S):
            price = re.search(r'_EX_SHOWROOM_PRICE">([\d,]+)<', card)
            img = re.search(r'class="dpbc_product_card_up"><img src="([^"]+)"', card)
            kwh = re.search(r'([\d.]+)\s*kWh</p>\s*<p class="dpbc_product_card_info_subtitle">Battery', card)
            if not price:
                continue
            # "S1 Pro+" -> "S1 Pro Plus": the catalogue key drops "+", which would merge S1 Pro+ into S1 Pro
            model = re.sub(r"\s*[\d.]+\s*kWh$", "", name).strip().replace("+", " Plus")
            out.append({"model": "Ola " + model, "variant": name, "price": inr(price.group(1)),
                        "image": img.group(1) if img else None, "kwh": float(kwh.group(1)) if kwh else None, "src": url})
        return out

    def models(self) -> list[dict]:
        seen = {}
        for c in self._cards():
            seen.setdefault(c["model"], {"name": c["model"], "url": c["src"], "body_type": "Electric Scooter", "image_url": c["image"]})
        return list(seen.values())

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        cards = self._cards(city)
        if not cards:
            raise NotSupported(f"Ola price cards not found for {city!r}")
        return [Variant(model=c["model"], variant=c["variant"], fuel="Electric", transmission="Automatic",
                        ex_showroom_inr=c["price"], city=NATIONAL, source_url=c["src"], body_type="Electric Scooter",
                        battery_kwh=c["kwh"], model_url=c["src"], image_url=c["image"]) for c in cards]

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        url, page = self._page(city)
        m = re.search(r"id='current_city_data' style='display:none' data-value='(\[.*?\])'", page, re.S)
        if not m:
            raise NotSupported("Ola city page carries no store list")
        state = geo(city)[0]
        out = []
        for d in json.loads(m.group(1)):
            out.append(Dealer(name=clean(d.get("businessName") or d.get("name")), address=clean(d.get("store_address")),
                              city=city, state=state, pincode=d.get("pincode"), phone=None, email=None,
                              lat=float(d["lat"]) if d.get("lat") else None, lng=float(d["lng"]) if d.get("lng") else None,
                              kind="sales+service" if "service" in (d.get("type") or "") else "sales", source_url=url))
        return out

    def offers(self, city: str = "Hyderabad"):
        raise NotSupported("offers not read by this adapter")


ADAPTER = OlaElectricAdapter()
