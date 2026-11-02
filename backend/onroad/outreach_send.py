"""
Sends showroom outreach emails that an admin has approved (status 'approved' in the outreach table; drafts are never sent).

    python -m onroad.outreach_send --dry-run          # print what would go out, send nothing
    python -m onroad.outreach_send --limit 20         # send up to 20 approved emails (the daily cap)

Settings (env): OUTREACH_SMTP_HOST, OUTREACH_SMTP_PORT (587), OUTREACH_SMTP_USER, OUTREACH_SMTP_PASSWORD (SECRET),
OUTREACH_FROM_NAME ("Saathvik from OnRoad"), OUTREACH_REPLY_TO (where showroom replies should go; defaults to the sender).
Each send is recorded (status 'sent' + sent_at, or 'failed'); anyone who replies "no" is marked opted out by the admin
and never written to again. The signature always shows the sending address, never a personal one.
"""
from __future__ import annotations

import argparse
import os
import smtplib
import time
from contextlib import closing
from email.message import EmailMessage

from . import db

PERSONAL = "saathvikk202@gmail.com"


def _sender() -> str:
    return os.environ["OUTREACH_SMTP_USER"]


def configured() -> bool:
    return bool(os.getenv("OUTREACH_SMTP_HOST") and os.getenv("OUTREACH_SMTP_USER") and os.getenv("OUTREACH_SMTP_PASSWORD"))


def _message(row) -> EmailMessage:
    body = (row["body"] or "").replace(PERSONAL, _sender())
    m = EmailMessage()
    m["From"] = f'{os.getenv("OUTREACH_FROM_NAME", "Saathvik from OnRoad")} <{_sender()}>'
    m["To"] = row["recipient"]
    m["Reply-To"] = os.getenv("OUTREACH_REPLY_TO") or _sender()
    m["Subject"] = row["subject"]
    m.set_content(body)
    return m


def run(limit: int = 20, dry_run: bool = False) -> dict:
    with closing(db.connect()) as conn:
        rows = conn.execute("""SELECT o.*, d.name AS dealer FROM outreach o JOIN dealers d ON d.id = o.dealer_id
                               WHERE o.channel = 'email' AND o.status = 'approved' ORDER BY o.id LIMIT ?""", (limit,)).fetchall()
    if dry_run:
        for r in rows:
            m = _message(r) if configured() else None
            print(f"--- to {r['recipient']} ({r['dealer']})\nSubject: {r['subject']}\n{(m.get_content() if m else r['body'])[:600]}\n")
        return {"would_send": len(rows)}
    if not configured():
        return {"skipped": "OUTREACH_SMTP_* not set"}
    sent = failed = 0
    with smtplib.SMTP(os.environ["OUTREACH_SMTP_HOST"], int(os.getenv("OUTREACH_SMTP_PORT", "587")), timeout=30) as s:
        s.starttls()
        s.login(_sender(), os.environ["OUTREACH_SMTP_PASSWORD"])
        for r in rows:
            try:
                s.send_message(_message(r))
                status = "sent"; sent += 1
            except Exception:
                status = "failed"; failed += 1
            with closing(db.connect()) as conn, conn:
                conn.execute("UPDATE outreach SET status = ?, sent_at = datetime('now') WHERE id = ?", (status, r["id"]))
            time.sleep(4)                         # gentle pace; providers flag bursts
    return {"sent": sent, "failed": failed}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    print(run(a.limit, a.dry_run))
