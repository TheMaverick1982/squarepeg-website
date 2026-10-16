"""The gift-card-bonus holiday set: TV slide, Facebook, Instagram, flyer.

QR on the two pieces people stand in front of (the TV and the flyer).
Nothing to scan on the social pieces — the link lives in the caption there,
and a QR in a feed is just a dead square.

Vertical rhythm is measured, not guessed: every headline is positioned from
the cap height of the size that actually fit, and the card motif reports its
own bounding box. Eyeballing those is how an eyebrow ends up sitting on the
first line of a headline.

Run: python3 make.py
"""
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor, Color

from giftcard_holiday import (OUT, RED, WHITE, PINE, PINE_DEEP, GOLD, GOLD_HI,
                     draw_logo, pine_ground, tracked, tracked_c, tracked_w,
                     fit, cap_top, sparkle, card_pair, pair_box, pair_cx,
                     qr_block, render)

OUT.mkdir(exist_ok=True)

EYEBROW = "NOVEMBER & DECEMBER  ·  IN STORE"
HEAD3 = ["THE GIFT CARD", "IS FOR THEM.", "THE $20 IS FOR YOU."]
HEAD2 = ["THE GIFT CARD IS FOR THEM.", "THE $20 IS FOR YOU."]
BODY = ["Every $100 in gift cards comes with a $20 voucher.",
        "Yours to spend January 1 – February 13."]
URL_PLAIN = "squarepegpizzeria.com/gift-card-bonus"
MIST = HexColor("#CFE0D6")
SLATE = HexColor("#3A4A42")


def headline(c, lines, size, x, top, colors, centred=False, lead=0.88):
    """Draw from the cap line down, so `top` means the top of the letters."""
    y = top - size * 0.73
    for line, col in zip(lines, colors):
        c.setFont("D", size)
        c.setFillColor(col)
        if centred:
            c.drawCentredString(x, y, line)
        else:
            c.drawString(x, y, line)
        y -= size * lead
    return y + size * lead          # baseline of the last line


# ------------------------------------------------------------------ TV

def tv():
    """1920x1080. Everything that matters stays inside a 5% title-safe
    margin — TVs in dining rooms still overscan, and the one thing you cannot
    afford to lose off the edge is the QR."""
    W, H = 1920, 1080
    SAFE = 96
    pdf = str(OUT / "giftcard-tv.pdf")
    c = rl_canvas.Canvas(pdf, pagesize=(W, H))
    c.drawImage(ImageReader(pine_ground(W, H, 1390, 520, seed=11)), 0, 0, W, H)

    x = 120
    draw_logo(c, x, H - 78, 252, (255, 255, 255), anchor="tl")
    tracked(c, EYEBROW, "B", 25, x, 812, 4.4, GOLD)

    s = fit(c, HEAD3, "D", 880, 108)
    last = headline(c, HEAD3, s, x, 790, [WHITE, WHITE, GOLD_HI])

    c.setFillColor(GOLD)
    c.rect(x, last - 46, 132, 4, fill=1, stroke=0)

    c.setFont("M", 28)
    c.setFillColor(MIST)
    y = last - 94
    for line in BODY:
        c.drawString(x, y, line)
        y -= 40

    qr_block(c, "https://squarepegpizzeria.com/gift-card-bonus/?utm_source=tv",
             x, 112, 196,
             [("SCAN FOR THE DETAILS", "B", 23, 2.6), (URL_PLAIN, "M", 20, 0)],
             WHITE, str(OUT / "_qr_tv.png"))

    cx, cy, sc = 1432, 548, 0.76
    card_pair(c, cx, cy, sc)
    x0, y0, x1, y1 = pair_box(cx, cy, sc)
    assert x1 <= W - SAFE and y1 <= H - SAFE and y0 >= SAFE, (x0, y0, x1, y1)
    assert x0 > x + 880 + 24, "cards are crowding the headline column"

    sparkle(c, 1178, 846, 26, GOLD_HI)
    sparkle(c, 1856, 300, 16, GOLD)
    sparkle(c, 1106, 246, 12, GOLD)

    render(c, pdf, "TV slide 1920x1080")


