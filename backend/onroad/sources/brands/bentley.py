"""
Bentley Motors adapter (India) - NOT AVAILABLE with plain httpx.

Checked 2026-10-19/20: https://www.bentleymotors.com/ (home, /en.html, robots.txt) answers 403 "Access Denied"
(Akamai) to plain httpx. Bentley publishes no prices anyway (price on request); its dealer locator and model pages
are on the blocked host. Every method raises NotSupported. Whether Bentley currently has an Indian retailer could not
be verified from its own site in this run.
"""

from __future__ import annotations

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._lux_common import blocked

SITE = "https://www.bentleymotors.com/en.html"


class BentleyAdapter(BrandAdapter):
    brand = "Bentley"
    slug = "bentley"
    website = "https://www.bentleymotors.com"

    def models(self) -> list[dict]:
        raise blocked(self.brand, SITE, "model range")

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        raise NotSupported("price on request: Bentley publishes no prices (and bentleymotors.com blocks plain httpx)")

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        raise blocked(self.brand, SITE, "dealer locator")

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise NotSupported("Bentley publishes no offers for India")


ADAPTER = BentleyAdapter()
