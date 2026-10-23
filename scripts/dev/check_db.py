import sqlite3

conn = sqlite3.connect('data/onroad.db')
c = conn.cursor()
c.execute("SELECT id, name, slug, brand_slug, image_url FROM models WHERE id LIKE '%scorpio%'")
print("MODELS:", c.fetchall())

c.execute("SELECT id, name, image_url FROM variants WHERE model_id LIKE '%scorpio-n%' LIMIT 5")
print("VARIANTS:", c.fetchall())

c.execute("SELECT model_id, key, image_url FROM feature_images WHERE model_id LIKE '%scorpio%'")
print("FEATURE_IMAGES:", c.fetchall())
