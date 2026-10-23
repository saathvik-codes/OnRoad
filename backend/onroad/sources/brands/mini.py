"""
MINI India adapter - dealers only; mini.in itself cannot be read with plain httpx.

Endpoints:
  - https://www.mini.in/ (any path, incl. robots.txt): connection held open until timeout / HTTP/2 stream reset -
    Akamai edge bot protection, checked 2026-10-19/20 -> models, prices, offers: NotSupported.
  - https://c2b-services.bmw.com/c2b-localsearch/services/api/v4/clients/BMWSTAGE2_DLO/IN/pois
        ?brand=MINI&category=MI&country=IN&...   BMW Group's public dealer-locator service (see bmw.py for caveat:
        not confirmed from mini.in page source because mini.in is unreachable).
Verified 2026-10-20: 43 MINI outlets in India; Hyderabad = 3: "MINI Integrated KUN Motoren Pvt. Ltd. Khairatabad"
(SA = sales) plus two shared BMW Group service outlets (KUN Motoren RTC X Roads, Krishna Automotive MAS Industries).
Gaps: no models / prices / offers (site blocked).
"""

from __future__ import annotations

from ..base import BrandAdapter, Dealer, Offer, Variant
from ._lux_common import blocked, bmw_group_dealers

SITE = "https://www.mini.in/en_IN/home.html"


class MiniAdapter(BrandAdapter):
    brand = "MINI"
    slug = "mini"
    website = "https://www.mini.in"

    def models(self) -> list[dict]:
        raise blocked(self.brand, SITE, "model range")

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        raise blocked(self.brand, SITE, "ex-showroom price list")

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        return bmw_group_dealers("MINI", "MI", city, "https://www.mini.in/en_IN/home/find-a-dealer.html")

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise blocked(self.brand, SITE, "offers")


ADAPTER = MiniAdapter()
