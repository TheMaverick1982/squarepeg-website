"""The partner promo card: a business card a partner tucks in with their order.

3.5 x 2in trim, 1/8in bleed on all four sides, trim and bleed boxes set in the
PDF so a commercial printer does not have to guess. This one is NOT the
desktop-printer treatment the flyers use -- it is going to a press, which is
why it bleeds.

Front is the offer, back is where to use it. Everything that changes between
partners is an argument, so the next one is a command line rather than a new
file.

Run:  python3 card_partner_promo.py
Out:  Claude outputs/SquarePeg-PartnerCard-<slug>-<side>.pdf
"""
import subprocess
import sys
from pathlib import Path

import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).parent
FONTS = ROOT / "src" / "fonts-ttf"
LOGO_DARK = ROOT / "src" / "brand" / "logo-src.png"
LOGO_LIGHT = ROOT / "src" / "brand" / "logo-on-dark.png"
OUT = ROOT / "Claude outputs"

IN = 72.0
TRIM_W, TRIM_H = 3.5 * IN, 2.0 * IN
BLEED = 0.125 * IN
SAFE = 0.125 * IN                      # keep type this far inside the trim
W, H = TRIM_W + 2 * BLEED, TRIM_H + 2 * BLEED

for alias, fn in [("D", "big-shoulders-display-latin-900-normal"),
                  ("B", "figtree-latin-800-normal"),
                  ("S", "figtree-latin-700-normal"),
                  ("M", "figtree-latin-600-normal"),
                  ("R", "figtree-latin-400-normal")]:
    pdfmetrics.registerFont(TTFont(alias, str(FONTS / f"{fn}.ttf")))

CREAM = HexColor("#FBF6EC")
GREEN = HexColor("#13503C")
RED = HexColor("#D50117")
INK = HexColor("#1A1614")
GREY = HexColor("#6F6761")
PALE = HexColor("#CDE0D6")
PALE_RED = HexColor("#FFD2D6")

OFFER = "10% OFF"
OFFER_SUB = "YOUR WHOLE CHECK"
STORE = "Square Peg Delray Beach"
STREET = "4957 W Atlantic Ave, Delray Beach, FL 33445"
PHONE = "(561) 566-8828"
QR_URL = "https://squarepegpizzeria.com/locations/delray-beach-fl/"
TERMS = ("Dine in only. One card per table. Not valid with other offers or "
         "during happy hour. Tax and gratuity not included.")


def wide(c, text, x, y, font, size, track, color, anchor="l"):
    c.setFont(font, size)
    c.setFillColor(color)
    total = sum(pdfmetrics.stringWidth(ch, font, size) + track for ch in text) - track
    if anchor == "c":
        x -= total / 2
    for ch in text:
        c.drawString(x, y, ch)
        x += pdfmetrics.stringWidth(ch, font, size) + track
    return total


def wrap(text, font, size, limit):
    out, line = [], ""
    for w in text.split():
        t = (line + " " + w).strip()
        if pdfmetrics.stringWidth(t, font, size) <= limit:
            line = t
        else:
            out.append(line)
            line = w
    if line:
        out.append(line)
    return out


_PALE_MARK = [None]


def pale_mark():
    """The logo flattened to cream, for the dark side of the card."""
    if _PALE_MARK[0] is None:
        from PIL import Image
        src = Image.open(LOGO_LIGHT).convert("RGBA")
        flat = Image.new("RGBA", src.size, (251, 246, 236, 0))
        flat.putalpha(src.getchannel("A"))
        _PALE_MARK[0] = flat
    return _PALE_MARK[0]


def logo(c, img, x, y, h, anchor="l"):
    im = ImageReader(img if isinstance(img, (str, Path)) is False else str(img))
    iw, ih = im.getSize()
    w = h * iw / ih
    if anchor == "c":
        x -= w / 2
    c.drawImage(im, x, y, w, h, mask="auto")


def qr_img(data, px=600):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                      box_size=10, border=1)
    q.add_data(data)
    q.make(fit=True)
    img = q.make_image(fill_color="#13503C", back_color="#FBF6EC").convert("RGB")
    return img.resize((px, px)), q.modules_count


