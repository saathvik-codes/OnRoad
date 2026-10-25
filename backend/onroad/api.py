"""
OnRoad API (FastAPI).   uvicorn onroad.api:app --port 8100   (from backend/)

Public: catalogue, prices, offers, dealers, on-road breakdowns, search, compare.
Buyers: saved cars (price alerts), quote requests and ranked dealer quotes.
Dealers: claim a showroom (admin approves), answer quote requests, post showroom offers.
Admin: approve dealer claims; review dealer-onboarding invitations (nothing is ever sent without approval).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import math
import logging
import os
import re
import secrets
import time
from collections import defaultdict
from contextlib import closing
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import db, onroad_calc, ingest

ENABLE_DOCS = os.getenv("ENABLE_DOCS", "1") == "1"
app = FastAPI(
    title="OnRoad API", 
    docs_url="/api/docs" if ENABLE_DOCS else None, 
    openapi_url="/api/openapi.json" if ENABLE_DOCS else None,
    redoc_url=None
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    if request.method in ("POST", "PUT", "PATCH", "DELETE") and response.status_code < 400:
        from . import firestore_sync
        firestore_sync.mark_dirty()
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"
    return response

_RESP_CACHE: dict[str, tuple[float, int, bytes, dict]] = {}
_CACHEABLE = ("/api/brands", "/api/explore", "/api/offers", "/api/campaigns", "/api/models/", "/api/bands", "/api/cities",
              "/api/meta", "/api/variant-specs", "/api/loan-rates", "/api/states", "/api/model-features")
_CACHE_TTL = float(os.getenv("RESPONSE_CACHE_SECONDS", "300"))


@app.middleware("http")
async def cache_public_reads(request: Request, call_next):
    """Public catalogue reads are identical for everyone until the next data refresh, so keep them for a few minutes."""
    import time as _time
    from fastapi.responses import Response as _Resp
    path = request.url.path
    if request.method != "GET" or not path.startswith(_CACHEABLE) or _CACHE_TTL <= 0:
        return await call_next(request)
    key = str(request.url.path) + "?" + str(request.url.query)
    hit = _RESP_CACHE.get(key)
    if hit and hit[0] > _time.time():
        return _Resp(content=hit[2], status_code=hit[1], headers=hit[3])
    response = await call_next(request)
    if response.status_code != 200:
        return response
    body = b"".join([chunk async for chunk in response.body_iterator])
    headers = {k: v for k, v in response.headers.items() if k.lower() not in ("content-length", "set-cookie")}
    if len(_RESP_CACHE) > 2000:
        _RESP_CACHE.clear()
    _RESP_CACHE[key] = (_time.time() + _CACHE_TTL, 200, body, headers)
    return _Resp(content=body, status_code=200, headers=headers)


db.init()
LOGOS = db.ROOT / "data" / "logos"
COOKIE = "or_session"
SECURE = os.getenv("COOKIE_SECURE", "0") == "1"


def q(sql: str, params: tuple = ()) -> list[dict]:
    with closing(db.connect()) as conn:
        return [dict(r) for r in conn.execute(sql, params)]


def one(sql: str, params: tuple = ()) -> dict | None:
    rows = q(sql, params)
    return rows[0] if rows else None


# ── Auth (salted PBKDF2 passwords, signed httpOnly cookie) ──────────────────────────────────────────────
def _secret() -> bytes:
    if os.getenv("API_SECRET"):
        return os.getenv("API_SECRET").encode()
    f = db.ROOT / "data" / ".api_secret"
    if not f.exists():
        f.write_text(secrets.token_hex(32))
    return f.read_text().strip().encode()


def _hash(pw: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    return f"pbkdf2${salt}${hashlib.pbkdf2_hmac('sha256', pw.encode(), bytes.fromhex(salt), 310_000).hex()}"


def _check(pw: str, stored: str) -> bool:
    _, salt, digest = stored.split("$")
    return secrets.compare_digest(hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 310_000).hex(), digest)


def _sign(uid: int) -> str:
    payload = f"{uid}.{int(time.time()) + 14 * 86400}"
    sig = base64.urlsafe_b64encode(hmac.new(_secret(), payload.encode(), hashlib.sha256).digest()).decode().rstrip("=")
    return f"{payload}.{sig}"


def _uid(token: str | None) -> int | None:
    try:
        uid, exp, sig = (token or "").split(".")
        good = base64.urlsafe_b64encode(hmac.new(_secret(), f"{uid}.{exp}".encode(), hashlib.sha256).digest()).decode().rstrip("=")
        return int(uid) if hmac.compare_digest(sig, good) and int(exp) > time.time() else None
    except (ValueError, TypeError):
        return None


def account(request: Request) -> dict:
    uid = _uid(request.cookies.get(COOKIE))
    acc = one("SELECT id, email, name, phone, role FROM accounts WHERE id = ?", (uid,)) if uid else None
    if not acc:
        raise HTTPException(401, "Please log in")
    return acc


def role(*allowed: str):
    def dep(acc: dict = Depends(account)) -> dict:
        if acc["role"] not in allowed:
            raise HTTPException(403, "Not allowed for this account")
        return acc
    return dep


_tries: dict[str, list[float]] = defaultdict(list)


class SignupIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: str = Field(max_length=120)
    phone: str | None = Field(default=None, max_length=20)
    password: str = Field(min_length=8, max_length=200)
    role: str = "buyer"


class LoginIn(BaseModel):
    email: str
    password: str


@app.post("/api/auth/signup")
def signup(body: SignupIn, response: Response):
    email = body.email.strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", email, re.I):
        raise HTTPException(400, "Enter a valid email address.")
    if body.role not in ("buyer", "dealer"):
        raise HTTPException(400, "Unknown account type.")
    if one("SELECT 1 AS x FROM accounts WHERE email = ?", (email,)):
        raise HTTPException(400, "An account with this email already exists.")
    with closing(db.connect()) as conn, conn:
        uid = conn.execute("INSERT INTO accounts (email, name, phone, pw_hash, role) VALUES (?, ?, ?, ?, ?)",
                           (email, body.name.strip(), body.phone, _hash(body.password), body.role)).lastrowid
    response.set_cookie(COOKIE, _sign(uid), max_age=14 * 86400, httponly=True, samesite="lax", secure=SECURE, path="/")
    return {"id": uid, "email": email, "name": body.name, "role": body.role}


@app.post("/api/auth/login")
def login(body: LoginIn, request: Request, response: Response):
    key = f"{body.email.lower()}|{request.client.host if request.client else ''}"
    _tries[key] = [t for t in _tries[key] if time.time() - t < 900]
    if len(_tries[key]) >= 8:
        raise HTTPException(429, "Too many attempts. Try again in 15 minutes.")
    _tries[key].append(time.time())
    acc = one("SELECT * FROM accounts WHERE email = ?", (body.email.strip().lower(),))
    if not acc or not _check(body.password, acc["pw_hash"]):
        raise HTTPException(401, "Email or password is wrong.")
    response.set_cookie(COOKIE, _sign(acc["id"]), max_age=14 * 86400, httponly=True, samesite="lax", secure=SECURE, path="/")
    return {k: acc[k] for k in ("id", "email", "name", "role")}


class GoogleIn(BaseModel):
    id_token: str


# Google OAuth client IDs whose sign-in tokens we accept (web client first; the Android app asks Google for a token
# issued to the web client too). GOOGLE_CLIENT_IDS="id1,id2" overrides.
GOOGLE_CLIENT_IDS = [x.strip() for x in os.getenv("GOOGLE_CLIENT_IDS",
                     "725690528227-vtrohp3ga3aguno26glvdfefu4lacecu.apps.googleusercontent.com").split(",") if x.strip()]


@app.get("/api/auth/google/config")
def google_config():
    return {"client_id": GOOGLE_CLIENT_IDS[0] if GOOGLE_CLIENT_IDS else None}


@app.post("/api/auth/google")
def google_login(body: GoogleIn, response: Response):
    """Sign in with Google: the ID token is checked by Google itself (signature, expiry), and must be issued to one of
    our client IDs for a verified email. An existing OnRoad account with that email is signed in; otherwise one is made."""
    import secrets
    import httpx
    try:
        r = httpx.get("https://oauth2.googleapis.com/tokeninfo", params={"id_token": body.id_token}, timeout=15)
    except Exception:
        raise HTTPException(503, "Couldn't reach Google. Try again.")
    t = r.json() if r.status_code == 200 else {}
    if not t or t.get("aud") not in GOOGLE_CLIENT_IDS or t.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise HTTPException(401, "Google sign-in couldn't be verified.")
    if str(t.get("email_verified")).lower() != "true" or not t.get("email"):
        raise HTTPException(401, "Your Google account's email isn't verified.")
    email = t["email"].strip().lower()
    acc = one("SELECT * FROM accounts WHERE email = ?", (email,))
    if not acc:
        with closing(db.connect()) as conn, conn:
            uid = conn.execute("INSERT INTO accounts (email, name, phone, pw_hash, role) VALUES (?, ?, ?, ?, ?)",
                               (email, (t.get("name") or email.split("@")[0]).strip(), None,
                                _hash(secrets.token_urlsafe(24)), "buyer")).lastrowid      # no password: Google signs them in
        acc = one("SELECT * FROM accounts WHERE id = ?", (uid,))
    response.set_cookie(COOKIE, _sign(acc["id"]), max_age=14 * 86400, httponly=True, samesite="lax", secure=SECURE, path="/")
    return {k: acc[k] for k in ("id", "email", "name", "role")}


@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@app.get("/api/auth/me")
def me(acc: dict = Depends(account)):
    return acc


# ── Catalogue ───────────────────────────────────────────────────────────────────────────────────────────
LATEST_PRICE = """SELECT p.ex_showroom_inr, p.fetched_at, p.source_url FROM prices p
                  WHERE p.variant_id = v.id AND p.city = ? ORDER BY p.fetched_at DESC LIMIT 1"""


LIVE = ("o.active = 1 AND (o.valid_until IS NULL OR o.valid_until = '' OR o.valid_until >= date('now', 'localtime')) "
        "AND (o.city IS NULL OR o.city = '' OR lower(o.city) = lower(?))")


def _offers(where: str, params: tuple, city: str) -> list[dict]:
    """Current offers (expired ones hidden), one row per distinct offer, biggest first."""
    rows = q(f"""SELECT o.* FROM offers o WHERE {LIVE} AND {where}
                 GROUP BY o.brand_slug, ifnull(o.model_name, ''), o.title, ifnull(o.amount_inr, 0), ifnull(o.kind, ''), ifnull(o.variant, ''),
                          ifnull(o.dealer_id, '')
                 ORDER BY o.amount_inr IS NULL, o.amount_inr DESC""", (city, *params))
    _link_offer_models(rows)
    today = __import__("datetime").date.today()
    for r in rows:
        r["days_left"] = ((__import__("datetime").date.fromisoformat(r["valid_until"]) - today).days
                          if r.get("valid_until") else None)
    return rows


CRASH_TESTS = db.ROOT / "data" / "research" / "crash_tests.json"


def _crash_tests(brand_name: str, model_name: str) -> list[dict]:
    """Official Bharat NCAP / Global NCAP results for this model (data/research/crash_tests.json, every record sourced).
    Empty list = no verified official result; the UI says so instead of showing a rating."""
    if not CRASH_TESTS.exists():
        return []
    import json as _json
    norm = lambda t: re.sub(r"[^a-z0-9]", "", (t or "").lower())
    b, m = norm(brand_name), norm(model_name)
    out = [r for r in _json.loads(CRASH_TESTS.read_text(encoding="utf-8"))
           if norm(r.get("brand"))[:4] == b[:4] and norm(r.get("model")) and
           (norm(r.get("model")) == m or (len(norm(r.get("model"))) >= 4 and (m.startswith(norm(r.get("model"))) or norm(r.get("model")).startswith(m))))]
    return sorted(out, key=lambda r: r.get("test_date") or "", reverse=True)


def _gallery(m: dict, variants: list[dict]) -> list[dict]:
    """Model image, then each distinct variant / colour image, then the manufacturer's feature photos (official only)."""
    out, seen = [], set()
    def add(url, label, kind):
        if url and url not in seen:
            seen.add(url); out.append({"url": url, "label": label, "kind": kind})
    img = m.get("image_url")
    if not img:
        alt = one("SELECT image_url FROM models WHERE brand_slug = ? AND (name = ? OR slug = ?) AND image_url IS NOT NULL AND image_url != '' LIMIT 1",
                  (m.get("brand_slug"), m.get("name"), m.get("slug")))
        if alt and alt.get("image_url"):
            img = alt["image_url"]
            m["image_url"] = img
    if not img:
        for v in variants:
            if v.get("image_url"):
                img = v["image_url"]
                m["image_url"] = img
                break
    add(img, m.get("name"), "model")
    for v in variants:
        add(v.get("image_url"), v.get("name"), "variant")
    try:                                   # model photo galleries (onroad/gallery_sync.py): exterior first, then interior
        for r in q("SELECT url, label, kind FROM model_gallery WHERE model_id = ? ORDER BY kind = 'Interior', rowid", (m["id"],)):
            add(r["url"], r["label"], (r["kind"] or "photo").lower())
    except Exception:
        pass
    try:
        alt_id1 = m["id"].replace('-', '_')
        alt_id2 = m["id"].replace('_', '-')
        for r in q("SELECT key, image_url FROM feature_images WHERE model_id = ? OR model_id = ? OR model_id = ? LIMIT 8", (m["id"], alt_id1, alt_id2)):
            add(r["image_url"], r["key"].replace("_", " ").title(), "feature")
    except Exception:
        pass
    return out


