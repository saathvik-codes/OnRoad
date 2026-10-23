"""
Volvo Cars India adapter - NOT AVAILABLE with plain httpx.

Checked 2026-10-19/20: https://www.volvocars.com/in/ (home, /in/sitemap.xml, /in/robots.txt) answers 403 "Access
Denied" (Akamai) to plain httpx; only the global /robots.txt is served. That robots.txt also lists AI agents
(ClaudeBot, Claude-User, ...) with Disallow /api/*, /*/shop/*/*, /*/build/*, /*/checkout/* - so Volvo's JSON APIs
(/api/...) are off-limits by policy as well, and the price/retailer data behind them must not be fetched.
Every method raises NotSupported with the live probe result. Volvo does sell in India (not verifiable from its own
site in this run).
"""

from __future__ import annotations

from ..base import BrandAdapter, Dealer, Offer, Variant
from ._lux_common import blocked

SITE = "https://www.volvocars.com/in/"


class VolvoAdapter(BrandAdapter):
    brand = "Volvo"
    slug = "volvo"
    website = SITE

    def models(self) -> list[dict]:
        raise blocked(self.brand, SITE, "model range")

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        raise blocked(self.brand, SITE, "ex-showroom prices (and /api/* is disallowed for AI agents in robots.txt)")

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        raise blocked(self.brand, SITE, "retailer locator (and /api/* is disallowed for AI agents in robots.txt)")

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise blocked(self.brand, SITE, "offers")


ADAPTER = VolvoAdapter()