# ------------------------------------------------------------ Facebook

def facebook():
    W, H = 1200, 630
    pdf = str(OUT / "giftcard-facebook.pdf")
    c = rl_canvas.Canvas(pdf, pagesize=(W, H))
    c.drawImage(ImageReader(pine_ground(W, H, 880, 300, seed=4)), 0, 0, W, H)

    x = 70
    draw_logo(c, x, H - 46, 158, (255, 255, 255), anchor="tl")
    tracked(c, EYEBROW, "B", 15.5, x, 478, 2.8, GOLD)

    s = fit(c, HEAD3, "D", 585, 66)
    last = headline(c, HEAD3, s, x, 462, [WHITE, WHITE, GOLD_HI])

    c.setFillColor(GOLD)
    c.rect(x, last - 30, 84, 2.6, fill=1, stroke=0)

    c.setFont("M", 17.5)
    c.setFillColor(MIST)
    y = last - 60
    for line in BODY:
        c.drawString(x, y, line)
        y -= 25

    tracked(c, URL_PLAIN, "B", 15, x, 52, .6, GOLD)

    cx, cy, sc = 905, 330, 0.455
    card_pair(c, cx, cy, sc)
    x0, y0, x1, y1 = pair_box(cx, cy, sc)
    assert x1 <= W - 30 and y1 <= H - 24 and y0 >= 24, (x0, y0, x1, y1)
    assert x0 > x + 585 + 20, "cards are crowding the headline column"

    sparkle(c, 700, 500, 15, GOLD_HI)
    sparkle(c, 1160, 150, 10, GOLD)

    render(c, pdf, "Facebook 1200x630")


# ----------------------------------------------------------- Instagram

def instagram():
    W, H = 1080, 1080
    pdf = str(OUT / "giftcard-instagram.pdf")
    c = rl_canvas.Canvas(pdf, pagesize=(W, H))
    c.drawImage(ImageReader(pine_ground(W, H, 560, 600, seed=21)), 0, 0, W, H)

    # Fenced off: a translucent fill leaves its alpha in the graphics state,
    # and drawImage — unlike setFillColor — never resets it. Without the
    # restore, the wordmark below renders at 55% and reads grey, not white.
    c.saveState()
    c.setFillColor(Color(PINE_DEEP.red, PINE_DEEP.green, PINE_DEEP.blue, alpha=.92))
    c.rect(0, 0, W, 192, fill=1, stroke=0)
    c.setFillColor(Color(GOLD.red, GOLD.green, GOLD.blue, alpha=.55))
    c.rect(0, 190, W, 2, fill=1, stroke=0)
    c.restoreState()

    draw_logo(c, W / 2, H - 62, 224, (255, 255, 255), anchor="tc")
    tracked_c(c, EYEBROW, "B", 19, W / 2, 896, 3.4, GOLD)

    s = fit(c, HEAD3, "D", 860, 92)
    headline(c, HEAD3, s, W / 2, 872, [WHITE, WHITE, GOLD_HI], centred=True)

    sc = 0.565
    cx, cy = pair_cx(W / 2, sc), 424
    card_pair(c, cx, cy, sc)
    x0, y0, x1, y1 = pair_box(cx, cy, sc)
    assert x0 >= 24 and x1 <= W - 24, (x0, x1)
    assert y0 >= 192 + 20, "cards are overlapping the footer band"

    c.setFont("M", 25)
    c.setFillColor(MIST)
    c.drawCentredString(W / 2, 132, BODY[0])
    c.drawCentredString(W / 2, 100, BODY[1])
    tracked_c(c, URL_PLAIN, "B", 19, W / 2, 48, 1.0, GOLD)

    sparkle(c, 118, 560, 20, GOLD_HI)
    sparkle(c, 980, 470, 14, GOLD)
    sparkle(c, 148, 282, 12, GOLD)

    render(c, pdf, "Instagram 1080x1080")


# --------------------------------------------------------------- flyer