def _pick(city: str) -> tuple[str, tuple]:
    """CTE `pick`: one current ex-showroom price per variant for `city`: that city's own price, else the brand's national
    list, else its list for the city's state, else Hyderabad (the launch city, always ingested). Newest first within each."""
    st = onroad_calc.STATE_OF_CITY.get(city.strip().lower(), "TS")
    state_name = ((onroad_calc.rules().get("states") or {}).get(st) or {}).get("name", "")
    sql = """pick AS (SELECT variant_id, ex_showroom_inr, city, fetched_at, source_url FROM (
                 SELECT p.*, ROW_NUMBER() OVER (PARTITION BY p.variant_id ORDER BY lower(p.city) = lower(?) DESC,
                        p.city = 'India (national)' DESC, p.city = ? DESC, p.city = 'Hyderabad' DESC, p.fetched_at DESC) AS rn
                 FROM prices p) WHERE rn = 1)"""
    return sql, (city, state_name)


def _price_city(city: str) -> str:
    """Brands with one national list publish it under one city; fall back to it when the city has no prices."""
    return city


@app.get("/api/brands")
def brands(city: str = "Hyderabad", vehicle_type: str | None = None):
    cte, cp = _pick(city)
    vt_cond = "AND b.vehicle_type = ?" if vehicle_type else ""
    vt_params = (vehicle_type,) if vehicle_type else ()
    rows = q(f"""WITH {cte} SELECT b.slug, b.name, b.segment, b.vehicle_type, b.website, b.last_refresh, b.refresh_note,
                       (SELECT COUNT(*) FROM models m WHERE m.brand_slug = b.slug AND m.active = 1) AS models,
                       (SELECT MIN(px.ex_showroom_inr) FROM variants v JOIN models m ON m.id = v.model_id
                          JOIN pick px ON px.variant_id = v.id
                          WHERE m.brand_slug = b.slug AND v.active = 1) AS from_inr,
                       (SELECT COUNT(*) FROM dealers d WHERE d.brand_slug = b.slug AND d.active = 1 AND lower(d.city) = lower(?)) AS dealers_here,
                       (SELECT COUNT(*) FROM offers o WHERE o.brand_slug = b.slug AND {LIVE}) AS offers
                FROM brands b WHERE 1=1 {vt_cond} ORDER BY b.segment = 'luxury', b.name""", (*cp, city, city, *vt_params))
    for r in rows:
        r["logo"] = _logo_url(r["slug"])
    return rows



def _logo_file(slug: str) -> Path | None:
    for ext in ("svg", "png", "webp", "jpg"):
        f = LOGOS / f"{slug}.{ext}"
        if f.exists():
            return f
    return None


def _logo_url(slug: str) -> str | None:
    f = _logo_file(slug)
    if not f:
        return None
    try:
        v = int(f.stat().st_mtime)
        return f"/api/logos/{slug}?v={v}"
    except Exception:
        return f"/api/logos/{slug}"


@app.get("/api/logos/{slug}")
def logo(slug: str, v: str | None = None):
    f = _logo_file(re.sub(r"[^a-z0-9_-]", "", slug))
    if not f:
        raise HTTPException(404, "No logo")
    cache = "public, max-age=31536000, immutable" if v else "no-cache, must-revalidate"
    return FileResponse(f, headers={"Cache-Control": cache})


def _variants(model_id: str, city: str) -> list[dict]:
    cte, cp = _pick(city)
    rows = q(f"""WITH {cte}
                SELECT v.*, pk.ex_showroom_inr, pk.city AS price_city, pk.fetched_at AS price_as_of, pk.source_url AS price_source
                FROM variants v LEFT JOIN pick pk ON pk.variant_id = v.id
                WHERE v.model_id = ? AND v.active = 1 ORDER BY pk.ex_showroom_inr""", (*cp, model_id))
    return rows


def _engine_cc(v: dict) -> int | None:
    """Engine size for the insurance band: published cc, else read from the variant name ("1.5 MPi" -> 1497 cc band)."""
    if v.get("engine_cc"):
        return v["engine_cc"]
    m = re.search(r"(?<![\d.])([0-4]\.\d)\s?(?:l\b|litre|mpi|crdi|turbo|tsi|tgdi|gdi|dsl|diesel|petrol|vtvt|k|ecoboost|[a-z]|$)", (v.get("name") or "").lower())
    if not m:
        return None
    litres = float(m.group(1))
    return int(litres * 1000) - (3 if litres in (1.0, 1.5) else 0)   # 1.0 L ~ 998 cc, 1.5 L ~ 1497 cc stay inside their bands


METRO_CLUSTERS = {
    "gurugram": ["gurugram", "gurgaon", "delhi", "new delhi", "noida", "faridabad", "ghaziabad"],
    "gurgaon": ["gurgaon", "gurugram", "delhi", "new delhi", "noida", "faridabad", "ghaziabad"],
    "delhi": ["delhi", "new delhi", "gurugram", "gurgaon", "noida", "faridabad", "ghaziabad"],
    "new delhi": ["new delhi", "delhi", "gurugram", "gurgaon", "noida", "faridabad", "ghaziabad"],
    "noida": ["noida", "delhi", "new delhi", "ghaziabad", "gurugram", "gurgaon", "faridabad"],
    "faridabad": ["faridabad", "delhi", "new delhi", "gurugram", "gurgaon", "noida"],
    "ghaziabad": ["ghaziabad", "noida", "delhi", "new delhi"],
    "bengaluru": ["bengaluru", "bangalore"],
    "bangalore": ["bangalore", "bengaluru"],
    "mumbai": ["mumbai", "navi mumbai", "thane"],
    "navi mumbai": ["navi mumbai", "mumbai", "thane"],
    "thane": ["thane", "mumbai", "navi mumbai"],
    "hyderabad": ["hyderabad", "secunderabad", "rangareddy"],
    "secunderabad": ["secunderabad", "hyderabad", "rangareddy"],
    "chennai": ["chennai", "poonamallee"],
    "ahmedabad": ["ahmedabad", "gandhinagar"],
    "gandhinagar": ["gandhinagar", "ahmedabad"],
    "jaipur": ["jaipur", "jaipur (rj)"],
    "jaipur (rj)": ["jaipur (rj)", "jaipur"],
}


def _dealers_for(brand_slug: str, city: str, lat: float | None = None, lng: float | None = None) -> list[dict]:
    if lat is not None and lng is not None:
        # the buyer shared their location (works for any village / town): nearest showrooms of this brand anywhere,
        # by straight-line distance from that exact point, using the coordinates from the brand's own dealer locator
        near = q("SELECT * FROM dealers WHERE brand_slug = ? AND active = 1 AND lat IS NOT NULL AND lng IS NOT NULL", (brand_slug,))
        for d in near:
            d["distance_km"] = _km(lat, lng, d["lat"], d["lng"])
            d["near_you"] = True
        near.sort(key=lambda d: d["distance_km"])
        if near:
            return near[:25]
    city_norm = (city or "").strip().lower()
    st_city = onroad_calc.STATE_OF_CITY.get(city_norm)
    # metro aliases only within the same state (Gurugram is Haryana: Delhi / Noida showrooms register in other states)
    aliases = [a for a in METRO_CLUSTERS.get(city_norm, [city_norm])
               if onroad_calc.STATE_OF_CITY.get(a, st_city) == st_city] or [city_norm]
    placeholders = ",".join("?" for _ in aliases)
    rows = q(f"SELECT * FROM dealers WHERE brand_slug = ? AND active = 1 AND lower(city) IN ({placeholders})",
             (brand_slug, *aliases))

    if not rows:
        st = onroad_calc.STATE_OF_CITY.get(city_norm)
        if st:
            state_info = (onroad_calc.rules().get("states") or {}).get(st) or {}
            state_name = state_info.get("name", "")
            rows = q("""SELECT * FROM dealers WHERE brand_slug = ? AND active = 1 AND
                        (upper(state) = ? OR lower(state) LIKE ? OR lower(state) LIKE ?)""",
                     (brand_slug, st.upper(), f"%{state_name.lower()}%", f"%{city_norm}%"))
            # trust the showroom's city over its state field (some brand locators mislabel the state)
            rows = [d for d in rows if onroad_calc.STATE_OF_CITY.get((d.get("city") or "").strip().lower(), st) == st]
            for d in rows:
                d["outside_city"] = True       # same state, different city: the UI labels these as nearest in the state

    # no showroom in this city or state: say so (never show another region's showrooms as if they were local)

    c_coords = CITIES.get(city.title()) or CITIES.get(city)
    ref_lat = lat if lat is not None else (c_coords[0] if c_coords else None)
    ref_lng = lng if lng is not None else (c_coords[1] if c_coords else None)

    for d in rows:
        if ref_lat and ref_lng and d.get("lat") and d.get("lng"):
            d["distance_km"] = _km(ref_lat, ref_lng, d["lat"], d["lng"])
        else:
            d["distance_km"] = None

    if ref_lat and ref_lng:
        rows.sort(key=lambda d: d["distance_km"] if d["distance_km"] is not None else 1e9)

    try:                                   # OnRoad buyers' rating summary
        own = {r["dealer_id"]: r for r in q("""SELECT dealer_id, AVG(rating) AS avg, COUNT(*) AS n,
                     AVG(CASE WHEN no_forced_addons THEN 1.0 ELSE 0 END) AS no_addons FROM dealer_reviews GROUP BY dealer_id""")}
        for d in rows:
            if d["id"] in own:
                d["onroad_rating"], d["onroad_count"], d["no_addons_share"] = own[d["id"]]["avg"], own[d["id"]]["n"], own[d["id"]]["no_addons"]
    except Exception:
        pass
    _google(rows)
    return rows


