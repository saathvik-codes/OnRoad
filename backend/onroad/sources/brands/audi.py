"""
Audi India adapter - NOT AVAILABLE with plain httpx.

Checked 2026-10-19/20: every path on https://www.audi.in/ (home, robots.txt) answers 403 "Access Denied"
(Akamai, errors.edgesuite.net reference) to plain httpx, with or without browser-like headers, HTTP/1.1 and HTTP/2.
audi.com (global) is reachable but carries no India models, prices or dealers. The India dealer search and price
pages live on the blocked host, so every method raises NotSupported with the live probe result. Audi does sell in
India (not verifiable from its own India site in this run).
"""

from __future__ import annotations

from ..base import BrandAdapter, Dealer, Offer, Variant
from ._lux_common import blocked

SITE = "https://www.audi.in/"


class AudiAdapter(BrandAdapter):
    brand = "Audi"
    slug = "audi"
    website = SITE

    def models(self) -> list[dict]:
        raise blocked(self.brand, SITE, "model range")

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        raise blocked(self.brand, SITE, "ex-showroom prices")

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        raise blocked(self.brand, SITE, "dealer search")

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise blocked(self.brand, SITE, "offers")


ADAPTER = AudiAdapter()
