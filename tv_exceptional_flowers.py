"""TV slide — Exceptional Flowers & Gifts, the Delray partner offer.

Deliberately NOT built like the other slides. The in-store ones are dark
grounds and big red type; the Serve & Savor one is confetti. A florist's
offer wants to look like a florist, so this is ivory, generous white space,
their own green, and their wordmark given room. The only Square Peg marks
are a small logo and one eyebrow line, because the offer is theirs -- we are
the reason the viewer is getting it, not the subject.

The code is printed in a box of its own: a discount code read off a screen
across a dining room has to survive being half-remembered at a checkout.

Run:  python3 tv_exceptional_flowers.py
Out:  Claude outputs/tv-slide-exceptional-flowers-1920x1080.{png,jpg,pdf}
"""
import subprocess
from pathlib import Path

import qrcode
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).parent
FONTS = ROOT / "src" / "fonts-ttf"
PARTNER_LOGO = ROOT / "assets" / "img-src" / "partner-exceptional-flowers.png"
SP_LOGO = ROOT / "src" / "brand" / "logo-src.png"
OUT = ROOT / "Claude outputs"

for alias, fn in [("D", "big-shoulders-display-latin-900-normal"),
                  ("B", "figtree-latin-800-normal"),
                  ("S", "figtree-latin-700-normal"),
                  ("M", "figtree-latin-600-normal"),
                  ("R", "figtree-latin-400-normal")]:
    pdfmetrics.registerFont(TTFont(alias, str(FONTS / f"{fn}.ttf")))

# Sampled straight off their wordmark, so the slide and the logo agree.
GREEN = HexColor("#90C840")
DEEP = HexColor("#20411C")      # the same hue taken down for the panel
INK = HexColor("#121212")
IVORY = HexColor("#FBFAF6")
GREY = HexColor("#6B655E")
WHITE = HexColor("#FFFFFF")
PALE = HexColor("#F0F6E4")

W, H = 1920, 1080
PANEL = 600                      # right-hand green column
URL = "https://exceptionalflowersgifts.net/?utm_source=tv&utm_medium=qr"
CODE = "SQUAREPEG10"


def left(c, t, f, s, x, y, fill):
    c.setFont(f, s); c.setFillColor(fill); c.drawString(x, y, t)


def centered(c, t, f, s, cx, y, fill):
    c.setFont(f, s); c.setFillColor(fill); c.drawCentredString(cx, y, t)


def tracked(c, t, f, s, x, y, track, fill):
    """Glyph by glyph. Big Shoulders sets % and & hard against the character
    before them, so a headline with either in it collides when drawn whole."""
    c.setFont(f, s); c.setFillColor(fill)
    for ch in t:
        c.drawString(x, y, ch); x += c.stringWidth(ch, f, s) + track
    return x


def tracked_w(t, f, s, track):
    return sum(pdfmetrics.stringWidth(ch, f, s) + track for ch in t) - track


def tracked_centered(c, t, f, s, cx, y, track, fill):
    tracked(c, t, f, s, cx - tracked_w(t, f, s, track) / 2, y, track, fill)


def wrap(c, text, f, s, width):
    out, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if c.stringWidth(trial, f, s) <= width:
            line = trial
        else:
            out.append(line); line = word
    if line:
        out.append(line)
    return out


def place(c, img, x, y, h, anchor="l"):
    im = ImageReader(img)
    iw, ih = im.getSize()
    w = h * iw / ih
    if anchor == "c":
        x -= w / 2
    c.drawImage(im, x, y, w, h, mask="auto")
    return w


def qr_image(url):
    q = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M,
                      box_size=10, border=0)
    q.add_data(url); q.make(fit=True)
    return q.make_image(fill_color="black", back_color="white").convert("RGB"), len(q.get_matrix())


