"""
Aprilia India (Piaggio) - https://www.aprilia.com/in_EN/

Status 2026-10-23: www.aprilia.com answers every request from this crawler (robots.txt included) with an Akamai
"Access Denied" page (HTTP 403, errors.edgesuite.net reference). That is bot protection and is not worked around,
so nothing can be read: every method raises NotSupported with the reason. models() re-checks the site each run and
says so if it ever becomes readable (a parser would then still have to be written).
"""

from __future__ import annotations

from ..base import BrandAdapter, NotSupported
from ._2w_common import Site

BASE = "https://www.aprilia.com"


class ApriliaAdapter(BrandAdapter):
    brand = "Aprilia India"
    slug = "aprilia"
    website = BASE + "/in_EN/"
    vehicle_type = "bike"

    def _check(self):
        r = Site(BASE).get("/in_EN/", ok=(200, 403))
        if r.status_code == 403:
            raise NotSupported("aprilia.com returns Akamai 'Access Denied' (HTTP 403) to this crawler; not bypassed")
        raise NotSupported("aprilia.com became readable; adapter parser not implemented yet")

    def models(self):
        self._check()

    def prices(self, city: str = "Hyderabad"):
        raise NotSupported("aprilia.com blocked by Akamai bot protection (HTTP 403); no prices read")

    def dealers(self, city: str = "Hyderabad"):
        raise NotSupported("aprilia.com blocked by Akamai bot protection (HTTP 403)")

    def offers(self, city: str = "Hyderabad"):
        raise NotSupported("aprilia.com blocked by Akamai bot protection (HTTP 403)")


ADAPTER = ApriliaAdapter()
