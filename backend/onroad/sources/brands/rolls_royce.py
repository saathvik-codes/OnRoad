"""
Rolls-Royce Motor Cars adapter (India) - dealers only.

Endpoints:
  - https://www.rolls-roycemotorcars.com/ (any path, incl. robots.txt): connection held open until timeout - edge bot
    protection, checked 2026-10-19/20 -> models: NotSupported (blocked).
  - https://c2b-services.bmw.com/c2b-localsearch/services/api/v4/clients/BMWSTAGE2_DLO/IN/pois
        ?brand=RR&category=RR&country=IN&...  BMW Group's public dealer-locator service, which lists Rolls-Royce
        outlets (portfolioCode RR / category ROLLS_ROYCE). Not confirmed from rolls-roycemotorcars.com page source
        because that site is unreachable with httpx.
Verified 2026-10-20: India outlets = Rolls-Royce Motor Cars Hyderabad (FU = sales+service), New Delhi (FU),
Mumbai Ownership Services (SE, Navi Mumbai) and Chennai (SE).
Prices: Rolls-Royce publishes no prices -> NotSupported("price on request"). Offers: none -> NotSupported.
"""

from __future__ import annotations

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._lux_common import blocked, bmw_group_dealers

SITE = "https://www.rolls-roycemotorcars.com/en_GB/home.html"


class RollsRoyceAdapter(BrandAdapter):
    brand = "Rolls-Royce"
    slug = "rolls_royce"
    website = "https://www.rolls-roycemotorcars.com"

    def models(self) -> list[dict]:
        raise blocked(self.brand, SITE, "model range")

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        raise NotSupported("price on request: Rolls-Royce publishes no prices (and rolls-roycemotorcars.com blocks plain httpx)")

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        return bmw_group_dealers("RR", "RR", city, "https://www.rolls-roycemotorcars.com/en_GB/find-a-dealer.html")

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise NotSupported("Rolls-Royce publishes no offers or finance schemes for India")


ADAPTER = RollsRoyceAdapter()
