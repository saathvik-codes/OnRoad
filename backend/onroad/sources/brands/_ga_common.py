"""
Small helpers shared by the group-A brand adapters (Maruti Suzuki, Hyundai, Tata, Mahindra, Kia, Toyota).

Not an adapter itself (no ADAPTER); the leading underscore keeps brand loaders from treating it as one.
"""

from __future__ import annotations

import html
import re
import time

import httpx

from ..base import USER_AGENT

POLITE_DELAY_S = 1.0          # pause before every request after the first one


class Polite:
    """httpx.Client wrapper that sleeps POLITE_DELAY_S between requests and raises on HTTP errors."""

    def __init__(self, client: httpx.Client, delay: float = POLITE_DELAY_S):
        self.c = client
        self.delay = delay
        self._last = 0.0

    def _wait(self):
        gap = time.monotonic() - self._last
        if self._last and gap < self.delay:
            time.sleep(self.delay - gap)
        self._last = time.monotonic()

    def get(self, url: str, **kw) -> httpx.Response:
        self._wait()
        r = self.c.get(url, **kw)
        r.raise_for_status()
        return r

    def post(self, url: str, **kw) -> httpx.Response:
        self._wait()
        r = self.c.post(url, **kw)
        r.raise_for_status()
        return r

    def json(self, url: str, **kw):
        return self.get(url, **kw).json()

    def close(self):
        self.c.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def make_client(verify: bool | str = True, extra_headers: dict | None = None) -> httpx.Client:
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-IN"}
    if extra_headers:
        headers.update(extra_headers)
    return httpx.Client(timeout=30, follow_redirects=True, headers=headers, verify=verify)


_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_DIGITS = re.compile(r"\d+")


def clean(text: str | None) -> str:
    """HTML fragment -> single-line plain text."""
    if not text:
        return ""
    return _WS.sub(" ", html.unescape(_TAG.sub(" ", text))).strip()


_NONVISIBLE = re.compile(r"<!--.*?-->|<script\b.*?</script>|<style\b.*?</style>|<noscript\b.*?</noscript>", re.S | re.I)


def visible_text(page: str) -> str:
    """Whole HTML page -> the text a visitor sees (scripts, JSON-LD, styles and comments removed)."""
    return clean(_NONVISIBLE.sub(" ", page or ""))


def inr(value) -> int | None:
    """'10 90 700' / '₹ 10,90,700' / 1090700.0 -> 1090700. Returns None when there is no number."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(round(value))
    digits = "".join(_DIGITS.findall(str(value).split(".")[0]))
    return int(digits) if digits else None


def norm(s: str) -> str:
    """Loose key for matching names across endpoints: lower-case alphanumerics only."""
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


TRANSMISSION_MAP = {
    "MT": "Manual", "MANUAL": "Manual",
    "AT": "Automatic", "AUTOMATIC": "Automatic", "TC": "Automatic", "TCA": "Automatic",
    "AMT": "AMT", "AGS": "AMT", "IVT": "CVT", "CVT": "CVT", "ECVT": "CVT", "E-CVT": "CVT",
    "DCT": "DCT", "DCA": "DCT", "IMT": "iMT",
}


def transmission(code: str | None) -> str:
    if not code:
        return ""
    return TRANSMISSION_MAP.get(code.strip().upper().replace(" ", ""), code.strip())
