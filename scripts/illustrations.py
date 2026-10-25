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
# images whose background cut-out is broken (regenerate, then remove from here)
SKIP = set()
WEB_ONLY = {"og-share", "web-404", "web-dealer-portal", "play-feature-graphic", "store-backdrop"}


def fit(im: Image.Image, max_w: int) -> Image.Image:
    if im.width <= max_w:
        return im
    return im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)


def dark_shadows(im: Image.Image) -> Image.Image:
    """The generator bakes in light-grey soft shadows, which show as white smudges on the dark theme. Semi-transparent,
    near-white, unsaturated pixels (shadows only; solid white objects are opaque) become a soft dark shadow, which
    reads naturally on both themes."""
    if im.mode != "RGBA":
        return im
    import numpy as np
    a = np.asarray(im).astype(np.float32)
    rgb, alpha = a[..., :3], a[..., 3]
    light = rgb.mean(axis=2) > 150
    grey = (rgb.max(axis=2) - rgb.min(axis=2)) < 28
    soft = (alpha > 0) & (alpha < 235)
    m = light & grey & soft
    a[m, 0], a[m, 1], a[m, 2] = 17, 21, 34
    a[m, 3] = alpha[m] * 0.38
    return Image.fromarray(a.clip(0, 255).astype("uint8"), "RGBA")


def main():
    for d in (ANDROID, WEB):
        d.mkdir(parents=True, exist_ok=True)
    done = []
    for f in sorted(list(SRC.glob("*.png")) + list(SRC.glob("*.jpg")) + list(SRC.glob("*.jpeg")) + list(SRC.glob("*.webp"))):
        name = f.stem.lower().replace("_", "-")
        if name in SKIP:
            continue
        im = Image.open(f)
        im = im.convert("RGBA") if im.mode in ("RGBA", "LA", "P") else im.convert("RGB")
        big = dark_shadows(fit(im, 1200))
        big.save(WEB / f"{name}.webp", "WEBP", quality=82, method=6)
        if name == "og-share":
            og = Image.new("RGB", (1200, 630), (244, 245, 248))
            s = im.convert("RGBA").copy(); s.thumbnail((1200, 630), Image.LANCZOS)
            og.paste(s, ((1200 - s.width) // 2, (630 - s.height) // 2), s)
            og.save(WEB.parent / "og.jpg", "JPEG", quality=86)
        if name in WEB_ONLY:
            done.append(f"{name} (web only)")
            continue
        big.save(ANDROID / f"{name}.webp", "WEBP", quality=82, method=6)
        iset = IOS / f"{name}.imageset"
        iset.mkdir(parents=True, exist_ok=True)
        big.save(iset / f"{name}.png", "PNG", optimize=True)
        (iset / "Contents.json").write_text(json.dumps({"images": [{"filename": f"{name}.png", "idiom": "universal"}],
                                                        "info": {"author": "xcode", "version": 1}}, indent=1))
        done.append(f"{name} {big.size[0]}x{big.size[1]} ({(ANDROID / f'{name}.webp').stat().st_size // 1024} KB)")
    print("\n".join(done) if done else "no images in design/illustrations yet")


if __name__ == "__main__":
    main()
