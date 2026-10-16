"""Two web assets for the home page promo blade.

  giftcard-blade  2000x560, the pine/snow ground on its own. It sits full-bleed
                  behind the band under object-fit: cover, so it carries no
                  content that could be cropped away — just atmosphere, with the
                  glow pushed right where the cards land on a wide screen.

  giftcard-cards  the $100 and $20 cards on transparency, as a foreground image.
                  Keeping them out of the background is what lets the band
                  reflow on a phone: the cards drop below the copy instead of
                  being sliced off the right edge.

This poppler has no -transp, so the alpha is recovered exactly rather than
keyed out: render the same page over white and over black, and for a composite
over background B, result = C*a + B*(1-a). Subtracting the two renders gives
  a = 1 - (white - black) / 255,  C = black / a
which is exact for soft shadows and antialiased edges alike — a chroma key
would leave a dark halo on every rounded corner.

Run: python3 blade_art.py
"""
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader

from holiday import OUT, pine_ground, card_pair, PAIR

OUT.mkdir(exist_ok=True)


def rasterise(draw, W, H, bg, path):
    """Draw the page over a flat background and return it as an array."""
    pdf = str(OUT / "_tmp.pdf")
    c = rl_canvas.Canvas(pdf, pagesize=(W, H))
    c.setFillColorRGB(*bg)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    draw(c)
    c.showPage()
    c.save()
    stem = str(Path(path).with_suffix(""))
    subprocess.run(["pdftoppm", "-r", "72", "-png", "-singlefile", pdf, stem], check=True)
    return np.asarray(Image.open(stem + ".png").convert("RGB")).astype(np.float32)


def with_alpha(draw, W, H, path):
    black = rasterise(draw, W, H, (0, 0, 0), str(OUT / "_k.png"))
    white = rasterise(draw, W, H, (1, 1, 1), str(OUT / "_w.png"))

    a = 1.0 - (white - black).mean(axis=2) / 255.0
    a = np.clip(a, 0.0, 1.0)
    safe = np.maximum(a, 1e-4)[..., None]
    rgb = np.clip(black / safe, 0, 255)

    out = np.dstack([rgb, a[..., None] * 255.0]).astype(np.uint8)
    im = Image.fromarray(out, "RGBA")
    im.save(path)
    for f in (OUT / "_k.png", OUT / "_w.png", OUT / "_tmp.pdf"):
        f.unlink(missing_ok=True)
    cover = (a > 0.02).mean()
    print(f"  {Path(path).name:24s} {im.size[0]}x{im.size[1]}  "
          f"{cover*100:.0f}% of the canvas is ink  "
          f"{Path(path).stat().st_size//1024}KB")
    return im


def blade_bg():
    W, H = 2000, 560
    im = pine_ground(W, H, 1320, 250, seed=33)
    p = OUT / "giftcard-blade.png"
    im.save(p)
    print(f"  {p.name:24s} {W}x{H}  {p.stat().st_size//1024}KB")


def cards():
    sc = 1.42
    pad = 26
    W = round(PAIR["left"] * sc + PAIR["right"] * sc) + pad * 2
    H = round(PAIR["up"] * sc + PAIR["down"] * sc) + pad * 2
    cx = pad + PAIR["left"] * sc
    cy = pad + PAIR["down"] * sc

    im = with_alpha(lambda c: card_pair(c, cx, cy, sc), W, H,
                    str(OUT / "giftcard-cards.png"))

    # The shadow is the whole reason for doing this the hard way: if the corners
    # came back fully opaque, the alpha recovery silently failed and the asset
    # would ship as a black rectangle on a pine band.
    a = np.asarray(im)[..., 3]
    assert a[0, 0] == 0 and a[-1, -1] == 0, "corners are not transparent"
    assert 0 < (a > 0).mean() < 0.95, "alpha looks wrong"
    soft = ((a > 8) & (a < 230)).mean()
    assert soft > 0.02, f"no soft edge recovered ({soft:.3%}) — shadow is missing"
    print(f"  soft (shadow/antialiased) pixels: {soft*100:.1f}%")


if __name__ == "__main__":
    print("blade assets:")
    blade_bg()
    cards()
    print("done ->", OUT)
