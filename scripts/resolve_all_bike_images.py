"""
Directly resolve and update all 66 bike model images in data/onroad.db.
Verifies HTTP 200 for every image URL.
"""

import sqlite3
import urllib.request
import re

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

EXACT_SLUGS = {
    # Aprilia
    "aprilia/rs_457": ("aprilia-bikes", "rs-457"),
    "aprilia/sr_160": ("aprilia-bikes", "sr-160"),
    # Ather
    "ather/ather_450x": ("ather-bikes", "450x"),
    "ather/ather_rizta": ("ather-bikes", "rizta"),
    # Bajaj
    "bajaj/chetak_3201": ("bajaj-bikes", "chetak"),
    "bajaj/dominar_400": ("bajaj-bikes", "dominar-400"),
    "bajaj/freedom_125": ("bajaj-bikes", "freedom-125"),
    "bajaj/pulsar_150": ("bajaj-bikes", "pulsar-150"),
    "bajaj/pulsar_n160": ("bajaj-bikes", "pulsar-n160"),
    "bajaj/pulsar_ns200": ("bajaj-bikes", "new-pulsar-ns200"),
    "bajaj/pulsar_ns400z": ("bajaj-bikes", "pulsar-ns400z"),
    # BMW
    "bmw_motorrad/g_310_gs": ("bmw-bikes", "g-310-gs"),
    "bmw_motorrad/g_310_r": ("bmw-bikes", "g-310-r"),
    # Harley
    "harley_davidson/x440": ("harleydavidson-bikes", "x440"),
    # Hero
    "hero/destini_125": ("hero-bikes", "destini-125"),
    "hero/hf_deluxe": ("hero-bikes", "hf-deluxe"),
    "hero/karizma_xmr": ("hero-bikes", "karizma-xmr"),
    "hero/mavrick_440": ("hero-bikes", "mavrick-440"),
    "hero/splendor_plus": ("hero-bikes", "splendor-plus"),
    "hero/xpulse_200_4v": ("hero-bikes", "xpulse-200-4v"),
    "hero/xtreme_125r": ("hero-bikes", "xtreme-125r"),
    # Honda
    "honda_2wheelers/activa_125": ("honda-bikes", "activa-125"),
    "honda_2wheelers/activa_6g": None,  # Keep existing 44686/activa-6g-right-side-view-2.png
    "honda_2wheelers/cb350_hness": ("honda-bikes", "hness-cb350"),
    "honda_2wheelers/hornet_2_0": ("honda-bikes", "hornet"),
    "honda_2wheelers/sp_125": ("honda-bikes", "sp-125"),
    "honda_2wheelers/shine_125": ("honda-bikes", "shine"),
    "honda_2wheelers/unicorn": ("honda-bikes", "unicorn"),
    # Jawa
    "jawa/42_bobber": ("jawa-bikes", "42-bobber"),
    "jawa/jawa_350": ("jawa-bikes", "350"),
    # Kawasaki
    "kawasaki/ninja_300": ("kawasaki-bikes", "ninja-300"),
    "kawasaki/ninja_500": ("kawasaki-bikes", "ninja-500"),
    "kawasaki/z900": ("kawasaki-bikes", "z900"),
    # KTM
    "ktm/250_duke": ("ktm-bikes", "250-duke"),
    "ktm/390_adventure": ("ktm-bikes", "390-adventure"),
    "ktm/390_duke": ("ktm-bikes", "390-duke"),
    "ktm/rc_390": ("ktm-bikes", "rc-390"),
    # Ola
    "ola_electric/s1_air": ("ola-bikes", "s1-air"),
    "ola_electric/s1_pro": ("ola-bikes", "s1-pro-gen-2"),
    "ola_electric/s1_x": ("ola-bikes", "s1-x"),
    # Royal Enfield
    "royal_enfield/bullet_350": ("royalenfield-bikes", "bullet"),
    "royal_enfield/classic_350": ("royalenfield-bikes", "classic-350"),
    "royal_enfield/continental_gt_650": ("royalenfield-bikes", "continental-gt-650"),
    "royal_enfield/guerrilla_450": ("royalenfield-bikes", "guerrilla-450"),
    "royal_enfield/himalayan_450": ("royalenfield-bikes", "himalayan"),
    "royal_enfield/hunter_350": ("royalenfield-bikes", "hunter-350"),
    "royal_enfield/interceptor_650": ("royalenfield-bikes", "interceptor"),
    "royal_enfield/meteor_350": ("royalenfield-bikes", "meteor-350"),
    # Suzuki
    "suzuki_2wheelers/access_125": ("suzuki-bikes", "access-125"),
    "suzuki_2wheelers/burgman_street": ("suzuki-bikes", "burgman-street-125"),
    "suzuki_2wheelers/gixxer_sf_250": ("suzuki-bikes", "gixxer-sf-250"),
    "suzuki_2wheelers/v_strom_sx_250": ("suzuki-bikes", "v-strom-sx"),
    # Triumph
    "triumph/scrambler_400x": ("triumph-bikes", "scrambler-400x"),
    "triumph/speed_400": ("triumph-bikes", "speed-400"),
    # TVS
    "tvs/apache_rr_310": ("tvs-bikes", "apache-rr-310"),
    "tvs/apache_rtr_160_4v": ("tvs-bikes", "apache-rtr-160-4v"),
    "tvs/jupiter_110": ("tvs-bikes", "jupiter"),
    "tvs/jupiter_125": ("tvs-bikes", "jupiter-125"),
    "tvs/ntorq_125": ("tvs-bikes", "ntorq-125"),
    "tvs/raider_125": ("tvs-bikes", "raider-125"),
    "tvs/ronin": ("tvs-bikes", "ronin"),
    "tvs/iqube": ("tvs-bikes", "iqube"),
    # Yamaha
    "yamaha/aerox_155": ("yamaha-bikes", "aerox-155"),
    "yamaha/fzs_fi_v4": ("yamaha-bikes", "fzs-fi-v4"),
    "yamaha/mt_15_v2": ("yamaha-bikes", "mt-15"),
    "yamaha/r15_v4": ("yamaha-bikes", "yzf-r15"),
}

