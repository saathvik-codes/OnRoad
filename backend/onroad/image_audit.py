"""
Checks that each model's main photo actually shows that model, by looking at the picture (not its address).

CLIP (openai/clip-vit-base-patch32, run locally) scores the photo against "a photo of a <brand> <model>" for every
active model of the same brand. A photo is flagged when another model of the brand clearly wins (its probability is at
least MARGIN above this model's). For a flagged model, its own gallery and variant photos are scored the same way and
the best one that CLIP attributes to this model becomes the main photo. Nothing is changed without --write.

    python -m onroad.image_audit            # dry run: list suspect photos
    python -m onroad.image_audit --write    # replace them where a better own photo exists
"""
from __future__ import annotations

import io
import sys

from . import db

MARGIN = 0.25
_model = None


def _clip():
    global _model
    if _model is None:
        from transformers import CLIPModel, CLIPProcessor
        name = "openai/clip-vit-base-patch32"
        _model = (CLIPModel.from_pretrained(name).eval(), CLIPProcessor.from_pretrained(name))
    return _model


def _image(url: str):
    """The photo as RGB, or None. Downloads the original (photos are only looked at, not stored)."""
    from PIL import Image
    if url.startswith("/models/"):
        p = db.ROOT / "data" / "model_images" / url[len("/models/"):]
        return Image.open(p).convert("RGB") if p.is_file() else None
    try:
        import httpx
        from .brochure_specs import UA
        r = httpx.get(url, headers=UA, timeout=20, follow_redirects=True)
        return Image.open(io.BytesIO(r.content)).convert("RGB") if r.status_code == 200 else None
    except Exception:
        return None


def scores(img, labels: list[str]) -> list[float]:
    import torch
    m, proc = _clip()
    with torch.no_grad():
        inp = proc(text=[f"a photo of a {l}, a car" for l in labels], images=img, return_tensors="pt", padding=True)
        return m(**inp).logits_per_image.softmax(dim=1)[0].tolist()


def audit(write: bool = False) -> dict:
    conn = db.connect()
    brands = {}
    for r in conn.execute("""SELECT m.id, m.name, b.name, m.image_url FROM models m JOIN brands b ON b.slug = m.brand_slug
                             WHERE m.active = 1 AND b.vehicle_type = 'car'"""):
        brands.setdefault(r[2], []).append(r)
    flagged, fixed = [], 0
    for brand, models in brands.items():
        if len(models) < 2:
            continue
        labels = [f"{brand} {m[1]}" for m in models]
        for i, (mid, name, _, url) in enumerate(models):
            img = url and _image(url)
            if img is None:
                continue
            p = scores(img, labels)
            best = max(range(len(p)), key=p.__getitem__)
            if best == i or p[best] - p[i] < MARGIN:
                continue
            flagged.append((mid, labels[best], round(p[best], 2), round(p[i], 2)))
            # look for a better photo of its own
            cands = [r[0] for r in conn.execute("SELECT url FROM model_gallery WHERE model_id = ?", (mid,))]
            cands += [r[0] for r in conn.execute("SELECT DISTINCT image_url FROM variants WHERE model_id = ? AND image_url IS NOT NULL", (mid,))]
            good = None
            for c in cands:
                ci = _image(c)
                if ci is None:
                    continue
                pc = scores(ci, labels)
                if max(range(len(pc)), key=pc.__getitem__) == i:
                    good = c
                    break
            print(f"{mid}: looks like {labels[best]} ({p[best]:.2f} vs {p[i]:.2f})" + (f" -> {good[-60:]}" if good else " (no better own photo)"))
            if write and good:
                conn.execute("UPDATE models SET image_url = ? WHERE id = ?", (good, mid)); conn.commit(); fixed += 1
    return {"flagged": len(flagged), "fixed": fixed}


if __name__ == "__main__":
    print(audit(write="--write" in sys.argv))
