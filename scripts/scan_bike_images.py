"""
Scan and update all bike model images in data/onroad.db.
Fetches high-res, transparent official images from BikeWale/CarDekho/OEM CDNs,
verifies HTTP 200 for every single image, and updates the database.
"""

import sqlite3
import urllib.request
import re
import json
import time

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

BRAND_SLUGS = {
    "aprilia": "aprilia-bikes",
    "ather": "ather-bikes",
    "bmw_motorrad": "bmw-bikes",
    "bajaj": "bajaj-bikes",
    "harley_davidson": "harleydavidson-bikes",
    "hero": "hero-bikes",
    "honda_2wheelers": "honda-bikes",
    "jawa": "jawa-bikes",
    "ktm": "ktm-bikes",
    "kawasaki": "kawasaki-bikes",
    "ola_electric": "ola-bikes",
    "royal_enfield": "royalenfield-bikes",
    "suzuki_2wheelers": "suzuki-bikes",
    "tvs": "tvs-bikes",
    "triumph": "triumph-bikes",
    "yamaha": "yamaha-bikes",
}

# Manual overrides for models where slug names diverge on BikeWale
MODEL_PAGE_OVERRIDES = {
    "bmw_motorrad/g_310_gs": "bmw-bikes/g-310-gs",
    "bmw_motorrad/g_310_r": "bmw-bikes/g-310-r",
    "honda_2wheelers/shine_125": "honda-bikes/shine",
    "honda_2wheelers/sp_125": "honda-bikes/sp-125",
    "honda_2wheelers/activa_6g": "honda-bikes/activa",
    "honda_2wheelers/activa_125": "honda-bikes/activa-125",
    "honda_2wheelers/cb350_hness": "honda-bikes/hness-cb350",
    "honda_2wheelers/hornet_2_0": "honda-bikes/hornet-20",
    "honda_2wheelers/unicorn": "honda-bikes/unicorn",
    "triumph/scrambler_400x": "triumph-bikes/scrambler-400x",
    "triumph/speed_400": "triumph-bikes/speed-400",
    "yamaha/fzs_fi_v4": "yamaha-bikes/fzs-fi-v4",
    "yamaha/r15_v4": "yamaha-bikes/yzf-r15",
    "yamaha/mt_15_v2": "yamaha-bikes/mt-15",
    "yamaha/aerox_155": "yamaha-bikes/aerox-155",
    "bajaj/dominar_400": "bajaj-bikes/dominar-400",
    "bajaj/freedom_125": "bajaj-bikes/freedom",
    "bajaj/pulsar_ns400z": "bajaj-bikes/pulsar-ns400z",
    "bajaj/pulsar_n160": "bajaj-bikes/pulsar-n160",
    "bajaj/pulsar_ns200": "bajaj-bikes/pulsar-ns200",
    "bajaj/pulsar_150": "bajaj-bikes/pulsar-150",
    "bajaj/chetak_3201": "bajaj-bikes/chetak",
    "hero/karizma_xmr": "hero-bikes/karizma-xmr",
    "hero/mavrick_440": "hero-bikes/mavrick-440",
    "hero/splendor_plus": "hero-bikes/splendor-plus",
    "hero/xpulse_200_4v": "hero-bikes/xpulse-200-4v",
    "hero/xtreme_125r": "hero-bikes/xtreme-125r",
    "hero/hf_deluxe": "hero-bikes/hf-deluxe",
    "hero/destini_125": "hero-bikes/destini-125",
    "jawa/42_bobber": "jawa-bikes/42-bobber",
    "jawa/jawa_350": "jawa-bikes/350",
    "harley_davidson/x440": "harleydavidson-bikes/x440",
    "ktm/250_duke": "ktm-bikes/250-duke",
    "ktm/390_duke": "ktm-bikes/390-duke",
    "ktm/390_adventure": "ktm-bikes/390-adventure",
    "ktm/rc_390": "ktm-bikes/rc-390",
    "ola_electric/s1_pro": "ola-bikes/s1-pro-gen-2",
    "ola_electric/s1_air": "ola-bikes/s1-air",
    "ola_electric/s1_x": "ola-bikes/s1-x",
    "royal_enfield/bullet_350": "royalenfield-bikes/bullet",
    "royal_enfield/classic_350": "royalenfield-bikes/classic-350",
    "royal_enfield/hunter_350": "royalenfield-bikes/hunter-350",
    "royal_enfield/meteor_350": "royalenfield-bikes/meteor-350",
    "royal_enfield/himalayan_450": "royalenfield-bikes/himalayan",
    "royal_enfield/continental_gt_650": "royalenfield-bikes/continental-gt-650",
    "royal_enfield/interceptor_650": "royalenfield-bikes/interceptor",
    "royal_enfield/guerrilla_450": "royalenfield-bikes/guerrilla-450",
    "suzuki_2wheelers/access_125": "suzuki-bikes/access-125",
    "suzuki_2wheelers/burgman_street": "suzuki-bikes/burgman-street-125",
    "suzuki_2wheelers/gixxer_sf_250": "suzuki-bikes/gixxer-sf-250",
    "suzuki_2wheelers/v_strom_sx_250": "suzuki-bikes/v-strom-sx",
    "tvs/apache_rr_310": "tvs-bikes/apache-rr-310",
    "tvs/apache_rtr_160_4v": "tvs-bikes/apache-rtr-160-4v",
    "tvs/jupiter_110": "tvs-bikes/jupiter",
    "tvs/jupiter_125": "tvs-bikes/jupiter-125",
    "tvs/ntorq_125": "tvs-bikes/ntorq-125",
    "tvs/raider_125": "tvs-bikes/raider-125",
    "tvs/ronin": "tvs-bikes/ronin",
    "tvs/iqube": "tvs-bikes/iqube",
    "kawasaki/ninja_300": "kawasaki-bikes/ninja-300",
    "kawasaki/ninja_500": "kawasaki-bikes/ninja-500",
    "kawasaki/z900": "kawasaki-bikes/z900",
    "ather/ather_450x": "ather-bikes/450x",
    "ather/ather_rizta": "ather-bikes/rizta",
    "aprilia/rs_457": "aprilia-bikes/rs-457",
    "aprilia/sr_160": "aprilia-bikes/sr-160",
}


