#!/usr/bin/env python3
"""Journal cover images, derived from photographs already in assets/.

One cover per post (S-28). Bonnie has no artwork for the twelve journal
posts, so each cover is a distinct crop of a photograph she already owns,
with a light tonal wash in the brand palette so no two read the same. Each
is a placeholder in the honest sense: swap the file in assets/ for real
artwork and nothing else changes.

Run:  python3 make_covers.py
"""
import pathlib
from PIL import Image, ImageEnhance

ROOT = pathlib.Path(__file__).parent
ASSETS = ROOT / "assets"
W, H = 1400, 933  # 3:2, matching the existing journal images

# slug -> (source, horizontal focus 0-1, vertical focus 0-1, zoom, wash rgb, wash strength)
INK, SAGE, GOLD, CREAM = (25, 48, 77), (168, 184, 166), (199, 169, 107), (251, 248, 241)

COVERS = {
    "why-anxiety-returns-after-therapy":            ("hero-water-ripple.jpg",   0.20, 0.50, 1.00, INK,   0.10),
    "cortisol-connection-distance-healing":         ("orbit-art.jpg",           0.30, 0.35, 1.15, SAGE,  0.10),
    "seekers-dilemma-successful-professionals":     ("botanical-still-life.jpg",0.25, 0.40, 1.10, CREAM, 0.12),
    "beyond-talk-therapy-somatic-trauma":           ("hero-water-ripple.jpg",   0.55, 0.55, 1.25, INK,   0.14),
    "revenue-ceiling-business-blocks":              ("orbit-art.jpg",           0.70, 0.45, 1.00, GOLD,  0.09),
    "what-happens-in-a-session":                    ("botanical-still-life.jpg",0.60, 0.55, 1.20, CREAM, 0.08),
    "quantum-entanglement-distance-healing":        ("orbit-art.jpg",           0.50, 0.70, 1.30, INK,   0.12),
    "migraines-ibs-chronic-pain":                   ("hero-water-ripple.jpg",   0.85, 0.40, 1.10, SAGE,  0.12),
    "why-eft-results-vary":                         ("botanical-still-life.jpg",0.40, 0.70, 1.30, SAGE,  0.10),
    "nlp-eft-energy-healing-difference":            ("orbit-art.jpg",           0.15, 0.60, 1.20, CREAM, 0.10),
    "relationship-healing-without-couples-therapy": ("botanical-still-life.jpg",0.80, 0.30, 1.15, GOLD,  0.10),
    "how-to-choose-an-energy-healer":               ("hero-water-ripple.jpg",   0.40, 0.65, 1.35, CREAM, 0.11),
}


def crop(im: Image.Image, fx: float, fy: float, zoom: float) -> Image.Image:
    """Crop to 3:2 around a focal point, then resize. zoom > 1 tightens in."""
    target = W / H
    sw, sh = im.size
    box_w = min(sw, sh * target) / zoom
    box_h = box_w / target
    if box_h > sh:
        box_h = sh
        box_w = box_h * target
    left = (sw - box_w) * fx
    top = (sh - box_h) * fy
    out = im.crop((round(left), round(top), round(left + box_w), round(top + box_h)))
    return out.resize((W, H), Image.LANCZOS)


def wash(im: Image.Image, rgb: tuple, strength: float) -> Image.Image:
    """A quiet tint so each cover sits apart from its siblings."""
    layer = Image.new("RGB", im.size, rgb)
    return Image.blend(im, layer, strength)


def main() -> int:
    made = []
    for slug, (src, fx, fy, zoom, rgb, strength) in COVERS.items():
        source = ASSETS / src
        if not source.exists():
            print(f"  MISSING source {src} for {slug}")
            continue
        im = Image.open(source).convert("RGB")
        im = crop(im, fx, fy, zoom)
        im = wash(im, rgb, strength)
        im = ImageEnhance.Contrast(im).enhance(0.97)
        out = ASSETS / f"journal-{slug}-cover.jpg"
        im.save(out, "JPEG", quality=82, optimize=True, progressive=True)
        made.append((out.name, out.stat().st_size // 1024, src))
    for name, kb, src in made:
        print(f"  cover  {name}  {kb} KB  (from {src})")
    print(f"\n{len(made)} cover(s) written to assets/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