def _google(rows: list[dict]) -> None:
    """Google rating and showroom photo where the dealer is matched (onroad/places.py; nothing without GOOGLE_PLACES_KEY).
    The photo is served live through /api/dealer-photo (Google's terms: photos are not stored), credited to its author."""
    try:
        rated = {r["dealer_id"]: r for r in q("SELECT * FROM dealer_places WHERE place_id IS NOT NULL")}
    except Exception:
        rated = {}
    from urllib.parse import quote
    from . import places
    street = places.street_enabled()
    for d in rows:
        g = rated.get(d["id"])
        if not g:
            if street and d.get("lat") and d.get("lng"):        # no Places listing: the street-front photo, if any exists
                d["photo_url"] = f"/api/dealer-photo?id={quote(d['id'], safe='')}"
                d["photo_credit"] = "Street view of this address"
            continue
        if g.get("rating") is not None:
            d["google_rating"], d["google_count"], d["google_maps_uri"] = g["rating"], g["rating_count"], g["maps_uri"]
        if g.get("photo"):
            d["photo_url"] = f"/api/dealer-photo?id={quote(d['id'], safe='')}"
            d["photo_credit"] = f"Photo: {g.get('photo_by') or 'Google user'} · Google"
        elif street and d.get("lat") and d.get("lng"):
            d["photo_url"] = f"/api/dealer-photo?id={quote(d['id'], safe='')}"
            d["photo_credit"] = "Street view of this address"


@app.get("/api/dealer-photo")
def dealer_photo(id: str, w: int = 800):
    from fastapi.responses import RedirectResponse
    from . import places
    from fastapi.responses import Response
    u = places.photo_uri(id, max(200, min(w, 1600)))
    if u:
        return RedirectResponse(u, status_code=302, headers={"Cache-Control": "public, max-age=3600"})
    d = one("SELECT lat, lng FROM dealers WHERE id = ?", (id,))
    got = places.street_photo(d["lat"], d["lng"], w) if d and d.get("lat") and d.get("lng") else None
    if not got:
        raise HTTPException(404, "No photo for this showroom")
    body, ctype, credit = got                      # served live, not stored (Street View / Mapillary terms)
    return Response(body, media_type=ctype, headers={"Cache-Control": "public, max-age=3600", "X-Photo-Credit": credit})



@app.get("/api/brands/{slug}")
def brand(slug: str, city: str = "Hyderabad"):
    b = one("SELECT * FROM brands WHERE slug = ?", (slug,))
    if not b:
        raise HTTPException(404, "Unknown brand")
    models = q("SELECT * FROM models WHERE brand_slug = ? AND active = 1 ORDER BY name", (slug,))
    for m in models:
        vs = _variants(m["id"], city)
        prices = [v["ex_showroom_inr"] for v in vs if v["ex_showroom_inr"]]
        m.update(variants=len(vs), from_inr=min(prices) if prices else None, to_inr=max(prices) if prices else None,
                 fuels=sorted({v["fuel"] for v in vs if v["fuel"]}), transmissions=sorted({v["transmission"] for v in vs if v["transmission"]}))
    b["logo"] = _logo_url(slug)
    return {**b, "models": models,
            "offers": _offers("o.brand_slug = ?", (slug,), city),
            "dealers": _dealers_for(slug, city)}


@app.get("/api/models/{brand}/{model}")
def model(brand: str, model: str, city: str = "Hyderabad", lat: float | None = None, lng: float | None = None):
    mid = f"{brand}/{model}"
    mid_alt = f"{brand.replace('-', '_')}/{model.replace('-', '_')}"
    mid_alt2 = f"{brand.replace('_', '-')}/{model.replace('_', '-')}"
    m = one("""SELECT m.*, b.name AS brand_name, b.vehicle_type AS brand_vehicle_type 
               FROM models m JOIN brands b ON b.slug = m.brand_slug 
               WHERE m.id = ? OR m.id = ? OR m.id = ?""", (mid, mid_alt, mid_alt2))
    if not m:
        raise HTTPException(404, "Unknown model")
    mid = m["id"]
    brand = m["brand_slug"]
    vt = m.get("vehicle_type") or m.get("brand_vehicle_type") or "car"
    variants = _variants(mid, city)
    from .names import display_names                  # tidy names for buyers; the published one stays as published_name
    display_names(m.get("brand_name") or "", m.get("name") or "", variants)
    for v in variants:
        v["published_name"], v["name"] = v["name"], v.pop("display_name")
    for v in variants:
        if v["ex_showroom_inr"]:
            v["onroad"] = onroad_calc.estimate(v["ex_showroom_inr"], city=city, fuel=v["fuel"], engine_cc=_engine_cc(v),
                                               battery_kwh=v["battery_kwh"], vehicle_type=vt).to_dict()

    dealers = _dealers_for(brand, city, lat, lng)
    offers = _offers("o.brand_slug = ? AND (o.model_name IS NULL OR o.model_name = '' OR lower(o.model_name) = lower(?))",
                     (brand, m["name"]), city)
    history = q("""SELECT p.variant_id, p.city, p.ex_showroom_inr, p.fetched_at FROM prices p JOIN variants v ON v.id = p.variant_id
                   WHERE v.model_id = ? ORDER BY p.fetched_at""", (mid,))
    best_quotes = q("""SELECT qt.on_road_inr, qt.discount_inr, qt.created, d.name AS dealer, v.name AS variant FROM quotes qt
                       JOIN quote_requests r ON r.id = qt.request_id JOIN variants v ON v.id = r.variant_id
                       JOIN dealers d ON d.id = qt.dealer_id WHERE v.model_id = ? AND lower(r.city) = lower(?)
                       ORDER BY qt.on_road_inr LIMIT 5""", (mid, city))
    crash_tests = _crash_tests(m["brand_name"], m["name"])
    return {**m, "logo": _logo_url(brand), "variants": variants, "dealers": dealers,
            "offers": offers, "price_history": history, "recent_dealer_quotes": best_quotes,
            "crash_tests": crash_tests, "gallery": _gallery(m, variants)}


def _km(a1, o1, a2, o2) -> float:
    p = math.pi / 180
    h = 0.5 - math.cos((a2 - a1) * p) / 2 + math.cos(a1 * p) * math.cos(a2 * p) * (1 - math.cos((o2 - o1) * p)) / 2
    return round(12742 * math.asin(math.sqrt(h)), 1)


@app.get("/api/onroad")
def onroad(variant_id: str, city: str = "Hyderabad", loan: bool = False, ownership: str = "first_vehicle"):
    v = one("""SELECT v.*, m.vehicle_type FROM variants v
               JOIN models m ON m.id = v.model_id WHERE v.id = ?""", (variant_id,))
    if not v:
        raise HTTPException(404, "Unknown variant")
    cte, cp = _pick(city)
    p = one(f"WITH {cte} SELECT * FROM pick WHERE variant_id = ?", (*cp, variant_id))
    if not p:
        raise HTTPException(404, "No published price for this variant yet")
    vt = v.get("vehicle_type") or "car"
    b = onroad_calc.estimate(p["ex_showroom_inr"], city=city, fuel=v["fuel"], engine_cc=_engine_cc(v), battery_kwh=v["battery_kwh"],
                             ownership=ownership, loan=loan, vehicle_type=vt)
    return {**b.to_dict(), "price_city": p["city"], "price_as_of": p["fetched_at"], "price_source": p["source_url"], "vehicle_type": vt}


@app.get("/api/onroad/quick")
def onroad_quick(ex_showroom: int = Query(gt=20_000, lt=200_000_000), city: str = "Hyderabad", state: str | None = None,
                 fuel: str = "Petrol", engine_cc: int | None = None, motor_kw: float | None = None, loan: bool = False,
                 ownership: str = "first_vehicle", variant_id: str | None = None, vehicle_type: str = "car"):
    """Calculator for any price (the buyer types the ex-showroom price, e.g. from a dealer quote).
    With variant_id, missing engine size / battery come from that variant (as on the model page)."""
    if ownership not in ("first_vehicle", "second_vehicle", "company"):
        raise HTTPException(400, "Unknown ownership type")
    v = one("""SELECT v.*, m.vehicle_type FROM variants v
               JOIN models m ON m.id = v.model_id WHERE v.id = ?""", (variant_id,)) if variant_id else None
    if v and engine_cc is None and (v.get("fuel") or "").lower() != "electric":
        engine_cc = _engine_cc(v)
    vt = v.get("vehicle_type") if v and v.get("vehicle_type") else vehicle_type
    return onroad_calc.estimate(ex_showroom, city=city, state=state, fuel=fuel, engine_cc=engine_cc, motor_kw=motor_kw,
                                loan=loan, ownership=ownership, vehicle_type=vt).to_dict()


# Cities buyers can pick (lat/lng for "use my location"). State comes from onroad_calc.STATE_OF_CITY.
CITIES = {
    "Hyderabad": (17.385, 78.487), "Secunderabad": (17.44, 78.498), "Warangal": (17.968, 79.594), "Karimnagar": (18.439, 79.129),
    "Nizamabad": (18.672, 78.094), "Khammam": (17.247, 80.151), "Bengaluru": (12.972, 77.594), "Mysuru": (12.296, 76.639),
    "Chennai": (13.083, 80.271), "Coimbatore": (11.017, 76.956), "Madurai": (9.925, 78.12), "Mumbai": (19.076, 72.878),
    "Pune": (18.52, 73.857), "Nagpur": (21.146, 79.088), "Delhi": (28.614, 77.209), "Gurugram": (28.459, 77.027),
    "Noida": (28.535, 77.391), "Lucknow": (26.847, 80.947), "Kolkata": (22.573, 88.364), "Ahmedabad": (23.023, 72.571),
    "Surat": (21.17, 72.831), "Kochi": (9.931, 76.267), "Thiruvananthapuram": (8.524, 76.937), "Vijayawada": (16.506, 80.648),
    "Visakhapatnam": (17.687, 83.218), "Jaipur": (26.912, 75.787), "Chandigarh": (30.733, 76.779), "Bhopal": (23.26, 77.413),
    "Indore": (22.72, 75.858), "Patna": (25.594, 85.138), "Bhubaneswar": (20.296, 85.825), "Guwahati": (26.144, 91.736),
    "Panaji": (15.491, 73.828), "Dehradun": (30.317, 78.032), "Ranchi": (23.344, 85.31), "Raipur": (21.251, 81.63),
    "Shimla": (31.105, 77.173), "Ludhiana": (30.901, 75.857), "Srinagar": (34.084, 74.797), "Puducherry": (11.942, 79.808),
    "Port Blair": (11.623, 92.726), "Itanagar": (27.084, 93.605), "Daman": (20.397, 72.832), "Leh": (34.152, 77.577), "Kavaratti": (10.566, 72.642), "Shillong": (25.578, 91.893), "Imphal": (24.817, 93.937), "Aizawl": (23.727, 92.718), "Kohima": (25.674, 94.11), "Gangtok": (27.339, 88.607), "Agartala": (23.831, 91.286),
}


