"""The Growth Meeting one-pager: the five things, every week.

Letter portrait, white ground, no bleed, generous white border -- it gets run
off on the office printer and pinned up, so nothing bleeds to the edge and
nothing relies on colour fidelity to be readable.

Companion to the Manager Outreach sheet and deliberately the same furniture:
red pill eyebrow, condensed green headline, red callout, tracked small-cap
rules, red numerals. A manager with both on the wall should see one system.

Run:  python3 onepager_growth.py
Out:  Claude outputs/SquarePeg-Growth-Meeting-OnePager.pdf (+ .png preview)
"""
import subprocess
import sys
from pathlib import Path

import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).parent
FONTS = ROOT / "src" / "fonts-ttf"
LOGO = ROOT / "src" / "brand" / "logo-src.png"
OUT = ROOT / "Claude outputs"
NAME = "SquarePeg-Growth-Meeting-OnePager"

W, H = letter                     # 612 x 792 pt
M = 54                            # the white border. Printers eat 1/4in; this clears it.

for alias, fn in [("D", "big-shoulders-display-latin-900-normal"),
                  ("B", "figtree-latin-800-normal"),
                  ("S", "figtree-latin-700-normal"),
                  ("M", "figtree-latin-600-normal"),
                  ("R", "figtree-latin-400-normal")]:
    pdfmetrics.registerFont(TTFont(alias, str(FONTS / f"{fn}.ttf")))

RED = HexColor("#D50117")
GREEN = HexColor("#13503C")
INK = HexColor("#1A1614")
BODY = HexColor("#3D3733")
GREY = HexColor("#8A807A")
LINE = HexColor("#DED7D0")
CREAM = HexColor("#FBF6EC")

UPLOAD = "https://connect.squarepegpizzeria.com/public/photo-upload"

# Each step: title, how, track. Brian's wording, tightened to fit a page that
# has to stay readable pinned to a wall.
STEPS = [
    ("Loyalty",
     "Dine-in: every server brings the laminated loyalty card to the table once "
     "the order is in. To-go: ask at pickup, or on the phone before they arrive.",
     "Your weekly loyalty report. Come to the call with the numbers."),
    ("Local outreach, on foot",
     "Walk into local businesses and organizations with tokens, bounceback cards, "
     "flyers and pizza. Every new contact and follow-up note goes into Wingman.",
     "Toast comp report for your tokens — keep a record of which color went to "
     "which business — and for bouncebacks. Plus what you entered in Wingman."),
    ("Emails & follow-ups",
     "Work the leads and contacts you already have: past catering customers, "
     "fundraiser partners, possible business partners. CC Carla on catering and "
     "events, Brian on marketing and cross-promotion.",
     "The CCs to Carla and Brian, the replies, and what they turned into."),
    ("Catering & large reservations",
     "Turn the outreach and the follow-ups into catering orders, large "
     "reservations and event bookings.",
     "Come with what you booked. Every booking goes into "
     "connect.squarepegpizzeria.com."),
    ("Pictures & events",
     "Photograph events, groups and anything happening in your restaurant, and "
     "upload them with the code at the foot of this page.",
     "We review the week's uploads on the call."),
]


def wide(c, text, x, y, font, size, track, color, anchor="l"):
    """Letter-spaced text. reportlab has no tracking, so place each glyph."""
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
    for word in text.split():
        trial = (line + " " + word).strip()
        if pdfmetrics.stringWidth(trial, font, size) <= limit:
            line = trial
        else:
            out.append(line)
            line = word
    if line:
        out.append(line)
    return out


def para(c, text, x, y, font, size, lead, limit, color):
    c.setFillColor(color)
    c.setFont(font, size)
    for ln in wrap(text, font, size, limit):
        c.drawString(x, y, ln)
        y -= lead
    return y


def rule(c, label, y):
    """A tracked small-cap header with a hairline running out to the margin."""
    w = wide(c, label, M, y, "B", 9, 2.2, RED)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.line(M + w + 10, y + 3, W - M, y + 3)
    return y


def qr_img(data, px=600):
    q = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M,
                      box_size=10, border=2)
    q.add_data(data)
    q.make(fit=True)
    img = q.make_image(fill_color="#1A1614", back_color="white").convert("RGB")
    return img.resize((px, px))


