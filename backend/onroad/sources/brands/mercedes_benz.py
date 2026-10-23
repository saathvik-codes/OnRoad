"""
Mercedes-Benz India adapter - NOT AVAILABLE with plain httpx.

Checked 2026-10-19/20: https://www.mercedes-benz.co.in/ (home, /passengercars.html, robots.txt) holds the connection
open until timeout over HTTP/1.1 and resets the stream over HTTP/2; https://www.mercedes-benz.com/en/ answers
403 "Access Denied" (Akamai). The dealer locator (api.corpinter.net DLC) needs an API key that is only published in
those blocked pages, and the India price list / offers are on the blocked host. We do not evade bot protection, so
every method raises NotSupported with the live probe result. Mercedes-Benz does sell in India (not verifiable from
its own site in this run - the site could not be read).
"""

from __future__ import annotations

from ..base import BrandAdapter, Dealer, Offer, Variant
from ._lux_common import blocked

SITE = "https://www.mercedes-benz.co.in/passengercars.html"


class MercedesBenzAdapter(BrandAdapter):
    brand = "Mercedes-Benz"
    slug = "mercedes_benz"
    website = "https://www.mercedes-benz.co.in"

    def models(self) -> list[dict]:
        raise blocked(self.brand, SITE, "model range")

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        raise blocked(self.brand, SITE, "ex-showroom price list")

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        raise blocked(self.brand, SITE, "dealer locator (its API key is only in the blocked pages)")

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise blocked(self.brand, SITE, "offers")


ADAPTER = MercedesBenzAdapter()
