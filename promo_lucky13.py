"""The $13 Trivia & Bingo promo: one TV slide and a 4-up sheet of table cards.

The joke is that the price and the number are the same, so the number is the
whole design: a bingo ball reading 13, which is also the answer to the only
trivia question that matters. 13 is the unlucky number everywhere except here,
and the line leans on that rather than explaining the offer twice.

Cream ground on both pieces. The TV slide is deliberately light while the
other slides on the screens are dark, so it is the one that interrupts; the
card is light because it goes through the office printer, which means white
paper, no bleed and a white border (see /areas/square-peg-pizzeria.md).

Run:  python3 promo_lucky13.py
Out:  Claude outputs/tv-lucky13.png
      Claude outputs/cards-lucky13-4up.pdf
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
OUT = ROOT / "Claude outputs"
LOGO_DARK = ROOT / "src" / "brand" / "logo-src.png"      # red mark, for light grounds
LOGO_LIGHT = ROOT / "src" / "brand" / "logo-on-dark.png"

for alias, fn in [("D", "big-shoulders-display-latin-900-normal"),
                  ("B", "figtree-latin-800-normal"),
                  ("S", "figtree-latin-700-normal"),
                  ("M", "figtree-latin-600-normal"),
                  ("R", "figtree-latin-400-normal")]:
    pdfmetrics.registerFont(TTFont(alias, str(FONTS / f"{fn}.ttf")))

RED = HexColor("#D50117")
DEEP = HexColor("#9E0512")
INK = HexColor("#17120F")
CREAM = HexColor("#FBF6EC")
WHITE = HexColor("#FFFFFF")
SMOKE = HexColor("#6B625C")
FAINT = HexColor("#EFE4D2")

HEAD = "THE ANSWER IS 13"
DECK = "The only 13 anybody has ever been happy about."
WHAT = ["Small cheese pizza", "One topping, your pick", "A fountain drink"]
FINE = "Dine-in only, during trivia and bingo."


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
    while size > 6 and pdfmetrics.stringWidth(text, font, size) > limit:
        size -= 1
    return size


def logo(c, img, x, y, h, anchor="l"):
    im = ImageReader(str(img))
    iw, ih = im.getSize()
    w = h * iw / ih
    if anchor == "c":
        x -= w / 2
    elif anchor == "r":
        x -= w
    c.drawImage(im, x, y, w, h, mask="auto")
    return w


CAP = 0.72   # cap height of Big Shoulders Display, as a share of point size


def ball(c, cx, cy, r, num, face, ring, ink, ringw):
    """A bingo ball. The ring is what makes it read as a ball rather than a
    dot, so it is drawn even at card size where it is only a hairline."""
    c.setFillColor(face)
    c.circle(cx, cy, r, fill=1, stroke=0)
    rr = r * 0.80
    c.setStrokeColor(ring)
    c.setLineWidth(ringw)
    c.circle(cx, cy, rr, fill=0, stroke=1)

    # Size against the CORNER of the numerals, not their width. Sized by width
    # alone the glyph box is wider than the circle is tall where it sits, and
    # the tops and tails push straight through the ring.
    size = r * 1.6
    while size > 6:
        half_w = pdfmetrics.stringWidth(num, "D", size) / 2
        half_h = size * CAP / 2
        if half_w ** 2 + half_h ** 2 <= (rr * 0.93) ** 2:
            break
        size -= 0.5
    c.setFont("D", size)
    c.setFillColor(ink)
    c.drawString(cx - pdfmetrics.stringWidth(num, "D", size) / 2,
                 cy - size * CAP / 2, num)


def strew(c, items, color, width):
    """Faint outline balls in the dead space. Texture, not decoration: they
    say 'numbers being called' without another line of copy."""
    c.setStrokeColor(color)
    c.setLineWidth(width)
    for cx, cy, r in items:
        c.circle(cx, cy, r, fill=0, stroke=1)
        c.circle(cx, cy, r * 0.80, fill=0, stroke=1)


# ------------------------------------------------------------------ TV slide
TW, TH = 1920, 1080


def tv(c):
    c.setFillColor(CREAM); c.rect(0, 0, TW, TH, fill=1, stroke=0)
    strew(c, [(300, 980, 70), (1760, 880, 92), (1560, 150, 58),
              (120, 230, 48), (980, 1010, 40)], FAINT, 6)

    # The ball, left, oversized on purpose -- at twelve feet the number is the
    # only thing that has to land.
    ball(c, 470, 540, 330, "13", RED, HexColor("#E8536A"), CREAM, 12)

    x = 900
    wide(c, "TRIVIA NIGHT & BINGO NIGHT", x, 790, "B", 34, 9, DEEP)
    c.setStrokeColor(RED); c.setLineWidth(5); c.line(x, 762, x + 470, 762)

    size = fit(HEAD, "D", 150, TW - x - 110)
    c.setFont("D", size); c.setFillColor(INK)
    c.drawString(x, 620, HEAD)

    c.setFont("M", 38); c.setFillColor(SMOKE)
    c.drawString(x, 552, DECK)

    y = 452
    for item in WHAT:
        c.setFillColor(RED); c.circle(x + 11, y + 12, 11, fill=1, stroke=0)
        c.setFont("S", 40); c.setFillColor(INK)
        c.drawString(x + 44, y, item)
        y -= 66

    # The price, set as a stamp rather than a line of copy, so the two 13s
    # read as the same gag from across the room.
    c.setFillColor(INK)
    c.rect(x, 110, 300, 118, fill=1, stroke=0)
    c.setFont("D", 104); c.setFillColor(CREAM)
    w = pdfmetrics.stringWidth("$13", "D", 104)
    c.drawString(x + 150 - w / 2, 142, "$13")

    c.setFont("M", 30); c.setFillColor(SMOKE)
    c.drawString(x + 334, 186, "all three, together")
    c.drawString(x + 334, 144, FINE)

    logo(c, LOGO_DARK, TW - 110, TH - 182, 96, anchor="r")


# --------------------------------------------------------------- table cards
PW, PH = 612, 792          # 8.5 x 11 at 72dpi
CW, CH = PW / 2, PH / 2    # 4.25 x 5.5
MARG = 26                  # the white border the office printer needs


# The card says it in one line rather than three. It is read at arm's length
# off a table, not across a room, and three bullets cost the height the ball
# needs to still look like a ball.
CARD_WHAT = ["Small cheese pizza, one topping,", "and a fountain drink."]


def card(c, ox, oy):
    """One 4.25 x 5.5 card, drawn at the given corner. No bleed: everything
    stays inside a white margin, because these come off a desktop printer."""
    x0, y0 = ox + MARG, oy + MARG
    w, h = CW - MARG * 2, CH - MARG * 2

    c.setFillColor(CREAM)
    c.rect(x0, y0, w, h, fill=1, stroke=0)
    c.setStrokeColor(RED); c.setLineWidth(2)
    c.rect(x0 + 7, y0 + 7, w - 14, h - 14, fill=0, stroke=1)
    cx = x0 + w / 2

    # --- from the bottom, where everything is fixed
    c.setFont("R", 8); c.setFillColor(SMOKE)
    c.drawCentredString(cx, y0 + 16, FINE)

    c.setFillColor(INK)
    c.rect(cx - 54, y0 + 32, 108, 44, fill=1, stroke=0)
    c.setFont("D", 40); c.setFillColor(CREAM)
    c.drawString(cx - pdfmetrics.stringWidth("$13", "D", 40) / 2, y0 + 46, "$13")

    y = y0 + 110
    for line in CARD_WHAT:
        c.setFont("S", 11.5); c.setFillColor(INK)
        c.drawCentredString(cx, y, line)
        y -= 16

    c.setStrokeColor(FAINT); c.setLineWidth(1.2)
    c.line(x0 + 40, y0 + 140, x0 + w - 40, y0 + 140)

    c.setFont("M", 9.2); c.setFillColor(SMOKE)
    c.drawCentredString(cx, y0 + 152, DECK)

    size = fit(HEAD, "D", 36, w - 36)
    c.setFont("D", size); c.setFillColor(INK)
    c.drawString(cx - pdfmetrics.stringWidth(HEAD, "D", size) / 2, y0 + 172, HEAD)

    # --- and from the top
    logo(c, LOGO_DARK, cx, y0 + h - 30, 21, anchor="c")
    wide(c, "TRIVIA & BINGO NIGHTS", cx, y0 + h - 47, "B", 9.5, 2.8, DEEP, anchor="c")

    # The ball takes the gap that is left, so the card stays balanced if any
    # of the copy above or below it changes length.
    top, bottom = y0 + h - 60, y0 + 172 + size * CAP + 8
    r = min((top - bottom) / 2, w * 0.34)
    ball(c, cx, (top + bottom) / 2, r, "13", RED, HexColor("#E8536A"), CREAM, 2.4)


def sheet(c):
    c.setFillColor(WHITE); c.rect(0, 0, PW, PH, fill=1, stroke=0)
    for ox in (0, CW):
        for oy in (0, CH):
            card(c, ox, oy)
    # Cut guides, in the margin only, so a stray line never crosses the art.
    c.setStrokeColor(HexColor("#C9C2BA")); c.setLineWidth(0.4)
    c.line(CW, 0, CW, 10); c.line(CW, PH - 10, CW, PH)
    c.line(0, CH, 10, CH); c.line(PW - 10, CH, PW, CH)


def main():
    OUT.mkdir(exist_ok=True)

    pdf = OUT / "tv-lucky13.pdf"
    c = canvas.Canvas(str(pdf), pagesize=(TW, TH)); tv(c); c.showPage(); c.save()
    png = OUT / "tv-lucky13"
    subprocess.run(["pdftoppm", "-png", "-r", "72", "-singlefile", str(pdf), str(png)],
                   check=True)
    pdf.unlink()
    print("  ", png.with_suffix(".png").name)

    out = OUT / "cards-lucky13-4up.pdf"
    c = canvas.Canvas(str(out), pagesize=(PW, PH)); sheet(c); c.showPage(); c.save()
    subprocess.run(["pdftoppm", "-png", "-r", "110", "-singlefile", str(out),
                    str(OUT / "cards-lucky13-4up")], check=True)
    print("  ", out.name)


if __name__ == "__main__":
    main()
