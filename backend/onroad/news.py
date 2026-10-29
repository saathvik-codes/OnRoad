"""
Automotive news from Indian publishers' public RSS feeds (each allows feed access in robots.txt; checked 2026-10-29).
We keep what a feed reader shows, the headline, the feed's own short summary and image, the publisher and the link,
and send readers to the publisher for the full story. Stories are tagged with the car they are about (matched against
our catalogue) and a topic, and near-duplicates of one story across publishers are collapsed.

    python -m onroad.news          # fetch now
"""
from __future__ import annotations

import datetime as dt
import email.utils
import hashlib
import html
import logging
import re
import threading
import time
import xml.etree.ElementTree as ET
from contextlib import closing

import httpx

from . import db

log = logging.getLogger("onroad.news")
UA = {"User-Agent": "Mozilla/5.0 (compatible; OnRoadBot/1.0; +https://onroad-frontend.onrender.com)"}
FEEDS = [
    ("Autocar India", "https://www.autocarindia.com/rss/all"),
    ("ET Auto", "https://auto.economictimes.indiatimes.com/rss/passenger-vehicle"),
    ("ET Auto", "https://auto.economictimes.indiatimes.com/rss/topstories"),
    ("Rushlane", "https://www.rushlane.com/feed"),
    ("MotorBeam", "https://www.motorbeam.com/feed/"),
    ("GaadiWaadi", "https://www.gaadiwaadi.com/feed"),
    ("autoX", "https://www.autox.com/feed/"),
    ("DriveSpark", "https://www.drivespark.com/rss/drivespark-fb.xml"),
]
TOPICS = [   # first match wins: government and safety news before generic "introduces"/"launch" wording
    ("policy", r"\bgst\b|\broad tax|\bpolicy\b|\bgovt\b|\bgovernment\b|\bministry|\bmorth\b|\bregulation|\bnorms?\b|\bban\b|\bfastag\b|\btoll"),
    ("safety", r"\bncap\b|\bcrash test|\bstar (safety )?rating|\bairbags?\b|\brecall"),
    ("price", r"\bprice (hike|cut|increase|revision)|\bprices? (up|down|hiked|cut|increase|reduced)|\bcosts? more|\bcheaper\b|\bdiscount|\bdeals?\b|\boffers?\b"),
    ("spied", r"\bspied\b|\bspotted\b|\btesting\b|\bspy\b|\bteased?\b|\bteaser"),
    ("launch", r"\blaunch(es|ed)?\b|\bdebuts?\b|\bunveil|\brevealed?\b|\bintroduc|\bbookings? open"),
    ("sales", r"\bsales\b|\bsold\b|\bunits\b|\bmarket share|\bmilestone|\bproduction"),
    ("ev", r"\belectric\b|\bev\b|\bevs\b|\bbattery\b|\bcharging"),
]
NS = {"media": "http://search.yahoo.com/mrss/", "content": "http://purl.org/rss/1.0/modules/content/"}
KEEP_DAYS = 30


