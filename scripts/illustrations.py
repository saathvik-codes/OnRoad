"""
Publishes the generated illustrations in design/illustrations/ to the apps:
  * Android: android/app/src/main/assets/illustrations/<name>.webp  (max 1200 px wide, transparency kept)
  * iOS:     ios/OnRoad/Assets.xcassets/<name>.imageset/<name>.png (max 1200 px, compressed PNG)
  * web:     web/public/illustrations/<name>.webp
Only images that exist are published; every screen falls back to its current look when an image is missing.

    python scripts/illustrations.py
"""
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "design" / "illustrations"
ANDROID = ROOT / "android" / "app" / "src" / "main" / "assets" / "illustrations"
IOS = ROOT / "ios" / "OnRoad" / "Assets.xcassets"
WEB = ROOT / "web" / "public" / "illustrations"


def fit(im: Image.Image, max_w: int) -> Image.Image:
    if im.width <= max_w:
        return im
    return im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)


def main():
    for d in (ANDROID, WEB):
        d.mkdir(parents=True, exist_ok=True)
    done = []
    for f in sorted(list(SRC.glob("*.png")) + list(SRC.glob("*.jpg")) + list(SRC.glob("*.jpeg")) + list(SRC.glob("*.webp"))):
        name = f.stem.lower().replace("_", "-")
        im = Image.open(f)
        im = im.convert("RGBA") if im.mode in ("RGBA", "LA", "P") else im.convert("RGB")
        big = fit(im, 1200)
        big.save(ANDROID / f"{name}.webp", "WEBP", quality=82, method=6)
        big.save(WEB / f"{name}.webp", "WEBP", quality=82, method=6)
        iset = IOS / f"{name}.imageset"
        iset.mkdir(parents=True, exist_ok=True)
        big.save(iset / f"{name}.png", "PNG", optimize=True)
        (iset / "Contents.json").write_text(json.dumps({"images": [{"filename": f"{name}.png", "idiom": "universal"}],
                                                        "info": {"author": "xcode", "version": 1}}, indent=1))
        done.append(f"{name} {big.size[0]}x{big.size[1]} ({(ANDROID / f'{name}.webp').stat().st_size // 1024} KB)")
    print("\n".join(done) if done else "no images in design/illustrations yet")


if __name__ == "__main__":
    main()
