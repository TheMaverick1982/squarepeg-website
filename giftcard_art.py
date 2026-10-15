"""Artwork for /gift-card-bonus/ — the hero background and the social card.

Two files rather than one, because the two slots crop differently and want
opposite things:

  giftcard-hero  2000x1125, motif on the RIGHT. It sits full-bleed behind the
                 headline, which is left-aligned, so the left half stays dark
                 and quiet on purpose.
  giftcard-og    900x746, motif CENTRED. make_og() cover-crops the middle of
                 this into a 760x630 panel on the right of the share card, so
                 anything near an edge is lost.

Both carry the actual numbers. A stock photo of a $25 card on a page about
$100 and $20 is just a wrong number in a nice typeface.

Run:  python3 giftcard_art.py
"""
import math
import subprocess
from pathlib import Path

from PIL import Image
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color

ROOT = Path(__file__).parent
FONTS = ROOT / "src" / "fonts-ttf"
IMG_SRC = ROOT / "assets" / "img-src"
LOGO_ON_DARK = ROOT / "src" / "brand" / "logo-on-dark.png"

for alias, fn in [("D", "big-shoulders-display-latin-900-normal"),
                  ("B", "figtree-latin-800-normal"),
                  ("M", "figtree-latin-600-normal")]:
    pdfmetrics.registerFont(TTFont(alias, str(FONTS / f"{fn}.ttf")))

RED = HexColor("#D50117")
RED_DEEP = HexColor("#8E0310")
FLAME = HexColor("#FFB524")
INK = HexColor("#1A1614")
WHITE = HexColor("#FFFFFF")


_WHITE_LOGO = []


def _white_logo():
    """The wordmark reversed out solid. logo-on-dark keeps the script red,
    which on a red card is red on red — i.e. nothing."""
    if not _WHITE_LOGO:
        im = Image.open(LOGO_ON_DARK).convert("RGBA")
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                a = px[x, y][3]
                if a:
                    px[x, y] = (255, 255, 255, a)
        _WHITE_LOGO.append(im)
    return _WHITE_LOGO[0]


def backdrop(w, h, cx, cy):
    """Warm near-black with an ember glow behind the cards. Built in pixels so
    there are no seams — a gradient drawn as stacked translucent rectangles
    leaves a hairline at every join, which is invisible on paper and obvious on
    a backlit screen."""
    im = Image.new("RGB", (w, h))
    px = im.load()
    far = math.hypot(max(cx, w - cx), max(cy, h - cy))
    for y in range(h):
        for x in range(w):
            t = min(1.0, math.hypot(x - cx, y - cy) / far) ** 0.85
            px[x, y] = (
                int(round(96 * (1 - t) + 20 * t)),
                int(round(22 * (1 - t) + 17 * t)),
                int(round(16 * (1 - t) + 16 * t)),
            )
    return im


def tracked(c, t, f, s, x, y, track, fill):
    c.setFont(f, s)
    c.setFillColor(fill)
    for ch in t:
        c.drawString(x, y, ch)
        x += c.stringWidth(ch, f, s) + track


def centered(c, t, f, s, cx, y, fill):
    c.setFont(f, s)
    c.setFillColor(fill)
    c.drawCentredString(cx, y, t)


def card_100(c, cx, cy, w, h, rot):
    """The card you buy. Red, with the wordmark and the number."""
    c.saveState()
    c.translate(cx, cy)
    c.rotate(rot)
    c.setFillColor(Color(0, 0, 0, alpha=0.38))
    c.roundRect(-w / 2 + 10, -h / 2 - 14, w, h, h * 0.075, fill=1, stroke=0)
    c.setFillColor(RED)
    c.roundRect(-w / 2, -h / 2, w, h, h * 0.075, fill=1, stroke=0)
    c.setFillColor(RED_DEEP)                       # magnetic-stripe band
    c.rect(-w / 2, -h / 2 + h * 0.13, w, h * 0.085, fill=1, stroke=0)

    lw = w * 0.34
    logo = _white_logo()
    lh = lw * logo.height / logo.width
    c.drawImage(ImageReader(logo), -w / 2 + w * 0.070, h / 2 - lh - h * 0.085,
                lw, lh, mask="auto")
    centered(c, "$100", "D", h * 0.40, 0, -h * 0.155, WHITE)
    tracked(c, "GIFT CARD", "B", h * 0.055, -w / 2 + w * 0.070, -h / 2 + h * 0.255,
            h * 0.028, Color(1, 1, 1, alpha=0.82))
    c.restoreState()


def card_20(c, cx, cy, w, h, rot):
    """The one that comes with it. Amber, so it reads as the bonus."""
    c.saveState()
    c.translate(cx, cy)
    c.rotate(rot)
    c.setFillColor(Color(0, 0, 0, alpha=0.42))
    c.roundRect(-w / 2 + 8, -h / 2 - 12, w, h, h * 0.075, fill=1, stroke=0)
    c.setFillColor(FLAME)
    c.roundRect(-w / 2, -h / 2, w, h, h * 0.075, fill=1, stroke=0)
    tracked(c, "ON US", "B", h * 0.075, -w / 2 + w * 0.085, h / 2 - h * 0.215,
            h * 0.038, INK)
    centered(c, "$20", "D", h * 0.42, 0, -h * 0.17, INK)
    c.restoreState()


def build(name, W, H, cx, cy, scale, spread, rot_a, rot_b):
    pdf = IMG_SRC / f"{name}.pdf"
    c = rl_canvas.Canvas(str(pdf), pagesize=(W, H))
    c.drawImage(ImageReader(backdrop(W, H, cx, H - cy)), 0, 0, W, H)

    w20, h20 = 460 * scale, 294 * scale
    card_20(c, cx + spread * 1.62, cy + spread * 1.18, w20, h20, rot_b)
    w100, h100 = 700 * scale, 440 * scale
    card_100(c, cx - spread * 0.42, cy - spread * 0.34, w100, h100, rot_a)

    c.showPage()
    c.save()
    png = IMG_SRC / f"{name}.png"
    subprocess.run(["pdftoppm", "-r", "72", "-png", "-singlefile", str(pdf),
                    str(png.with_suffix(""))], check=True)
    pdf.unlink()
    im = Image.open(png).convert("RGB")
    im.save(png)
    print(f"wrote {png.name}  {im.size[0]}x{im.size[1]}")


if __name__ == "__main__":
    # Hero: motif right of centre, left half left dark for the headline.
    build("giftcard-hero", 2000, 1125, cx=1290, cy=548, scale=1.00,
          spread=210, rot_a=-6, rot_b=9)
    # Share card: centred, and tighter, because make_og crops this to 760x630.
    # Wider than the 760x630 panel needs, with the motif pushed right: the
    # share card's headline wraps across the left of that panel, and at 900 wide
    # the $100 card sat under the last word of it.
    build("giftcard-og", 1100, 912, cx=700, cy=456, scale=0.58,
          spread=128, rot_a=-6, rot_b=9)