def build():
    OUT.mkdir(exist_ok=True)
    pdf = OUT / f"{NAME}.pdf"
    c = canvas.Canvas(str(pdf), pagesize=letter)
    c.setTitle("Square Peg Pizzeria — Growth Meeting one-pager")

    # ---- masthead
    im = ImageReader(str(LOGO))
    iw, ih = im.getSize()
    lh = 40
    c.drawImage(im, M, H - M - lh, lh * iw / ih, lh, mask="auto")

    y = H - M - lh - 26
    pill_w = wide(c, "GROWTH MEETING", 0, -999, "B", 9, 2.2, RED) + 24
    c.setFillColor(RED)
    c.roundRect(M, y - 5, pill_w, 20, 10, fill=1, stroke=0)
    wide(c, "GROWTH MEETING", M + 12, y + 1, "B", 9, 2.2, HexColor("#FFFFFF"))

    y -= 20
    c.setFont("D", 64)
    c.setFillColor(GREEN)
    c.drawString(M - 2, y - 44, "THE FIVE")

    c.setFont("M", 10.5)
    c.setFillColor(BODY)
    c.drawString(M, y - 62, "The five things we review on every Growth Meeting call.")

    # ---- the callout, top right
    bx, bw, bh = W - M - 250, 250, 76
    by = y - 58
    c.setFillColor(RED)
    c.roundRect(bx, by, bw, bh, 4, fill=1, stroke=0)
    wide(c, "EVERY WEEK, ALL FIVE", bx + 16, by + bh - 22, "B", 8.5, 2, HexColor("#FFC9CE"))
    head = "COME WITH NUMBERS"
    hs = 30
    while pdfmetrics.stringWidth(head, "D", hs) > bw - 32:
        hs -= 1
    c.setFont("D", hs)
    c.setFillColor(HexColor("#FFFFFF"))
    c.drawString(bx + 15, by + bh - 52, head)
    c.setFont("R", 8.6)
    c.drawString(bx + 16, by + 14, "Not impressions. What you actually did.")

    # ---- the five
    y = by - 32
    rule(c, "THE FIVE, IN ORDER", y)
    top = y - 24

    col_x = M + 26
    lim = W - M - col_x

    # The goal block and the code sit at a fixed height off the bottom, so the
    # five steps get whatever is left and are spaced to fill it. Laying them out
    # top-down and hoping was how step five ended up underneath the goal box.
    goal_h = 64
    goal_y = M + 44
    floor = goal_y + goal_h + 22

    def measure(how, track):
        return (18 + 13
                + 12 * len(wrap(how, "R", 9.6, lim - 34)) - 12
                + 12 * len(wrap(track, "M", 9.6, lim - 40)) - 12)

    heights = [measure(h, t) for _, h, t in STEPS]
    slack = (top - floor) - sum(heights)
    gap = max(14, slack / (len(STEPS) - 1)) if len(STEPS) > 1 else 14

    y = top
    for i, (title, how, track) in enumerate(STEPS, 1):
        c.setFillColor(RED)
        c.circle(M + 9, y + 1, 9, fill=1, stroke=0)
        c.setFont("B", 10)
        c.setFillColor(HexColor("#FFFFFF"))
        n = str(i)
        c.drawString(M + 9 - pdfmetrics.stringWidth(n, "B", 10) / 2, y - 2.5, n)

        c.setFont("B", 13)
        c.setFillColor(GREEN)
        c.drawString(col_x, y - 3, title)
        y -= 18

        wide(c, "HOW", col_x, y, "B", 8, 1.8, RED)
        y = para(c, how, col_x + 34, y, "R", 9.6, 12, lim - 34, BODY) + 12
        y -= 13

        wide(c, "TRACK", col_x, y, "B", 8, 1.8, GREEN)
        y = para(c, track, col_x + 40, y, "M", 9.6, 12, lim - 40, INK) + 12
        if i < len(STEPS):
            y -= gap

    # ---- the goal, and the code for the photo upload
    qs = 88
    qx = W - M - qs
    c.drawImage(ImageReader(qr_img(UPLOAD)), qx, goal_y + 14, qs, qs)
    wide(c, "PHOTO UPLOAD", qx + qs / 2, goal_y + 2, "B", 7.5, 1.6, GREY, "c")

    gw = W - 2 * M - qs - 26
    c.setFillColor(CREAM)
    c.roundRect(M, goal_y, gw, goal_h, 4, fill=1, stroke=0)
    c.setFillColor(RED)
    c.rect(M, goal_y, 4, goal_h, fill=1, stroke=0)
    wide(c, "THE GOAL", M + 18, goal_y + goal_h - 18, "B", 8, 1.8, RED)
    c.setFont("D", 23)
    c.setFillColor(GREEN)
    c.drawString(M + 17, goal_y + 24, "KEEP IT SIMPLE. STAY CONSISTENT.")
    c.setFont("R", 9)
    c.setFillColor(BODY)
    c.drawString(M + 18, goal_y + 11, "Show measurable progress every week.")

    # ---- footer
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.line(M, M + 16, W - M, M + 16)
    wide(c, "SQUARE PEG PIZZERIA  ·  GROWTH MEETING  ·  PIN THIS WHERE YOU CLOCK IN",
         W / 2, M + 2, "B", 7.5, 1.6, GREY, "c")

    c.showPage()
    c.save()
    subprocess.run(["pdftoppm", "-png", "-r", "110", "-singlefile", str(pdf),
                    str(OUT / NAME)], check=True)
    print("  ", pdf.name)
    print("  ", NAME + ".png")


if __name__ == "__main__":
    build()
