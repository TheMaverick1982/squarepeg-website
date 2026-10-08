"""Peg or Treat table card: 8.5 x 5.5, two-up on a letter sheet, double-sided.

Side 1 of the sheet holds two copies of the kids menu, side 2 two copies of the
drinks list, so one letter page cut once across the middle gives two identical
double-sided half-sheet cards for the tables.

Both halves of a side are the same artwork, printed at the same place on each
sheet, so the fronts and backs line up after cutting however the printer feeds.
The trim line is a hairline across the middle of each side rather than crop
marks, because this prints on the office printer with no bleed.

Copy comes from HALLOWEEN in data/content.py, so the card can't say something the
website doesn't.

Run:  python3 card_halloween_menu.py
"""
import subprocess
import sys
from pathlib import Path

from PIL import ImageFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "data"))
from content import HALLOWEEN  # noqa: E402

FONTS = ROOT / "src" / "fonts-ttf"
LOGO_R = ROOT / "src" / "brand" / "logo-on-dark.png"
OUT = Path("/mnt/user-data/outputs")

for alias, fn in [("D", "big-shoulders-display-latin-900-normal"),
                  ("B", "figtree-latin-800-normal"),
                  ("S", "figtree-latin-700-normal"),
                  ("M", "figtree-latin-600-normal"),
                  ("R", "figtree-latin-400-normal")]:
    pdfmetrics.registerFont(TTFont(alias, str(FONTS / f"{fn}.ttf")))

INK = HexColor("#120E0C")
RED = HexColor("#D50117")
PUMPKIN = HexColor("#D85F0A")
GREY = HexColor("#6B625C")
HAIR = HexColor("#D9D2CA")
SAND = HexColor("#F4F2F0")
PAPER = HexColor("#FFFFFF")

HW = HALLOWEEN
CARD_W, CARD_H = 8.5 * 72, 5.5 * 72       # half of a letter sheet, cut across
M = 34                                     # white border; nothing bleeds

PIL_FONT = {
    "D": FONTS / "big-shoulders-display-latin-900-normal.ttf",
    "B": FONTS / "figtree-latin-800-normal.ttf",
    "S": FONTS / "figtree-latin-700-normal.ttf",
    "M": FONTS / "figtree-latin-600-normal.ttf",
    "R": FONTS / "figtree-latin-400-normal.ttf",
}


def tw(t, f, s):
    return pdfmetrics.stringWidth(t, f, s)


def fit(t, f, maxw, start, floor=8):
    size = start
    while size > floor and tw(t, f, size) > maxw:
        size -= 0.5
    return size


def ink_box(t, f, size):
    pf = ImageFont.truetype(str(PIL_FONT[f]), max(1, int(size)))
    ascent, _ = pf.getmetrics()
    x0, y0, x1, y1 = pf.getbbox(t)
    return y1 - y0, ascent - y1


def cap_top(t, f, size):
    pf = ImageFont.truetype(str(PIL_FONT[f]), max(1, int(size)))
    ascent, _ = pf.getmetrics()
    return ascent - pf.getbbox(t)[1]


def band_text(c, t, f, size, cx, band_y, band_h, fill=PAPER):
    ink_h, below = ink_box(t, f, size)
    c.setFont(f, size); c.setFillColor(fill)
    c.drawCentredString(cx, band_y + (band_h - ink_h) / 2 + below, t)


def text(c, t, f, s, x, y, fill=INK):
    c.setFont(f, s); c.setFillColor(fill); c.drawString(x, y, t)


def centred(c, t, f, s, cx, y, fill=INK):
    c.setFont(f, s); c.setFillColor(fill); c.drawCentredString(cx, y, t)


def right(c, t, f, s, x, y, fill=INK):
    c.setFont(f, s); c.setFillColor(fill); c.drawRightString(x, y, t)


def leader(c, x0, x1, y):
    """The dotted run between a dish and its price, as on the website."""
    if x1 - x0 < 10:
        return
    c.setStrokeColor(HAIR); c.setLineWidth(1.6)
    c.setDash(1, 4); c.line(x0, y, x1, y); c.setDash()


def head_block(c, ox, oy, title):
    """Red strip carrying the name and the dates, then the title.

    The dates used to sit on their own line between the strip and the title, which
    cost 28pt on a 5.5in card and left the menu squeezed. They fit the strip."""
    inner = CARD_W - M * 2
    cx = ox + CARD_W / 2
    bh = 32
    by = oy + CARD_H - M - bh
    c.setFillColor(RED); c.rect(ox + M, by, inner, bh, fill=1, stroke=0)
    when = HW["when"].replace("Monday, ", "").replace("Saturday, ", "").replace(" – ", " \u2013 ")
    band_text(c, f"{HW['name'].upper()}   ·   {when.upper()}", "B", 12.5, cx, by, bh)

    y = by - 20
    ts = fit(title.upper(), "D", inner, 40)
    y -= cap_top(title.upper(), "D", ts)
    centred(c, title.upper(), "D", ts, cx, y, INK)
    return y - 26        # the title descends; leave the menu clear of it


