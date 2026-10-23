"""Shared helpers for brand offers() parsers: rupee amounts, offer kinds, dates. Not a brand adapter (no ADAPTER).
Pure text helpers - they never invent numbers or dates; they only read what the brand's own text says."""

from __future__ import annotations

import datetime as dt
import re

MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}

_AMT = re.compile(r"(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d+)?)\s*(lakh|lac|l\b|k\b|crore|cr\b)?|([\d,]+(?:\.\d+)?)\s*(lakh|lac|k)\b", re.I)


def amount(text: str | None) -> int | None:
    """First rupee figure in `text` ('INR 1,50,000', '₹ 1.5 lakh', 'Rs. 25K', '25K') as int rupees, else None."""
    if not text:
        return None
    m = _AMT.search(text)
    if not m:
        return None
    num, unit = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
    try:
        v = float(num.replace(",", ""))
    except ValueError:
        return None
    u = (unit or "").lower()
    if u in ("lakh", "lac", "l"):
        v *= 100000
    elif u == "k":
        v *= 1000
    elif u in ("crore", "cr"):
        v *= 10000000
    return int(round(v)) if v else None


def inr(n: int | None) -> str:
    """12345678 -> '₹1,23,45,678' (Indian grouping)."""
    if n is None:
        return ""
    s = str(int(n))
    head, tail = s[:-3], s[-3:]
    while len(head) > 2:
        tail = head[-2:] + "," + tail
        head = head[:-2]
    return "₹" + (head + "," + tail if head else tail)


_KINDS = [("scrappage", r"scrap|relive|vehicle scrapping"),
          ("exchange", r"exchange|trade[- ]?in|upgrade bonus"),
          ("corporate", r"corporate|institutional|psu|government employee"),
          ("loyalty", r"loyalty|existing customer|repeat"),
          ("finance", r"finance|rate of interest|\broi\b|emi|interest rate|loan|lease"),
          ("insurance", r"insurance"),
          ("warranty", r"warranty|extended guarantee"),
          ("accessories", r"accessor"),
          ("cash", r"cash|consumer offer|discount|price benefit")]


def kind_of(text: str) -> str:
    t = text.lower()
    for k, rx in _KINDS:
        if re.search(rx, t):
            return k
    return "other"


def day_month_year(d: str, mon: str, yr: str | None) -> dt.date | None:
    m = MONTHS.get(mon.lower()[:3])
    if not m or not yr:
        return None
    y = int(yr)
    y = y + 2000 if y < 100 else y
    try:
        return dt.date(y, m, int(d))
    except ValueError:
        return None


def date_text(s: str) -> str | None:
    """'31st October 2026' / '31 Oct'26' / '31-10-2026' / '2026-10-31' / '31/10/2026' -> ISO, else None."""
    m = re.search(r"(\d{1,2})(?:st|nd|rd|th)?[\s\-]*([A-Za-z]{3,9})[\s,'’\-]*(\d{2,4})", s)
    if m:
        d = day_month_year(m.group(1), m.group(2), m.group(3))
        if d:
            return d.isoformat()
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return m.group(0)
    m = re.search(r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})", s)
    if m:
        try:
            return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
        except ValueError:
            return None
    return None


def expired(valid_until: str | None, today: dt.date | None = None) -> bool:
    return bool(valid_until) and valid_until < (today or dt.date.today()).isoformat()
