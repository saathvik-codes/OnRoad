"""
Monthly sales ranks (data/research/popularity.json) from each brand's model-wise wholesale numbers.

Model-level dispatch numbers are published by manufacturers to SIAM and reported per brand each month by Rushlane
("<brand>-sales-breakup-<mon>-<year>" posts). Their tables are images, but every model's figure is written in the text:
"Splendor range registered 3,53,842 units, growing 13.52% over 3,11,698 units a year earlier." The first figure in a
sentence that starts with the model's name is that month's number.

Safety checks before anything is written (otherwise the model keeps its old numbers and the run reports why):
  * the figure must be below the brand's total for the month stated in the same post;
  * if last month is known, the new figure must be within 4x up or down of it.
Ranks are then recomputed over the latest six months, separately for cars and two-wheelers.

    python -m onroad.popularity_sync            # update
    python -m onroad.popularity_sync --check    # parse only, compare with months already on file
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import time

import httpx

from . import db

FILE = db.ROOT / "data" / "research" / "popularity.json"
SITEMAP_INDEX = "https://www.rushlane.com/sitemap_index.xml"
UA = {"User-Agent": "Mozilla/5.0 (compatible; OnRoadBot/0.1)"}
MON = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7, "aug": 8,
       "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12}
# url slug -> brand names as popularity.json writes them (car brand first where a slug is shared)
SLUG_BRANDS = {"maruti": ["Maruti Suzuki"], "tata": ["Tata Motors"], "mahindra": ["Mahindra"], "hyundai": ["Hyundai"], "kia": ["Kia"],
               "toyota": ["Toyota"], "honda": ["Honda 2Wheelers", "Honda"], "honda-cars": ["Honda"], "skoda-vw": ["Skoda", "Volkswagen"],
               "renault": ["Renault"], "nissan": ["Nissan"], "hero": ["Hero MotoCorp"], "tvs": ["TVS Motor Company"],
               "bajaj": ["Bajaj Auto"], "royal-enfield": ["Royal Enfield"], "yamaha": ["Yamaha"], "suzuki": ["Suzuki Two Wheelers"],
               "ather": ["Ather Energy"], "mg": ["MG Motor"], "jsw-mg": ["MG Motor"]}


# sentences about a quarter / half-year / year-to-date carry multi-month totals, never a single month's figure
PERIOD_WORDS = re.compile(r"\b(?:Q[1-4]|H[12]|quarter|quarterly|half|first six months|YTD|year[- ]to[- ]date|fiscal|FY ?\d+|cumulative|three months)\b", re.I)


def _num(s: str) -> int:
    return int(s.replace(",", ""))


def breakup_posts(client: httpx.Client) -> list[tuple[str, str, str]]:
    """(url, slug, 'YYYY-MM') for brand sales-breakup posts in the newest post sitemaps."""
    maps = re.findall(r"https://www\.rushlane\.com/post-sitemap\d*\.xml", client.get(SITEMAP_INDEX).text)
    out = []
    for sm in maps[-2:]:
        time.sleep(1)
        for u in re.findall(r"<loc>([^<]+)</loc>", client.get(sm).text):
            m = re.search(r"rushlane\.com/([a-z\-]+?)-sales-breakup-([a-z]+)-(20\d{2})", u)
            if m and m.group(2) in MON and m.group(1) in SLUG_BRANDS:
                out.append((u, m.group(1), f"{m.group(3)}-{MON[m.group(2)]:02d}"))
    return out


def parse_post(html: str, names: list[str]) -> tuple[int | None, dict[str, int]]:
    """Brand total for the month and {model name: units} for models named at the start of a sentence."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    body = " ".join(p.get_text(" ", strip=True) for p in (soup.find("article") or soup).find_all("p"))
    body = re.sub(r"\s+", " ", body)
    total = re.search(r"(?:domestic )?sales of ([\d,]{5,}) units", body)
    sentences = re.split(r"(?<=[.;])\s+", body)
    found: dict[str, int] = {}
    for name in sorted(names, key=len, reverse=True):              # longest first: "Xoom 160" before "Xoom"
        # "Shine" must not match "Shine 100 …" (a different model); a name with its own number is fine ("Destini 125")
        tail = r"(?![\w-])" + ("" if re.search(r"\d", name) else r"(?!\s+\d)")
        rx = re.compile(r"^(?:The\s+)?" + re.escape(name) + r"\b" + tail, re.I)
        for s in sentences:
            if rx.search(s) and not re.match(r"^(?:Together|Combined)", s) and not PERIOD_WORDS.search(s):
                m = re.search(r"([\d,]{3,}) units", s)
                if m and name not in found:
                    found[name] = _num(m.group(1))
                break
    return (_num(total.group(1)) if total else None), found


def run(check: bool = False) -> dict:
    data = json.loads(FILE.read_text(encoding="utf-8"))
    models = data["models"]
    by_brand: dict[str, list[dict]] = {}
    for m in models:
        by_brand.setdefault(m["brand"], []).append(m)
    applied, rejected, compared = [], [], []
    with httpx.Client(headers=UA, timeout=30, follow_redirects=True) as c:
        for url, slug, month in breakup_posts(c):
            brands = [b for b in SLUG_BRANDS[slug] if b in by_brand]
            if not brands:
                continue
            time.sleep(1)
            entries = [m for b in brands for m in by_brand[b]]
            total, found = parse_post(c.get(url).text, [m["model"] for m in entries])
            for m in entries:
                n = found.get(m["model"])
                if n is None:
                    continue
                old = m["monthly_units"].get(month)
                if check:
                    if old is not None:
                        compared.append((m["brand"], m["model"], month, old, n))
                    continue
                if old is not None:
                    continue                                   # months on file were checked by hand: never overwritten
                prev_month = f"{int(month[:4]) - (month[5:] == '01')}-{(int(month[5:]) - 2) % 12 + 1:02d}"
                prev = m["monthly_units"].get(prev_month)
                why = ("above the brand total" if total and n > total else
                       "more than 2.5x off last month" if prev and not (prev / 2.5 <= n <= prev * 2.5) else None)
                if why:
                    rejected.append(f"{m['brand']} {m['model']} {month}: {n:,} ({why})"); continue
                if old != n:
                    m["monthly_units"][month] = n
                    m.setdefault("sources", []).append(url) if url not in m.get("sources", []) else None
                    applied.append(f"{m['brand']} {m['model']} {month}: {n:,}")
    if check:
        exact = sum(1 for *_, a, b in compared if a == b)
        return {"compared": len(compared), "exact_match": exact, "differences": [x for x in compared if x[3] != x[4]]}
    if applied:
        months = sorted({mo for m in models for mo in m["monthly_units"]})[-6:]
        for m in models:
            m["six_month_units"] = sum(m["monthly_units"].get(mo, 0) for mo in months)
            m["complete_6_months"] = all(mo in m["monthly_units"] for mo in months)
            m["months_missing"] = [mo for mo in months if mo not in m["monthly_units"]]
        for vt in ("car", "bike"):
            group = sorted((m for m in models if m.get("vehicle_type", "car") == vt), key=lambda m: -m["six_month_units"])
            for i, m in enumerate(group, 1):
                m["rank"] = i
        data["period"] = f"{months[0]} to {months[-1]} (latest six months on file)"
        data["as_of"] = time.strftime("%Y-%m-%d")
        shutil.copyfile(FILE, FILE.with_suffix(".backup.json"))
        FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"applied": applied, "rejected": rejected}


if __name__ == "__main__":
    print(json.dumps(run(check="--check" in sys.argv), ensure_ascii=False, indent=1))
