"""
SQLite store (WAL) for OnRoad. Every price and offer row keeps its source URL and the time it was read; prices are
append-only history, so "latest" is a query and price-change alerts come for free.
"""

import sqlite3
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Allow overriding via env var for cloud deployments (e.g. Render persistent disk at /data)
import os as _os
DB_PATH = Path(_os.environ["DB_PATH"]) if _os.environ.get("DB_PATH") else ROOT / "data" / "onroad.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS brands (
    slug TEXT PRIMARY KEY, name TEXT NOT NULL, website TEXT, logo TEXT, segment TEXT,  -- mass | premium | luxury
    last_refresh TEXT, refresh_note TEXT
);
CREATE TABLE IF NOT EXISTS models (
    id TEXT PRIMARY KEY,                -- brand_slug/model_slug
    brand_slug TEXT REFERENCES brands(slug), name TEXT NOT NULL, slug TEXT NOT NULL,
    body_type TEXT, url TEXT, image_url TEXT, active INTEGER DEFAULT 1, first_seen TEXT, last_seen TEXT
);
CREATE TABLE IF NOT EXISTS variants (
    id TEXT PRIMARY KEY,                -- model_id/variant_slug
    model_id TEXT REFERENCES models(id), name TEXT NOT NULL, fuel TEXT, transmission TEXT,
    engine_cc INTEGER, battery_kwh REAL, seats INTEGER, active INTEGER DEFAULT 1, first_seen TEXT, last_seen TEXT
);
CREATE TABLE IF NOT EXISTS prices (     -- append-only: one row per read that changed (or first read)
    variant_id TEXT REFERENCES variants(id), city TEXT, ex_showroom_inr INTEGER, source_url TEXT, fetched_at TEXT,
    PRIMARY KEY (variant_id, city, fetched_at)
);
CREATE INDEX IF NOT EXISTS idx_prices_latest ON prices(variant_id, city, fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_models_brand ON models(brand_slug, active);
CREATE INDEX IF NOT EXISTS idx_variants_model ON variants(model_id, active);
CREATE INDEX IF NOT EXISTS idx_dealers_brand_city ON dealers(brand_slug, active, city);
CREATE INDEX IF NOT EXISTS idx_offers_brand_active ON offers(brand_slug, active, valid_until);
CREATE INDEX IF NOT EXISTS idx_specs_variant ON specs(variant_id);
CREATE INDEX IF NOT EXISTS idx_features_variant ON features(variant_id);
CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT, brand_slug TEXT, model_name TEXT, title TEXT, amount_inr INTEGER,
    details TEXT, valid_until TEXT, city TEXT, source TEXT, source_url TEXT, fetched_at TEXT, active INTEGER DEFAULT 1,
    dealer_id TEXT                      -- set when a dealer posted it
);
CREATE TABLE IF NOT EXISTS dealers (
    id TEXT PRIMARY KEY,                -- brand_slug/normalised name+pincode
    brand_slug TEXT, name TEXT, address TEXT, city TEXT, state TEXT, pincode TEXT, phone TEXT, email TEXT,
    lat REAL, lng REAL, kind TEXT, website TEXT, source_url TEXT, fetched_at TEXT, active INTEGER DEFAULT 1,
    claimed_by INTEGER                  -- dealer account that verified ownership
);
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, name TEXT, phone TEXT, pw_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'buyer',   -- buyer | dealer | admin
    created TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS saved_cars (
    account_id INTEGER, variant_id TEXT, city TEXT, target_inr INTEGER, created TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (account_id, variant_id, city)
);
CREATE TABLE IF NOT EXISTS quote_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER, variant_id TEXT, city TEXT, pincode TEXT,
    colour TEXT, finance INTEGER DEFAULT 0, exchange INTEGER DEFAULT 0, purchase_by TEXT, note TEXT,
    status TEXT DEFAULT 'open', created TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS quotes (     -- a dealer's answer to one request
    id INTEGER PRIMARY KEY AUTOINCREMENT, request_id INTEGER REFERENCES quote_requests(id), dealer_id TEXT,
    ex_showroom_inr INTEGER, road_tax_inr INTEGER, registration_inr INTEGER, insurance_inr INTEGER,
    accessories_inr INTEGER, other_inr INTEGER, discount_inr INTEGER, on_road_inr INTEGER, waiting_weeks INTEGER,
    valid_until TEXT, note TEXT, created TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS outreach (   -- dealer onboarding invitations: drafted here, sent only after admin approval
    id INTEGER PRIMARY KEY AUTOINCREMENT, dealer_id TEXT, channel TEXT, recipient TEXT, subject TEXT, body TEXT,
    status TEXT DEFAULT 'draft',        -- draft | approved | sent | failed | opted_out
    approved_by INTEGER, sent_at TEXT, created TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS refresh_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT, started TEXT, finished TEXT, summary TEXT
);
CREATE TABLE IF NOT EXISTS specs (
    variant_id TEXT, grp TEXT, key TEXT, label TEXT, value TEXT, source_url TEXT, fetched_at TEXT,
    PRIMARY KEY (variant_id, key)
);
CREATE TABLE IF NOT EXISTS features (
    variant_id TEXT, key TEXT, label TEXT, source_url TEXT, fetched_at TEXT,
    PRIMARY KEY (variant_id, key, label)
);
CREATE TABLE IF NOT EXISTS dealer_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT, dealer_id TEXT, account_id INTEGER, rating INTEGER,
    price_honesty INTEGER, no_forced_addons INTEGER, delivery_on_time INTEGER, visit TEXT, text TEXT,
    created TEXT DEFAULT (datetime('now')), UNIQUE (dealer_id, account_id)
);
"""


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


MIGRATIONS = [
    "ALTER TABLE offers ADD COLUMN kind TEXT",
    "ALTER TABLE offers ADD COLUMN conditions TEXT",
    "ALTER TABLE offers ADD COLUMN valid_from TEXT",
    "ALTER TABLE offers ADD COLUMN variant TEXT",
    "ALTER TABLE variants ADD COLUMN image_url TEXT",
    "ALTER TABLE brands ADD COLUMN vehicle_type TEXT DEFAULT 'car'",
    "ALTER TABLE models ADD COLUMN vehicle_type TEXT DEFAULT 'car'",
]



def init() -> None:
    with closing(connect()) as conn, conn:
        conn.executescript(SCHEMA)
        for m in MIGRATIONS:
            try:
                conn.execute(m)
            except sqlite3.OperationalError:   # column already there
                pass
        # an offer we can't link back to the manufacturer's page is never shown (removes seeded / unsourced rows)
        conn.execute("UPDATE offers SET active = 0 WHERE source = 'brand_site' AND (source_url IS NULL OR source_url = '')")
