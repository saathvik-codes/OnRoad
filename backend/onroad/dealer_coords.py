"""
Clears showroom coordinates that are clearly wrong, so maps never send a buyer to the wrong place.

Carmakers' dealer locators sometimes publish placeholder or copied coordinates. A pin is cleared (lat/lng set to NULL)
when it is:
  * outside India;
  * rounded to two decimals or fewer in both values (a placeholder like 31.0, 77.0);
  * the same point as showrooms in a different city (copied from another dealer);
  * more than 60 km from the centre of the showroom's own city (for cities OnRoad knows).
Showrooms without a pin are still listed; directions then search Google Maps by the showroom's name and address.
Runs on start and after every dealer refresh (the refresh rewrites coordinates from the makers' sites).
"""
from __future__ import annotations

import logging
import math
from contextlib import closing

from . import db

log = logging.getLogger("onroad.dealer_coords")
MAX_KM_FROM_CITY = 60


def _km(a: float, b: float, c: float, d: float) -> float:
    p = math.pi / 180
    h = 0.5 - math.cos((c - a) * p) / 2 + math.cos(a * p) * math.cos(c * p) * (1 - math.cos((d - b) * p)) / 2
    return 12742 * math.asin(math.sqrt(max(0.0, min(1.0, h))))


def _rounded(x: float) -> bool:
    return abs(x * 100 - round(x * 100)) < 1e-9


def clean() -> dict:
    from .api import CITIES                                   # city centres OnRoad already uses for distances
    centres = {k.lower(): v for k, v in CITIES.items()}
    with closing(db.connect()) as conn:
        rows = conn.execute("SELECT id, city, lat, lng FROM dealers WHERE lat IS NOT NULL AND lng IS NOT NULL").fetchall()
        cities_at: dict[tuple, set] = {}
        for r in rows:
            cities_at.setdefault((round(r[2], 4), round(r[3], 4)), set()).add((r[1] or "").strip().lower())
        bad: dict[str, str] = {}
        for did, city, lat, lng in rows:
            key = (city or "").strip().lower()
            if not (6.0 <= lat <= 37.6 and 68.0 <= lng <= 97.5):
                bad[did] = "outside India"
            elif _rounded(lat) and _rounded(lng):
                bad[did] = "placeholder"
            elif len(cities_at[(round(lat, 4), round(lng, 4))]) > 1:
                bad[did] = "shared with another city"
            elif key in centres and _km(lat, lng, *centres[key]) > MAX_KM_FROM_CITY:
                bad[did] = "far from its city"
        if bad:
            conn.executemany("UPDATE dealers SET lat = NULL, lng = NULL WHERE id = ?", [(d,) for d in bad])
            conn.commit()
    counts: dict[str, int] = {}
    for why in bad.values():
        counts[why] = counts.get(why, 0) + 1
    if bad:
        log.info("cleared %d wrong showroom pins: %s", len(bad), counts)
    return {"cleared": len(bad), **counts}
