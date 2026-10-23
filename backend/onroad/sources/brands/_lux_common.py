"""
Small helpers shared by the premium/luxury brand adapters (Lexus, Land Rover, Porsche, Lamborghini, Ferrari, Aston Martin,
McLaren, Lotus, BMW, MINI and the bot-blocked brands).

Not an adapter itself (no ADAPTER); the leading underscore keeps brand loaders from treating it as one.
"""

from __future__ import annotations

import html
import json
import re
import time

import httpx

from ..base import USER_AGENT, NotSupported

POLITE_DELAY_S = 1.0          # pause between consecutive requests to the same brand


class Polite:
    """httpx.Client wrapper: sleeps POLITE_DELAY_S between requests and raises on HTTP errors."""

    def __init__(self, extra_headers: dict | None = None, timeout: float = 30, delay: float = POLITE_DELAY_S):
        headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-IN,en;q=0.9"}
        if extra_headers:
            headers.update(extra_headers)
        self.c = httpx.Client(timeout=timeout, follow_redirects=True, headers=headers)
        self.delay = delay
        self._last = 0.0

    def get(self, url: str, **kw) -> httpx.Response:
        gap = time.monotonic() - self._last
        if self._last and gap < self.delay:
            time.sleep(self.delay - gap)
        try:
            r = self.c.get(url, **kw)
        finally:
            self._last = time.monotonic()
        r.raise_for_status()
        return r

    def text(self, url: str, **kw) -> str:
        return self.get(url, **kw).text

    def json(self, url: str, **kw):
        return self.get(url, **kw).json()

    def close(self):
        self.c.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def clean(text: str | None) -> str:
    """HTML fragment -> single-line plain text."""
    if not text:
        return ""
    return _WS.sub(" ", html.unescape(_TAG.sub(" ", text))).replace("\xa0", " ").strip()


def inr(value) -> int | None:
    """'INR 67,93,000' / '₹ 14 600 000' / 21129000 -> int rupees (drops paise like '.00')."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(round(value))
    s = str(value)
    s = re.sub(r"\.\d{1,2}\b", "", s)            # '2,11,29,000.00' -> '2,11,29,000'
    digits = re.sub(r"\D", "", s)
    return int(digits) if digits else None


def next_data(page: str) -> dict:
    """Parse the Next.js __NEXT_DATA__ JSON blob of a page."""
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page, re.S)
    if not m:
        raise ValueError("__NEXT_DATA__ not found")
    return json.loads(m.group(1))


def astro_decode(v):
    """Decode Astro island serialisation: [0, x] -> x (objects recursively), [1, [...]] -> list."""
    if isinstance(v, list) and len(v) == 2 and isinstance(v[0], int):
        kind, x = v
        if kind == 0:
            return {k: astro_decode(i) for k, i in x.items()} if isinstance(x, dict) else x
        if kind == 1:
            return [astro_decode(i) for i in x]
        return x
    if isinstance(v, list) and len(v) == 1 and isinstance(v[0], int):
        return None                                # [0] == undefined
    return v


def astro_islands(page: str) -> list[dict]:
    """All <astro-island props="..."> payloads of a page, decoded."""
    out = []
    for attrs in re.findall(r"<astro-island([^>]*)>", page):
        m = re.search(r'props="([^"]*)"', attrs)
        if not m:
            continue
        try:
            raw = json.loads(html.unescape(m.group(1)))
        except ValueError:
            continue
        out.append({k: astro_decode(v) for k, v in raw.items()})
    return out


def city_match(city: str, *candidates: str | None) -> bool:
    """Loose city equality: 'Hyderabad' matches 'HYDERABAD', 'Hyderabad, Telangana'; Bengaluru == Bangalore etc."""
    alias = {"bangalore": "bengaluru", "bombay": "mumbai", "gurgaon": "gurugram", "calcutta": "kolkata",
             "madras": "chennai", "bengalore": "bengaluru", "cochin": "kochi", "newdelhi": "delhi"}

    def key(s):
        k = re.sub(r"[^a-z]", "", (s or "").lower())
        return alias.get(k, k)
    want = key(city)
    for c in candidates:
        if not c:
            continue
        for part in re.split(r"[,/-]", c):
            if key(part) == want:
                return True
    return False


BMW_C2B = "https://c2b-services.bmw.com/c2b-localsearch/services/api/v4/clients/BMWSTAGE2_DLO/IN/pois"
_BMW_KIND = {"SA": "sales", "SE": "service", "FU": "sales+service"}


def bmw_group_dealers(brand_param: str, category: str, city: str, source_url: str):
    """BMW Group dealer-locator service (c2b-services.bmw.com) for India. The API needs a search point, so we search
    from the geographic centre of India with a large result cap and filter the outlets on their city field."""
    from ..base import Dealer
    params = {"brand": brand_param, "cached": "off", "category": category, "maxResults": 999, "country": "IN",
              "language": "en", "lat": 22.0, "lng": 79.0}
    with Polite(extra_headers={"Accept": "application/json"}) as p:
        data = p.json(BMW_C2B, params=params)
    out = []
    for x in (data.get("data") or {}).get("pois") or []:
        if not city_match(city, x.get("city"), x.get("settlement")):
            continue
        a = x.get("attributes") or {}
        types = a.get("outletTypes") or []
        kinds = {_BMW_KIND.get(t, "") for t in types} - {""}
        kind = "sales+service" if "sales+service" in kinds or {"sales", "service"} <= kinds else (kinds.pop() if kinds else "")
        out.append(Dealer(name=clean(x.get("name")), address=", ".join(s for s in (x.get("street"), x.get("additionalStreet"),
                          x.get("settlement"), x.get("city"), x.get("postalCode")) if s),
                          city=x.get("city") or city, state=x.get("state") or "", pincode=x.get("postalCode"),
                          phone=a.get("phone") or None, email=a.get("mail") or None, lat=x.get("lat"), lng=x.get("lng"),
                          kind=kind, source_url=source_url, website=a.get("homepage") or None))
    return out


def blocked(brand: str, url: str, what: str) -> NotSupported:
    """Probe `url` once with plain httpx and build a NotSupported explaining what the brand's site returned.

    Used for brands whose own sites refuse plain-httpx requests (Akamai/edge bot protection answering 403 'Access
    Denied' or holding the connection until timeout). We do not try to evade such protection.
    """
    try:
        with Polite(timeout=15) as p:
            r = p.c.get(url)
        seen = f"HTTP {r.status_code}"
        if r.status_code == 403 and "Access Denied" in r.text:
            seen += " 'Access Denied' (Akamai edge bot protection)"
        elif r.status_code == 200:
            seen += " (site answered this time: adapter needs re-verification before use)"
    except httpx.TimeoutException:
        seen = "connection held open until timeout (edge bot protection)"
    except httpx.HTTPError as e:
        seen = f"{type(e).__name__}: {e}"
    return NotSupported(f"{brand}: {what} unavailable - {url} refuses plain httpx requests ({seen}); "
                        "data would need a real browser, which this project does not use")
