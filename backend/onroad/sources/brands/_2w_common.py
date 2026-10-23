"""
Shared plumbing for the two-wheeler brand adapters (Hero, Honda 2W, TVS, Bajaj, Royal Enfield, Yamaha, Suzuki 2W,
Ather, Ola Electric, ...). Not an adapter itself (no ADAPTER).

Every request goes through Site: it reads the host's robots.txt first (urllib.robotparser) and refuses disallowed
paths, waits at least 1 s between requests (more when robots.txt sets Crawl-delay), keeps TLS verification on and
keeps cookies like a browser session. A bot-protection page (Cloudflare / Akamai / Incapsula challenge or block) is
never worked around: it raises NotSupported.
"""

from __future__ import annotations

import html as _html
import json
import re
import time
import urllib.robotparser
from urllib.parse import urlsplit

import httpx

from ..base import USER_AGENT, Dealer, NotSupported

NATIONAL = "India (national)"
BODY_TYPES = {"Commuter", "Scooter", "Cruiser", "Sports", "Adventure", "Street", "Electric Scooter"}

_CHALLENGE = re.compile(r"cf-chl|Attention Required! \| Cloudflare|challenge-platform|Just a moment\.\.\.|_Incapsula_Resource|Access Denied</TITLE>|"
                        r"Request unsuccessful\. Incapsula|errors\.edgesuite\.net|px-captcha|captcha-delivery", re.I)


class Site:
    """Polite, robots-aware session for one brand."""

    def __init__(self, base: str, delay: float = 1.0, headers: dict | None = None):
        self.base = base.rstrip("/")
        self.delay = delay
        h = {"User-Agent": USER_AGENT, "Accept-Language": "en-IN"}
        h.update(headers or {})
        self.c = httpx.Client(timeout=40, follow_redirects=True, headers=h, verify=True)
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self._last = 0.0

    def _rp(self, url: str):
        p = urlsplit(url)
        host = f"{p.scheme}://{p.netloc}"
        if host not in self._robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                self._wait(1.0)
                r = self.c.get(host + "/robots.txt")
                if r.status_code == 200 and "html" not in r.headers.get("content-type", ""):
                    rp.parse(r.text.splitlines())
                elif r.status_code in (401, 403):
                    rp.disallow_all = True
                else:
                    rp.parse([])        # no robots.txt: everything allowed
            except httpx.HTTPError:
                rp.parse([])
            self._robots[host] = rp
        return self._robots[host]

    def _wait(self, delay: float):
        gap = time.monotonic() - self._last
        if self._last and gap < delay:
            time.sleep(delay - gap)
        self._last = time.monotonic()

    def url(self, path: str) -> str:
        return path if path.startswith("http") else self.base + path

    def get(self, path: str, ok=(200,), **kw) -> httpx.Response:
        url = self.url(path)
        rp = self._rp(url)
        if not rp.can_fetch(USER_AGENT, url):
            raise NotSupported(f"robots.txt disallows {url}")
        cd = rp.crawl_delay(USER_AGENT) or 0
        self._wait(max(self.delay, float(cd)))
        r = self.c.get(url, **kw)
        if r.status_code in (403, 429, 503) and _CHALLENGE.search(r.text[:5000]):
            raise NotSupported(f"bot protection on {url} (HTTP {r.status_code}); not bypassed")
        if r.status_code not in ok:
            r.raise_for_status()
        return r

    def post(self, path: str, ok=(200,), **kw) -> httpx.Response:
        url = self.url(path)
        rp = self._rp(url)
        if not rp.can_fetch(USER_AGENT, url):
            raise NotSupported(f"robots.txt disallows {url}")
        self._wait(max(self.delay, float(rp.crawl_delay(USER_AGENT) or 0)))
        r = self.c.post(url, **kw)
        if r.status_code in (403, 429, 503) and _CHALLENGE.search(r.text[:5000]):
            raise NotSupported(f"bot protection on {url} (HTTP {r.status_code}); not bypassed")
        if r.status_code not in ok:
            r.raise_for_status()
        return r

    def text(self, path: str, **kw) -> str:
        return self.get(path, **kw).text

    def json(self, path: str, **kw):
        r = self.get(path, **kw)
        try:
            return r.json()
        except json.JSONDecodeError:
            if _CHALLENGE.search(r.text[:5000]):
                raise NotSupported(f"bot protection on {r.url}; not bypassed")
            raise


