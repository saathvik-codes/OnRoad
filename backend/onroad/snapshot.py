"""
Catalogue snapshots: the data refresh runs on GitHub Actions (scripts/refresh_job.py), not on the API server.

  * build()  - on GitHub: copy the refreshed database without any user data, gzip it, write a small manifest.
  * apply()  - on the server: swap the catalogue tables for the snapshot's in one transaction; user tables
               (accounts, saved cars, quotes, reviews, push tokens...) are never touched. Saved cars whose price
               dropped get their push notification here, because only the server knows who saved what.
  * start()  - on the server: check the manifest at start-up and every 30 minutes; download only when newer.

The server does no scraping, and a restart on a fresh disk catches up from the latest snapshot within a minute.
"""
from __future__ import annotations

import gzip
import json
import logging
import os
import shutil
import sqlite3
import threading
import time
from contextlib import closing
from pathlib import Path

from . import db

log = logging.getLogger("onroad.snapshot")

RELEASE = os.getenv("SNAPSHOT_RELEASE", "https://github.com/saathvik-codes/OnRoad/releases/download/data-latest")
# everything people create; never shipped in a snapshot and never replaced by one
USER_TABLES = {"accounts", "sessions", "saved_cars", "quote_requests", "quotes", "dealer_reviews", "opinions", "outreach",
               "push_tokens", "dealer_claims", "app_state", "refresh_runs", "sqlite_sequence",
               "news"}                            # the server fetches news itself
RESEARCH = ("popularity.json", "crash_tests.json")


