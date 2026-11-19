"""The Golden Pie card: hidden in store, found by a guest, good for a free
small cheese pizza on their next visit.

3.5 x 2in trim, 1/8in bleed all round, TrimBox and BleedBox set in the PDF so
a press does not have to guess. Like the partner card and unlike the flyers,
this one bleeds -- it is going to a press, not the office printer.

"Pie", not "Peg": the menu already calls them RED PIES and WHITE PIES, so the
word is house vocabulary, and "peg" carries slang the card does not need.

Front is the find. Back is how to claim it and the terms. The terms follow
the Roll Doubles wording, including "no purchase necessary" -- consideration
plus chance plus prize is the definition of a lottery, and finding a card on
a shelf costs nothing, which is what keeps this a promotion.

Run:  python3 card_golden_pie.py ["Use by ..." ]
Out:  Claude outputs/SquarePeg-GoldenPie-{front,back}.pdf + .png proofs
"""
import subprocess
import sys
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
LOGO_DARK = ROOT / "src" / "brand" / "logo-src.png"
LOGO_LIGHT = ROOT / "src" / "brand" / "logo-on-dark.png"
OUT = ROOT / "Claude outputs"

IN = 72.0
TRIM_W, TRIM_H = 3.5 * IN, 2.0 * IN
BLEED = 0.125 * IN
SAFE = 0.125 * IN
W, H = TRIM_W + 2 * BLEED, TRIM_H + 2 * BLEED

for alias, fn in [("D", "big-shoulders-display-latin-900-normal"),
                  ("B", "figtree-latin-800-normal"),
                  ("S", "figtree-latin-700-normal"),
                  ("M", "figtree-latin-600-normal"),
                  ("R", "figtree-latin-400-normal")]:
    pdfmetrics.registerFont(TTFont(alias, str(FONTS / f"{fn}.ttf")))

# Gold as CMYK can only ever be a warm yellow -- it reads as gold because of
# what it sits on, which is why the front is near-black. If this ever goes to
# a press with budget, ask for a metallic or a foil on the front only.
GOLD = HexColor("#C9A227")
GOLD_LT = HexColor("#EBD68A")
GOLD_DP = HexColor("#8A6E16")
INK = HexColor("#141110")
CREAM = HexColor("#FBF6EC")
GREY = HexColor("#6F6761")
RED = HexColor("#D50117")

EXPIRY = sys.argv[1] if len(sys.argv) > 1 else "Use by March 31, 2027"
QR_URL = "https://squarepegpizzeria.com/golden-pie/?utm_source=card"

# Spelled out rather than a double-prime mark: Figtree has no glyph for it
# and it set as an empty box on the first proof.
TERMS = ("One per customer. Free 12-inch small cheese pizza on your next visit; "
         "no substitutions, no cash value, not transferable, not for resale. "
         "Must present this card — photocopies are not accepted. Not valid "
         "with any other offer, discount or loyalty reward. No purchase "
         "necessary to find or claim. Employees and immediate family are not "
         "eligible. Management may end the promotion at any time.")


def wide(c, text, x, y, font, size, track, color, anchor="l"):
    c.setFont(font, size); c.setFillColor(color)
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
            out.append(line); line = w
    if line:
        out.append(line)
    return out


_MARK = {}


def mark(hexcol):
    """The logo flattened to one flat colour. The on-dark file is still the red
    mark, so it cannot just be dropped onto a near-black card."""
    if hexcol not in _MARK:
        src = Image.open(LOGO_LIGHT).convert("RGBA")
        r, g, b = (int(hexcol[i:i + 2], 16) for i in (1, 3, 5))
        flat = Image.new("RGBA", src.size, (r, g, b, 0))
        flat.putalpha(src.getchannel("A"))
        _MARK[hexcol] = flat
    return _MARK[hexcol]


def logo(c, img, x, y, h, anchor="l"):
    im = ImageReader(img if not isinstance(img, (str, Path)) else str(img))
    iw, ih = im.getSize()
    w = h * iw / ih
    if anchor == "c":
        x -= w / 2
    c.drawImage(im, x, y, w, h, mask="auto")


def qr_img(data, px=600):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                      box_size=10, border=1)
    q.add_data(data); q.make(fit=True)
    img = q.make_image(fill_color="#141110", back_color="#FBF6EC").convert("RGB")
    return img.resize((px, px)), q.modules_count


def star(c, cx, cy, r, color):
    """A small five-pointed star, drawn rather than set as a glyph so it does
    not depend on a font having one."""
    import math
    p = c.beginPath()
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.42
        x, y = cx + rad * math.cos(a), cy + rad * math.sin(a)
        p.moveTo(x, y) if i == 0 else p.lineTo(x, y)
    p.close()
    c.setFillColor(color); c.drawPath(p, fill=1, stroke=0)


