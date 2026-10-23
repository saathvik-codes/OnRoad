"""
Download missing brand logos (SVG) from Wikimedia Commons into data/logos/<slug>.svg and record the source in CREDITS.md.
Logos are trademarks of their owners, used only to identify the brand.

    python scripts/fetch_logos.py
"""
import json
import re
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
LOGOS = ROOT / "data" / "logos"
API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "OnRoadBot/0.1 (logo identification; contact: saathvikk202@gmail.com)"}

# slug -> Commons search phrase (exact file titles vary, so search and keep the best SVG hit)
BRANDS = {
    "maruti_suzuki": "Maruti Suzuki logo", "hyundai": "Hyundai Motor Company logo", "tata_motors": "Tata Motors logo",
    "mahindra": "Mahindra logo 2021", "kia": "Kia logo 2021", "toyota": "Toyota logo", "honda": "Honda logo automobile",
    "mg": "MG Motor logo", "skoda": "Skoda logo 2022", "volkswagen": "Volkswagen logo 2019", "renault": "Renault logo 2021",
    "nissan": "Nissan logo 2020", "citroen": "Citroen logo 2022", "jeep": "Jeep logo", "byd": "BYD logo",
    "isuzu": "Isuzu logo", "force_motors": "Force Motors logo", "tesla": "Tesla Motors logo", "vinfast": "VinFast logo",
    "ferrari": "Ferrari logo", "rolls_royce": "Rolls-Royce Motor Cars logo", "bentley": "Bentley logo",
    "maserati": "Maserati logo", "aston_martin": "Aston Martin logo", "mclaren": "McLaren logo", "lotus": "Lotus Cars logo",
}


def search(client: httpx.Client, phrase: str) -> list[str]:
    r = client.get(API, params={"action": "query", "list": "search", "srsearch": f"{phrase} filetype:drawing",
                                "srnamespace": 6, "srlimit": 15, "format": "json"})
    return [h["title"] for h in r.json().get("query", {}).get("search", [])]


def file_url(client: httpx.Client, title: str) -> tuple[str, str] | None:
    r = client.get(API, params={"action": "query", "titles": title, "prop": "imageinfo", "iiprop": "url|extmetadata", "format": "json"})
    page = next(iter(r.json()["query"]["pages"].values()))
    info = (page.get("imageinfo") or [None])[0]
    if not info:
        return None
    lic = (info.get("extmetadata", {}).get("LicenseShortName", {}) or {}).get("value", "unknown")
    return info["url"], lic


def main() -> None:
    only = set(sys.argv[1:])
    credits = LOGOS / "CREDITS.md"
    with httpx.Client(timeout=30, headers=UA, follow_redirects=True) as client:
        for slug, phrase in BRANDS.items():
            if only and slug not in only:
                continue
            if any((LOGOS / f"{slug}.{e}").exists() for e in ("svg", "png")):
                continue
            words = [w for w in re.findall(r"[a-z]+", phrase.lower()) if w not in ("logo", "motor", "motors", "company", "cars", "automobile")]
            hits = [t for t in search(client, phrase) if t.lower().endswith(".svg") and "logo" in t.lower()
                    and all(w in t.lower().replace("š", "s").replace("ë", "e") for w in words[:1])]
            if not hits:
                print(f"{slug:<15} no SVG found")
                continue
            got = file_url(client, hits[0])
            if not got:
                continue
            url, lic = got
            svg = client.get(url).content
            if b"<svg" not in svg[:2000]:
                print(f"{slug:<15} not an svg")
                continue
            (LOGOS / f"{slug}.svg").write_bytes(svg)
            with credits.open("a", encoding="utf-8") as f:
                f.write(f"- {slug}: {hits[0]} — {url} — {lic}; trademark of its owner, used only to identify the brand.\n")
            print(f"{slug:<15} {hits[0]}  ({lic})")
            time.sleep(0.5)


if __name__ == "__main__":
    main()
