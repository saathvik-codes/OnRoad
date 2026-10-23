"""
BMW Motorrad India - https://www.bmw-motorrad.in

Status 2026-10-23: www.bmw-motorrad.in resets the TLS connection (WinError 10054) or times out for this crawler on
every URL, robots.txt included - the edge drops non-browser clients. That is bot protection and is not worked
around, so every method raises NotSupported with the reason.
"""

from __future__ import annotations

import httpx

from ..base import BrandAdapter, NotSupported
from ._2w_common import Site

BASE = "https://www.bmw-motorrad.in"


class BMWMotorradAdapter(BrandAdapter):
    brand = "BMW Motorrad"
    slug = "bmw_motorrad"
    website = BASE
    vehicle_type = "bike"

    def models(self):
        try:
            Site(BASE).get("/en/home.html")
        except (httpx.TransportError, httpx.TimeoutException) as e:
            raise NotSupported(f"bmw-motorrad.in drops this crawler's connection ({type(e).__name__}); not bypassed")
        raise NotSupported("bmw-motorrad.in became readable; adapter parser not implemented yet")

    def prices(self, city: str = "Hyderabad"):
        raise NotSupported("bmw-motorrad.in drops non-browser connections; no prices read")

    def dealers(self, city: str = "Hyderabad"):
        raise NotSupported("bmw-motorrad.in drops non-browser connections")

    def offers(self, city: str = "Hyderabad"):
        raise NotSupported("bmw-motorrad.in drops non-browser connections")


ADAPTER = BMWMotorradAdapter()