_TAG = re.compile(r"<[^>]+>")


def clean(s: str | None) -> str:
    return re.sub(r"\s+", " ", _html.unescape(_TAG.sub(" ", s or ""))).strip()


def inr(s) -> int | None:
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return int(round(s))
    d = re.sub(r"[^\d]", "", str(s).split(".")[0] if re.search(r"\.\d{1,2}$", str(s)) else str(s))
    return int(d) if d else None


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def meta(page: str, prop: str) -> str | None:
    m = (re.search(r'<meta[^>]+(?:property|name)="%s"[^>]+content="([^"]*)"' % re.escape(prop), page)
         or re.search(r'<meta[^>]+content="([^"]*)"[^>]+(?:property|name)="%s"' % re.escape(prop), page))
    return _html.unescape(m.group(1)).strip() or None if m else None


def cc_of(text: str | None) -> int | None:
    m = re.search(r"(\d{2,4}(?:\.\d+)?)\s*(?:<[^>]+>\s*)*cc\b", text or "", re.I)
    return int(round(float(m.group(1)))) if m else None


def trans_2w(body_type: str | None, fuel: str | None = None, text: str = "") -> str:
    """Scooters (CVT/automatic) and electric two-wheelers are 'Automatic'; geared motorcycles 'Manual'."""
    if body_type in ("Scooter", "Electric Scooter") or fuel == "Electric" or re.search(r"\b(CVT|DCT|automatic)\b", text, re.I):
        return "Automatic"
    return "Manual"


# manufacturer wording -> canonical two-wheeler feature key
_FEATURES = [
    (r"dual[\s-]*channel\s*abs|\bdual\s*abs\b|abs\s*\(dual", "abs_dual"),
    (r"single[\s-]*channel\s*abs|\bsingle\s*abs\b", "abs_single"),
    (r"\bcbs\b|combi(?:ned)?[\s-]*brak", "cbs"),
    (r"front\s*disc|front brake.*\bdisc", "front_disc"),
    (r"\btft\b", "tft_display"),
    (r"bluetooth|smartxonnect|roadsync|connected\s*console|tripper", "bluetooth_console"),
    (r"usb", "usb_charging"),
    (r"traction\s*control|\btcs\b|\bhstc\b|torque\s*control", "traction_control"),
    (r"ride\s*modes?|riding\s*modes?", "ride_modes"),
    (r"slipper|assist\s*(?:&|and)?\s*slipper|a\s*&\s*s\s*clutch", "slipper_clutch"),
    (r"\bled\b.*(?:head|lamp|light)|(?:head|lamp|light).*\bled\b", "led_lamps_2w"),
]


def feature_key(label: str) -> str:
    for pat, key in _FEATURES:
        if re.search(pat, label or "", re.I):
            return key
    return "other"


def dashloc_dealers(site: Site, company_id: str, city: str, state: str, origin: str, page_url: str) -> list[Dealer]:
    """Dealer locators hosted on dashloc (dealers.<brand>.com pages load weblocationapi.dashloc.com/v1/branches-by-company)."""
    out, offset, total = [], 0, None
    api = f"https://weblocationapi.dashloc.com/v1/branches-by-company/{company_id}/"
    while total is None or offset < total:
        d = site.json(api, params={"limit": 25, "offset": offset, "state": state.lower(), "city": city.lower()},
                      headers={"Origin": origin, "Referer": page_url})
        data = (d.get("data") or {})
        rows = data.get("data") or []
        total = int(data.get("total") or 0)
        if not rows:
            break
        for b in rows:
            info = b.get("web_info") or {}
            if isinstance(info, str):
                try:
                    info = json.loads(info)
                except ValueError:
                    info = {}
            addr = ", ".join(x for x in (b.get("address"), b.get("landmark"), b.get("locality")) if x and x.strip())
            cat = (info.get("primary_category") or "").lower()
            out.append(Dealer(
                name=b.get("name", "").strip(), address=addr, city=city, state=state, pincode=b.get("pincode") or None,
                phone=(b.get("mobile") or b.get("landline") or None), email=None,
                lat=float(b["lat"]) if b.get("lat") else None, lng=float(b["long"]) if b.get("long") else None,
                kind="service" if "service" in cat and "dealer" not in cat else "sales",
                source_url=page_url, website=info.get("website_url")))
        offset += len(rows)
    return out