def front(c):
    c.setFillColor(RED)
    c.rect(0, 0, W, H, fill=1, stroke=0)          # colour runs to the bleed

    # The dashed rule says "coupon" before anyone reads a word -- the same cue
    # the clip-out boxes use on the 8.5x11 promo flyer.
    c.setStrokeColor(CREAM)
    c.setLineWidth(1)
    c.setDash(3, 2.4)
    c.rect(BLEED + 7, BLEED + 7, TRIM_W - 14, TRIM_H - 14, fill=0, stroke=1)
    c.setDash()

    cx = W / 2
    logo(c, pale_mark(), cx, H - BLEED - SAFE - 24, 22, "c")

    c.setFont("D", 54)
    c.setFillColor(CREAM)
    c.drawString(cx - pdfmetrics.stringWidth(OFFER, "D", 54) / 2, H / 2 - 12, OFFER)

    wide(c, OFFER_SUB, cx, H / 2 - 26, "B", 9, 2.2, PALE_RED, "c")

    # No partner name anywhere on it: one print run serves every partner, and
    # a card that names one of them cannot be handed to the next.
    wide(c, "DINE IN  ·  " + STORE.upper(), cx, BLEED + SAFE + 7, "B", 6.6, 1.4, CREAM, "c")


def back(c):
    c.setFillColor(GREEN)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    left = BLEED + SAFE + 4
    logo(c, pale_mark(), left, H - BLEED - SAFE - 22, 20)

    c.setFont("M", 7.4)
    c.setFillColor(CREAM)
    y = H / 2 + 4
    for ln in wrap(STREET, "M", 7.4, TRIM_W - 2 * SAFE - 76):
        c.drawString(left, y, ln)
        y -= 9.4
    c.setFont("B", 9)
    c.drawString(left, y - 1, PHONE)

    c.setFont("R", 4.9)
    c.setFillColor(PALE)
    ty = BLEED + SAFE + 16
    for ln in wrap(TERMS, "R", 4.9, TRIM_W - 2 * SAFE - 76):
        c.drawString(left, ty, ln)
        ty -= 6
    wide(c, "SQUAREPEGPIZZERIA.COM", left, BLEED + SAFE - 1, "B", 5.8, 1.2, CREAM)

    # The code has to survive being printed at this size: a module under about
    # 0.4mm is where phone cameras start to struggle.
    qs = 52
    qx, qy = W - BLEED - SAFE - qs - 4, (H - qs) / 2 - 2
    img, modules = qr_img(QR_URL)
    c.setFillColor(CREAM)
    c.roundRect(qx - 4, qy - 4, qs + 8, qs + 8, 3, fill=1, stroke=0)
    c.drawImage(ImageReader(img), qx, qy, qs, qs)
    mm = (qs / modules) * 25.4 / 72
    assert mm >= 0.40, f"QR module is {mm:.2f}mm — too small to scan reliably"
    # clear of the tile, which overhangs the code by 4pt
    wide(c, "FIND US", qx + qs / 2, qy - 12, "B", 5.2, 1.1, PALE, "c")


def build(name, draw):
    pdf = OUT / f"SquarePeg-PartnerCard-{name}.pdf"
    c = canvas.Canvas(str(pdf), pagesize=(W, H))
    c.setTitle(f"Square Peg partner card — {name}")
    draw(c)
    # So the printer trims where we meant, not where it guesses.
    c.setCropBox((0, 0, W, H))
    c.setBleedBox((0, 0, W, H))
    c.setTrimBox((BLEED, BLEED, BLEED + TRIM_W, BLEED + TRIM_H))
    c.showPage()
    c.save()
    subprocess.run(["pdftoppm", "-png", "-r", "300", "-singlefile", str(pdf),
                    str(OUT / f"SquarePeg-PartnerCard-{name}")], check=True)
    print("  ", pdf.name)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    build("delray-front", front)
    build("delray-back", back)
    print("   trim %.0f x %.0f pt, bleed %.1f pt, page %.0f x %.0f pt"
          % (TRIM_W, TRIM_H, BLEED, W, H))
