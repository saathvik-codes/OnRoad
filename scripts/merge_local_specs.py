"""
Adds spec rows gathered on this machine (e.g. a local variant_specs_fill run) to the latest published snapshot without
touching anything the scheduled refresh collected, repairs, audits and republishes it.

    python scripts/merge_local_specs.py            # needs the gh CLI
"""
import gzip
import os
import shutil
import sqlite3
import subprocess
import sys
import urllib.request
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "dist"
SNAP = WORK / "base.db"
os.environ["DB_PATH"] = str(SNAP)
os.environ["SNAPSHOT_PULL"] = "0"
sys.path.insert(0, str(ROOT / "backend"))
RELEASE = "https://github.com/saathvik-codes/OnRoad/releases/download/data-latest"


def main():
    WORK.mkdir(exist_ok=True)
    with urllib.request.urlopen(f"{RELEASE}/catalogue.db.gz", timeout=300) as r, gzip.open(r) as g, open(SNAP, "wb") as f:
        shutil.copyfileobj(g, f)
    local = ROOT / "data" / "onroad.db"
    with closing(sqlite3.connect(SNAP)) as c:
        c.execute("ATTACH ? AS loc", (str(local),))
        before = c.execute("SELECT COUNT(*) FROM specs").fetchone()[0]
        # fallback (online_*) rows: this machine's set is the reviewed one, so it replaces the snapshot's for every
        # variant it covers; manufacturer rows are never touched
        c.execute("""DELETE FROM specs WHERE key LIKE 'online_%' AND variant_id IN (SELECT DISTINCT variant_id FROM loc.specs)""")
        c.execute("""INSERT OR IGNORE INTO specs SELECT l.* FROM loc.specs l
                     WHERE l.key LIKE 'online_%' AND EXISTS (SELECT 1 FROM variants v WHERE v.id = l.variant_id)""")
        c.commit()
        print("spec rows added:", c.execute("SELECT COUNT(*) FROM specs").fetchone()[0] - before)
    from onroad import snapshot, spec_repair, db
    with closing(db.connect()) as conn, conn:
        print("repair:", spec_repair.repair(conn))
    subprocess.run([sys.executable, str(ROOT / "scripts" / "data_audit.py"), str(SNAP), "--fix"], check=False)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "spec_coverage.py"), str(SNAP), "car"], check=False)
    m = snapshot.build(WORK)
    print("built", m["built_at"])
    gh = ["gh", "release", "upload", "data-latest", "-R", "saathvik-codes/OnRoad", "--clobber"]
    subprocess.run(gh + [str(WORK / "catalogue.db.gz")], check=True)
    subprocess.run(gh + [str(WORK / "manifest.json")], check=True)
    SNAP.unlink()
    print("published")


if __name__ == "__main__":
    main()