def draw():
    c = canvas.Canvas(str(OUT / "tv-slide-exceptional-flowers-1920x1080.pdf"),
                      pagesize=(W, H))
    c.setFillColor(IVORY); c.rect(0, 0, W, H, stroke=0, fill=1)

    # ---- right-hand green column, carrying the QR ------------------------
    c.setFillColor(DEEP); c.rect(W - PANEL, 0, PANEL, H, stroke=0, fill=1)
    c.setFillColor(GREEN); c.rect(W - PANEL, 0, 10, H, stroke=0, fill=1)
    pcx = W - PANEL / 2

    img, modules = qr_image(URL)
    px_per = max(5, round(300 / modules))
    side = px_per * modules
    pad = 30
    qx, qy = pcx - side / 2, 470
    c.setFillColor(WHITE)
    c.roundRect(qx - pad, qy - pad, side + pad * 2, side + pad * 2, 20, stroke=0, fill=1)
    c.drawImage(ImageReader(img), qx, qy, side, side)

    tracked_centered(c, "SCAN TO ORDER", "B", 34, pcx, qy - 92, 3.4, WHITE)
    centered(c, "exceptionalflowersgifts.net", "R", 25, pcx, qy - 130, HexColor("#BFD3B4"))

    # delivery promise, the one fact that makes it usable tonight
    c.setFillColor(GREEN)
    c.rect(pcx - 170, 232, 340, 3, stroke=0, fill=1)
    centered(c, "Same-day delivery to", "M", 27, pcx, 180, WHITE)
    centered(c, "Delray Beach", "B", 33, pcx, 142, GREEN)

    # ---- left column -----------------------------------------------------
    x = 110
    col = W - PANEL - x - 110

    place(c, Image.open(SP_LOGO), x, H - 150, 62)
    tracked(c, "A SQUARE PEG PARTNER", "B", 23, x + 210, H - 132, 3.6, GREEN)

    place(c, Image.open(PARTNER_LOGO), x, H - 390, 170)

    c.setFillColor(HexColor("#E6E2D8")); c.rect(x, H - 452, col, 2, stroke=0, fill=1)

    # the offer
    y = H - 600
    tracked(c, "10% OFF", "D", 150, x, y, 4, INK)
    left(c, "for Square Peg customers", "M", 40, x, y - 62, GREY)

    # the code, boxed so it survives being read across a room
    by = 212
    bw, bh = 640, 132
    c.setFillColor(PALE); c.roundRect(x, by, bw, bh, 16, stroke=0, fill=1)
    c.setStrokeColor(GREEN); c.setLineWidth(3)
    c.roundRect(x, by, bw, bh, 16, stroke=1, fill=0)
    tracked(c, "USE CODE AT CHECKOUT", "B", 21, x + 34, by + bh - 42, 3.2, HexColor("#4C7A2E"))
    # Figtree, not Big Shoulders, for the code itself: the condensed display
    # zero is near enough to an O that someone reading it across a dining room
    # would type the wrong character. A discount code has to be unambiguous
    # before it is handsome.
    tracked(c, CODE, "B", 58, x + 34, by + 30, 2.5, DEEP)

    # what they actually sell, kept to the things worth scanning for
    blurb = ("Fresh flowers, bouquets and plants, gift baskets, wine and champagne, "
             "gourmet chocolate truffles and more.")
    c.setFont("R", 29)
    ty = by - 62
    for line in wrap(c, blurb, "R", 29, col)[:3]:
        left(c, line, "R", 29, x, ty, GREY); ty -= 42

    c.setTitle("Exceptional Flowers & Gifts — 10% off for Square Peg customers")
    c.showPage(); c.save()
    return modules, side


def main():
    OUT.mkdir(exist_ok=True)
    modules, side = draw()
    stem = OUT / "tv-slide-exceptional-flowers-1920x1080"
    subprocess.run(["pdftoppm", "-r", "72", "-png", "-singlefile",
                    str(stem) + ".pdf", str(stem)], check=True)
    Image.open(str(stem) + ".png").convert("RGB").save(str(stem) + ".jpg", quality=92)
    print("QR: %d modules at %dpx" % (modules, side))
    print("wrote", stem.name + ".png / .jpg / .pdf")


if __name__ == "__main__":
    main()
