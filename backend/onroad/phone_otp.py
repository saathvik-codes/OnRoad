"""
Mobile number verification by SMS code, through Message Central VerifyNow (https://www.messagecentral.com).

The server sends and checks every code, so the OnRoad website and apps share one flow and no client ever sees the
provider's credentials. Message Central sends from its own approved sender, so no DLT registration is needed.

Settings (env):
  PHONE_VERIFICATION          off | optional | required   (required = a student must verify before saving a profile)
  MESSAGECENTRAL_CUSTOMER_ID  e.g. C-XXXXXXXXXXXXXXX
  MESSAGECENTRAL_AUTH_TOKEN   auth token from the console (SECRET), used as-is; or
  MESSAGECENTRAL_KEY          the account password (SECRET), exchanged for a token (sent base64-encoded)

Limits (abuse and cost control): one code per 30 s and 5 per hour per student, 5 per day per number, 5 wrong tries
per code, codes expire after 10 minutes.
"""
from __future__ import annotations

import base64
import os
import re
import time
from contextlib import closing

import requests

from . import db

BASE = "https://cpaas.messagecentral.com"
_token: dict = {"value": "", "at": 0.0}


class OtpError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def mode() -> str:
    """off, optional or required. Defaults to required once Message Central is configured."""
    m = os.getenv("PHONE_VERIFICATION", "").strip().lower()
    if m in ("off", "optional", "required"):
        return m if (m == "off" or configured()) else "off"
    return "required" if configured() else "off"


def configured() -> bool:
    return bool(os.getenv("MESSAGECENTRAL_CUSTOMER_ID") and (os.getenv("MESSAGECENTRAL_AUTH_TOKEN") or os.getenv("MESSAGECENTRAL_KEY")))


def indian_mobile(raw: str) -> str:
    """"+91 98765 43210", "098765-43210", "9876543210" -> "9876543210". Only Indian mobiles (6-9 first digit)."""
    d = re.sub(r"\D", "", raw or "")
    if d.startswith("91") and len(d) == 12:
        d = d[2:]
    d = d.lstrip("0") if len(d) == 11 else d
    if not re.fullmatch(r"[6-9]\d{9}", d):
        raise OtpError("Enter a 10-digit Indian mobile number.")
    return d


def init() -> None:
    with closing(db.connect()) as conn, conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS phone_otps (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
                        phone TEXT NOT NULL, verification_id TEXT NOT NULL, attempts INTEGER DEFAULT 0,
                        created REAL NOT NULL, done INTEGER DEFAULT 0)""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_otp_user ON phone_otps(user_id, created)")


def _auth() -> str:
    if os.getenv("MESSAGECENTRAL_AUTH_TOKEN"):
        return os.environ["MESSAGECENTRAL_AUTH_TOKEN"].strip()
    if _token["value"] and time.time() - _token["at"] < 20 * 3600:
        return _token["value"]
    key = base64.b64encode(os.environ["MESSAGECENTRAL_KEY"].encode()).decode()
    r = requests.get(f"{BASE}/auth/v1/authentication/token", timeout=15, params={
        "customerId": os.environ["MESSAGECENTRAL_CUSTOMER_ID"], "key": key, "scope": "NEW", "country": "91"})
    tok = (r.json() if r.content else {}).get("token") if r.ok else None
    if not tok:
        raise OtpError("SMS service sign-in failed. Check MESSAGECENTRAL_CUSTOMER_ID and MESSAGECENTRAL_KEY.", 503)
    _token.update(value=tok, at=time.time())
    return tok


def _call(method: str, path: str, params: dict) -> dict:
    for retry in (0, 1):
        r = requests.request(method, f"{BASE}{path}", params={**params, "customerId": os.environ["MESSAGECENTRAL_CUSTOMER_ID"]},
                             headers={"authToken": _auth()}, timeout=20)
        if r.status_code == 401 and not retry and not os.getenv("MESSAGECENTRAL_AUTH_TOKEN"):   # fetched token expired: renew once
            _token["value"] = ""
            continue
        try:
            return r.json()
        except ValueError:
            raise OtpError("The SMS service didn't answer properly. Try again in a minute.", 502)
    return {}


