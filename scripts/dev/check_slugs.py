import sqlite3

conn = sqlite3.connect('data/onroad.db')
c = conn.cursor()

print("--- THAR ---")
c.execute("SELECT id, name, slug, brand_slug, image_url FROM models WHERE id LIKE '%thar%'")
for r in c.fetchall():
    print(r)

print("\n--- HUNTER ---")
c.execute("SELECT id, name, slug, brand_slug, image_url FROM models WHERE id LIKE '%hunter%'")
for r in c.fetchall():
    print(r)

print("\n--- TATA ---")
c.execute("SELECT id, name, slug, brand_slug, image_url FROM models WHERE id LIKE '%nexon%'")
for r in c.fetchall():
    print(r)

print("\n--- BRANDS ---")
c.execute("SELECT slug, name FROM brands WHERE slug IN ('tata', 'tata_motors', 'mahindra', 'royal_enfield')")
for r in c.fetchall():
    print(r)
