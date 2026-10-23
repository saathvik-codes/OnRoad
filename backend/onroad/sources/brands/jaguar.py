"""
Jaguar India adapter - Jaguar currently has NO new cars on sale in India.

Endpoint checked: https://www.jaguar.in/ -> https://www.jaguar.com/en-in/index.html (and /en-in/type-01.html).
Verified 2026-10-19/20: the India site only shows the rebranded "Type 01" teaser ("Final customer models and features
are not yet available for sale and may vary prior to launch"), plus Find us / Support / Approved Used. There is no
model range, price list or offer. models() confirms this live and returns [] while that is still true; the other
methods raise NotSupported. Jaguar service outlets are part of the JLR retailer network (see land_rover.py).
"""

from __future__ import annotations

from ..base import BrandAdapter, Dealer, NotSupported, Offer, Variant
from ._lux_common import Polite

HOME = "https://www.jaguar.com/en-in/index.html"
WHY = "Jaguar has no new models on sale in India (jaguar.com/en-in shows only the 'Type 01' pre-launch teaser)"


class JaguarAdapter(BrandAdapter):
    brand = "Jaguar"
    slug = "jaguar"
    website = HOME

    def models(self) -> list[dict]:
        with Polite() as p:
            page = p.text(HOME.replace("index.html", "type-01.html"))
        if "not yet available for sale" in page:
            return []
        raise NotSupported("Jaguar India home page changed (no longer only Type 01) - adapter needs re-verification")

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        raise NotSupported(WHY)

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        raise NotSupported(WHY + "; no sales outlets")

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        raise NotSupported(WHY)


ADAPTER = JaguarAdapter()
