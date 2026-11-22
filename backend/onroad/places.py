"""
Google ratings for showrooms (Places API (New)). Needs GOOGLE_PLACES_KEY; without it everything here is a no-op.

  * match: each dealer from a brand's own locator is looked up once with Text Search ("<name> <address>", biased to
    1 km around the dealer's coordinates); accepted only if the result is within 1 km and its name shares a word.
  * rating + userRatingCount are refreshed weekly in batches (Google's terms: keep place_id, refresh other content,
    never older than 30 days). Review text is fetched live per request (/api/dealer-reviews), never stored.
    python -m onroad.places [max_dealers]
"""
from __future__ import annotations

import datetime as dt
import math
import os
import re
import sys
from contextlib import closing

import httpx

from . import db

BASE = "https://places.googleapis.com/v1"


def key() -> str | None:
    return os.getenv("GOOGLE_PLACES_KEY")


def _km(a1, o1, a2, o2):
    p = math.pi / 180
    h = 0.5 - math.cos((a2 - a1) * p) / 2 + math.cos(a1 * p) * math.cos(a2 * p) * (1 - math.cos((o2 - o1) * p)) / 2
    return 12742 * math.asin(math.sqrt(h))


def _init(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS dealer_places (dealer_id TEXT PRIMARY KEY, place_id TEXT, rating REAL,
                    rating_count INTEGER, maps_uri TEXT, fetched_at TEXT)""")
    for col in ("photo TEXT", "photo_by TEXT", "g_lat REAL", "g_lng REAL", "g_phone TEXT", "g_address TEXT", "status TEXT"):                # Places photo resource name + its author (credit shown)
        try:
            conn.execute(f"ALTER TABLE dealer_places ADD COLUMN {col}")
        except Exception:
            pass


def match_and_rate(limit: int = 200) -> dict:
    """Match unmatched dealers, then refresh the stalest ratings (older than 7 days), up to `limit` API calls."""
    if not key():
        return {"skipped": "GOOGLE_PLACES_KEY not set"}
    now = dt.datetime.now(dt.timezone.utc)
    with closing(db.connect()) as conn, conn:
        _init(conn)
        todo = conn.execute("""SELECT d.id, d.name, d.address, d.lat, d.lng, p.place_id FROM dealers d
                               LEFT JOIN dealer_places p ON p.dealer_id = d.id
                               WHERE d.active = 1 AND d.lat IS NOT NULL
                                 AND (p.dealer_id IS NULL OR p.fetched_at < ?)
                               ORDER BY p.fetched_at IS NOT NULL, p.fetched_at LIMIT ?""",
                            ((now - dt.timedelta(days=7)).isoformat(), limit)).fetchall()
    done = matched = 0
    hdr = {"X-Goog-Api-Key": key(), "Content-Type": "application/json"}
    with httpx.Client(timeout=20) as c:
        for did, name, addr, lat, lng, place_id in todo:
            try:
                if place_id:
                    r = c.get(f"{BASE}/places/{place_id}", headers={**hdr, "X-Goog-FieldMask": "id,rating,userRatingCount,googleMapsUri,location,nationalPhoneNumber,formattedAddress,businessStatus"}).json()
                    if "error" in r:                      # quota / key problem: not an answer, try again next run
                        if r["error"].get("code") == 429:
                            break
                        continue
                    place = r if r.get("id") else None
                else:
                    body = {"textQuery": f"{name} {addr}"[:200], "maxResultCount": 3,
                            "locationBias": {"circle": {"center": {"latitude": lat, "longitude": lng}, "radius": 1000.0}}}
                    res = c.post(f"{BASE}/places:searchText", json=body, headers={**hdr,
                                 "X-Goog-FieldMask": "places.id,places.displayName,places.location,places.rating,places.userRatingCount,places.googleMapsUri,places.nationalPhoneNumber,places.formattedAddress,places.businessStatus"}).json()
                    if "error" in res:                    # daily quota used up: stop; nothing is recorded as "no match"
                        if res["error"].get("code") == 429:
                            break
                        continue
                    words = {w for w in re.findall(r"[a-z]{4,}", name.lower())}
                    place = next((p for p in res.get("places", [])
                                  if _km(lat, lng, p["location"]["latitude"], p["location"]["longitude"]) <= 1.0
                                  and words & set(re.findall(r"[a-z]{4,}", p.get("displayName", {}).get("text", "").lower()))), None)
                done += 1
            except Exception:
                continue
            with closing(db.connect()) as conn, conn:
                ph = ((place or {}).get("photos") or [{}])[0]
                by = ((ph.get("authorAttributions") or [{}])[0]).get("displayName")
                loc = (place or {}).get("location") or {}
                # Google's pin, phone, address and open/closed status, refreshed weekly (kept under 30 days per its terms)
                conn.execute("""INSERT OR REPLACE INTO dealer_places (dealer_id, place_id, rating, rating_count, maps_uri, fetched_at, photo, photo_by,
                                                                      g_lat, g_lng, g_phone, g_address, status)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                             (did, (place or {}).get("id"), (place or {}).get("rating"), (place or {}).get("userRatingCount"),
                              (place or {}).get("googleMapsUri"), now.isoformat(), ph.get("name"), by,
                              loc.get("latitude"), loc.get("longitude"), (place or {}).get("nationalPhoneNumber"),
                              (place or {}).get("formattedAddress"), (place or {}).get("businessStatus")))
            matched += bool(place)
    return {"calls": done, "matched": matched}


