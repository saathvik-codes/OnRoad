"""
Ather Energy - https://www.atherenergy.com  (robots.txt: Allow /, Disallow /api/, /_next/, Crawl-delay: 10)

Endpoints used (Next.js pages; the price data is server-rendered into the page, not fetched from /api/):
  GET /rizta, GET /450      page props "transformedProductData": {"<City>": [{model, variantCode, name (colour),
                            basePrice, fameIncentive, stateSubsidy, introductoryOffer, total, insurance,
                            rtoRegistration, onRoadPrice, ...}]}  - the city price table behind the configurator.
                            Colour cut-outs under /images/gen4/<model>/colors/*.webp.
Price stored: "total" = Ather's *effective ex-showroom* for that city (basePrice - PM E-DRIVE incentive - state
subsidy - introductory offer); the page's own onRoadPrice = total + insurance + RTO. Variant = Ather's model code
(e.g. RIZS1LR = Rizta S family) because the page publishes no display name per code.
Verified 2026-10-23 (Hyderabad, /rizta): RIZS1LR total Rs 1,22,891 (basePrice 1,31,891 - 5,000 - 4,000);
RIZZ1HR Rs 1,57,891.
Gaps / protection: Cloudflare answers some requests (sitemap, /450, /450/configurator) with an "Attention
Required" challenge; those are never worked around -> that model is skipped (NotSupported if both are blocked).
Robots Crawl-delay 10 s is honoured. Dealers (/locate-ather-dealer) and offers not read.
"""

from __future__ import annotations

import json
import re

from ..base import BrandAdapter, NotSupported, Variant
from ._2w_common import Site, inr

BASE = "https://www.atherenergy.com"
PAGES = {"Rizta": "/rizta", "450": "/450"}
FAMILY = {"RIZS": "Rizta S", "RIZZ": "Rizta Z"}


class AtherAdapter(BrandAdapter):
    brand = "Ather Energy"
    slug = "ather"
    website = BASE
    vehicle_type = "bike"

    def __init__(self):
        self._s = None
        self._data = {}
        self._blocked = []

    @property
    def s(self) -> Site:
        if self._s is None:
            self._s = Site(BASE)
        return self._s

    def _load(self):
        if self._data or self._blocked:
            return
        for model, path in PAGES.items():
            try:
                page = self.s.text(path)
            except NotSupported as e:
                self._blocked.append(f"{path}: {e}")
                continue
            i = page.find('"transformedProductData":')
            if i < 0:
                self._blocked.append(f"{path}: no transformedProductData")
                continue
            data, _ = json.JSONDecoder().raw_decode(page[i + len('"transformedProductData":'):])
            imgs = re.findall(r'(https://www\.atherenergy\.com/images/gen4/[a-z0-9]+/colors/[^"\\ ]+\.webp)', page)
            self._data[model] = {"prices": data, "url": BASE + path, "image": imgs[0] if imgs else None}
        if not self._data:
            raise NotSupported("Ather pages blocked by Cloudflare challenge (not bypassed): " + "; ".join(self._blocked))

    def models(self) -> list[dict]:
        self._load()
        return [{"name": m, "url": d["url"], "body_type": "Electric Scooter", "image_url": d["image"]} for m, d in self._data.items()]

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        self._load()
        out = []
        for model, d in self._data.items():
            rows = next((v for k, v in d["prices"].items() if k.lower() == city.lower()), None) or []
            seen = set()
            for x in rows:
                code = x.get("model") or x.get("variantCode")
                price = inr(x.get("total"))
                if not code or not price or code in seen:
                    continue
                seen.add(code)
                fam = FAMILY.get(code[:4], model)
                out.append(Variant(model=model, variant=f"{fam} ({code})", fuel="Electric", transmission="Automatic",
                                   ex_showroom_inr=price, city=city, source_url=f"{d['url']}#transformedProductData.{city}.{code}",
                                   body_type="Electric Scooter", model_url=d["url"], image_url=d["image"]))
        if not out:
            raise NotSupported(f"Ather publishes no price rows for {city!r}" + (f" (blocked: {self._blocked})" if self._blocked else ""))
        return out


    def specs(self):
        """The model page's schema.org Product JSON-LD additionalProperty list is Ather Energy's spec sheet for the model
        (displacement, power, torque, brakes, tank ...); it is attached to each priced variant of that model."""
        from ._spec_kit import model_sheet_specs
        return model_sheet_specs(self, "Ather Energy")

    def dealers(self, city: str = "Hyderabad"):
        raise NotSupported("Ather dealer locator not read by this adapter")

    def offers(self, city: str = "Hyderabad"):
        raise NotSupported("offers not read by this adapter (introductory offer is folded into the effective ex-showroom)")


ADAPTER = AtherAdapter()