FEATURE_SHOTS = {
    "alloy_wheels": r"^(?:alloy )?wheels?$|alloy wheel", "digital_cluster": r"instrument cluster|digital cluster",
    "tft_display": r"instrument cluster|tft|console", "touchscreen": r"infotainment|touch ?screen",
    "android_auto_carplay": r"infotainment system main menu|apple carplay|android auto", "led_headlamps": r"head ?(?:light|lamp)",
    "auto_headlamps": r"head ?(?:light|lamp)", "led_drl": r"\bdrl|daytime running|head ?(?:light|lamp)",
    "led_lamps_2w": r"head ?(?:light|lamp)|tail ?(?:light|lamp)", "fog_lamps": r"fog ?lamp", "airbags_6": r"air ?bags?",
    "airbags_2": r"air ?bags?", "sunroof": r"sun ?roof", "panoramic_sunroof": r"panoramic|sun ?roof",
    "push_button_start": r"start[- ]stop|engine start|push button", "auto_climate": r"climate control|ac controls?|dashboard controls",
    "rear_ac_vents": r"rear (?:ac )?vents?", "rear_armrest": r"rear armrest|front armrest", "wireless_charger": r"wireless charg",
    "electric_parking_brake": r"parking brake|\bepb\b", "rear_camera": r"rear camera|parking camera", "camera_360": r"360",
    "ventilated_seats": r"ventilated|seats? (?:aerial|controls)", "powered_driver_seat": r"seat (?:adjust|controls)",
    "roof_rails": r"roof rails?", "rain_sensing_wipers": r"wiper", "front_disc": r"front (?:disc|brake)", "rear_disc_brakes": r"rear (?:disc|brake)",
}


@app.get("/api/variant-specs")
def variant_specs(variant_id: str):
    """Published specs + standard equipment for one variant (empty lists when the brand's spec sheet isn't read yet)."""
    specs = q("SELECT grp, key, label, value, source_url, fetched_at FROM specs WHERE variant_id = ? ORDER BY grp, label", (variant_id,))
    feats = q("SELECT key, label, source_url FROM features WHERE variant_id = ? ORDER BY key", (variant_id,))
    v = one("SELECT v.*, m.url AS model_url, m.brand_slug FROM variants v JOIN models m ON m.id = v.model_id WHERE v.id = ?", (variant_id,))
    if not v:
        raise HTTPException(404, "Unknown variant")
    try:
        photos = {r["key"]: r for r in q("SELECT key, image_url, source_url FROM feature_images WHERE model_id = ?", (v["model_id"],))}
    except Exception:
        photos = {}
    # gallery shots labelled with what they show ("Instrument cluster", "Wheel", "Sunroof") stand in where the maker
    # gave no dedicated feature photo; only for equipment this variant actually has
    try:
        have = {f["key"] for f in feats}
        gallery = q("SELECT url, label, source_url FROM model_gallery WHERE model_id = ?", (v["model_id"],))
        for key, rx in FEATURE_SHOTS.items():
            if key in have and key not in photos:
                hit = next((g for g in gallery if re.search(rx, g["label"] or "", re.I)), None)
                if hit:
                    photos[key] = {"key": key, "image_url": hit["url"], "source_url": hit["source_url"]}
    except Exception:
        pass
    return {"variant_id": variant_id, "specs": specs, "features": feats, "model_url": v["model_url"], "photos": photos,
            "basics": {k: v[k] for k in ("fuel", "transmission", "engine_cc", "battery_kwh", "seats")}}


@app.get("/api/loan-rates")
def loan_rates(vehicle_type: str = "car"):
    """Car or two-wheeler loan rate ranges as each bank publishes them (onroad/loan_rates.py, refreshed with the data)."""
    try:
        return q("""SELECT bank, product, ev_only, min_pct, max_pct, source_url, fetched_at, coalesce(vehicle_type, 'car') AS vehicle_type
                    FROM loan_rates WHERE coalesce(vehicle_type, 'car') = ? ORDER BY min_pct""",
                 ("bike" if vehicle_type in ("bike", "two_wheeler") else "car",))
    except Exception:
        return []


@app.get("/api/model-features")
def model_features(model_id: str):
    """Every equipment item listed on ANY variant of this model (manufacturer data), how many variants have it,
    and the model's own photo of it where we have one. Drives the per-model feature guide."""
    total = one("SELECT COUNT(*) AS n FROM variants WHERE model_id = ? AND active = 1", (model_id,))["n"]
    rows = q("""SELECT f.key, MIN(f.label) AS label, COUNT(DISTINCT f.variant_id) AS variants
                FROM features f JOIN variants v ON v.id = f.variant_id
                WHERE v.model_id = ? AND v.active = 1 GROUP BY f.key ORDER BY variants DESC""", (model_id,))
    try:
        photos = {r["key"]: r["image_url"] for r in q("SELECT key, image_url FROM feature_images WHERE model_id = ?", (model_id,))}
    except Exception:
        photos = {}
    for r in rows:
        r["photo"] = photos.get(r["key"])
    return {"total_variants": total, "features": rows}


@app.get("/api/feature-photos")
def feature_photos():
    """One manufacturer photo per equipment key (for the feature guide), with the brand it came from."""
    try:
        return q("""SELECT f.key, f.image_url, f.source_url, b.name AS brand FROM feature_images f
                    JOIN models m ON m.id = f.model_id JOIN brands b ON b.slug = m.brand_slug GROUP BY f.key""")
    except Exception:
        return []


import os as _os_img
IMG_CACHE = (_os_img.environ.get("IMG_CACHE") and __import__("pathlib").Path(_os_img.environ["IMG_CACHE"])) or db.ROOT / "data" / "img_cache"


def _img_path(u: str, w: int):
    import hashlib
    return IMG_CACHE / f"{hashlib.sha1(f'{u}|{w}'.encode()).hexdigest()}.webp"


def _render_images(u: str, widths) -> None:
    """Download one manufacturer image once and write every missing width as WebP (atomic writes, small memory)."""
    import io
    from PIL import Image
    import httpx as _httpx
    todo = [w for w in widths if not _img_path(u, w).exists()]
    if not todo:
        return
    IMG_CACHE.mkdir(parents=True, exist_ok=True)
    r = _httpx.get(u, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/129 Safari/537.36 OnRoadBot/0.1"},
                   timeout=30, follow_redirects=True)
    r.raise_for_status()
    with Image.open(io.BytesIO(r.content)) as src:
        src.draft("RGB", (max(todo), max(todo)))          # JPEGs decode straight at a smaller size
        base = src.convert("RGBA") if src.mode in ("P", "LA", "RGBA") or "transparency" in src.info else src.convert("RGB")
    for w in sorted(todo, reverse=True):
        im = base if base.width <= w else base.resize((w, round(base.height * w / base.width)), Image.LANCZOS)
        f = _img_path(u, w)
        tmp = f.with_suffix(".tmp")
        im.save(tmp, "WEBP", quality=84, method=4)
        tmp.replace(f)                                    # a half-written file is never served


def _img_file(u: str, w: int):
    """Downscaled WebP of a known manufacturer image, cached on disk."""
    f = _img_path(u, w)
    if not f.exists():
        _render_images(u, [w])
    return f


@app.get("/models/{brand}/{name}")
def model_cutout(brand: str, name: str):
    """Model cut-outs kept with the data (data/model_images/<brand>/<file>), the same paths the website serves."""
    from fastapi.responses import FileResponse
    if not re.fullmatch(r"[a-z0-9_-]+", brand) or not re.fullmatch(r"[A-Za-z0-9_.-]+\.(?:png|jpe?g|webp)", name):
        raise HTTPException(404, "Unknown image")
    f = db.ROOT / "data" / "model_images" / brand / name
    if not f.is_file():
        raise HTTPException(404, "Unknown image")
    return FileResponse(f, headers={"Cache-Control": "public, max-age=604800"})


@app.get("/api/img")
def img(u: str, w: int = Query(default=640, ge=64, le=1600)):
    """Serves a manufacturer image we already store (models / feature photos), downscaled to WebP and cached on disk.
    Avoids huge originals (1-2 MB PNGs) and hotlink / referrer blocks. Only URLs present in our DB are allowed."""
    from fastapi.responses import Response
    known = (one("SELECT 1 AS x FROM models WHERE image_url = ?", (u,)) or one("SELECT 1 AS x FROM variants WHERE image_url = ?", (u,))
             or one("SELECT 1 AS x FROM feature_images WHERE image_url = ?", (u,)))
    if not known:
        try:                                      # model photo galleries (gallery_sync)
            known = one("SELECT 1 AS x FROM model_gallery WHERE url = ?", (u,))
        except Exception:
            known = None
    if not known:
        raise HTTPException(404, "Unknown image")
    if u.startswith("/models/"):                     # a local cut-out: downscale it like any other image
        local = db.ROOT / "data" / "model_images" / u[len("/models/"):]
        if not local.is_file():
            raise HTTPException(404, "Unknown image")
        import io
        from PIL import Image
        im = Image.open(local); im.thumbnail((w, w * 2))
        buf = io.BytesIO(); im.save(buf, "WEBP", quality=82)
        return Response(buf.getvalue(), media_type="image/webp", headers={"Cache-Control": "public, max-age=604800"})
    try:
        f = _img_file(u, w)
    except Exception as e:
        raise HTTPException(502, f"Image unavailable ({type(e).__name__})")
    return Response(f.read_bytes(), media_type="image/webp", headers={"Cache-Control": "public, max-age=604800"})


def _warm_images() -> None:
    """Pre-render every model / variant / feature photo at the sizes the site and app use, so visitors get the cached
    copy (~0.3 s) instead of a 3-6 s fetch from the manufacturer. Deliberately gentle for a small server: one image at a
    time, each downloaded once for all its sizes, with a pause between images, starting after the server is up."""
    import threading, time as _t
    def run():
        _t.sleep(45)
        jobs: dict[str, set[int]] = {}
        for r in q("SELECT DISTINCT image_url FROM models WHERE active = 1 AND image_url LIKE 'http%'"):
            jobs.setdefault(r["image_url"], set()).update((480, 800, 1200))
        for r in q("""SELECT DISTINCT v.image_url FROM variants v JOIN models m ON m.id = v.model_id
                      WHERE v.active = 1 AND m.active = 1 AND v.image_url LIKE 'http%'"""):
            jobs.setdefault(r["image_url"], set()).add(1200)
        for r in q("SELECT DISTINCT image_url FROM feature_images WHERE image_url LIKE 'http%'"):
            jobs.setdefault(r["image_url"], set()).update((640, 1200))
        done = 0
        for u, widths in jobs.items():
            try:
                if any(not _img_path(u, w).exists() for w in widths):
                    _render_images(u, widths)
                    done += 1
                    _t.sleep(0.5)
            except Exception:
                pass                                       # unreachable image: the endpoint retries on demand
        logging.getLogger("onroad.img").info("image cache warmed: %d new images (%d known)", done, len(jobs))
    threading.Thread(target=run, name="onroad-img-warm", daemon=True).start()