def photo_uri(dealer_id: str, width: int = 800) -> str | None:
    """A short-lived Google URL for the showroom's first Places photo (fetched live, never stored)."""
    if not key():
        return None
    with closing(db.connect()) as conn:
        _init(conn)
        row = conn.execute("SELECT photo FROM dealer_places WHERE dealer_id = ?", (dealer_id,)).fetchone()
    if not row or not row[0]:
        return None
    r = httpx.get(f"{BASE}/{row[0]}/media", params={"maxWidthPx": width, "skipHttpRedirect": "true", "key": key()}, timeout=20)
    return r.json().get("photoUri") if r.status_code == 200 else None


def reviews(dealer_id: str) -> dict:
    """Live review text for one showroom (not stored)."""
    if not key():
        return {"reviews": [], "note": "Ratings are not enabled on this server."}
    with closing(db.connect()) as conn:
        _init(conn)
        row = conn.execute("SELECT place_id FROM dealer_places WHERE dealer_id = ?", (dealer_id,)).fetchone()
    if not row or not row[0]:
        return {"reviews": [], "note": "This showroom isn't matched to a Google listing yet."}
    r = httpx.get(f"{BASE}/places/{row[0]}", timeout=20, headers={"X-Goog-Api-Key": key(),
                  "X-Goog-FieldMask": "rating,userRatingCount,googleMapsUri,reviews"}).json()
    return {"rating": r.get("rating"), "count": r.get("userRatingCount"), "maps_uri": r.get("googleMapsUri"),
            "reviews": [{"author": (v.get("authorAttribution") or {}).get("displayName"), "rating": v.get("rating"),
                         "when": v.get("relativePublishTimeDescription"), "text": (v.get("text") or {}).get("text", "")}
                        for v in r.get("reviews", [])[:5]], "attribution": "Google"}


if __name__ == "__main__":
    print(match_and_rate(int(sys.argv[1]) if len(sys.argv) > 1 else 200))


