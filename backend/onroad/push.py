"""
Push notifications through Firebase Cloud Messaging (HTTP v1), signed with the same service account as Firestore.

Sent for things a buyer asked to follow, never for marketing:
  * a saved car's ex-showroom price goes down (ingest calls price_dropped);
  * a dealer answers the buyer's quote request (api.submit_quote calls quote_received).
Phones register their FCM token at /api/me/push-token; tokens Google reports as gone are deleted.
"""
from __future__ import annotations

import logging
import threading

from . import db
from .firestore_sync import _creds

log = logging.getLogger("onroad.push")
_session = None


def _sess():
    global _session
    if _session is None:
        info = _creds()
        if not info:
            return None, None
        from google.auth.transport.requests import AuthorizedSession
        from google.oauth2 import service_account
        cr = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/firebase.messaging"])
        _session = (AuthorizedSession(cr), info["project_id"])
    return _session


def already_told(conn, account_id: int, key: str, value: str) -> bool:
    """True if this buyer was already sent this exact news (same key and value); otherwise records it and returns False."""
    row = conn.execute("SELECT value FROM push_log WHERE account_id = ? AND key = ?", (account_id, key)).fetchone()
    if row and row[0] == value:
        return True
    conn.execute("INSERT OR REPLACE INTO push_log (account_id, key, value, sent) VALUES (?, ?, ?, datetime('now'))", (account_id, key, value))
    conn.commit()
    return False


def send_to_accounts(account_ids: list[int], title: str, body: str, data: dict | None = None, image: str | None = None,
                     tag: str | None = None) -> int:
    """Send in the background; returns how many phones were addressed. image: an https picture shown when the
    notification is expanded; tag: notifications with the same tag replace each other on the phone instead of stacking."""
    if not account_ids:
        return 0
    conn = db.connect()
    tokens = [r[0] for r in conn.execute(f"SELECT token FROM push_tokens WHERE account_id IN ({','.join('?' * len(account_ids))})",
                                         tuple(account_ids))]
    if not tokens:
        return 0

    def go():
        s, project = _sess()
        if not s:
            return
        for t in tokens:
            note = {"title": title, "body": body, **({"image": image} if image else {})}
            extra = {**(data or {}), **({"image": image} if image else {}), **({"tag": tag} if tag else {})}
            android = {"channel_id": "deals", **({"tag": tag} if tag else {})}
            msg = {"message": {"token": t, "notification": note, "data": {k: str(v) for k, v in extra.items()},
                               "android": {"priority": "high", "notification": android}}}
            try:
                r = s.post(f"https://fcm.googleapis.com/v1/projects/{project}/messages:send", json=msg, timeout=15)
                if r.status_code in (404, 400) and ("UNREGISTERED" in r.text or "INVALID_ARGUMENT" in r.text and "token" in r.text):
                    c = db.connect(); c.execute("DELETE FROM push_tokens WHERE token = ?", (t,)); c.commit()
            except Exception as e:
                log.warning("push failed: %s", e)
    threading.Thread(target=go, daemon=True).start()
    return len(tokens)


def price_dropped(conn, variant_id: str, city: str, old: int, new: int) -> None:
    """Buyers who saved this variant for this city. With a target price, they hear only once it's at or under the
    target (the moment it crosses it); without one, any drop."""
    rows = conn.execute("""SELECT s.account_id, s.target_inr, m.name AS model, v.name AS variant, m.id AS mid, b.name AS brand, m.image_url
                           FROM saved_cars s JOIN variants v ON v.id = s.variant_id JOIN models m ON m.id = v.model_id
                           JOIN brands b ON b.slug = m.brand_slug
                           WHERE s.variant_id = ? AND lower(s.city) = lower(?)""", (variant_id, city)).fetchall()
    for r in rows:
        target = r[1]
        if target and new > target:
            continue                                   # still above what the buyer is waiting for
        if target and old <= target:
            continue                                   # already told when it first crossed the target
        if target:
            title = f"🎯 The {r[2]} hit your price"
            body = f"{r[5]} {r[3]} is now ₹{new:,} ex-showroom in {city}, under your ₹{target:,} target. Your move."
        else:
            title = f"📉 Your {r[2]} just got cheaper"
            body = f"{r[5]} {r[3]} is down ₹{old - new:,}, now ₹{new:,} ex-showroom in {city}. Prices move, so grab a quote."
        if already_told(conn, r[0], f"price:{variant_id}:{city.lower()}", str(new)):
            continue                                   # ingest and snapshot both report the same drop: say it once
        img = r[6] if r[6] and str(r[6]).startswith("https://") else None
        send_to_accounts([r[0]], title, body, {"model": r[4]}, image=img, tag=f"price-{variant_id}-{city.lower()}")


def quote_received(request_id: int, dealer_name: str, on_road: int) -> None:
    conn = db.connect()
    row = conn.execute("""SELECT r.account_id, m.name, v.name FROM quote_requests r JOIN variants v ON v.id = r.variant_id
                          JOIN models m ON m.id = v.model_id WHERE r.id = ?""", (request_id,)).fetchone()
    if row and not already_told(conn, row[0], f"quote:{request_id}:{dealer_name}", str(on_road)):
        send_to_accounts([row[0]], f"💬 {dealer_name} sent you a quote",
                         f"₹{on_road:,} on-road for the {row[1]} {row[2]}. Stack it against your other quotes.", {"screen": "account"},
                         tag=f"quote-{request_id}")
