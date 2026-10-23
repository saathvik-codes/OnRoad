"""
Nationwide dealer sweep for brands whose official locator lists every outlet (adapter.all_dealers()).
City runs only cover the 50 launch cities; this fills in every town so GPS 'nearest showroom' works anywhere.
    python -m onroad.dealer_sweep [brand ...]
"""
from __future__ import annotations

import importlib
import json
import pkgutil
import sys
from contextlib import closing

from . import db
from .ingest import slugify
from .sources import brands as _brands
from .sources.brands._geo import coords_ok


def sweep(only: list[str] | None = None) -> list[dict]:
    out = []
    for m in pkgutil.iter_modules(_brands.__path__):
        if m.name.startswith("_") or (only and m.name not in only):
            continue
        a = getattr(importlib.import_module(f"{_brands.__name__}.{m.name}"), "ADAPTER", None)
        if a is None or not hasattr(a, "all_dealers"):
            continue
        try:
            dealers = a.all_dealers()
        except Exception as e:                       # keep what we have if the locator is down
            out.append({"brand": m.name, "error": repr(e)[:200]}); continue
        slug = a.slug or slugify(a.brand)
        with closing(db.connect()) as conn, conn:
            for d in dealers:
                if not coords_ok(d.pincode, d.lat, d.lng):
                    d.lat = d.lng = None               # wrong-state pin on the brand's page: keep the outlet, drop the map point
                did = f"{slug}/{slugify(d.name)}-{d.pincode or slugify(d.address)[:20]}"
                conn.execute("""INSERT INTO dealers (id, brand_slug, name, address, city, state, pincode, phone, email, lat, lng, kind,
                                    website, source_url, fetched_at, active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                                ON CONFLICT(id) DO UPDATE SET address = excluded.address, city = excluded.city, state = excluded.state,
                                    phone = COALESCE(excluded.phone, dealers.phone), lat = COALESCE(excluded.lat, dealers.lat),
                                    lng = COALESCE(excluded.lng, dealers.lng), fetched_at = excluded.fetched_at, active = 1""",
                             (did, slug, d.name, d.address, d.city, d.state, d.pincode, d.phone, d.email, d.lat, d.lng, d.kind,
                              d.website, d.source_url, d.fetched_at))
        out.append({"brand": slug, "dealers": len(dealers)})
    return out


if __name__ == "__main__":
    for r in sweep(sys.argv[1:] or None):
        print(json.dumps(r))