def _text(s: str | None, n: int = 260) -> str:
    s = re.sub(r"<[^>]+>", " ", html.unescape(s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s*(The post .* appeared first on .*|Read more.*|Continue reading.*)$", "", s)
    return s if len(s) <= n else s[: s.rfind(" ", 0, n)].rstrip(",;:") + "…"


def _image(item: ET.Element) -> str | None:
    for path in ("media:content", "media:thumbnail"):
        for e in item.findall(path, NS):
            u = e.get("url")
            if u and not re.search(r"\.(mp4|webm)(\?|$)", u):
                return u
    enc = item.find("enclosure")
    if enc is not None and (enc.get("type") or "").startswith("image"):
        return enc.get("url")
    for tag in ("content:encoded", "description"):
        e = item.find(tag, NS) if ":" in tag else item.find(tag)
        m = re.search(r'<img[^>]+src="([^"]+)"', html.unescape(e.text or "") if e is not None else "")
        if m:
            return m.group(1)
    return None


def _when(s: str | None) -> str:
    try:
        return email.utils.parsedate_to_datetime(s).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _models(conn) -> list[tuple[re.Pattern, str, str]]:
    """(pattern, model_id, brand_slug), longest names first so "Grand Vitara" wins over "Vitara"."""
    rows = conn.execute("""SELECT m.id, m.name, m.brand_slug, b.name FROM models m JOIN brands b ON b.slug = m.brand_slug
                           WHERE m.active = 1""").fetchall()
    out = []
    for mid, name, bslug, bname in rows:
        n = re.sub(r"\s+", " ", name).strip()
        if len(n) < 3 or n.lower() in ("new", "ev", "plus"):
            continue
        brand = bname.split()[0]
        out.append((re.compile(rf"\b{re.escape(brand)}\s+{re.escape(n)}\b|\b{re.escape(n)}\b(?=.*\b{re.escape(brand)}\b)|"
                               rf"(?<=\b{re.escape(brand)}\b).*\b{re.escape(n)}\b", re.I), mid, bslug, len(n)))
    out.sort(key=lambda x: -x[3])
    return [(p, m, b) for p, m, b, _ in out]


def _key(title: str) -> str:
    words = [w for w in re.findall(r"[a-z0-9]+", title.lower()) if len(w) > 3]
    return " ".join(sorted(set(words))[:8])


def fetch() -> dict:
    db.init()
    n_new, n_seen = 0, 0
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with closing(db.connect()) as conn, httpx.Client(headers=UA, timeout=25, follow_redirects=True) as h:
        conn.execute("""CREATE TABLE IF NOT EXISTS news (id TEXT PRIMARY KEY, title TEXT, summary TEXT, url TEXT, image_url TEXT,
                        source TEXT, published TEXT, model_id TEXT, brand_slug TEXT, topic TEXT, dedup TEXT, fetched_at TEXT)""")
        models = _models(conn)
        for source, feed in FEEDS:
            try:
                root = ET.fromstring(h.get(feed).content)
            except Exception as e:
                log.warning("news feed %s failed: %s", feed, e)
                continue
            for item in root.iter("item"):
                title = _text(item.findtext("title"), 200)
                url = (item.findtext("link") or "").strip()
                if not title or not url.startswith("http"):
                    continue
                nid = hashlib.sha1(url.encode()).hexdigest()[:16]
                if conn.execute("SELECT 1 FROM news WHERE id = ?", (nid,)).fetchone():
                    n_seen += 1
                    continue
                blob = f"{title} {item.findtext('category') or ''}"
                model_id = brand = None
                for pat, mid, bslug in models:
                    if pat.search(title):
                        model_id, brand = mid, bslug
                        break
                topic = next((t for t, rx in TOPICS if re.search(rx, blob, re.I)), "industry")
                dedup = _key(title)
                if conn.execute("SELECT 1 FROM news WHERE dedup = ? AND substr(published, 1, 10) >= date('now', '-3 day')",
                                (dedup,)).fetchone():
                    continue
                # the same story from another publisher: same car, same topic, within two days
                if model_id and conn.execute("""SELECT 1 FROM news WHERE model_id = ? AND topic = ?
                                                AND published >= datetime('now', '-2 day')""", (model_id, topic)).fetchone():
                    continue
                desc = item.findtext("description") or item.findtext("content:encoded", namespaces=NS)
                conn.execute("INSERT OR IGNORE INTO news VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                             (nid, title, _text(desc), url, _image(item), source, _when(item.findtext("pubDate")),
                              model_id, brand, topic, dedup, now))
                n_new += 1
        conn.execute("DELETE FROM news WHERE published < ?", ((dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d"),))
        conn.commit()
    return {"new": n_new, "already_had": n_seen}


def latest(limit: int = 40, topic: str | None = None, model_id: str | None = None, brand: str | None = None) -> list[dict]:
    where, params = ["1=1"], []
    if topic:
        where.append("topic = ?"); params.append(topic)
    if model_id:
        where.append("model_id = ?"); params.append(model_id)
    if brand:
        where.append("brand_slug = ?"); params.append(brand)
    try:
        with closing(db.connect()) as conn:
            rows = conn.execute(f"""SELECT n.id, n.title, n.summary, n.url, n.image_url, n.source, n.published, n.model_id,
                                           n.brand_slug, n.topic, m.name AS model_name, m.image_url AS model_image
                                    FROM news n LEFT JOIN models m ON m.id = n.model_id
                                    WHERE {' AND '.join(where)} ORDER BY n.published DESC LIMIT ?""", (*params, limit)).fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []


def start(every_minutes: float = 60, on_new=None) -> None:
    def loop():
        time.sleep(45)
        while True:
            try:
                res = fetch()
                log.info("news: %s", res)
                if res["new"] and on_new:
                    on_new()
            except Exception as e:
                log.warning("news fetch failed: %s", e)
            time.sleep(every_minutes * 60)
    threading.Thread(target=loop, name="onroad-news", daemon=True).start()


if __name__ == "__main__":
    print(fetch())