def send(user_id: int, raw_phone: str) -> dict:
    if not configured():
        raise OtpError("Phone verification isn't set up on this server.", 404)
    phone = indian_mobile(raw_phone)
    init()
    now = time.time()
    with closing(db.connect()) as conn:
        taken = conn.execute("""SELECT 1 FROM accounts WHERE phone IN (?, ?) AND id != ? AND phone_verified_at IS NOT NULL""",
                             (phone, "+91" + phone, user_id)).fetchone()
        if taken:
            raise OtpError("This number is already verified on another OnRoad account.", 409)
        last = conn.execute("SELECT MAX(created) FROM phone_otps WHERE user_id = ?", (user_id,)).fetchone()[0] or 0
        hour = conn.execute("SELECT COUNT(*) FROM phone_otps WHERE user_id = ? AND created > ?", (user_id, now - 3600)).fetchone()[0]
        day = conn.execute("SELECT COUNT(*) FROM phone_otps WHERE phone = ? AND created > ?", (phone, now - 86400)).fetchone()[0]
    if now - last < 30:
        raise OtpError(f"Wait {int(30 - (now - last)) + 1} seconds before asking for another code.", 429)
    if hour >= 5 or day >= 5:
        raise OtpError("Too many codes asked for. Try again later.", 429)
    j = _call("POST", "/verification/v3/send", {"countryCode": "91", "flowType": "SMS", "mobileNumber": phone, "otpLength": "6"})
    vid = ((j or {}).get("data") or {}).get("verificationId")
    if not vid:
        msg = (j or {}).get("message") or "Couldn't send the code. Try again in a minute."
        raise OtpError(msg if "invalid" in msg.lower() else "Couldn't send the code. Try again in a minute.", 502)
    with closing(db.connect()) as conn, conn:
        conn.execute("INSERT INTO phone_otps (user_id, phone, verification_id, created) VALUES (?, ?, ?, ?)", (user_id, phone, str(vid), now))
    return {"sent_to": "+91" + phone, "resend_after": 30, "length": 6}


def verify(user_id: int, raw_phone: str, code: str) -> str:
    """Checks the code; returns the verified number as +91XXXXXXXXXX."""
    phone = indian_mobile(raw_phone)
    code = re.sub(r"\D", "", code or "")
    if not 4 <= len(code) <= 8:
        raise OtpError("Enter the code from the SMS.")
    init()
    with closing(db.connect()) as conn:
        row = conn.execute("""SELECT id, verification_id, attempts, created FROM phone_otps WHERE user_id = ? AND phone = ? AND done = 0
                              ORDER BY id DESC LIMIT 1""", (user_id, phone)).fetchone()
    if not row or time.time() - row["created"] > 600:
        raise OtpError("That code has expired. Send a new one.", 410)
    if row["attempts"] >= 5:
        raise OtpError("Too many wrong tries. Send a new code.", 429)
    with closing(db.connect()) as conn, conn:
        conn.execute("UPDATE phone_otps SET attempts = attempts + 1 WHERE id = ?", (row["id"],))
    j = _call("GET", "/verification/v3/validateOtp", {"countryCode": "91", "mobileNumber": phone,
                                                       "verificationId": row["verification_id"], "code": code})
    status = (((j or {}).get("data") or {}).get("verificationStatus") or "").upper()
    if status != "VERIFICATION_COMPLETED":
        raise OtpError("That code isn't right. Check the SMS and try again.")
    with closing(db.connect()) as conn, conn:
        conn.execute("UPDATE phone_otps SET done = 1 WHERE id = ?", (row["id"],))
    return "+91" + phone
