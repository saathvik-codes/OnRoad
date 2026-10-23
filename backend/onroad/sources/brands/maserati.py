"""
Maserati India adapter - NOT AVAILABLE with plain httpx.

Checked 2026-10-19/20: https://www.maserati.com/in/en (home, /in/en/models, /robots.txt) answers 403 "Access Denied"
(Akamai) to plain httpx. Models, any India prices, dealer locator and offers are on the blocked host, so every method
raises NotSupported with the live probe result. Whether Maserati currently sells in India could not be verified from
its own site in this run.
"""

from __future__ import annotations

from ..base import BrandAdapter, Dealer, Offer, Variant
from ._lux_common import blocked

SITE = "https://www.maserati.com/in/en"


class MaseratiAdapter(BrandAdapter):
    brand = "Maserati"
    slug = "maserati"
    website = SITE

    def models(self) -> list[dict]:
        raise blocked(self.brand, SITE, "model range")

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        raise blocked(self.brand, SITE, "prices")

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        raise blocked(self.brand, SITE, "dealer locator")

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise blocked(self.brand, SITE, "offers")


ADAPTER = MaseratiAdapter()