def front(c):
    """A gold ticket, playing off the one everybody pictures when you say
    "golden ticket" -- without going near it. The idiom is doing the work:
    gold ground, engraved double frame, corner ornaments and an ADMIT-ONE
    style bar. None of the film's artwork, name or wording appears here, and
    none of it needs to: the shape of the thing is the reference."""
    # Metallic can only be faked flat, so the ground is a gradient: lighter at
    # the edges, deeper through the middle, which is how gold foil catches a
    # room. On a press with budget, ask for a foil and drop this.
    c.linearGradient(0, 0, W, 0,
                     (HexColor("#E8CE7A"), HexColor("#C9A227"),
                      HexColor("#EBD68A"), HexColor("#C09A1F")),
                     positions=(0, 0.34, 0.62, 1), extend=True)

    # Engraved double frame.
    c.setStrokeColor(INK); c.setLineWidth(1.4)
    c.rect(BLEED + 5, BLEED + 5, TRIM_W - 10, TRIM_H - 10, fill=0, stroke=1)
    c.setLineWidth(0.4)
    c.rect(BLEED + 8.5, BLEED + 8.5, TRIM_W - 17, TRIM_H - 17, fill=0, stroke=1)

    # Corner ornaments: a filled diamond where the two rules meet.
    for ox, oy in ((BLEED + 5, BLEED + 5), (BLEED + TRIM_W - 5, BLEED + 5),
                   (BLEED + 5, BLEED + TRIM_H - 5), (BLEED + TRIM_W - 5, BLEED + TRIM_H - 5)):
        pth = c.beginPath()
        pth.moveTo(ox, oy + 4); pth.lineTo(ox + 4, oy)
        pth.lineTo(ox, oy - 4); pth.lineTo(ox - 4, oy); pth.close()
        c.setFillColor(INK); c.drawPath(pth, fill=1, stroke=0)

    cx = W / 2
    top = H - BLEED - SAFE

    w = wide(c, "THE GOLDEN PIE", cx, top - 15, "B", 8.2, 2.6, INK, "c")
    star(c, cx - w / 2 - 11, top - 12, 3.3, INK)
    star(c, cx + w / 2 + 11, top - 12, 3.3, INK)

    c.setFont("D", 38); c.setFillColor(INK)
    c.drawCentredString(cx, top - 52, "YOU FOUND IT.")

    # The ADMIT ONE bar: the single strongest ticket cue, and it carries the
    # offer rather than decorating around it.
    bw, bh = TRIM_W - 44, 17
    bx, by = (W - bw) / 2, top - 74
    c.setFillColor(INK); c.rect(bx, by, bw, bh, fill=1, stroke=0)
    wide(c, "GOOD FOR ONE SMALL CHEESE PIZZA", cx, by + 5.6, "B", 7.0, 1.5,
         HexColor("#EBD68A"), "c")

    foot_size = 7.8
    foot_base = by - 13
    c.setFont("M", foot_size); c.setFillColor(HexColor("#4A3B0C"))
    c.drawCentredString(cx, foot_base, "Bring it back on your next visit. On us.")

    # The mark is centred in the space left between the bottom of that line and
    # the inner frame rule, rather than pinned at a fixed offset from the trim.
    # Expressed this way the air above and below it stays equal on its own if
    # the bar above ever moves, instead of needing re-nudging by eye.
    inner_rule = BLEED + 8.5
    foot_bottom = foot_base - foot_size * 0.22        # descender depth
    logo_h = 19                                        # was 14
    gap = (foot_bottom - inner_rule - logo_h) / 2
    logo(c, mark("#141110"), cx, inner_rule + gap, logo_h, "c")
    print("   logo %.0fpt, %.1fpt of air above and below" % (logo_h, gap))


def back(c):
    c.setFillColor(CREAM); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(INK); c.rect(0, H - BLEED - 22, W, 22 + BLEED, fill=1, stroke=0)
    wide(c, "HOW TO CLAIM IT", BLEED + SAFE + 2, H - BLEED - 15, "B", 7.6, 2.2, GOLD)

    x = BLEED + SAFE + 2
    col = TRIM_W - 2 * SAFE - 68          # leave the QR its corner

    c.setFont("M", 8.2); c.setFillColor(INK)
    c.drawString(x, H - BLEED - 36, "Hand this card to your server or the counter.")
    c.setFont("R", 7.4); c.setFillColor(GREY)
    c.drawString(x, H - BLEED - 46, "Good at any Square Peg Pizzeria.")

    c.setFont("B", 7.2); c.setFillColor(RED)
    c.drawString(x, H - BLEED - 60, EXPIRY)

    c.setFont("R", 5.3); c.setFillColor(GREY)
    y = H - BLEED - 74
    for line in wrap(TERMS, "R", 5.3, col):
        c.drawString(x, y, line); y -= 6.4

    qs = 46
    qx, qy = W - BLEED - SAFE - qs - 2, BLEED + SAFE + 14
    img, modules = qr_img(QR_URL)
    c.drawImage(ImageReader(img), qx, qy, qs, qs)
    mm = (qs / modules) * 25.4 / 72
    assert mm >= 0.40, f"QR module is {mm:.2f}mm — too small to scan reliably"
    wide(c, "THE RULES", qx + qs / 2, qy - 8, "B", 4.8, 1.0, GREY, "c")

    c.setFont("R", 5.4); c.setFillColor(GREY)
    c.drawString(x, BLEED + SAFE + 3, "squarepegpizzeria.com/golden-pie")


def build(name, draw):
    pdf = OUT / f"SquarePeg-GoldenPie-{name}.pdf"
    c = canvas.Canvas(str(pdf), pagesize=(W, H))
    c.setTitle(f"Square Peg — The Golden Pie ({name})")
    draw(c)
    c.setCropBox((0, 0, W, H))
    c.setBleedBox((0, 0, W, H))
    c.setTrimBox((BLEED, BLEED, BLEED + TRIM_W, BLEED + TRIM_H))
    c.showPage(); c.save()
    subprocess.run(["pdftoppm", "-png", "-r", "300", "-singlefile", str(pdf),
                    str(OUT / f"SquarePeg-GoldenPie-{name}")], check=True)
    print("  ", pdf.name)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    build("front", front)
    build("back", back)
    print("   trim %.0f x %.0f pt, bleed %.1f pt, page %.0f x %.0f pt"
          % (TRIM_W, TRIM_H, BLEED, W, H))
    print("  ", EXPIRY)
