"""
Shared parser for brand dealer locators hosted on the Singleinterface store-locator platform
(e.g. dealers.skoda-auto.co.in, dealers.volkswagen.co.in). These are the brands' official dealer-locator sub-domains.
City listing pages live at /location/<state-slug>/<city-slug>[?page=N] and are allowed by their robots.txt
(only /storelocator/*, /storemap/* etc. are disallowed). Not a brand adapter (no ADAPTER).
"""

from __future__ import annotations

import html as _html
import re
import time

from ..base import Dealer

# state used in the /location/<state>/<city> URL; only needed when a caller does not pass the state explicitly
CITY_STATE = {
    "hyderabad": "telangana", "secunderabad": "telangana", "bengaluru": "karnataka", "bangalore": "karnataka",
    "mumbai": "maharashtra", "pune": "maharashtra", "chennai": "tamil-nadu", "kolkata": "west-bengal",
    "delhi": "delhi", "new delhi": "delhi", "ahmedabad": "gujarat", "jaipur": "rajasthan", "lucknow": "uttar-pradesh",
    "kochi": "kerala", "visakhapatnam": "andhra-pradesh", "vijayawada": "andhra-pradesh", "chandigarh": "chandigarh",
    "gurugram": "haryana", "gurgaon": "haryana", "noida": "uttar-pradesh", "indore": "madhya-pradesh",
    "bhopal": "madhya-pradesh", "nagpur": "maharashtra", "coimbatore": "tamil-nadu", "surat": "gujarat",
}


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _text(fragment: str) -> str:
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def parse_cards(page: str) -> list[dict]:
    out = []
    for card in page.split('class="store-info-box"')[1:]:
        card = card.split('class="store-info-box"')[0]
        g = lambda p: (re.search(p, card, re.S) or [None, None])[1]
        name = g(r'class="outlet-name">.*?<a[^>]*>(.*?)</a>')
        addr = g(r'class="outlet-address">.*?<div class="info-text">(.*?)</div>')
        company = g(r'icn-outlet"></span>\s*</div>\s*<div class="info-text">(.*?)</div>')
        addr_t = _text(addr or "")
        pin = re.search(r"\b(\d{6})\b", addr_t)
        out.append({
            "name": _text(name or ""), "company": _text(company or "") or None,
            "address": re.sub(r"\s*-\s*\d{6}\s*$", "", addr_t).strip(" ,"), "pincode": pin.group(1) if pin else None,
            "phone": g(r'href="tel:([^"]+)"'), "lat": g(r'class="outlet-latitude" value="([-\d.]+)"'),
            "lng": g(r'class="outlet-longitude" value="([-\d.]+)"'),
            "website": g(r'class="btn btn-website" href="([^"]+)"'),
            "cta": _text(g(r'class="btn btn-getintouch"[^>]*>(.*?)</a>') or ""),
        })
    return out


def fetch_city(client, base: str, city: str, state: str | None = None, delay: float = 0.8, max_pages: int = 10) -> tuple[str, list[dict]]:
    state_slug = _slug(state) if state else CITY_STATE.get(city.lower())
    if not state_slug:
        raise LookupError(f"state for {city!r} unknown; pass state=")
    url = f"{base}/location/{state_slug}/{_slug(city)}"
    cards, seen = [], set()
    for page in range(1, max_pages + 1):
        time.sleep(delay)
        r = client.get(url, params={"page": page} if page > 1 else None)
        if r.status_code != 200:
            break
        new = [c for c in parse_cards(r.text) if (c["name"], c["address"]) not in seen]
        if not new:
            break
        for c in new:
            seen.add((c["name"], c["address"]))
        cards += new
        if f"page={page + 1}" not in r.text:
            break
    return url, cards


def to_dealers(cards: list[dict], city: str, state: str, source_url: str, sales_words=("showroom", "sales", "test drive")) -> list[Dealer]:
    """Keep outlets that sell cars: name or call-to-action mentions showroom/sales/test drive."""
    out = []
    for c in cards:
        label = f'{c["name"]} {c["cta"]}'.lower()
        sells = any(w in label for w in sales_words)
        if not sells:
            continue
        services = "service" in c["name"].lower() or "workshop" in c["name"].lower()
        out.append(Dealer(
            name=c["name"] + (f' ({c["company"]})' if c["company"] else ""), address=c["address"], city=city, state=state,
            pincode=c["pincode"], phone=c["phone"], email=None,
            lat=float(c["lat"]) if c["lat"] else None, lng=float(c["lng"]) if c["lng"] else None,
            kind="sales+service" if services else "sales", source_url=source_url, website=c["website"]))
    return out
