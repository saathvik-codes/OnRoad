"""
Builds the app-store images for OnRoad into design/store/out/:
  icon-512.png, icon-114.png        app icons (Amazon: 512x512 and 114x114 PNG)
  feature-1024x500.png              promotional / feature graphic
  screenshot-N.png (1200x1920)      captioned phone screenshots (Amazon accepts 1200x1920 portrait)

    python design/store/make_store_assets.py [screenshot-folder]   # default D:/dev
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent / "out"
SRC = Path(sys.argv[1] if len(sys.argv) > 1 else "D:/dev")
ICON = ROOT / "web" / "public" / "icon-512.png"
BOLD, REG = "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/segoeui.ttf"
ORANGE, INK, PAPER, MUTE = (255, 77, 46), (20, 20, 24), (247, 245, 242), (95, 95, 105)

SHOTS = [
    ("shot_home_light.png", "The real on-road price\nof every car", "Road tax, registration and insurance for your city"),
    ("shot_model2_light.png", "Every rupee, itemised", "Compare variants and see exactly what you pay"),
    ("shot_explore_light.png", "Find your car faster", "Filter by budget, body type and fuel"),
    ("shot_offers.png", "Offers from carmakers", "Festive benefits, updated from official sites"),
    ("shot_showrooms.png", "Showrooms near you", "Directions, calls and buyer ratings"),
    ("shot_profile2.png", "Alerts when prices drop", "Set a target price and we tell you once it's there"),
    ("shot_home_dark.png", "Easy on the eyes at night", "Full dark mode"),
]


def rounded(im: Image.Image, r: int) -> Image.Image:
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, *im.size), r, fill=255)
    im = im.convert("RGBA")
    im.putalpha(m)
    return im


def phone(path: Path, height: int) -> Image.Image:
    """The screenshot in a thin dark bezel with rounded corners."""
    s = Image.open(path).convert("RGB")
    w = round(s.width * height / s.height)
    s = rounded(s.resize((w, height), Image.LANCZOS), 44)
    b = 14
    frame = rounded(Image.new("RGB", (w + 2 * b, height + 2 * b), (28, 28, 32)), 56)
    frame.alpha_composite(s, (b, b))
    return frame


def shadowed(canvas: Image.Image, im: Image.Image, xy: tuple[int, int]) -> None:
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    a = im.split()[3].point(lambda v: v * 0.35)
    sh.paste((0, 0, 0, 255), (xy[0], xy[1] + 24), a)
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(28)))
    canvas.alpha_composite(im, xy)


def screenshot(i: int, file: str, title: str, sub: str) -> None:
    W, H = 1200, 1920
    c = Image.new("RGBA", (W, H), PAPER + (255,))
    d = ImageDraw.Draw(c)
    d.rectangle((0, 0, W, 10), fill=ORANGE)
    tf, sf = ImageFont.truetype(BOLD, 76), ImageFont.truetype(REG, 40)
    y = 120
    for line in title.split("\n"):
        d.text((W / 2, y), line, font=tf, fill=INK, anchor="mt")
        y += 92
    d.text((W / 2, y + 18), sub, font=sf, fill=MUTE, anchor="mt")
    p = phone(SRC / file, H - (y + 130) + 120)
    shadowed(c, p, ((W - p.width) // 2, y + 110))
    c.convert("RGB").save(OUT / f"screenshot-{i}.png", optimize=True)


def feature() -> None:
    W, H = 1024, 500
    c = Image.new("RGBA", (W, H), INK + (255,))
    d = ImageDraw.Draw(c)
    d.text((56, 92), "on", font=ImageFont.truetype(BOLD, 64), fill=(255, 255, 255))
    on_w = d.textlength("on", font=ImageFont.truetype(BOLD, 64))
    d.text((56 + on_w, 92), "road", font=ImageFont.truetype(BOLD, 64), fill=ORANGE)
    hf = ImageFont.truetype(BOLD, 46)
    d.text((56, 210), "The real on-road price", font=hf, fill=(255, 255, 255))
    d.text((56, 266), "of every car in India", font=hf, fill=(255, 255, 255))
    d.text((56, 350), "Tax, insurance and offers for your city.\nQuotes from showrooms near you.",
           font=ImageFont.truetype(REG, 26), fill=(190, 190, 198), spacing=10)
    p = phone(SRC / "shot_model2_dark.png", 760)
    shadowed(c, p, (W - p.width - 70, 60))
    c.convert("RGB").save(OUT / "feature-1024x500.png", optimize=True)


def icons() -> None:
    ic = Image.open(ICON).convert("RGBA")
    for s in (512, 114):
        ic.resize((s, s), Image.LANCZOS).save(OUT / f"icon-{s}.png", optimize=True)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    icons()
    feature()
    for n, row in enumerate(SHOTS, 1):
        screenshot(n, *row)
    print("wrote", sorted(p.name for p in OUT.iterdir()))
