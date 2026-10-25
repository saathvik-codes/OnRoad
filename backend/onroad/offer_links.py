"""
Daily check of every live offer's link. Offers come from each maker's own offer pages; when that page answers
404 / 410 the offer is gone from the maker's site, so it is switched off here too (the next brand refresh brings back
anything still running). Links carrying a note after the address ("<url> (API ...)") are cut back to the address.
Other failures (timeouts, 403, 5xx) prove nothing and change nothing.

    python -m onroad.offer_links
"""
from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor

import httpx

from . import db
from .brochure_specs import UA


def _status(c: httpx.Client, u: str):
    try:
        return c.get(u).status_code
    except Exception:
        return None


def run() -> dict:
    conn = db.connect()
    live = conn.execute("""SELECT id, source_url FROM offers WHERE active = 1
                           AND (valid_until IS NULL OR valid_until = '' OR valid_until >= date('now'))""").fetchall()
    fixed = 0
    for oid, u in live:
        clean = re.split(r"\s+\(", (u or "").strip())[0]
        if u and clean != u:
            conn.execute("UPDATE offers SET source_url = ? WHERE id = ?", (clean, oid)); fixed += 1
    conn.commit()
    urls = sorted({re.split(r"\s+\(", (u or "").strip())[0] for _, u in live if u})
    with httpx.Client(headers=UA, timeout=25, follow_redirects=True) as c, ThreadPoolExecutor(6) as ex:
        status = dict(zip(urls, ex.map(lambda u: _status(c, u), urls)))
    gone = [u for u, s in status.items() if s in (404, 410)]
    ended = 0
    for u in gone:
        ended += conn.execute("UPDATE offers SET active = 0 WHERE active = 1 AND source_url = ?", (u,)).rowcount
    # an offer with no link at all can't be checked by a buyer: not shown
    ended += conn.execute("UPDATE offers SET active = 0 WHERE active = 1 AND (source_url IS NULL OR source_url = '')").rowcount
    conn.commit()
    return {"links": len(urls), "repaired": fixed, "pages_gone": gone, "offers_switched_off": ended}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1))