def street_photo(lat: float, lng: float, width: int = 800) -> tuple[bytes, str, str] | None:
    """(image bytes, content type, credit) of the street in front of a showroom, when no Places photo exists:
    Google Street View (needs the Street View Static API enabled for GOOGLE_PLACES_KEY; the metadata check is free and
    tells us whether imagery exists before a billed image call), else Mapillary (MAPILLARY_TOKEN, free, CC BY-SA)."""
    w, h = max(320, min(width, 640)), max(200, min(width * 9 // 16, 400))
    if key():
        try:
            meta = httpx.get("https://maps.googleapis.com/maps/api/streetview/metadata",
                             params={"location": f"{lat},{lng}", "radius": 60, "source": "outdoor", "key": key()}, timeout=15).json()
            if meta.get("status") == "OK":
                r = httpx.get("https://maps.googleapis.com/maps/api/streetview", timeout=20, params={
                    "size": f"{w}x{h}", "location": f"{lat},{lng}", "radius": 60, "source": "outdoor", "fov": 80, "key": key()})
                if r.status_code == 200 and r.headers.get("content-type", "").startswith("image/"):
                    return r.content, r.headers["content-type"], f"Street View · {meta.get('copyright', 'Google')}".replace("© ", "")
        except Exception:
            pass
    tok = os.getenv("MAPILLARY_TOKEN")
    if tok:
        try:
            d = 0.0006                                         # about 60 m around the showroom
            r = httpx.get("https://graph.mapillary.com/images", timeout=20, params={
                "access_token": tok, "fields": "thumb_1024_url,creator,geometry", "limit": 10,
                "bbox": f"{lng - d},{lat - d},{lng + d},{lat + d}"}).json()
            best = min(r.get("data") or [], key=lambda x: _km(lat, lng, x["geometry"]["coordinates"][1], x["geometry"]["coordinates"][0]),
                       default=None)
            if best and best.get("thumb_1024_url"):
                img = httpx.get(best["thumb_1024_url"], timeout=20)
                if img.status_code == 200:
                    by = (best.get("creator") or {}).get("username") or "Mapillary contributor"
                    return img.content, img.headers.get("content-type", "image/jpeg"), f"Street photo: {by} · Mapillary (CC BY-SA)"
        except Exception:
            pass
    return None


def street_enabled() -> bool:
    return bool(key() or os.getenv("MAPILLARY_TOKEN"))


def accessory_shops(lat: float, lng: float, vehicle_type: str = "car") -> list[dict]:
    """Car / bike accessory shops near a point, live from Google Places (Text Search, 8 km bias). Cached a week per
    ~1 km grid cell so a busy area costs one call. Fields Google allows us to show: name, address, pin, phone,
    rating, open now, Maps link."""
    import json
    if not key():
        return []
    cell = f"{vehicle_type}:{round(lat, 2)}:{round(lng, 2)}"
    now = dt.datetime.now(dt.timezone.utc)
    with closing(db.connect()) as conn, conn:
        conn.execute("CREATE TABLE IF NOT EXISTS accessory_cache (cell TEXT PRIMARY KEY, fetched_at TEXT, payload TEXT)")
        row = conn.execute("SELECT fetched_at, payload FROM accessory_cache WHERE cell = ?", (cell,)).fetchone()
    if row and dt.datetime.fromisoformat(row[0]) > now - dt.timedelta(days=7):
        shops = json.loads(row[1])
    else:
        body = {"textQuery": "bike accessories shop" if vehicle_type == "bike" else "car accessories shop", "maxResultCount": 20,
                "locationBias": {"circle": {"center": {"latitude": lat, "longitude": lng}, "radius": 8000.0}}}
        fields = ",".join("places." + f for f in ("id", "displayName", "formattedAddress", "location", "nationalPhoneNumber",
                                                   "rating", "userRatingCount", "googleMapsUri", "businessStatus", "currentOpeningHours.openNow"))
        try:
            res = httpx.post(f"{BASE}/places:searchText", json=body, timeout=20,
                             headers={"X-Goog-Api-Key": key(), "Content-Type": "application/json", "X-Goog-FieldMask": fields}).json()
        except Exception:
            return []
        if "error" in res:
            return []
        shops = [{"id": "g:" + p["id"], "name": p.get("displayName", {}).get("text", ""), "address": p.get("formattedAddress", ""),
                  "lat": p["location"]["latitude"], "lng": p["location"]["longitude"], "phone": p.get("nationalPhoneNumber"),
                  "google_rating": p.get("rating"), "google_count": p.get("userRatingCount"), "google_maps_uri": p.get("googleMapsUri"),
                  "open_now": (p.get("currentOpeningHours") or {}).get("openNow"), "kind": "accessories", "phone_verified": True,
                  "location_verified": True}
                 for p in res.get("places", []) if p.get("location") and p.get("businessStatus", "OPERATIONAL") == "OPERATIONAL"]
        with closing(db.connect()) as conn, conn:
            conn.execute("INSERT OR REPLACE INTO accessory_cache (cell, fetched_at, payload) VALUES (?, ?, ?)", (cell, now.isoformat(), json.dumps(shops)))
    for s in shops:
        s["distance_km"] = round(_km(lat, lng, s["lat"], s["lng"]), 1)
    return sorted(shops, key=lambda s: s["distance_km"])
