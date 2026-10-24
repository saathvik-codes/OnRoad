"""
Keeps data/research/crash_tests.json current with Bharat NCAP's own site (bncap.in, the government's programme).

  * The vehicle list comes from bncap.in's sitemap (wp-sitemap-posts-vehicle-1.xml); robots.txt allows it.
  * Each vehicle page gives the tested variant, the adult (AOP, out of 32) and child (COP, out of 49) scores, the month
    the rating applies from, its applicability ("Select Variants only"), the official fact sheet PDF and the test video.
  * Stars come from Bharat NCAP's published score bands (adult 27/22/16/10/4, child 41/35/27/18/9 for 5..1 stars).
    The page draws stars as identical icons, so they can't be read directly; these bands reproduce every one of the
    38 Bharat NCAP ratings already on file, which were taken from the official fact sheets.
  * New vehicles are added, re-tests update their record; Global NCAP records are never touched.

    python -m onroad.crash_tests_sync
"""
from __future__ import annotations

import json
import re
import shutil
import time

import httpx

from . import db

FILE = db.ROOT / "data" / "research" / "crash_tests.json"
SITEMAP = "https://www.bncap.in/wp-sitemap-posts-vehicle-1.xml"
UA = {"User-Agent": "Mozilla/5.0 (compatible; OnRoadBot/0.1; +https://onroad-uu9c.onrender.com)"}
ADULT = [(27, 5), (22, 4), (16, 3), (10, 2), (4, 1)]
CHILD = [(41, 5), (35, 4), (27, 3), (18, 2), (9, 1)]
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august", "september",
                                       "october", "november", "december"], 1)}
# brand as bncap.in writes it -> brand as OnRoad names it
BRANDS = {"maruti": "Maruti Suzuki", "tata": "Tata Motors", "mahindra": "Mahindra", "hyundai": "Hyundai", "kia": "Kia",
          "toyota": "Toyota", "honda": "Honda", "skoda": "Skoda", "volkswagen": "Volkswagen", "citroen": "Citroën",
          "renault": "Renault", "nissan": "Nissan", "mg": "MG Motor", "jsw mg": "MG Motor", "byd": "BYD", "force": "Force Motors",
          "isuzu": "Isuzu", "jeep": "Jeep", "vinfast": "VinFast"}


def _stars(score: float | None, bands) -> int | None:
    if score is None:
        return None
    return next((n for th, n in bands if score >= th), 0)


def _model_name(raw: str) -> str:
    """'BREZZA' -> 'Brezza', 'XUV 7XO' stays, 'PUNCH EV' -> 'Punch EV'."""
    keep = {"EV", "XUV", "XEV", "BE", "MG", "SUV", "CNG", "N", "X"}
    return " ".join(w if (w in keep or any(c.isdigit() for c in w)) else w.title() for w in raw.split())


def parse(url: str, html: str) -> dict | None:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.get_text() if soup.title else "").replace("– bncap", "").strip(" –-")
    parts = [p.strip() for p in re.split(r"\s+[–-]\s+", title) if p.strip()]
    if len(parts) == 1:                                   # older pages: "TATA NEXON" without a separator
        words = parts[0].split()
        n = 2 if len(words) > 2 and " ".join(words[:2]).lower() in BRANDS else 1
        parts = [" ".join(words[:n]), " ".join(words[n:])]
    if len(parts) < 2 or not parts[1]:
        return None
    text = re.sub(r"\s+", " ", soup.get_text(" "))
    scores = re.findall(r"(\d{1,2}\.\d{2})\s*/\s*(32\.00|49\.00)", text)
    adult = next((float(a) for a, mx in scores if mx == "32.00"), None)
    child = next((float(a) for a, mx in scores if mx == "49.00"), None)
    if adult is None:
        return None
    month = re.search(r"([A-Z][a-z]+)\s+(20\d{2})\s*-\s*Onwards", text)
    published = f"{month.group(2)}-{MONTHS.get(month.group(1).lower(), 0):02d}" if month and month.group(1).lower() in MONTHS else None
    variant = re.search(r"Tested Vehicle Model & Variant\s+(.+?)\s+Body Type", text)
    pdf = next((a["href"] for a in soup.find_all("a", href=True) if a["href"].lower().endswith(".pdf") and "fact" in a["href"].lower()), None)
    yt = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube-nocookie\.com/embed/)([A-Za-z0-9_-]{11})", html)
    brand_raw = parts[0].lower()
    return {
        "brand": BRANDS.get(brand_raw, parts[0].title()),
        "model": _model_name(parts[1]),
        "variant_tested": variant.group(1).strip() if variant else None,
        "agency": "Bharat NCAP", "protocol": "Bharat NCAP 2023", "test_date": None, "rating_published": published,
        "adult_stars": _stars(adult, ADULT), "child_stars": _stars(child, CHILD),
        "adult_score": adult, "adult_max": 32.0, "child_score": child, "child_max": 49.0 if child is not None else None,
        "airbags_tested": None,
        "notes": "Select variants only" if "Select Variants only" in text else None,
        "source_url": url, "fact_sheet_url": pdf,
        "video_url": f"https://www.youtube-nocookie.com/embed/{yt.group(1)}" if yt else None,
    }


def sync() -> dict:
    records = json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else []
    by_url = {r.get("source_url"): r for r in records if r.get("agency") == "Bharat NCAP"}
    added, updated, failed = [], [], []
    with httpx.Client(headers=UA, timeout=30, follow_redirects=True) as c:
        urls = re.findall(r"<loc>(https://www\.bncap\.in/vehicle/[^<]+)</loc>", c.get(SITEMAP).text)
        for u in urls:
            time.sleep(1.0)                                   # polite: one page a second
            try:
                rec = parse(u, c.get(u).text)
            except Exception:
                rec = None
            if not rec:
                failed.append(u); continue
            old = by_url.get(u)
            if old is None:
                records.append(rec); added.append(f"{rec['brand']} {rec['model']}")
            else:
                changed = {k: v for k, v in rec.items() if v is not None and old.get(k) != v
                           and k in ("adult_score", "child_score", "adult_stars", "child_stars", "rating_published", "fact_sheet_url",
                                     "video_url", "variant_tested", "notes")}
                if changed:
                    old.update(changed); updated.append(f"{old['brand']} {old['model']}")
    if added or updated:
        shutil.copyfile(FILE, FILE.with_suffix(".backup.json")) if FILE.exists() else None
        FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"vehicles_on_site": len(urls), "added": added, "updated": updated, "unreadable": failed}


if __name__ == "__main__":
    print(json.dumps(sync(), ensure_ascii=False, indent=1))
