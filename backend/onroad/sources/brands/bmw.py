"""
BMW India adapter - dealers only; bmw.in itself cannot be read with plain httpx.

Endpoints:
  - https://www.bmw.in/ (any path, incl. robots.txt): the connection is held open until timeout (HTTP/1.1) or reset
    (HTTP/2) - Akamai edge bot protection, checked 2026-10-19/20. So models, the BMW India price list and offers are
    not reachable without a real browser -> NotSupported (message built live by _lux_common.blocked()).
  - https://c2b-services.bmw.com/c2b-localsearch/services/api/v4/clients/BMWSTAGE2_DLO/IN/pois
        ?brand=BMW_BMWM&category=BM&country=IN&language=en&lat=..&lng=..&maxResults=..
        BMW Group's public dealer-locator service (the "Find a dealer" backend of BMW market sites). Answers plain
        JSON. NOTE: we could not open bmw.in to confirm from its page source that bmw.in calls this exact client id;
        the data (BMW India outlets, India phone numbers, BMW dealer homepages) is BMW's own.
Verified 2026-10-20: 56 BMW outlets in India; Hyderabad = 5: KUN Motoren Khairatabad (SA), KUN Motoren Jubilee
Hills (SA), Krishna Automotive Mahaveer Gateway (SA), KUN Motoren RTC X Roads (SE), Krishna Automotive MAS
Industries (SE). outletTypes SA = sales, SE = service, FU = sales+service.
Gaps: no models / prices / offers (site blocked); the API's `state` field is stale for some outlets (Hyderabad
outlets say "Andhra Pradesh").
"""

from __future__ import annotations

from ..base import BrandAdapter, Dealer, Offer, Variant
from ._lux_common import blocked, bmw_group_dealers

SITE = "https://www.bmw.in/en/index.html"


class BMWAdapter(BrandAdapter):
    brand = "BMW"
    slug = "bmw"
    website = SITE

    def models(self) -> list[dict]:
        raise blocked(self.brand, SITE, "model range")

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        raise blocked(self.brand, "https://www.bmw.in/en/all-models.html", "ex-showroom price list")

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        return bmw_group_dealers("BMW_BMWM", "BM", city, "https://www.bmw.in/en/fastlane/dealer-locator.html")

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise blocked(self.brand, SITE, "offers")


ADAPTER = BMWAdapter()
