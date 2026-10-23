"""
Car-loan interest rates, read from each bank's OWN published rate page (no aggregators). A bank whose page can't be
read reliably is simply left out; nothing is assumed. Run daily (scripts/daily_refresh.cmd) or: python -m onroad.loan_rates

Each row: bank, product, ev_only, min_pct, max_pct, source_url, fetched_at.
"""
from __future__ import annotations

import html
import re
from contextlib import closing

import httpx

from . import db
from .sources.base import USER_AGENT, now

H = {"User-Agent": USER_AGENT, "Accept-Language": "en-IN"}


def _text(url: str) -> tuple[str, str]:
    r = httpx.get(url, headers=H, timeout=30, follow_redirects=True)
    r.raise_for_status()
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " | ", r.text)))
    return re.sub(r"(\| )+", "| ", t), str(r.url)


def _range(pattern: str, text: str) -> tuple[float, float] | None:
    m = re.search(pattern, text, re.I)
    return (float(m.group(1)), float(m.group(2))) if m else None


def sbi() -> list[dict]:
    t, url = _text("https://sbi.co.in/web/interest-rates/interest-rates/loan-schemes-interest-rates/auto-loans")
    out = []
    for product, pat, ev in [
        ("SBI Car Loan", r"Assured Car Loan \|? ?From (\d+\.\d+)% to (\d+\.\d+)%", False),
        ("SBI Green Car Loan (electric cars)", r"Green Car Loan \(For Electric Cars\) \|? ?From (\d+\.\d+)% to (\d+\.\d+)%", True),
    ]:
        r = _range(pat, t)
        if r:
            out.append({"bank": "State Bank of India", "product": product, "ev_only": ev, "min_pct": r[0], "max_pct": r[1], "source_url": url})
    return out


def axis() -> list[dict]:
    t, url = _text("https://www.axisbank.com/retail/loans/car-loan/interest-rates-charges")
    r = _range(r"Axis Bank charges [^.]*?rates? ranging from (\d+\.\d+)% to (\d+\.\d+)%", t)
    return [{"bank": "Axis Bank", "product": "Axis Bank Car Loan", "ev_only": False, "min_pct": r[0], "max_pct": r[1], "source_url": url}] if r else []


def _starting(bank: str, product: str, url: str, pattern: str) -> list[dict]:
    """Banks that publish only a 'starting at x%' rate: min only, max unknown."""
    t, final = _text(url)
    m = re.search(pattern, t, re.I)
    return [{"bank": bank, "product": product, "ev_only": False, "min_pct": float(m.group(1)), "max_pct": None, "source_url": final}] if m else []


def hdfc() -> list[dict]:
    return _starting("HDFC Bank", "HDFC Bank Xpress Car Loan", "https://www.hdfcbank.com/personal/borrow/popular-loans/new-car-loan",
                     r"Car Loan Interest rate starting[ |]*@[ |]*(\d+\.\d+)[ |]*%")


def icici() -> list[dict]:
    return _starting("ICICI Bank", "ICICI Bank Car Loan", "https://www.icicibank.com/personal-banking/loans/car-loan",
                     r"interest rates starting at (\d+\.\d+)%")


def idfc() -> list[dict]:
    return _starting("IDFC FIRST Bank", "IDFC FIRST Bank Car Loan", "https://www.idfcfirstbank.com/personal-banking/loans/car-loan",
                     r"Interest Rate from (\d+\.\d+)%")


def bob() -> list[dict]:
    return _starting("Bank of Baroda", "Baroda Car Loan", "https://bankofbaroda.bank.in/personal-banking/loans/vehicle-loan/baroda-car-loan",
                     r"Car Loan from Bank of Baroda starting @ ?(\d+\.\d+)%")


BANKS = [sbi, axis, hdfc, icici, idfc, bob]


def refresh() -> dict:
    db.init()
    got, failed = [], []
    for fn in BANKS:
        try:
            rows = fn()
            (got.extend(rows) if rows else failed.append(f"{fn.__name__}: rate not found on page"))
        except Exception as e:                       # a bank's site being down must not stop the others
            failed.append(f"{fn.__name__}: {type(e).__name__}")
    with closing(db.connect()) as conn, conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS loan_rates (bank TEXT, product TEXT, ev_only INTEGER, min_pct REAL, max_pct REAL,
                        source_url TEXT, fetched_at TEXT, PRIMARY KEY (bank, product))""")
        if got:                                              # today's read replaces yesterday's set
            conn.execute("DELETE FROM loan_rates")
        for r in got:
            conn.execute("INSERT OR REPLACE INTO loan_rates VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (r["bank"], r["product"], int(r["ev_only"]), r["min_pct"], r["max_pct"], r["source_url"], now()))
    return {"rates": len(got), "failed": failed}


if __name__ == "__main__":
    print(refresh())
