import sqlite3

conn = sqlite3.connect('onroad/data/onroad.db')
c = conn.cursor()

print("--- LAND ROVER MODELS ---")
c.execute("SELECT id, name, image_url FROM models WHERE brand_slug = 'land_rover' OR name LIKE '%Discovery%'")
for r in c.fetchall():
    print(r)

print("\n--- BIKE BRANDS & MODEL COUNTS ---")
c.execute("""
    SELECT b.slug, b.name, COUNT(m.id) as model_count 
    FROM brands b 
    LEFT JOIN models m ON m.brand_slug = b.slug 
    WHERE b.vehicle_type = 'bike' 
    GROUP BY b.slug
""")
for r in c.fetchall():
    print(r)

conn.close()