if os.getenv("WARM_IMAGES", "1") == "1":
    _warm_images()


@app.get("/api/recommendations")
def recommendations(city: str = "Hyderabad", vehicle_type: str = "car", usage: str = "mixed", budget: int | None = None,
                    fuel: str | None = None, transmission: str | None = None, seats: int = 0, monthly_km: int = 1000,
                    home_charging: bool = False, priorities: str = "value,safety", limit: int = 6, body: str | None = None,
                    brands: str | None = None, budget_min: int | None = None):
    """Profile-based picks (onroad/recommender.py): every priced variant scored on the buyer's own on-road budget,
    seats, fuel / gearbox, usage, mileage, official crash ratings, equipment and sales rank. Best variant per model."""
    from .recommender import Profile, recommend
    usage = {"commute": "city", "family": "mixed", "performance": "highway"}.get(usage, usage)
    pr = [x.strip() for x in priorities.split(",") if x.strip()]
    if usage == "highway" and "performance" not in pr:
        pr.append("performance")
    prof = Profile(vehicle_type="bike" if vehicle_type in ("bike", "two_wheeler") else "car", city=city, budget=budget, usage=usage,
                   monthly_km=monthly_km, seats=seats, fuel=fuel if fuel and fuel != "any" else None,
                   transmission=transmission if transmission and transmission != "any" else None,
                   home_charging=home_charging, priorities=pr or ["value"], body_types=(body or "").split(","),
                   brands=(brands or "").split(","), budget_min=budget_min)
    out = []
    for r in recommend(prof, max(1, min(limit, 24))):
        brand_slug, slug = r["model_id"].split("/", 1)
        m = one("SELECT body_type FROM models WHERE id = ?", (r["model_id"],)) or {}
        out.append({"id": r["model_id"], "name": r["model"], "slug": slug, "brand_slug": brand_slug, "brand": r["brand"],
                    "body_type": m.get("body_type"), "image_url": r["image_url"], "logo": _logo_url(brand_slug),
                    "from_inr": r["onroad_inr"], "to_inr": r["onroad_inr"], "fuels": r["fuel"], "variants": 1,
                    "match_score": r["score"], "reasons": r["reasons"], "warnings": r.get("warnings", []), "variant": __import__("onroad.names", fromlist=["pretty"]).pretty(r["brand"], r["model"], r["variant"]), "variant_id": r["variant_id"],
                    "transmission": r["transmission"], "crash_stars": r["crash_stars"], "efficiency": r["efficiency"],
                    "pool": r["pool"]})
    return out


class DealerReviewIn(BaseModel):
    dealer_id: str
    rating: int = Field(ge=1, le=5)
    price_honesty: int | None = Field(default=None, ge=1, le=5)      # quoted price matched the final bill
    no_forced_addons: bool | None = None                              # no pressure for accessories / insurance / handling
    delivery_on_time: bool | None = None
    visit: str = Field(default="purchase", pattern="^(purchase|enquiry|service)$")
    text: str = Field(default="", max_length=1200)


