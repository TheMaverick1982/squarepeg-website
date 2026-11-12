"""Scoop & Sip float menu, 8.5x11, for Square Peg Delray Beach.

The source for this was a dark neon board, full bleed. This is the same menu
rebuilt light: white ground, red and charcoal, a white margin all round and no
bleed, because it goes through the office printer (see /areas/square-peg-
pizzeria.md). The drink artwork is the original artwork, lifted off its dark
tiles by tools/float_glasses.py and dropped straight onto white.

No bottle shot. Naming a spirit on a drinks menu is ordinary; reprinting
somebody else's product photography is not, so the Jagermeister float is sold
by its glass and its name.

Run:  python3 menu_scoop_sip.py
Out:  Claude outputs/menu-scoop-sip.pdf  (+ .png preview)
"""
import subprocess
from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).parent
FONTS = ROOT / "src" / "fonts-ttf"
GLASS = ROOT / "src" / "floats"
OUT = ROOT / "Claude outputs"
LOGO = ROOT / "src" / "brand" / "logo-src.png"      # red mark, for light grounds

for alias, fn in [("D", "big-shoulders-display-latin-900-normal"),
                  ("B", "figtree-latin-800-normal"),
                  ("S", "figtree-latin-700-normal"),
                  ("M", "figtree-latin-600-normal"),
                  ("R", "figtree-latin-400-normal")]:
    pdfmetrics.registerFont(TTFont(alias, str(FONTS / f"{fn}.ttf")))

RED = HexColor("#D50117")
DEEP = HexColor("#9E0512")
INK = HexColor("#17120F")
SMOKE = HexColor("#6B625C")
LINE = HexColor("#E2DDD8")
WHITE = HexColor("#FFFFFF")
CREAM = HexColor("#FBF6EC")

W, H = 612, 792          # 8.5 x 11
M = 40                   # the white border the office printer needs
CAP = 0.72               # cap height of Big Shoulders Display

ADULT = [
    ("jager",      ["Jägermeister", "Float"],       "$14"),
    ("dragon",     ["Tropical Dragon", "Float"],         "$14"),
    ("blueberry",  ["Blueberry Rum", "Float"],           "$14"),
    ("coconut",    ["Coconut Rum", "& Coke Float"],      "$13"),
    ("pumpkin",    ["Pumpkin Spice", "Martini Float"],   "$15"),
    ("baileys",    ["Cold Brew Baileys", "Martini Float"], "$15"),
    ("jackcoke",   ["Jack & Coke", "Float"],             "$13"),
    ("createsoda", ["Create Your Own", "Soda Float"],    "$14"),
]

KIDS = [
    ("cola",     ["Classic Coca-Cola", "Float"],  "$6"),
    ("sprite",   ["Sprite", "Float"],             "$6"),
    ("dietcoke", ["Diet Coke /", "Coke Zero Float"], "$6"),
    ("rootbeer", ["Root Beer", "Float"],          "$6"),
]


def wide(c, text, x, y, font, size, track, color, anchor="l"):
    """Letter-spaced text. reportlab has no tracking, so place each glyph."""
    c.setFont(font, size)
    c.setFillColor(color)
    total = sum(pdfmetrics.stringWidth(ch, font, size) + track for ch in text) - track
    if anchor == "c":
        x -= total / 2
    elif anchor == "r":
        x -= total
    for ch in text:
        c.drawString(x, y, ch)
        x += pdfmetrics.stringWidth(ch, font, size) + track
    return total


def fit(text, font, size, limit):
    while size > 5 and pdfmetrics.stringWidth(text, font, size) > limit:
        size -= 0.25
    return size


def glass(c, key, cx, base, h):
    """One drink, sitting on `base`, scaled to height `h`."""
    im = ImageReader(str(GLASS / f"{key}.png"))
    iw, ih = im.getSize()
    w = h * iw / ih
    c.drawImage(im, cx - w / 2, base, w, h, mask="auto")
    return w


def band(c, label, y, hgt, bg, fg):
    c.setFillColor(bg)
    c.rect(M, y, W - M * 2, hgt, fill=1, stroke=0)
    wide(c, label, W / 2, y + (hgt - 11 * CAP) / 2 + 1, "B", 11, 3.4, fg, anchor="c")


def cell(c, item, cx, base, gh, name_size, price_size, width):
    key, lines, price = item
    glass(c, key, cx, base + 34, gh)

    y = base + 22
    for ln in lines:
        size = fit(ln, "S", name_size, width - 4)
        c.setFont("S", size); c.setFillColor(INK)
        c.drawCentredString(cx, y, ln)
        y -= name_size + 1.5

    c.setFont("D", price_size); c.setFillColor(RED)
    c.drawCentredString(cx, base - price_size * CAP + 2, price)


def draw(c):
    c.setFillColor(WHITE); c.rect(0, 0, W, H, fill=1, stroke=0)

    # ---------------------------------------------------------- masthead
    im = ImageReader(str(LOGO))
    iw, ih = im.getSize()
    lh = 44
    c.drawImage(im, W / 2 - lh * iw / ih / 2, H - M - lh, lh * iw / ih, lh, mask="auto")

    c.setFont("D", 70); c.setFillColor(INK)
    c.drawCentredString(W / 2, H - M - lh - 62, "SCOOP & SIP")

    c.setFont("M", 11.5); c.setFillColor(SMOKE)
    c.drawCentredString(W / 2, H - M - lh - 80,
                        "Cocktail and fountain soda floats, each with a scoop "
                        "of your favorite ice cream.")

    wide(c, "SQUARE PEG PIZZERIA  ·  DELRAY BEACH", W / 2, H - M - lh - 98,
         "B", 9, 3, DEEP, anchor="c")

    # ------------------------------------------------------------ adults
    top = H - M - lh - 122
    band(c, "ADULT COCKTAIL FLOATS  ·  21+", top - 22, 22, RED, CREAM)

    cols, gut = 4, 13
    cw = (W - M * 2 - gut * (cols - 1)) / cols
    row_h = 163
    for i, item in enumerate(ADULT):
        r, col = divmod(i, cols)
        cx = M + cw / 2 + col * (cw + gut)
        base = top - 44 - row_h * (r + 1) + 34
        cell(c, item, cx, base, 98, 9.5, 21, cw)

    # -------------------------------------------------------------- kids
    ky = top - 44 - row_h * 2 - 14
    band(c, "KIDS’ FOUNTAIN FLOATS  ·  NO ALCOHOL", ky - 22, 22, INK, CREAM)

    for i, item in enumerate(KIDS):
        cx = M + cw / 2 + i * (cw + gut)
        cell(c, item, cx, ky - 44 - 130 + 34, 72, 9.5, 19, cw)

    # ------------------------------------------------------------ footer
    fy = ky - 44 - 130 + 4
    c.setStrokeColor(LINE); c.setLineWidth(1)
    c.line(M, fy, W - M, fy)
    c.setFont("R", 8); c.setFillColor(SMOKE)
    c.drawCentredString(W / 2, fy - 14,
                        "Cocktail floats are 21+ with valid ID. "
                        "Ice cream flavors vary — ask your server what we have in.")


def main():
    OUT.mkdir(exist_ok=True)
    pdf = OUT / "menu-scoop-sip.pdf"
    c = canvas.Canvas(str(pdf), pagesize=(W, H))
    draw(c); c.showPage(); c.save()
    subprocess.run(["pdftoppm", "-png", "-r", "110", "-singlefile", str(pdf),
                    str(OUT / "menu-scoop-sip")], check=True)
    print("  ", pdf.name)


if __name__ == "__main__":
    main()