def flyer():
    """8.5x11 on a desktop printer: white ground, a drawn frame, and colour
    only where it earns it. A full-bleed dark page is the thing that eats a
    cartridge and comes out banded."""
    W, H = 612, 792
    M = 30                                   # white border, all four sides
    pdf = str(OUT / "giftcard-flyer-8.5x11.pdf")
    c = rl_canvas.Canvas(pdf, pagesize=(W, H))

    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setStrokeColor(PINE)
    c.setLineWidth(1.6)
    c.rect(M, M, W - 2 * M, H - 2 * M, fill=0, stroke=1)
    c.setStrokeColor(GOLD)
    c.setLineWidth(.7)
    c.rect(M + 7, M + 7, W - 2 * M - 14, H - 2 * M - 14, fill=0, stroke=1)

    lh = draw_logo(c, W / 2, H - M - 28, 152, (213, 1, 23), anchor="tc")
    y = H - M - 28 - lh - 26

    tracked_c(c, "NOVEMBER & DECEMBER  ·  IN STORE  ·  ALL 10 LOCATIONS",
              "B", 9.6, W / 2, y, 2.1, PINE)

    s = fit(c, HEAD2, "D", 430, 46)
    last = headline(c, HEAD2, s, W / 2, y - 20, [PINE, RED], centred=True, lead=.86)

    c.setFont("M", 12.4)
    c.setFillColor(SLATE)
    c.drawCentredString(W / 2, last - 34, "Every $100 in gift cards you buy comes with a $20 voucher.")
    c.drawCentredString(W / 2, last - 51, "Yours to spend January 1 – February 13.")

    sc = 0.33
    cx = pair_cx(W / 2, sc) + 10      # the red card is the visual mass, so the
                                      # geometric centre still reads left-heavy
    cy = (last - 51 - 30) - 366.7 * sc            # hang the motif off the copy
    card_pair(c, cx, cy, sc, shadow=0.16)         # a hard shadow prints as a smudge
    x0, y0, x1, y1 = pair_box(cx, cy, sc)
    assert x0 >= M + 14 and x1 <= W - M - 14, (x0, x1)

    c.setFont("B", 13)
    c.setFillColor(PINE)
    c.drawCentredString(W / 2, y0 - 28, "Ask at the register.")

    c.setStrokeColor(GOLD)
    c.setLineWidth(.8)
    c.line(156, y0 - 50, 456, y0 - 50)

    size, quiet = 76, 76 * .085
    cw = size + quiet * 2
    labels = [("SCAN FOR THE DETAILS", "B", 10, 1.6), (URL_PLAIN, "M", 9.4, 0)]
    lw = max(tracked_w(c, t, f, fs, tr) for t, f, fs, tr in labels)
    gx = (W - (cw + size * .16 + lw)) / 2
    gy = y0 - 50 - 16 - cw
    qr_block(c, "https://squarepegpizzeria.com/gift-card-bonus/?utm_source=flyer",
             gx, gy, size, labels, PINE, str(OUT / "_qr_flyer.png"),
             card=HexColor("#F2F6F3"))

    c.setFont("R", 6.8)
    c.setFillColor(HexColor("#6B7A72"))
    fine = [
        "One $20 voucher for every full $100 of gift cards on the same purchase. Buy $250, get two. Gift cards must be bought in person at a Square Peg location —",
        "cards bought online don’t qualify. The $20 is a voucher, not a gift card: it isn’t redeemable for cash and can’t be put toward buying more gift cards.",
        "Usable January 1 – February 13, 2027 only; it doesn’t carry over. Not valid with other offers. Tax and gratuity not included. Management may end the promotion at any time.",
    ]
    fy = gy - 24
    for line in fine:
        c.drawCentredString(W / 2, fy, line)
        fy -= 9.4
    assert fy > M + 7, f"fine print is running into the frame ({fy:.0f})"

    render(c, pdf, "Flyer 8.5x11 (PDF)", dpi=110)


if __name__ == "__main__":
    print("building:")
    tv()
    facebook()
    instagram()
    flyer()
    for f in OUT.glob("_*"):
        f.unlink()
    print("done ->", OUT)