def check_url(url: str) -> bool:
    if not url:
        return False
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def get_model_image(page_slug: str) -> str | None:
    url = f"https://www.bikewale.com/{page_slug}/"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        html = urllib.request.urlopen(req, timeout=6).read().decode("utf-8", errors="ignore")
        
        # 1. Find all aeplcdn URLs
        pattern = r"https://imgd\.aeplcdn\.com/(?:[0-9x]+)/n/cw/ec/([0-9]+)/([^\"\'\s>]+\.(?:png|jpeg|webp))"
        matches = set(re.findall(pattern, html))
        
        # Filter for candidates
        candidates = []
        for aid, fn in matches:
            fn_l = fn.lower()
            score = 0
            if fn_l.endswith(".png"):
                score += 5
            elif fn_l.endswith(".webp"):
                score += 2
            
            if "right-side-view" in fn_l or "left-side-view" in fn_l or "side-view" in fn_l:
                score += 10
            elif "right-front-three-quarter" in fn_l or "three-quarter" in fn_l:
                score += 5
            
            # Avoid seats, headlights, accessories
            if any(bad in fn_l for bad in ["seat", "light", "wheel", "meter", "handle", "exhaust", "cluster", "brake"]):
                score -= 10
                
            candidates.append((score, aid, fn))
            
        candidates.sort(key=lambda x: -x[0])
        
        for score, aid, fn in candidates:
            # Construct high-res transparent URL
            test_url = f"https://imgd.aeplcdn.com/1056x594/n/cw/ec/{aid}/{fn}?isig=0"
            if check_url(test_url):
                return test_url
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        
    return None


def main():
    conn = sqlite3.connect("data/onroad.db")
    c = conn.cursor()
    c.execute("""
        SELECT m.id, m.brand_slug, m.name, m.image_url
        FROM models m
        JOIN brands b ON b.slug = m.brand_slug
        WHERE b.vehicle_type = 'bike' OR m.vehicle_type = 'bike'
        ORDER BY m.brand_slug, m.name
    """)
    models = c.fetchall()
    
    print(f"Processing {len(models)} bike models...")
    
    updated_count = 0
    valid_count = 0
    failed_models = []
    
    for mid, bslug, mname, cur_url in models:
        # First check if cur_url is already valid
        if cur_url and check_url(cur_url):
            print(f"[OK ALREADY] {mid} ({mname})")
            valid_count += 1
            continue
            
        print(f"[SCANNING] {mid} ({mname})...")
        page_slug = MODEL_PAGE_OVERRIDES.get(mid)
        if not page_slug:
            # Fallback deduction
            brand_part = BRAND_SLUGS.get(bslug, f"{bslug}-bikes")
            model_part = mid.split("/")[-1].replace("_", "-")
            page_slug = f"{brand_part}/{model_part}"
            
        new_url = get_model_image(page_slug)
        if new_url and check_url(new_url):
            c.execute("UPDATE models SET image_url = ? WHERE id = ?", (new_url, mid))
            conn.commit()
            print(f"  -> [UPDATED] {new_url}")
            updated_count += 1
            valid_count += 1
        else:
            print(f"  -> [FAILED] could not find valid image for {mid}")
            failed_models.append((mid, mname, page_slug))
            
        time.sleep(0.2)
        
    print("\n" + "="*50)
    print(f"Finished! Total: {len(models)}, Valid: {valid_count}, Newly Updated: {updated_count}, Failed: {len(failed_models)}")
    if failed_models:
        print("Failed models:")
        for f in failed_models:
            print(" ", f)


if __name__ == "__main__":
    main()