# ---- spec tables -> Spec / Feature -------------------------------------------------------------------------------
_SPEC_KEYS = [  # (pattern on the manufacturer's label, group, key)
    (r"displacement|cubic capacity|engine capacity|^capacity$", "Engine", "displacement"),
    (r"max(imum)?\s*power|^power|power \(", "Engine", "max_power"),
    (r"max(imum)?\s*torque|^torque", "Engine", "max_torque"),
    (r"engine type|^engine$", "Engine", "engine_type"),
    (r"cooling", "Engine", "cooling"),
    (r"gear\s*box|transmission|no\.? of gears", "Engine", "gearbox"),
    (r"fuel tank|tank capacity", "Capacity", "fuel_tank"),
    (r"kerb weight|curb weight|weight", "Dimensions", "kerb_weight"),
    (r"ground clearance", "Dimensions", "ground_clearance"),
    (r"seat height|saddle height", "Dimensions", "seat_height"),
    (r"wheel\s*base", "Dimensions", "wheelbase"),
    (r"^length|overall length", "Dimensions", "length"),
    (r"front brake", "Chassis", "front_brake"),
    (r"rear brake", "Chassis", "rear_brake"),
    (r"front suspension", "Chassis", "front_suspension"),
    (r"rear suspension", "Chassis", "rear_suspension"),
    (r"front tyre|front tire", "Chassis", "front_tyre"),
    (r"rear tyre|rear tire", "Chassis", "rear_tyre"),
    (r"frame|chassis", "Chassis", "frame"),
    (r"top speed", "Performance", "top_speed"),
    (r"range", "Battery", "range"),
    (r"battery capacity|battery", "Battery", "battery_capacity"),
    (r"charging time", "Battery", "charging_time"),
    (r"mileage|fuel efficiency", "Efficiency", "mileage"),
]


def spec_rows(model: str, variant: str, rows, url: str, fuel=None, transmission=None):
    """[(label, value)] from a manufacturer spec table -> (specs, features). Unknown labels keep a slug key in group
    'Other'; equipment wording that maps to a FEATURE_KEYS two-wheeler key also becomes a Feature."""
    from ..base import Feature, Spec
    specs, feats, seen = [], [], set()
    for label, value in rows:
        label, value = clean(label).rstrip(":"), clean(value)
        if not label or not value or value in ("-", "NA", "N/A"):
            continue
        group, key = "Other", re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")[:40]
        for pat, g, k in _SPEC_KEYS:
            if re.search(pat, label, re.I):
                group, key = g, k
                break
        if key in seen:
            key = f"{key}_{len(seen)}"
        seen.add(key)
        specs.append(Spec(model=model, variant=variant, fuel=fuel, transmission=transmission, group=group, key=key,
                          label=label, value=value, source_url=url))
        for part in re.split(r"\s*[|;]\s*|,\s+(?=[A-Z])", value):
            fk = feature_key(f"{label} {part}") if group in ("Other", "Chassis") else "other"
            if fk != "other" and not any(f.key == fk for f in feats):
                feats.append(Feature(model=model, variant=variant, fuel=fuel, transmission=transmission, key=fk,
                                     label=f"{label}: {part}"[:200], source_url=url))
    return specs, feats


def table_rows(html_fragment: str):
    """Two-cell table rows (<tr><td|th>label</td><td>value</td></tr>) -> [(label, value)]."""
    out = []
    for tr in re.findall(r"<tr\b[^>]*>(.*?)</tr>", html_fragment or "", re.S):
        cells = re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", tr, re.S)
        if len(cells) >= 2:
            out.append((cells[0], cells[1]))
    return out
