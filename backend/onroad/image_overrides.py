"""
Main-photo corrections checked by eye, kept in data/image_overrides.json so every data refresh re-applies them (the
scrapers would otherwise bring the wrong picture back). null means "no correct photo yet": the app shows the brand mark.
"""
from __future__ import annotations

import json

from . import db


def apply(conn) -> int:
    path = db.ROOT / "data" / "image_overrides.json"
    if not path.is_file():
        return 0
    n = 0
    for mid, url in json.loads(path.read_text(encoding="utf-8")).get("models", {}).items():
        n += conn.execute("UPDATE models SET image_url = ? WHERE id = ?", (url, mid)).rowcount
    return n