def foot_block(c, ox, oy, note):
    """The mark on the left, the one qualifying line on the right."""
    img = ImageReader(str(LOGO_R)); iw, ih = img.getSize()
    lw = 76
    lh = ih * lw / iw
    c.drawImage(img, ox + M, oy + M - 4, width=lw, height=lh, mask="auto",
                preserveAspectRatio=True)
    right(c, note, "R", 8.5, ox + CARD_W - M, oy + M + lh / 2 - 3, GREY)
    rule = oy + M + lh + 11
    c.setStrokeColor(HAIR); c.setLineWidth(1)
    c.line(ox + M, rule, ox + CARD_W - M, rule)
    return rule


def centre_start(top, bottom, block_h):
    """Where a block of this height starts so it sits centred in the gap.

    Returned as the first baseline, i.e. the top of the block less nothing — each
    caller draws downward from it."""
    slack = (top - bottom) - block_h
    return top - max(slack, 0) / 2


# ---------------------------------------------------------------- side 1
def kids_card(c, ox, oy):
    inner = CARD_W - M * 2
    top = head_block(c, ox, oy, "$5 Kids Menu")
    bottom = foot_block(c, ox, oy, HW["kids"]["note_short"])

    LABEL, ROW, GROUP = 18, 20, 10          # label→dish, dish→dish, group→group
    NAME, DESC = 16, 27                     # drink name→its line, line→next drink
    groups = HW["kids"].get("menu", [])
    left_h = sum(LABEL + len(items) * ROW for _, items in groups) + GROUP * (len(groups) - 1)
    right_h = LABEL + len(HW["drinks"]["kids"]) * (NAME + DESC) + 14

    y = centre_start(top, bottom, max(left_h, right_h))
    gap = 26
    colw = (inner - gap) / 2
    lx, rx = ox + M, ox + M + colw + gap
    ly = ry = y

    DISH = 19
    for n, (group, items) in enumerate(groups):
        text(c, group.upper(), "B", 9.5, lx, ly, RED)
        ly -= LABEL
        for it in items:
            ds = fit(it, "D", colw - 36, DISH)
            text(c, it.upper(), "D", ds, lx, ly, INK)
            leader(c, lx + tw(it.upper(), "D", ds) + 6, lx + colw - 26, ly + 5)
            right(c, HW["kids"]["price"], "D", DISH, lx + colw, ly, PUMPKIN)
            ly -= ROW
        if n < len(groups) - 1:
            ly -= GROUP

    text(c, "TO DRINK", "B", 9.5, rx, ry, RED)
    ry -= LABEL
    for name, desc in HW["drinks"]["kids"]:
        text(c, name.upper(), "D", DISH, rx, ry, INK)
        ry -= NAME
        text(c, desc, "R", 10, rx, ry, GREY)
        ry -= DESC
    text(c, "Drinks priced as usual.", "R", 8.5, rx, ry + 5, GREY)

    assert min(ly, ry) > bottom, f"the kids card overruns its footer ({min(ly, ry):.0f} vs {bottom:.0f})"


# ---------------------------------------------------------------- side 2
def drinks_card(c, ox, oy):
    inner = CARD_W - M * 2
    top = head_block(c, ox, oy, "Drinks in costume")
    bottom = foot_block(c, ox, oy, "21 and over.")

    NAME, ITEM = 17, 30                     # name→description, description→next name
    drinks = HW["drinks"]["adults"]
    block_h = len(drinks) * (NAME + ITEM) - ITEM + 12
    y = centre_start(top, bottom, block_h)

    price = HW["drinks"]["adults_price"]
    for name, desc in drinks:
        ns = fit(name, "D", inner - 76, 24)
        text(c, name.upper(), "D", ns, ox + M, y, INK)
        leader(c, ox + M + tw(name.upper(), "D", ns) + 7, ox + CARD_W - M - 36, y + 6)
        right(c, price, "D", 24, ox + CARD_W - M, y, PUMPKIN)
        y -= NAME
        text(c, desc, "R", 10.5, ox + M, y, GREY)
        y -= ITEM

    assert y + ITEM - 12 > bottom, f"the drinks card overruns its footer ({y:.0f} vs {bottom:.0f})"


# ---------------------------------------------------------------- the sheet
def sheet():
    W, H = 8.5 * 72, 11 * 72
    OUT.mkdir(parents=True, exist_ok=True)
    pdf = OUT / "SquarePeg-PegOrTreat-TableCard-8.5x5.5-2up.pdf"
    c = rl_canvas.Canvas(str(pdf), pagesize=(W, H))
    c.setTitle("Square Peg — Peg or Treat table card, 2 up")

    def cut_line():
        c.setStrokeColor(HAIR); c.setLineWidth(0.6)
        c.setDash(4, 4); c.line(18, H / 2, W - 18, H / 2); c.setDash()

    for draw in (kids_card, drinks_card):
        draw(c, 0, CARD_H)        # top half
        draw(c, 0, 0)             # bottom half, identical so fronts meet backs
        cut_line()
        c.showPage()
    c.save()

    png = str(pdf.with_suffix(""))
    subprocess.run(["pdftoppm", "-r", "150", "-png", str(pdf), png], check=True)
    return pdf


def ink_coverage(path):
    import numpy as np
    from PIL import Image
    a = np.array(Image.open(path).convert("L")).astype(float)
    return (255 - a).mean() / 255 * 100


if __name__ == "__main__":
    p = sheet()
    print("  ", p.name, "— 2 sides, 2 up")
    for n, label in ((1, "kids"), (2, "drinks")):
        f = str(p.with_suffix("")) + f"-{n}.png"
        print(f"   side {n} ({label}): ink coverage {ink_coverage(f):.1f}%")
