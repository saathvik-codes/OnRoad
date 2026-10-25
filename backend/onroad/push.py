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


def send_to_accounts(account_ids: list[int], title: str, body: str, data: dict | None = None) -> int:
    """Send in the background; returns how many phones were addressed."""
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
            msg = {"message": {"token": t, "notification": {"title": title, "body": body},
                               "data": {k: str(v) for k, v in (data or {}).items()},
                               "android": {"priority": "high", "notification": {"channel_id": "deals"}}}}
            try:
                r = s.post(f"https://fcm.googleapis.com/v1/projects/{project}/messages:send", json=msg, timeout=15)
                if r.status_code in (404, 400) and ("UNREGISTERED" in r.text or "INVALID_ARGUMENT" in r.text and "token" in r.text):
                    c = db.connect(); c.execute("DELETE FROM push_tokens WHERE token = ?", (t,)); c.commit()
            except Exception as e:
                log.warning("push failed: %s", e)
    threading.Thread(target=go, daemon=True).start()
    return len(tokens)


def price_dropped(conn, variant_id: str, city: str, old: int, new: int) -> None:
    rows = conn.execute("""SELECT s.account_id, m.name AS model, v.name AS variant, m.id AS mid FROM saved_cars s
                           JOIN variants v ON v.id = s.variant_id JOIN models m ON m.id = v.model_id
                           WHERE s.variant_id = ?""", (variant_id,)).fetchall()
    if rows:
        r = rows[0]
        send_to_accounts([x[0] for x in rows], f"Price drop: {r[1]}",
                         f"{r[2]} is now Rs {new:,} ex-showroom ({city}), Rs {old - new:,} less than before.",
                         {"model": r[3]})


def quote_received(request_id: int, dealer_name: str, on_road: int) -> None:
    conn = db.connect()
    row = conn.execute("""SELECT r.account_id, m.name, v.name FROM quote_requests r JOIN variants v ON v.id = r.variant_id
                          JOIN models m ON m.id = v.model_id WHERE r.id = ?""", (request_id,)).fetchone()
    if row:
        send_to_accounts([row[0]], f"New quote for your {row[1]}",
                         f"{dealer_name} quoted Rs {on_road:,} on-road for the {row[2]}.", {"screen": "account"})
