import sqlite3

conn = sqlite3.connect('data/onroad.db')
c = conn.cursor()

c.execute("SELECT id, name, slug, brand_slug, image_url, active FROM models WHERE id LIKE '%hunter%'")
for r in c.fetchall():
    print("Hunter:", r)

# Check all pairs of models with hyphen/underscore differences
c.execute("""
    SELECT m1.id, m1.image_url, m2.id, m2.image_url 
    FROM models m1 
    JOIN models m2 ON (replace(m1.id, '-', '_') = replace(m2.id, '-', '_') AND m1.id != m2.id)
""")
pairs = c.fetchall()
print(f"\nFound {len(pairs)} hyphen/underscore model pairs:")
for p in pairs[:20]:
    print(p)
