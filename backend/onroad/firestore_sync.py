"""
Keeps OnRoad's user data in Firestore so it survives redeploys (Render's disk is wiped on every deploy).

SQLite stays the working database. User tables (accounts, saved cars, quote requests, dealer quotes, showroom
reviews, outreach drafts, push tokens, dealer claims) are mirrored to Firestore collections "onroad_<table>":
  * on start, if this server's SQLite has no accounts but Firestore has, every user table is restored from Firestore;
  * after any request that changes data, and every 10 minutes anyway, changed rows are written (unchanged rows are
    skipped by a content hash, deleted rows are deleted).
The car catalogue (models, prices, specs ...) is rebuilt from the makers' sites and isn't mirrored.

Credentials (first found): FIREBASE_SERVICE_ACCOUNT (the JSON itself), FIREBASE_CREDENTIALS / GOOGLE_APPLICATION_CREDENTIALS
(a path), or a *firebase-adminsdk*.json next to the repo (local runs). Without any, everything here is a no-op.
"""
from __future__ import annotations

import glob
import hashlib
import json
import logging
import os
import threading
import time

from . import db

log = logging.getLogger("onroad.firestore")
TABLES = {"accounts": ("id",), "saved_cars": ("account_id", "variant_id"), "quote_requests": ("id",), "quotes": ("id",),
          "dealer_reviews": ("id",), "outreach": ("id",), "push_tokens": ("token",), "opinions": ("id",), "activity": ("id",)}
_STATUS: dict = {}
_dirty = threading.Event()
_hash: dict[str, dict[str, str]] = {}
_client = None


def _creds():
    raw = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if raw:
        return json.loads(raw)
    for path in (os.getenv("FIREBASE_CREDENTIALS"), os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
                 *glob.glob(str(db.ROOT / "*firebase-adminsdk*.json"))):
        if path and os.path.isfile(path):
            return json.load(open(path, encoding="utf-8"))
    return None


def _database(project: str, cr) -> str:
    """FIRESTORE_DATABASE if set; else "(default)" if the project has it, else its only database (the console can
    create one named e.g. "default")."""
    if os.getenv("FIRESTORE_DATABASE"):
        return os.environ["FIRESTORE_DATABASE"]
    try:
        from google.auth.transport.requests import AuthorizedSession
        dbs = [d["name"].rsplit("/", 1)[-1] for d in AuthorizedSession(cr).get(
            f"https://firestore.googleapis.com/v1/projects/{project}/databases", timeout=15).json().get("databases", [])]
        if dbs and "(default)" not in dbs:
            return dbs[0]
    except Exception:
        pass
    return "(default)"


def client():
    global _client
    if _client is None:
        info = _creds()
        if not info:
            return None
        from google.cloud import firestore
        from google.oauth2 import service_account
        cr = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/cloud-platform"])
        _client = firestore.Client(project=info["project_id"], credentials=cr, database=_database(info["project_id"], cr))
    return _client


def enabled() -> bool:
    return _creds() is not None


def _rows(conn, table: str):
    try:
        cur = conn.execute(f"SELECT * FROM {table}")
    except Exception:
        return []
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def _doc_id(table: str, row: dict) -> str:
    return "__".join(str(row[k]) for k in TABLES[table]).replace("/", "|")


def _claims(conn):
    return [{"id": r[0], "claimed_by": r[1]} for r in conn.execute("SELECT id, claimed_by FROM dealers WHERE claimed_by IS NOT NULL")]


def push() -> dict:
    """Write rows that changed since the last push; delete rows that are gone."""
    fs = client()
    if not fs:
        return {"skipped": "no Firebase credentials"}
    conn = db.connect()
    written = deleted = 0
    sets = {t: _rows(conn, t) for t in TABLES}
    sets["dealer_claims"] = _claims(conn)
    for table, rows in sets.items():
        pk = TABLES.get(table, ("id",))
        col = fs.collection(f"onroad_{table}")
        seen = _hash.setdefault(table, {})
        if not seen:                                   # first push this process: learn what Firestore already holds
            for d in col.stream():
                seen[d.id] = d.to_dict().get("_h", "")
        now: dict[str, str] = {}
        batch, n = fs.batch(), 0
        for r in rows:
            did = "__".join(str(r[k]) for k in pk).replace("/", "|")
            h = hashlib.sha1(json.dumps(r, sort_keys=True, default=str).encode()).hexdigest()
            now[did] = h
            if seen.get(did) != h:
                batch.set(col.document(did), {**r, "_h": h}); n += 1; written += 1
                if n == 400:
                    batch.commit(); batch, n = fs.batch(), 0
        for did in set(seen) - set(now):
            batch.delete(col.document(did)); n += 1; deleted += 1
            if n == 400:
                batch.commit(); batch, n = fs.batch(), 0
        if n:
            batch.commit()
        _hash[table] = now
    return {"written": written, "deleted": deleted}


def restore() -> dict:
    """Fresh disk: bring user data back from Firestore (only when this database has no accounts at all)."""
    fs = client()
    if not fs:
        return {"skipped": "no Firebase credentials"}
    conn = db.connect()
    if conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]:
        return {"skipped": "local accounts present"}
    got = {}
    for table in (*TABLES, "dealer_claims"):
        docs = [d.to_dict() for d in fs.collection(f"onroad_{table}").stream()]
        for r in docs:
            r.pop("_h", None)
            if table == "dealer_claims":
                conn.execute("UPDATE dealers SET claimed_by = ? WHERE id = ?", (r["claimed_by"], r["id"]))
                continue
            try:
                cols = [c[1] for c in conn.execute(f"PRAGMA table_info({table})")]
            except Exception:
                continue
            r = {k: v for k, v in r.items() if k in cols}
            if r:
                conn.execute(f"INSERT OR REPLACE INTO {table} ({','.join(r)}) VALUES ({','.join('?' * len(r))})", tuple(r.values()))
        got[table] = len(docs)
    conn.commit()
    return {"restored": got}


def status() -> dict:
    """For /api/health: is the backup on, what did the last restore bring back, when did the last push happen."""
    return {"enabled": enabled(), **_STATUS}


def mark_dirty() -> None:
    _dirty.set()


def start() -> None:
    """Restore once, then push after every change (a few seconds later) and every 10 minutes."""
    if not enabled():
        log.info("Firestore sync off (no credentials)")
        return

    try:                                               # before serving: a wiped disk gets its users back first
        r = restore(); _STATUS["restore"] = r
        log.info("firestore restore: %s", r)
    except Exception as e:
        log.warning("firestore restore failed: %s", e)

    def loop():
        last = 0.0
        while True:
            _dirty.wait(timeout=600)
            time.sleep(3)                              # gather a burst of writes into one push
            _dirty.clear()
            try:
                r = push()
                _STATUS["last_push"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()); _STATUS["last_push_result"] = r
                if r.get("written") or r.get("deleted") or time.time() - last > 3600:
                    log.info("firestore push: %s", r); last = time.time()
            except Exception as e:
                _STATUS["last_error"] = str(e)[:200]
                log.warning("firestore push failed: %s", e)
                _dirty.set(); time.sleep(60)
    threading.Thread(target=loop, daemon=True, name="firestore-sync").start()