def build(out_dir: Path) -> dict:
    """Catalogue-only copy of the current database as catalogue.db.gz, plus manifest.json and the research files."""
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / "catalogue.db"
    tmp.unlink(missing_ok=True)
    with closing(db.connect()) as conn:
        conn.execute(f"VACUUM INTO '{tmp.as_posix()}'")
    with closing(sqlite3.connect(tmp)) as c:
        for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall():
            if t in USER_TABLES and t != "sqlite_sequence":
                c.execute(f"DROP TABLE {t}")
        c.commit()
        c.execute("VACUUM")
        counts = {t: c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                  for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name <> 'sqlite_sequence'")}
        newest = c.execute("SELECT MAX(fetched_at) FROM prices").fetchone()[0]
    with open(tmp, "rb") as f, gzip.open(out_dir / "catalogue.db.gz", "wb", compresslevel=6) as g:
        shutil.copyfileobj(f, g)
    tmp.unlink()
    for name in RESEARCH:
        src = db.ROOT / "data" / "research" / name
        if src.exists():
            shutil.copy(src, out_dir / name)
    manifest = {"built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "newest_price": newest, "counts": counts}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return manifest


def _state(conn, k: str, v: str | None = None) -> str | None:
    conn.execute("CREATE TABLE IF NOT EXISTS app_state (k TEXT PRIMARY KEY, v TEXT)")
    if v is not None:
        conn.execute("INSERT OR REPLACE INTO app_state VALUES (?, ?)", (k, v))
        return v
    row = conn.execute("SELECT v FROM app_state WHERE k = ?", (k,)).fetchone()
    return row[0] if row else None


def _saved_prices(conn) -> dict:
    """Latest ex-showroom price of every saved (variant, city), to spot drops after the swap."""
    try:
        rows = conn.execute("""SELECT DISTINCT s.variant_id, s.city FROM saved_cars s""").fetchall()
    except sqlite3.OperationalError:
        return {}
    out = {}
    for vid, city in rows:
        r = conn.execute("""SELECT ex_showroom_inr FROM prices WHERE variant_id = ? AND (lower(city) = lower(?) OR city = 'India (national)')
                            ORDER BY lower(city) = lower(?) DESC, fetched_at DESC LIMIT 1""", (vid, city, city)).fetchone()
        if r and r[0]:
            out[(vid, city)] = int(r[0])
    return out


def apply(snapshot_db: Path) -> dict:
    """Replace the catalogue tables with the snapshot's, atomically. User tables stay as they are."""
    moved = {}
    with closing(db.connect()) as conn:
        before = _saved_prices(conn)
        conn.execute("ATTACH ? AS snap", (str(snapshot_db),))
        snap_tables = [r[0] for r in conn.execute("SELECT name FROM snap.sqlite_master WHERE type = 'table'")]
        have = {r[0] for r in conn.execute("SELECT name FROM main.sqlite_master WHERE type = 'table'")}
        conn.execute("PRAGMA foreign_keys = OFF")                    # rows go out and straight back in with the same ids
        conn.execute("BEGIN IMMEDIATE")
        try:
            for t in snap_tables:
                if t in USER_TABLES:
                    continue
                if t not in have:
                    conn.execute(conn.execute("SELECT sql FROM snap.sqlite_master WHERE name = ?", (t,)).fetchone()[0])
                mine = [r[1] for r in conn.execute(f"PRAGMA main.table_info({t})")]
                theirs = {r[1] for r in conn.execute(f"PRAGMA snap.table_info({t})")}
                for col in [r for r in conn.execute(f"PRAGMA snap.table_info({t})") if r[1] not in mine]:
                    conn.execute(f"ALTER TABLE main.{t} ADD COLUMN {col[1]} {col[2]}")     # newer code added a column
                    mine.append(col[1])
                common = ",".join(c for c in mine if c in theirs)
                conn.execute(f"DELETE FROM main.{t}")
                moved[t] = conn.execute(f"INSERT INTO main.{t} ({common}) SELECT {common} FROM snap.{t}").rowcount
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.execute("DETACH snap")
            conn.execute("PRAGMA foreign_keys = ON")
        after = _saved_prices(conn)
        drops = [(k, before[k], v) for k, v in after.items() if k in before and v < before[k]]
        if drops:
            try:
                from . import push
                for (vid, city), old, new in drops:
                    push.price_dropped(conn, vid, city, old, new)
            except Exception as e:
                log.warning("price-drop push failed: %s", e)
        conn.commit()
    return {"tables": moved, "price_drops": len(drops)}


def pull(force: bool = False) -> dict:
    """Download and apply the latest snapshot if it is newer than the one applied last."""
    import httpx
    with httpx.Client(timeout=120, follow_redirects=True) as c:
        r = c.get(f"{RELEASE}/manifest.json")
        if r.status_code != 200:
            return {"skipped": f"no manifest ({r.status_code})"}
        manifest = r.json()
        with closing(db.connect()) as conn, conn:
            last = _state(conn, "snapshot_built_at")
        if not force and last and last >= manifest["built_at"]:
            return {"up_to_date": last}
        work = db.ROOT / "data" / ".snapshot"
        work.mkdir(parents=True, exist_ok=True)
        gz, raw = work / "catalogue.db.gz", work / "catalogue.db"
        with c.stream("GET", f"{RELEASE}/catalogue.db.gz") as resp:
            resp.raise_for_status()
            with open(gz, "wb") as f:
                for chunk in resp.iter_bytes(1 << 20):
                    f.write(chunk)
        with gzip.open(gz, "rb") as g, open(raw, "wb") as f:
            shutil.copyfileobj(g, f)
        with closing(sqlite3.connect(raw)) as s:                      # a broken download must never wipe the catalogue
            ok = s.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            n = s.execute("SELECT COUNT(*) FROM variants").fetchone()[0] if ok else 0
        if not ok or n < 500:
            return {"skipped": f"snapshot failed checks (integrity={ok}, variants={n})"}
        res = apply(raw)
        for name in RESEARCH:
            rr = c.get(f"{RELEASE}/{name}")
            if rr.status_code == 200 and rr.content.strip().startswith((b"[", b"{")):
                (db.ROOT / "data" / "research" / name).write_bytes(rr.content)
        gz.unlink(missing_ok=True)
        raw.unlink(missing_ok=True)
        with closing(db.connect()) as conn, conn:
            _state(conn, "snapshot_built_at", manifest["built_at"])
            _state(conn, "snapshot_applied_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        return {"applied": manifest["built_at"], **res}


def start(on_applied=None, every_minutes: float = 30) -> None:
    def loop():
        time.sleep(20)                                                 # let the server finish starting
        while True:
            try:
                res = pull()
                log.info("snapshot: %s", res)
                if "applied" in res and on_applied:
                    on_applied()
            except Exception as e:
                log.warning("snapshot pull failed: %s", e)
            time.sleep(every_minutes * 60)
    threading.Thread(target=loop, name="onroad-snapshot", daemon=True).start()