# Fallbacks for specific known clean PNGs
FALLBACKS = {
    "honda_2wheelers/activa_6g": "https://imgd.aeplcdn.com/1056x594/n/cw/ec/44686/activa-6g-right-side-view-2.png?isig=0",
    "bajaj/pulsar_ns200": "https://imgd.aeplcdn.com/1056x594/n/cw/ec/58025/pulsar-ns-right-side-view-12.png?isig=0",
}


def main():
    conn = sqlite3.connect("data/onroad.db")
    c = conn.cursor()
    
    updates = {}
    
    for mid, spec in EXACT_SLUGS.items():
        if spec is None:
            if mid in FALLBACKS:
                updates[mid] = FALLBACKS[mid]
            continue
            
        brand_part, model_part = spec
        url = f"https://www.bikewale.com/{brand_part}/{model_part}/"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            html = urllib.request.urlopen(req, timeout=6).read().decode("utf-8", errors="ignore")
            og = re.findall(r'<meta[^>]+property=[\"\']og:image[\"\'][^>]+content=[\"\']([^\"\']+)[\"\']', html)
            if og:
                img_url = og[0]
                img_url = re.sub(r'https://imgd\.aeplcdn\.com/[0-9x]+/', 'https://imgd.aeplcdn.com/1056x594/', img_url)
                
                # Test the image
                img_req = urllib.request.Request(img_url, headers=HEADERS)
                with urllib.request.urlopen(img_req, timeout=5) as r:
                    if r.status == 200:
                        updates[mid] = img_url
                        print(f"[FETCHED] {mid:35} -> {img_url}")
                        continue
            print(f"[FAIL OG] {mid} at {url}")
        except Exception as e:
            print(f"[FAIL REQ] {mid} at {url}: {e}")
            if mid in FALLBACKS:
                updates[mid] = FALLBACKS[mid]

    # Apply all updates to database
    print(f"\nApplying {len(updates)} image updates to data/onroad.db...")
    for mid, img in updates.items():
        c.execute("UPDATE models SET image_url = ? WHERE id = ?", (img, mid))
    conn.commit()
    
    # Verification pass on all 66 bike models
    print("\n--- RUNNING FINAL 100% VERIFICATION PASS ---")
    c.execute("""
        SELECT m.id, m.brand_slug, m.name, m.image_url
        FROM models m
        JOIN brands b ON b.slug = m.brand_slug
        WHERE b.vehicle_type = 'bike' OR m.vehicle_type = 'bike'
        ORDER BY m.brand_slug, m.name
    """)
    all_bikes = c.fetchall()
    
    success = []
    broken = []
    
    for mid, bslug, mname, img_url in all_bikes:
        if not img_url:
            broken.append((mid, mname, "MISSING_URL"))
            continue
        try:
            r = urllib.request.urlopen(urllib.request.Request(img_url, headers=HEADERS), timeout=5)
            if r.status == 200:
                success.append((mid, mname, img_url))
            else:
                broken.append((mid, mname, f"HTTP {r.status}"))
        except Exception as e:
            broken.append((mid, mname, str(e)))
            
    print(f"\nTotal Bikes: {len(all_bikes)}")
    print(f"Verified 200 OK: {len(success)}")
    print(f"Broken / Failed: {len(broken)}")
    if broken:
        print("Broken items:")
        for b in broken:
            print(" ", b)
    else:
        print("PERFECT: 100% of bike models now have working, verified high-res images!")


if __name__ == "__main__":
    main()
