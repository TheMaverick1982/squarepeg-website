"""The $25 gift card graphic for the Halloween page.

Drawn rather than photographed so the denomination is a variable — change AMOUNT
and rerun if next year's prize is different. Transparent corners, so the page can
tilt it without a white box showing at the edges.

Run:  python3 make_giftcard.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).parent
FONTS = ROOT / "src" / "fonts-ttf"
LOGO = ROOT / "src" / "brand" / "logo-on-dark.png"
OUT = ROOT / "assets" / "img-src" / "gift-card-25.webp"

AMOUNT = "$25"
W, H = 1200, 756           # a credit-card ratio, with room for the shadow
CARD = (72, 40, 1128, 716)  # the card itself inside that canvas
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
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cw, ch = CARD[2] - CARD[0], CARD[3] - CARD[1]

    # drop shadow first, so the card sits on top of it
    shadow = rounded((cw, ch), R, (0, 0, 0, 115)).filter(ImageFilter.GaussianBlur(26))
    canvas.alpha_composite(shadow, (CARD[0] - 4, CARD[1] + 26))

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

    d.text((78, 300), AMOUNT, font=big, fill=CREAM)
    d.text((84, 560), "GIFT CARD", font=lab, fill=GOLD)

    logo = Image.open(LOGO).convert("RGBA")
    lw = 430
    logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
    white = Image.new("RGBA", logo.size, CREAM + (0,))
    white.putalpha(logo.getchannel("A"))        # the mark is red; on red it needs knocking out
    card.alpha_composite(white, (74, 86))

    canvas.alpha_composite(card, (CARD[0], CARD[1]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT, "WEBP", quality=94, method=6, lossless=False)
    print("wrote", OUT.name, canvas.size, "| alpha:", canvas.getchannel("A").getextrema())


if __name__ == "__main__":
    build()