@app.post("/api/dealer-reviews")
def add_dealer_review(body: DealerReviewIn, acc: dict = Depends(account)):
    """One review per buyer per showroom (editing replaces it). Free, first-party data; no rating is ever invented."""
    if not one("SELECT 1 AS x FROM dealers WHERE id = ?", (body.dealer_id,)):
        raise HTTPException(404, "Unknown showroom")
    with closing(db.connect()) as conn, conn:
        conn.execute("""INSERT OR REPLACE INTO dealer_reviews (dealer_id, account_id, rating, price_honesty, no_forced_addons,
                        delivery_on_time, visit, text) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                     (body.dealer_id, acc["id"], body.rating, body.price_honesty, body.no_forced_addons,
                      body.delivery_on_time, body.visit, body.text.strip()))
    return {"ok": True}


@app.get("/api/dealer-reviews")
def dealer_reviews(dealer_id: str):
    """OnRoad buyers' reviews of a showroom (+ live Google reviews when GOOGLE_PLACES_KEY is set)."""
    from . import places
    own = q("""SELECT r.rating, r.price_honesty, r.no_forced_addons, r.delivery_on_time, r.visit, r.text, r.created, a.name
               FROM dealer_reviews r JOIN accounts a ON a.id = r.account_id WHERE r.dealer_id = ? ORDER BY r.created DESC LIMIT 50""", (dealer_id,))
    for r in own:
        r["name"] = (r["name"] or "Buyer").split()[0]                  # first name only
    return {"onroad": own, "google": places.reviews(dealer_id) if places.key() else None}


@app.get("/api/cities")
def cities():
    states = onroad_calc.rules().get("states") or {}
    have = {r["city"].lower(): r["n"] for r in q("SELECT city, COUNT(DISTINCT variant_id) AS n FROM prices GROUP BY city")}
    out = []
    for name, (lat, lng) in CITIES.items():
        st = onroad_calc.STATE_OF_CITY.get(name.lower(), "TS")
        sr = states.get(st) or {}
        out.append({"name": name, "state": st, "state_name": sr.get("name", st), "tax_rules": sr.get("coverage", "not_found"),
                    "city_prices": have.get(name.lower(), 0), "lat": lat, "lng": lng})
    return out


@app.get("/api/states")
def states():
    r = onroad_calc.rules()
    return [{"code": k, "name": v.get("name", k), "coverage": v.get("coverage")} for k, v in sorted((r.get("states") or {}).items(),
            key=lambda kv: kv[1].get("name", kv[0]))]


# names buyers still search for, now sold as their successor (the maker renamed or replaced the model)
SUCCESSORS = {"xuv700": ("mahindra/xuv-7xo", "XUV700"), "xuv300": ("mahindra/xuv-3xo", "XUV300"),
              "xuv400ev": ("mahindra/xuv400", "XUV400 EV")}


@app.get("/api/search")
def search(text: str = Query(default="", alias="q"), city: str = "Hyderabad"):
    raw = (text or "").strip().lower()
    flat = re.sub(r"[^a-z0-9]", "", raw)                    # "xuv 700", "XUV-700", "xuv700" are one search
    if len(flat) < 2:
        return []
    rows = q("""SELECT m.id, m.name, m.brand_slug, b.name AS brand, m.body_type, m.image_url,
                       (SELECT MIN(p.ex_showroom_inr) FROM variants v JOIN prices p ON p.variant_id = v.id WHERE v.model_id = m.id AND v.active = 1) AS from_inr
                FROM models m JOIN brands b ON b.slug = m.brand_slug
                WHERE m.active = 1 AND (lower(m.name) LIKE ? OR lower(b.name) LIKE ? OR lower(b.name || ' ' || m.name) LIKE ?
                      OR replace(replace(replace(lower(b.name || m.name), ' ', ''), '-', ''), '.', '') LIKE ?
                      OR replace(replace(replace(lower(m.name), ' ', ''), '-', ''), '.', '') LIKE ?)
                ORDER BY from_inr LIMIT 20""", (f"%{raw}%", f"%{raw}%", f"%{raw}%", f"%{flat}%", f"%{flat}%"))
    for old, (mid, label) in SUCCESSORS.items():
        if flat and (old.startswith(flat) or flat.startswith(old)) and len(flat) >= 4 and not any(r["id"] == mid for r in rows):
            hit = q("""SELECT m.id, m.name, m.brand_slug, b.name AS brand, m.body_type, m.image_url,
                              (SELECT MIN(p.ex_showroom_inr) FROM variants v JOIN prices p ON p.variant_id = v.id WHERE v.model_id = m.id AND v.active = 1) AS from_inr
                       FROM models m JOIN brands b ON b.slug = m.brand_slug WHERE m.id = ? AND m.active = 1""", (mid,))
            for h in hit:
                h["note"] = f"Successor to the {label}"
            rows = hit + rows
    return rows



# Price bands as Indian buyers think about them (ex-showroom, starting price of the model)
PRICE_BANDS = [
    {"id": "budget", "label": "Budget", "hint": "Under ₹6 lakh", "min": 0, "max": 600_000},
    {"id": "middle", "label": "Middle class", "hint": "₹6–12 lakh", "min": 600_000, "max": 1_200_000},
    {"id": "upper-middle", "label": "Upper middle", "hint": "₹12–20 lakh", "min": 1_200_000, "max": 2_000_000},
    {"id": "premium", "label": "Premium", "hint": "₹20–40 lakh", "min": 2_000_000, "max": 4_000_000},
    {"id": "luxury", "label": "Luxury", "hint": "₹40 lakh – 1 crore", "min": 4_000_000, "max": 10_000_000},
    {"id": "ultra", "label": "Ultra luxury", "hint": "Above ₹1 crore", "min": 10_000_000, "max": None},
]


def _band(price):
    if not price:
        return None
    return next((b["id"] for b in PRICE_BANDS if price >= b["min"] and (b["max"] is None or price < b["max"])), None)


def _popularity() -> dict:
    """Six-month sales by (brand, model) from data/research/popularity.json (manufacturer/SIAM/FADA figures)."""
    f = db.ROOT / "data" / "research" / "popularity.json"
    if not f.exists():
        return {}
    import json as _json
    data = _json.loads(f.read_text(encoding="utf-8"))
    norm = lambda t: re.sub(r"[^a-z0-9]", "", (t or "").lower())
    return {(norm(m["brand"]), norm(m["model"])): m for m in data.get("models", [])}


def _pop_for(pop: dict, brand: str, name: str, raw: str = ""):
    """Exact (brand, model) match, else a family / prefix match ('Pulsar' ranks the Pulsar range, 'Innova Hycross' ~
    'Innova (Hycross + Crysta)'). An electric offshoot never inherits a petrol family's rank ('Activa e:' != 'Activa')."""
    if (brand, name) in pop:
        return pop[(brand, name)]
    electric = re.search(r"\be:|\bev\b|\.ev\b|electric|\be-", (raw or "").lower())
    for (b, m), row in pop.items():
        if b == brand and len(min(m, name, key=len)) >= 4 and (name.startswith(m) or m.startswith(name)):
            if electric and not re.search(r"ev|electric|iqube|chetak|rizta|vida", m):
                continue
            return row
    return None


@app.get("/api/bands")
def bands():
    return PRICE_BANDS

@app.get("/api/explore")
def explore(city: str = "Hyderabad", body: str | None = None, fuel: str | None = None, max_inr: int | None = None,
            min_inr: int | None = None, brand: str | None = None, band: str | None = None, sort: str = "popular",
            vehicle_type: str | None = None):
    cte, cp = _pick(city)
    # a model's vehicle type is its brand's (models.vehicle_type can lag behind when ingest adds new models)
    vt_cond = "AND coalesce(b.vehicle_type, 'car') = ?" if vehicle_type else ""
    vt_params = (vehicle_type,) if vehicle_type else ()
    rows = q(f"""WITH {cte} SELECT m.id, m.name, m.slug, m.brand_slug, b.name AS brand, b.segment, m.body_type, m.image_url,
                       m.vehicle_type,
                       MIN(p.ex_showroom_inr) AS from_inr, MAX(p.ex_showroom_inr) AS to_inr,
                       GROUP_CONCAT(DISTINCT v.fuel) AS fuels, GROUP_CONCAT(DISTINCT v.transmission) AS transmissions, COUNT(DISTINCT v.id) AS variants,
                       (SELECT COUNT(*) FROM offers o WHERE o.brand_slug = m.brand_slug AND o.active = 1
                          AND (o.model_name IS NULL OR lower(o.model_name) = lower(m.name))) AS offers
                FROM models m JOIN brands b ON b.slug = m.brand_slug
                LEFT JOIN variants v ON v.model_id = m.id AND v.active = 1
                LEFT JOIN pick p ON p.variant_id = v.id
                WHERE m.active = 1 {vt_cond} GROUP BY m.id""", (*cp, *vt_params))
    pop = _popularity()
    norm = lambda t: re.sub(r"[^a-z0-9]", "", (t or "").lower())
    for r in rows:
        p = _pop_for(pop, norm(r["brand"]), norm(r["name"]), r["name"])
        r["six_month_units"] = p["six_month_units"] if p else None
        r["sales_rank"] = p["rank"] if p else None
    # A published sales rank covers a model family ("Splendor" = Splendor+, Splendor+ Xtec, ...). Show it once, on the
    # family's base model (cheapest, then shortest name), not on every version; decided before filtering so it never moves.
    holders: dict[tuple, dict] = {}
    for r in rows:
        if r["sales_rank"] is not None:
            k = (r["brand_slug"], r["sales_rank"])
            score = lambda x: (x["from_inr"] is None, x["from_inr"] or 0, len(x["name"]))
            if k not in holders or score(r) < score(holders[k]):
                holders[k] = r
    for r in rows:
        if r["sales_rank"] is not None and holders[(r["brand_slug"], r["sales_rank"])] is not r:
            r["sales_rank"] = r["six_month_units"] = None
    out = []
    for r in rows:
        r["band"] = _band(r["from_inr"])
        if band and r["band"] != band:
            continue
        if body and (r["body_type"] or "").lower() != body.lower():
            continue
        if fuel and fuel.lower() not in (r["fuels"] or "").lower():
            continue
        if brand and r["brand_slug"] != brand:
            continue
        if max_inr and (r["from_inr"] or 10**12) > max_inr:
            continue
        if min_inr and (r["to_inr"] or 0) < min_inr:
            continue
        r["logo"] = _logo_url(r['brand_slug'])
        out.append(r)
    keys = {"price": lambda r: (r["from_inr"] is None, r["from_inr"] or 0),
            "offers": lambda r: (-(r["offers"] or 0),),
            "popular": lambda r: (r["sales_rank"] is None, r["sales_rank"] or 0, r["from_inr"] or 0)}
    out.sort(key=keys.get(sort, keys["popular"]))
    return out


@app.get("/api/compare")
def compare(ids: str, city: str = "Hyderabad"):
    out = []
    for vid in ids.split(",")[:4]:
        v = one("""SELECT v.*, m.name AS model, m.image_url, b.name AS brand, m.brand_slug FROM variants v JOIN models m ON m.id = v.model_id
                   JOIN brands b ON b.slug = m.brand_slug WHERE v.id = ?""", (vid,))
        if v:
            try:
                v["onroad"] = onroad(vid, city)
            except HTTPException:
                v["onroad"] = None
            out.append(v)
    return out


# ── Buyers: saved cars, quote requests ──────────────────────────────────────────────────────────────────
class SaveIn(BaseModel):
    variant_id: str
    city: str = "Hyderabad"
    target_inr: int | None = None


@app.get("/api/me/saved")
def saved(acc: dict = Depends(account)):
    rows = q("""SELECT s.*, v.name AS variant, m.name AS model, m.id AS model_id, b.name AS brand, m.image_url FROM saved_cars s
                JOIN variants v ON v.id = s.variant_id JOIN models m ON m.id = v.model_id JOIN brands b ON b.slug = m.brand_slug
                WHERE s.account_id = ?""", (acc["id"],))
    for r in rows:
        hist = q("SELECT ex_showroom_inr, fetched_at FROM prices WHERE variant_id = ? ORDER BY fetched_at", (r["variant_id"],))
        r["history"] = hist
        r["current_inr"] = hist[-1]["ex_showroom_inr"] if hist else None
        r["change_inr"] = (hist[-1]["ex_showroom_inr"] - hist[-2]["ex_showroom_inr"]) if len(hist) > 1 else 0
    return rows


@app.post("/api/me/saved")
def save(body: SaveIn, acc: dict = Depends(account)):
    with closing(db.connect()) as conn, conn:
        conn.execute("INSERT OR REPLACE INTO saved_cars (account_id, variant_id, city, target_inr) VALUES (?, ?, ?, ?)",
                     (acc["id"], body.variant_id, body.city, body.target_inr))
    return {"ok": True}


@app.delete("/api/me/saved")
def unsave(variant_id: str, city: str = "Hyderabad", acc: dict = Depends(account)):
    with closing(db.connect()) as conn, conn:
        conn.execute("DELETE FROM saved_cars WHERE account_id = ? AND variant_id = ? AND city = ?", (acc["id"], variant_id, city))
    return {"ok": True}


class QuoteRequestIn(BaseModel):
    variant_id: str
    city: str = "Hyderabad"
    pincode: str | None = Field(default=None, max_length=6)
    colour: str | None = Field(default=None, max_length=60)
    finance: bool = False
    exchange: bool = False
    purchase_by: str | None = Field(default=None, max_length=30)
    note: str | None = Field(default=None, max_length=500)
    consent: bool = False             # buyer agrees that nearby dealers of this brand see the request


@app.post("/api/quotes/request")
def request_quotes(body: QuoteRequestIn, acc: dict = Depends(role("buyer", "admin"))):
    if not body.consent:
        raise HTTPException(400, "Please agree to share your request with nearby dealers.")
    if not one("SELECT 1 AS x FROM variants WHERE id = ?", (body.variant_id,)):
        raise HTTPException(404, "Unknown variant")
    with closing(db.connect()) as conn, conn:
        rid = conn.execute("""INSERT INTO quote_requests (account_id, variant_id, city, pincode, colour, finance, exchange, purchase_by, note)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                           (acc["id"], body.variant_id, body.city, body.pincode, body.colour, int(body.finance), int(body.exchange),
                            body.purchase_by, body.note)).lastrowid
    brand_slug = body.variant_id.split("/")[0]
    n = one("SELECT COUNT(*) AS n FROM dealers WHERE brand_slug = ? AND lower(city) = lower(?) AND active = 1", (brand_slug, body.city))["n"]
    claimed = one("SELECT COUNT(*) AS n FROM dealers WHERE brand_slug = ? AND lower(city) = lower(?) AND claimed_by IS NOT NULL",
                  (brand_slug, body.city))["n"]
    return {"id": rid, "dealers_in_city": n, "dealers_on_onroad": claimed}


@app.get("/api/me/quotes")
def my_quotes(acc: dict = Depends(account)):
    reqs = q("""SELECT r.*, v.name AS variant, m.name AS model, b.name AS brand FROM quote_requests r JOIN variants v ON v.id = r.variant_id
                JOIN models m ON m.id = v.model_id JOIN brands b ON b.slug = m.brand_slug WHERE r.account_id = ? ORDER BY r.created DESC""",
             (acc["id"],))
    for r in reqs:
        r["quotes"] = q("""SELECT qt.*, d.name AS dealer, d.address, d.phone, d.lat, d.lng FROM quotes qt JOIN dealers d ON d.id = qt.dealer_id
                           WHERE qt.request_id = ? ORDER BY qt.on_road_inr""", (r["id"],))
        cte, cp = _pick(r["city"])
        p = one(f"WITH {cte} SELECT ex_showroom_inr FROM pick WHERE variant_id = ?", (*cp, r["variant_id"]))
        r["fair_onroad_inr"] = onroad_calc.estimate(p["ex_showroom_inr"], city=r["city"]).total_inr if p else None
    return reqs


# ── Dealers ─────────────────────────────────────────────────────────────────────────────────────────────
class ClaimIn(BaseModel):
    dealer_id: str
    designation: str = Field(max_length=80)


@app.post("/api/dealer/claim")
def claim(body: ClaimIn, acc: dict = Depends(role("dealer"))):
    d = one("SELECT * FROM dealers WHERE id = ?", (body.dealer_id,))
    if not d:
        raise HTTPException(404, "Unknown dealership")
    if d["claimed_by"]:
        raise HTTPException(400, "This dealership is already managed on OnRoad.")
    with closing(db.connect()) as conn, conn:
        conn.execute("INSERT INTO outreach (dealer_id, channel, recipient, subject, body, status) VALUES (?, 'claim', ?, ?, ?, 'claim_pending')",
                     (d["id"], acc["email"], f"Claim: {d['name']}", f"{acc['name']} ({body.designation}) requests access to {d['name']}"))
    return {"ok": True, "note": "We verify every claim with the dealership's published phone or email before granting access."}


def _my_dealers(acc: dict) -> list[dict]:
    return q("SELECT * FROM dealers WHERE claimed_by = ?", (acc["id"],))


@app.get("/api/dealer/requests")
def dealer_requests(acc: dict = Depends(role("dealer"))):
    mine = _my_dealers(acc)
    out = []
    for d in mine:
        for r in q("""SELECT r.id, r.variant_id, r.city, r.pincode, r.colour, r.finance, r.exchange, r.purchase_by, r.note, r.created,
                             v.name AS variant, m.name AS model,
                             (SELECT COUNT(*) FROM quotes qt WHERE qt.request_id = r.id AND qt.dealer_id = ?) AS answered
                      FROM quote_requests r JOIN variants v ON v.id = r.variant_id JOIN models m ON m.id = v.model_id
                      WHERE m.brand_slug = ? AND lower(r.city) = lower(?) AND r.status = 'open' ORDER BY r.created DESC""",
                   (d["id"], d["brand_slug"], d["city"])):
            out.append({**r, "dealer_id": d["id"], "dealer": d["name"]})   # buyer identity stays private until they accept
    return out


class QuoteIn(BaseModel):
    request_id: int
    dealer_id: str
    ex_showroom_inr: int = Field(gt=0)
    road_tax_inr: int = Field(ge=0)
    registration_inr: int = Field(ge=0)
    insurance_inr: int = Field(ge=0)
    accessories_inr: int = Field(default=0, ge=0)
    other_inr: int = Field(default=0, ge=0)
    discount_inr: int = Field(default=0, ge=0)
    waiting_weeks: int | None = Field(default=None, ge=0, le=104)
    valid_until: str | None = None
    note: str | None = Field(default=None, max_length=500)


class PushTokenIn(BaseModel):
    token: str = Field(min_length=20, max_length=4096)
    platform: str = "android"


@app.post("/api/me/push-token")
def push_token(body: PushTokenIn, request: Request):
    """A phone's FCM token. Signed in: tied to the account (price drops on saved cars, dealer quotes)."""
    uid = _uid(request.cookies.get(COOKIE))
    with closing(db.connect()) as conn, conn:
        conn.execute("""INSERT INTO push_tokens (token, account_id, platform, last_seen) VALUES (?, ?, ?, datetime('now'))
                        ON CONFLICT(token) DO UPDATE SET account_id = COALESCE(excluded.account_id, push_tokens.account_id),
                        platform = excluded.platform, last_seen = excluded.last_seen""", (body.token, uid, body.platform[:20]))
    return {"ok": True}


@app.post("/api/dealer/quotes")
def submit_quote(body: QuoteIn, acc: dict = Depends(role("dealer"))):
    if body.dealer_id not in {d["id"] for d in _my_dealers(acc)}:
        raise HTTPException(403, "You can quote only for your own dealership.")
    total = (body.ex_showroom_inr + body.road_tax_inr + body.registration_inr + body.insurance_inr + body.accessories_inr
             + body.other_inr - body.discount_inr)
    with closing(db.connect()) as conn, conn:
        conn.execute("""INSERT INTO quotes (request_id, dealer_id, ex_showroom_inr, road_tax_inr, registration_inr, insurance_inr,
                            accessories_inr, other_inr, discount_inr, on_road_inr, waiting_weeks, valid_until, note)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                     (body.request_id, body.dealer_id, body.ex_showroom_inr, body.road_tax_inr, body.registration_inr, body.insurance_inr,
                      body.accessories_inr, body.other_inr, body.discount_inr, total, body.waiting_weeks, body.valid_until, body.note))
    try:
        from . import push
        dn = one("SELECT name FROM dealers WHERE id = ?", (body.dealer_id,))
        push.quote_received(body.request_id, (dn or {}).get("name") or "A dealer", total)
    except Exception:
        pass
    return {"ok": True, "on_road_inr": total}


class DealerOfferIn(BaseModel):
    dealer_id: str
    model_name: str | None = None
    title: str = Field(max_length=120)
    amount_inr: int | None = Field(default=None, ge=0)
    details: str = Field(default="", max_length=600)
    valid_until: str | None = None


@app.post("/api/dealer/offers")
def dealer_offer(body: DealerOfferIn, acc: dict = Depends(role("dealer"))):
    d = next((d for d in _my_dealers(acc) if d["id"] == body.dealer_id), None)
    if not d:
        raise HTTPException(403, "You can post offers only for your own dealership.")
    with closing(db.connect()) as conn, conn:
        conn.execute("""INSERT INTO offers (brand_slug, model_name, title, amount_inr, details, valid_until, city, source, source_url, fetched_at, dealer_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'dealer', NULL, datetime('now'), ?)""",
                     (d["brand_slug"], body.model_name, body.title, body.amount_inr, body.details, body.valid_until, d["city"], d["id"]))
    return {"ok": True}


@app.get("/api/dealers/near")
def dealers_near(lat: float, lng: float, brand: str | None = None, vehicle_type: str | None = None, limit: int = Query(30, le=100)):
    """Nearest official showrooms to the user's location (any brand, or one brand), with distance in km."""
    cond, params = ["d.active = 1", "d.lat IS NOT NULL", "d.lng IS NOT NULL",
                    "d.lat BETWEEN ? AND ?", "d.lng BETWEEN ? AND ?"], [lat - 3, lat + 3, lng - 3, lng + 3]
    if brand:
        cond.append("d.brand_slug = ?"); params.append(brand)
    if vehicle_type:
        cond.append("b.vehicle_type = ?"); params.append(vehicle_type)
    rows = q(f"""SELECT d.id, d.brand_slug, b.name AS brand_name, d.name, d.address, d.city, d.state, d.pincode, d.phone, d.lat, d.lng, d.kind,
                        (SELECT round(avg(r.rating), 1) FROM dealer_reviews r WHERE r.dealer_id = d.id) AS rating,
                        (SELECT count(*) FROM dealer_reviews r WHERE r.dealer_id = d.id) AS rating_count
                 FROM dealers d JOIN brands b ON b.slug = d.brand_slug WHERE {' AND '.join(cond)}""", tuple(params))
    for r in rows:
        r["distance_km"] = round(_km(lat, lng, r["lat"], r["lng"]), 1)
    rows.sort(key=lambda r: r["distance_km"])
    rows = rows[:limit]
    _google(rows)
    return rows


@app.get("/api/dealers/search")
def dealer_search(brand: str, city: str | None = None, text: str = ""):
    text_pattern = f"%{(text or '').strip().lower()}%"
    city_norm = (city or "").strip().lower()
    
    if city_norm and city_norm != "all":
        st_city = onroad_calc.STATE_OF_CITY.get(city_norm)
        # metro aliases only within the same state (Gurugram is Haryana: Delhi / Noida showrooms register in other states)
        aliases = [a for a in METRO_CLUSTERS.get(city_norm, [city_norm])
                   if onroad_calc.STATE_OF_CITY.get(a, st_city) == st_city] or [city_norm]
        placeholders = ",".join("?" for _ in aliases)
        rows = q(f"""SELECT id, name, address, city, pincode, phone, lat, lng, claimed_by IS NOT NULL AS on_onroad FROM dealers
                    WHERE brand_slug = ? AND lower(city) IN ({placeholders})
                    AND (lower(name || ' ' || address || ' ' || city) LIKE ?) ORDER BY name LIMIT 50""",
                 (brand, *aliases, text_pattern))
        if rows:
            return rows
            
    # Search brand dealerships by text matching name, address, or city across all locations
    return q("""SELECT id, name, address, city, pincode, phone, lat, lng, claimed_by IS NOT NULL AS on_onroad FROM dealers
                WHERE brand_slug = ? AND (lower(name || ' ' || address || ' ' || city) LIKE ?)
                ORDER BY name LIMIT 50""",
             (brand, text_pattern))


def _link_offer_models(rows: list[dict]) -> None:
    """Offers name cars loosely ("New City", "The new Taigun", or only in the title). Link each to the model's own page
    and photo: same brand, name equal after dropping "new"/"the", else the longest model name found in the title."""
    unmatched = [r for r in rows if not r.get("model_image")]
    if not unmatched:
        return
    nm = lambda t: re.sub(r"[^a-z0-9]", "", re.sub(r"(the|new|all)", "", (t or "").lower()))
    cat: dict[str, list[dict]] = {}
    for m in q("SELECT id, brand_slug, name, image_url FROM models WHERE active = 1 AND image_url IS NOT NULL AND image_url != ''"):
        cat.setdefault(m["brand_slug"], []).append(m)
    for r in unmatched:
        models = cat.get(r["brand_slug"], [])
        key = nm(r.get("model_name"))
        hit = next((m for m in models if key and nm(m["name"]) == key), None)
        if not hit:
            text = nm((r.get("model_name") or "") + " " + (r.get("title") or ""))
            found = [m for m in models if len(nm(m["name"])) >= 3 and nm(m["name"]) in text]
            hit = max(found, key=lambda m: len(nm(m["name"])), default=None)
        if hit:
            r["model_image"], r["model_id"] = hit["image_url"], hit["id"]
            r["model_name"] = r.get("model_name") or hit["name"]


@app.get("/api/offers")
def offers(city: str = "Hyderabad", brand: str | None = None, model: str | None = None, limit: int = 50):
    """Live automotive offers: festive promotions, launch benefits, exchange bonuses, dealer discounts."""
    where_clauses = [LIVE]
    params: list = [city]
    if brand:
        where_clauses.append("o.brand_slug = ?")
        params.append(brand)
    if model:
        where_clauses.append("(o.model_name IS NULL OR o.model_name = '' OR lower(o.model_name) = lower(?))")
        params.append(model)
        
    where = " AND ".join(where_clauses)
    rows = q(f"""SELECT o.*, b.name AS brand_name, m.image_url AS model_image, m.id AS model_id
                 FROM offers o
                 JOIN brands b ON b.slug = o.brand_slug
                 LEFT JOIN models m ON m.brand_slug = o.brand_slug AND lower(m.name) = lower(o.model_name)
                 WHERE {where}
                 GROUP BY o.brand_slug, ifnull(o.model_name, ''), o.title, ifnull(o.amount_inr, 0)
                 ORDER BY o.amount_inr IS NULL, o.amount_inr DESC LIMIT ?""", (*params, limit))
                 
    # If city has few specific offers and not filtering by specific model, include national/brand offers
    if len(rows) < 8 and not model:
        extra_params: list = []
        brand_cond = ""
        if brand:
            brand_cond = "AND o.brand_slug = ?"
            extra_params.append(brand)
        extra_params.append(limit - len(rows))
        
        national_rows = q(f"""SELECT o.*, b.name AS brand_name, m.image_url AS model_image, m.id AS model_id
                              FROM offers o
                              JOIN brands b ON b.slug = o.brand_slug
                              LEFT JOIN models m ON m.brand_slug = o.brand_slug AND lower(m.name) = lower(o.model_name)
                              WHERE o.active = 1 AND (o.valid_until IS NULL OR o.valid_until >= date('now', 'localtime'))
                              AND (o.city IS NULL OR o.city = '' OR o.city = 'National')
                              {brand_cond}
                              GROUP BY o.brand_slug, ifnull(o.model_name, ''), o.title, ifnull(o.amount_inr, 0)
                              ORDER BY o.amount_inr IS NULL, o.amount_inr DESC LIMIT ?""",
                          tuple(extra_params))
        seen_ids = {r["id"] for r in rows}
        for nr in national_rows:
            if nr["id"] not in seen_ids:
                rows.append(nr)

    _link_offer_models(rows)
    today = __import__("datetime").date.today()
    for r in rows:
        r["days_left"] = ((__import__("datetime").date.fromisoformat(r["valid_until"]) - today).days
                          if r.get("valid_until") else None)
        title_lower = (r.get("title") or "").lower() + " " + (r.get("details") or "").lower()
        if "festive" in title_lower or "diwali" in title_lower or "navratri" in title_lower:
            r["category"] = "Festive Special"
        elif "launch" in title_lower or "introductory" in title_lower or "opening" in title_lower or "pioneer" in title_lower:
            r["category"] = "Opening Offer"
        elif "exchange" in title_lower or "upgrade" in title_lower:
            r["category"] = "Exchange Bonus"
        elif "interest" in title_lower or "roi" in title_lower or "finance" in title_lower:
            r["category"] = "Low EMI / Finance"
        elif "corporate" in title_lower:
            r["category"] = "Corporate Benefit"
        else:
            r["category"] = "Manufacturer Discount"
            
    return rows


@app.get("/api/campaigns")
def campaigns(city: str = "Hyderabad"):
    """Banner slides built only from live manufacturer offers (each with its source page and validity)."""
    rows = q(f"""SELECT o.*, b.name AS brand_name FROM offers o JOIN brands b ON b.slug = o.brand_slug
                 WHERE {LIVE} AND o.source = 'brand_site' AND o.amount_inr IS NOT NULL ORDER BY o.amount_inr DESC LIMIT 40""", (city,))
    out, seen = [], set()
    for r in rows:
        if r["brand_slug"] in seen:
            continue
        seen.add(r["brand_slug"])
        out.append({"id": f"offer-{r['id']}", "tag": "MANUFACTURER OFFER",
                    "title": f"{r['brand_name']} {r['model_name'] or 'all models'}: {r['title']}",
                    "highlight": f"{'Up to ' if 'up to' in (r['title'] or '').lower() else ''}₹{r['amount_inr']:,}",
                    "description": (r.get("conditions") or r.get("details") or "")[:220], "valid_until": r.get("valid_until"),
                    "cta_text": "See this offer", "cta_link": f"/cars?brand={r['brand_slug']}", "source_url": r.get("source_url"),
                    "disclaimer": f"From {r['brand_name']}'s official website" + (f", valid until {r['valid_until']}" if r.get("valid_until") else "")
                                  + ". Final benefits are confirmed by the dealer at booking."})
        if len(out) == 4:
            break
    return out

@app.get("/api/opinions")
def get_opinions(model_id: str | None = None, vehicle_type: str | None = None, limit: int = 12):
    """
    Verified Customer Opinions and Real-World Owner Intelligence.
    Authentic mileage benchmarks, annual maintenance costs, and owner satisfaction.
    """
    where_clauses = []
    params = []
    if model_id:
        where_clauses.append("model_id = ?")
        params.append(model_id)
    if vehicle_type:
        where_clauses.append("vehicle_type = ?")
        params.append(vehicle_type)
    where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    return q(f"SELECT * FROM opinions {where} ORDER BY rating DESC, created_at DESC LIMIT ?", (*params, limit))


class OpinionIn(BaseModel):
    model_id: str
    model_name: str
    vehicle_type: str = "car"
    author_name: str
    city: str
    rating: float = 5.0
    ownership_period: str
    real_mileage: str
    annual_service_cost: str
    pros: str
    cons: str
    verdict: str


@app.post("/api/opinions")
def create_opinion(op: OpinionIn, acc: dict = Depends(account)):
    """Submit a real-world owner review and mileage report."""
    with closing(db.connect()) as conn, conn:
        conn.execute("""
            INSERT INTO opinions (model_id, model_name, vehicle_type, author_name, city, rating,
                                  ownership_period, real_mileage, annual_service_cost, pros, cons, verdict, verified_buyer)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (op.model_id, op.model_name, op.vehicle_type, op.author_name, op.city, op.rating,
              op.ownership_period, op.real_mileage, op.annual_service_cost, op.pros, op.cons, op.verdict))
    return {"ok": True, "message": "Thank you! Your owner review has been published."}



# ── Admin ───────────────────────────────────────────────────────────────────────────────────────────────
@app.get("/api/admin/claims")
def claims(acc: dict = Depends(role("admin"))):
    return q("SELECT * FROM outreach WHERE status = 'claim_pending' ORDER BY created")


@app.post("/api/admin/claims/{claim_id}/approve")
def approve_claim(claim_id: int, acc: dict = Depends(role("admin"))):
    c = one("SELECT * FROM outreach WHERE id = ? AND status = 'claim_pending'", (claim_id,))
    if not c:
        raise HTTPException(404, "No such claim")
    dealer_acc = one("SELECT id FROM accounts WHERE email = ?", (c["recipient"],))
    with closing(db.connect()) as conn, conn:
        conn.execute("UPDATE dealers SET claimed_by = ? WHERE id = ?", (dealer_acc["id"], c["dealer_id"]))
        conn.execute("UPDATE outreach SET status = 'claim_approved', approved_by = ? WHERE id = ?", (acc["id"], claim_id))
    return {"ok": True}


@app.get("/api/admin/outreach")
def outreach(acc: dict = Depends(role("admin"))):
    return q("SELECT * FROM outreach WHERE channel != 'claim' ORDER BY created DESC")


@app.post("/api/admin/outreach/{oid}/approve")
def approve_outreach(oid: int, acc: dict = Depends(role("admin"))):
    with closing(db.connect()) as conn, conn:
        n = conn.execute("UPDATE outreach SET status = 'approved', approved_by = ? WHERE id = ? AND status = 'draft'", (acc["id"], oid)).rowcount
    if not n:
        raise HTTPException(404, "No such draft")
    return {"ok": True, "note": "Approved. Sending happens only from the outreach sender once SMTP is configured."}


@app.get("/api/meta")
def meta():
    r = onroad_calc.rules()
    last = one("SELECT finished FROM refresh_runs ORDER BY id DESC LIMIT 1")
    return {"rules_as_of": r.get("as_of"), "states_with_rules": sorted((r.get("states") or {}).keys()),
            "last_refresh": last["finished"] if last else None,
            "counts": one("""SELECT (SELECT COUNT(*) FROM brands) AS brands, (SELECT COUNT(*) FROM models WHERE active = 1) AS models,
                                    (SELECT COUNT(*) FROM variants WHERE active = 1) AS variants,
                                    (SELECT COUNT(*) FROM dealers WHERE active = 1) AS dealers,
                                    (SELECT COUNT(*) FROM offers WHERE active = 1) AS offers""")}


# ── Auto-Fetch & Live Brand Sync ─────────────────────────────────────────────────────────────
class QuickFetchCarIn(BaseModel):
    brand_slug: str
    model_name: str
    body_type: str | None = "SUV"
    fuel: str | None = "Petrol"
    transmission: str | None = "Automatic"
    engine_cc: int | None = None
    battery_kwh: float | None = None
    seats: int | None = 5
    ex_showroom_inr: int
    city: str = "Hyderabad"
    image_url: str | None = None
    source_url: str | None = None


@app.post("/api/sync/brand/{brand_slug}")
def sync_brand(brand_slug: str, city: str = "Hyderabad", acc: dict = Depends(role("admin"))):
    """Fetch all newly released models and updated variants directly from manufacturer adapter."""
    matching = [a for a in ingest.adapters([brand_slug])]
    if not matching:
        raise HTTPException(404, f"No manufacturer adapter found for brand '{brand_slug}'")
    try:
        res = ingest.refresh_brand(matching[0], city=city)
        return {"ok": True, "result": res}
    except Exception as e:
        raise HTTPException(500, f"Error refreshing brand {brand_slug}: {e}")


@app.post("/api/sync/all")
def sync_all(city: str = "Hyderabad", acc: dict = Depends(role("admin"))):
    """Refresh all brand adapters directly to fetch new releases across every brand."""
    try:
        results = ingest.run(None, city=city)
        return {"ok": True, "brands_refreshed": len(results), "summary": results}
    except Exception as e:
        raise HTTPException(500, f"Error during full brand refresh: {e}")


@app.get("/api/sync/status")
def sync_status():
    """Return latest sync logs, timestamp, and brand coverage statistics."""
    last_run = one("SELECT * FROM refresh_runs ORDER BY id DESC LIMIT 1")
    recent_models = q("SELECT id, brand_slug, name, body_type, image_url, first_seen FROM models WHERE active = 1 ORDER BY first_seen DESC LIMIT 10")
    total_models = one("SELECT COUNT(*) AS c FROM models WHERE active = 1")["c"]
    total_variants = one("SELECT COUNT(*) AS c FROM variants WHERE active = 1")["c"]
    return {
        "last_refresh": last_run,
        "total_active_models": total_models,
        "total_active_variants": total_variants,
        "latest_added_models": recent_models
    }


@app.get("/")
def root():
    return {"name": "OnRoad API", "status": "online", "docs": "/api/docs", "health": "/api/health"}


@app.get("/api/health")
def health():
    return {"ok": True}


# ── Self-refresh when deployed (Render etc.): set REFRESH_EVERY_HOURS, e.g. 6 ────────────────────────────
def _refresh_loop(hours: float) -> None:
    """Keeps prices, offers, dealers and specs current on a small server.

    Work is a queue of small steps (2 brands at a time for the launch city, then a few other cities, then bank rates,
    image fills and showroom ratings), spread evenly over `hours`. The position is stored in the database, so a restart
    resumes where it stopped instead of starting the whole refresh again, and no single step needs much memory."""
    import gc, threading, time as _t
    log = logging.getLogger("onroad.refresh")

    def steps() -> list[tuple[str, object]]:
        from . import ingest
        slugs = sorted(m.__module__.rsplit(".", 1)[-1] for m in ingest.adapters())
        out: list[tuple[str, object]] = [("brands", slugs[i:i + 2]) for i in range(0, len(slugs), 2)]
        out += [("city", c) for c in CITIES if c != "Hyderabad"]
        out += [("loans", None), ("images", None), ("places", None), ("crash", None), ("sales", None), ("photos", None),
                ("offerlinks", None)]
        return out

    def cursor(set_to: int | None = None) -> int:
        with closing(db.connect()) as conn, conn:
            conn.execute("CREATE TABLE IF NOT EXISTS app_state (k TEXT PRIMARY KEY, v TEXT)")
            if set_to is not None:
                conn.execute("INSERT OR REPLACE INTO app_state VALUES ('refresh_step', ?)", (str(set_to),))
                return set_to
            row = conn.execute("SELECT v FROM app_state WHERE k = 'refresh_step'").fetchone()
            return int(row[0]) if row else 0

    def run():
        from . import fill_images, ingest, loan_rates
        _t.sleep(90)                                          # let the server finish starting
        plan = steps()
        gap = max(60.0, hours * 3600 / max(1, len(plan)))     # one full pass every `hours`
        while True:
            i = cursor() % len(plan)
            kind, arg = plan[i]
            try:
                if kind == "brands":
                    ingest.run(arg, city="Hyderabad")           # prices, offers, dealers, specs for these brands
                elif kind == "city":
                    ingest.run(None, city=arg)                  # city prices and dealers, every brand
                elif kind == "loans":
                    loan_rates.refresh()
                elif kind == "images":
                    fill_images.run()
                    _warm_images()
                elif kind == "crash":
                    from . import crash_tests_sync
                    crash_tests_sync.sync()                     # new / revised Bharat NCAP ratings
                elif kind == "sales":
                    from . import popularity_sync
                    if _t.time() - popularity_sync.FILE.stat().st_mtime > 86400:   # new monthly figures: check daily
                        popularity_sync.run()
                elif kind == "places":
                    from . import places
                    places.match_and_rate(300)
                elif kind == "offerlinks":                     # offers whose own page is gone are over
                    from . import offer_links
                    offer_links.run()
                elif kind == "photos":                         # weekly: galleries for models short of pictures, drop dead links
                    mark = db.ROOT / "data" / ".photos_checked"
                    if not mark.exists() or _t.time() - mark.stat().st_mtime > 7 * 86400:
                        from . import gallery_sync, image_check
                        gallery_sync.run(); gallery_sync.run_fallback(); image_check.run()
                        mark.touch()
                _RESP_CACHE.clear()
            except Exception as e:                            # never kill the API because a site was down
                log.warning("refresh step %s %s failed: %s", kind, arg, e)
            cursor(i + 1)
            gc.collect()
            _t.sleep(gap)
    threading.Thread(target=run, name="onroad-refresh", daemon=True).start()


if os.getenv("FIRESTORE_SYNC", "1") == "1":       # user data mirrored to Firestore (onroad/firestore_sync.py)
    from . import firestore_sync as _fs
    _fs.start()

if os.getenv("REFRESH_EVERY_HOURS"):
    _refresh_loop(float(os.getenv("REFRESH_EVERY_HOURS")))
