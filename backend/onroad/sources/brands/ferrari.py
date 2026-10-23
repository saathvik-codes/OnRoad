"""
Ferrari adapter (ferrari.com, en-IN locale; content is the global range).

Endpoints used (robots.txt allows these paths):
  - https://www.ferrari.com/en-IN/auto/car-range   __NEXT_DATA__ pageData.content.blocks[]: CarBanner blocks of the
        "line-up" chapter (until the "Special series" text block) = current production range; image ids resolve on
        https://cdn.ferrari.com/cms/network/media/img/resize/<id>
  - https://www.ferrari.com/en-IN/auto/dealers     __NEXT_DATA__ blocks[] item list of official dealers
        (code, name, countryCode, city, urlsite). No street address / phone is published in this list.
Verified 2026-10-19/20: India dealers = Select Cars (New Delhi), Navnit Motors (Mumbai), Select Cars - Bengaluru.
No Hyderabad dealer -> dealers("Hyderabad") returns [] (nearest-city substitution is not done).
Line-up on 2026-10-20: Ferrari Luce, 12Cilindri, 12Cilindri Spider, Purosangue, 849 Testarossa, 849 Testarossa Spider,
Amalfi, Amalfi Spider, 296 GTB, 296 GTS.
Prices: none published -> NotSupported("price on request"). Offers: none -> NotSupported.
Gaps: Dealer.address is only the city (Ferrari's list has no street address; the dealers' own *.ferraridealers.com
sites failed TLS verification from httpx, so they are not read). body_type is our reading of the name
(Spider = Convertible, Purosangue = SUV, otherwise None).
"""

from __future__ import annotations

import re

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._lux_common import Polite, city_match, next_data

RANGE_URL = "https://www.ferrari.com/en-IN/auto/car-range"
DEALER_URL = "https://www.ferrari.com/en-IN/auto/dealers"
IMG = "https://cdn.ferrari.com/cms/network/media/img/resize/{}?width=1080"


def _blocks(page: str) -> list[dict]:
    d = next_data(page)
    return d["props"]["pageProps"]["initialProps"]["pageData"]["content"]["blocks"]


class FerrariAdapter(BrandAdapter):
    brand = "Ferrari"
    slug = "ferrari"
    website = "https://www.ferrari.com/en-IN"

    def models(self) -> list[dict]:
        with Polite() as p:
            blocks = _blocks(p.text(RANGE_URL))
        out, inside = [], False
        for b in blocks:
            if b.get("type") == "CarBanner" and (b.get("chapter") or {}).get("name", "").lower() == "line-up":
                inside = True
            elif b.get("type") == "TextBlock" and inside:
                break
            if not inside or b.get("type") != "CarBanner":
                continue
            cta = b.get("cta") or {}
            name = re.sub(r"(?i)^discover the\s+", "", cta.get("content") or b.get("slug", "")).strip()
            name = name.title().replace("Gtb", "GTB").replace("Gts", "GTS") if name.isupper() else name
            media = (b.get("media") or {}).get("landscapeBig") or {}
            low = name.lower()
            body = "Convertible" if "spider" in low else ("SUV" if "purosangue" in low else None)
            out.append({"name": name, "url": cta.get("url"), "body_type": body,
                        "image_url": IMG.format(media["id"]) if media.get("id") else None})
        return out

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        raise NotSupported("price on request: Ferrari publishes no prices for India")

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        with Polite() as p:
            blocks = _blocks(p.text(DEALER_URL))
        out = []
        for b in blocks:
            for it in b.get("items") or []:
                if not isinstance(it, dict) or it.get("countryCode") != "IN":
                    continue
                if not city_match(city, it.get("city")):
                    continue
                out.append(Dealer(name=it.get("name"), address=it.get("city") or "", city=it.get("city") or city,
                                  state="", pincode=None, phone=None, email=None, lat=None, lng=None,
                                  kind="sales+service", source_url=DEALER_URL, website=it.get("urlsite")))
        return out

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise NotSupported("Ferrari publishes no offers or finance schemes for India")


ADAPTER = FerrariAdapter()
