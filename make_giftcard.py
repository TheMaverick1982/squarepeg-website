"""The $25 gift card graphic for the Halloween page.

Drawn rather than photographed so the denomination is a variable — change AMOUNT
and rerun if next year's prize is different. Transparent corners, so the page can
tilt it without a white box showing at the edges.

Run:  python3 make_giftcard.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
FONTS = ROOT / "src" / "fonts-ttf"
LOGO = ROOT / "src" / "brand" / "logo-on-dark.png"
OUT = ROOT / "assets" / "img-src" / "gift-card-25.webp"

AMOUNT = "$25"
# No padding and no drawn shadow: the file is the card and nothing else, so there
# is no soft rectangle to show up as a box behind it on the page.
W, H = 1056, 676            # a credit-card ratio
R = 46                      # corner radius

RED = (213, 1, 23)
RED_DEEP = (150, 6, 20)
CREAM = (255, 253, 249)
GOLD = (255, 181, 36)


def rounded(size, radius, fill):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius, fill=fill)
    return im


def build():
    cw, ch = W, H

    # the card: a soft diagonal sheen across the brand red
    card = rounded((cw, ch), R, RED + (255,))
    sheen = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    for i in range(ch):
        t = i / ch
        sd.line([(0, i), (cw, i)], fill=RED_DEEP + (int(150 * t),))
    card.alpha_composite(Image.composite(sheen, Image.new("RGBA", (cw, ch), (0, 0, 0, 0)),
                                         card.getchannel("A")))

    d = ImageDraw.Draw(card)

    # checkerboard band down the right, the way the brand uses it
    sq = 34
    for i, y in enumerate(range(0, ch, sq)):
        x = cw - sq * 2 if i % 2 == 0 else cw - sq
        d.rectangle([x, y, x + sq, y + sq], fill=CREAM + (235,))
    # mask it back inside the rounded corner
    card = Image.composite(card, Image.new("RGBA", (cw, ch), (0, 0, 0, 0)),
                           rounded((cw, ch), R, (255, 255, 255, 255)).getchannel("A"))
    d = ImageDraw.Draw(card)

    big = ImageFont.truetype(str(FONTS / "big-shoulders-display-latin-900-normal.ttf"), 250)
    lab = ImageFont.truetype(str(FONTS / "figtree-latin-800-normal.ttf"), 40)

    # Stack from measured ink boxes, not guessed offsets — the "$" descends below
    # the digits, which is what made the label collide with the amount.
    GAP = 26
    ab = big.getbbox(AMOUNT)          # (x0, y0, x1, y1) of the drawn ink
    lb = lab.getbbox("GIFT CARD")
    amount_top = 296
    d.text((78 - ab[0], amount_top - ab[1]), AMOUNT, font=big, fill=CREAM)
    label_top = amount_top + (ab[3] - ab[1]) + GAP
    d.text((82 - lb[0], label_top - lb[1]), "GIFT CARD", font=lab, fill=GOLD)
    assert label_top + (lb[3] - lb[1]) < ch - 30, "the label runs off the bottom of the card"

    logo = Image.open(LOGO).convert("RGBA")
    lw = 430
    logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
    white = Image.new("RGBA", logo.size, CREAM + (0,))
    white.putalpha(logo.getchannel("A"))        # the mark is red; on red it needs knocking out
    card.alpha_composite(white, (74, 86))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    card.save(OUT, "WEBP", quality=94, method=6, lossless=False)
    print("wrote", OUT.name, card.size, "| alpha:", card.getchannel("A").getextrema())


if __name__ == "__main__":
    build()
