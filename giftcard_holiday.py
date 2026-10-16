"""Shared furniture for the gift-card-bonus holiday set.

The house style is char + ember red. Brian asked for something a bit
different, so this set moves to a deep pine ground with gold foil type and
keeps the red for the card itself — the card stays the loudest thing on the
page, which is the point. Snowfall and a warm bokeh do the holiday work;
no wreaths, no candy canes.

Everything is drawn in reportlab at 1pt = 1px for the screen pieces, then
rasterised at 72dpi so the numbers in the layout are the numbers in the file.
"""
import math
import random
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color

ROOT = Path(__file__).parent
FONTS = ROOT / "src" / "fonts-ttf"
OUT = ROOT / "out"
LOGO_ON_DARK = ROOT / "src" / "brand" / "logo-on-dark.png"
LOGO_SRC = ROOT / "src" / "brand" / "logo-src.png"

for alias, fn in [("D", "big-shoulders-display-latin-900-normal"),
                  ("B", "figtree-latin-800-normal"),
                  ("M", "figtree-latin-600-normal"),
                  ("R", "figtree-latin-400-normal")]:
    pdfmetrics.registerFont(TTFont(alias, str(FONTS / f"{fn}.ttf")))

RED = HexColor("#D50117")
RED_DEEP = HexColor("#8E0310")
FLAME = HexColor("#FFB524")
INK = HexColor("#1A1614")
WHITE = HexColor("#FFFFFF")
PINE = HexColor("#0C3A2C")
PINE_DEEP = HexColor("#061A14")
GOLD = HexColor("#E3BE79")
GOLD_HI = HexColor("#F7E3B6")
CREAM = HexColor("#FBF6EC")

# ---------------------------------------------------------------- logo

_CACHE = {}


def tinted_logo(rgb):
    """The wordmark flooded with one colour. logo-on-dark keeps the script in
    red, which on a red card is red on red — i.e. nothing."""
    key = ("logo", rgb)
    if key not in _CACHE:
        im = Image.open(LOGO_ON_DARK).convert("RGBA")
        a = np.array(im)
        a[..., 0], a[..., 1], a[..., 2] = rgb
        _CACHE[key] = Image.fromarray(a)
    return _CACHE[key]


def logo_path(rgb, w=None):
    """reportlab only honours PNG alpha from a file on disk, never from an
    RGBA object handed to ImageReader. Costs one temp file, saves an hour.

    Resampled to roughly the size it will be drawn at, because letting the PDF
    rasteriser shrink a 1500px wordmark to 210px thins the script until it
    reads grey instead of white."""
    tag = f"{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}" + (f"_{int(w)}" if w else "")
    p = OUT / f"_logo_{tag}.png"
    if not p.exists():
        im = tinted_logo(rgb)
        if w and im.width > w * 2:
            tw = int(w * 2)
            im = im.resize((tw, round(tw * im.height / im.width)), Image.LANCZOS)
        im.save(p)
    return str(p)


def draw_logo(c, x, y, w, rgb=(255, 255, 255), anchor="bl"):
    im = tinted_logo(rgb)
    h = w * im.height / im.width
    if anchor == "tl":
        y -= h
    elif anchor == "tc":
        x -= w / 2
        y -= h
    elif anchor == "bc":
        x -= w / 2
    c.drawImage(logo_path(rgb, w), x, y, w, h, mask="auto")
    return h


CAP = 0.73          # cap height of Big Shoulders Display, as a share of em


def cap_top(baseline, size):
    return baseline + size * CAP

# ---------------------------------------------------------------- ground


def pine_ground(w, h, cx, cy, seed=7, snow=True):
    """Deep pine falling off to near-black, with a warm glow where the cards
    sit. Composited in numpy rather than stacked translucent rects: every join
    in a stacked gradient leaves a hairline, invisible on paper and glaring on
    a backlit TV."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    far = math.hypot(max(cx, w - cx), max(cy, h - cy))
    t = np.clip(np.hypot(xx - cx, yy - cy) / far, 0, 1) ** 0.82

    near = np.array([18, 62, 47], np.float32)     # pine, lit
    away = np.array([6, 19, 16], np.float32)      # pine, unlit
    img = near * (1 - t)[..., None] + away * t[..., None]

    # a second, warmer pool right under the cards so the red has somewhere
    # to sit without looking stuck on
    warm = np.clip(np.hypot(xx - cx, yy - cy) / (far * 0.42), 0, 1) ** 1.6
    img += np.array([34, 10, 2], np.float32) * (1 - warm)[..., None]

    img = np.clip(img, 0, 255)
    im = Image.fromarray(img.astype(np.uint8))

    if snow:
        im = add_snow(im, seed)
    return im


def add_snow(im, seed):
    """Gold specks, a few of them soft and large so it reads as bokeh rather
    than dust on the lens."""
    from PIL import ImageDraw, ImageFilter
    w, h = im.size
    rnd = random.Random(seed)

    bok = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(bok)
    for _ in range(int(w * h / 250000)):
        r = rnd.uniform(w * 0.012, w * 0.032)
        x, y = rnd.uniform(0, w), rnd.uniform(0, h * 0.95)
        v = rnd.uniform(0.10, 0.26)
        d.ellipse([x - r, y - r, x + r, y + r],
                  fill=(int(227 * v), int(190 * v), int(121 * v)))
    bok = bok.filter(ImageFilter.GaussianBlur(w * 0.012))
    im = Image.fromarray(np.clip(np.array(im, np.int16) + np.array(bok, np.int16),
                                 0, 255).astype(np.uint8))

    flakes = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(flakes)
    for _ in range(int(w * h / 8600)):
        r = rnd.uniform(w * 0.0010, w * 0.0030)
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        v = rnd.uniform(0.22, 0.95)
        d.ellipse([x - r, y - r, x + r, y + r],
                  fill=(int(255 * v), int(243 * v), int(220 * v)))
    flakes = flakes.filter(ImageFilter.GaussianBlur(w * 0.0009))
    return Image.fromarray(np.clip(np.array(im, np.int16) + np.array(flakes, np.int16),
                                   0, 255).astype(np.uint8))

# ---------------------------------------------------------------- type


def tracked(c, t, f, s, x, y, track, fill):
    c.setFont(f, s)
    c.setFillColor(fill)
    for ch in t:
        c.drawString(x, y, ch)
        x += c.stringWidth(ch, f, s) + track
    return x


def tracked_w(c, t, f, s, track):
    return sum(c.stringWidth(ch, f, s) + track for ch in t) - track


def tracked_c(c, t, f, s, cx, y, track, fill):
    tracked(c, t, f, s, cx - tracked_w(c, t, f, s, track) / 2, y, track, fill)


def fit(c, lines, font, max_w, start):
    """Largest size at which every line clears max_w. Guessing a size and
    hoping is how a headline ends up one word wider than the slide."""
    s = start
    while s > 8 and max(c.stringWidth(l, font, s) for l in lines) > max_w:
        s -= 1
    return s


def sparkle(c, cx, cy, r, fill, ratio=0.30):
    """Four-pointed foil star. Concave sides, so it reads as a glint and not
    as a plus sign."""
    c.setFillColor(fill)
    p = c.beginPath()
    k = r * ratio
    p.moveTo(cx, cy + r)
    p.curveTo(cx + k * .3, cy + k, cx + k, cy + k * .3, cx + r, cy)
    p.curveTo(cx + k, cy - k * .3, cx + k * .3, cy - k, cx, cy - r)
    p.curveTo(cx - k * .3, cy - k, cx - k, cy - k * .3, cx - r, cy)
    p.curveTo(cx - k, cy + k * .3, cx - k * .3, cy + k, cx, cy + r)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

# ---------------------------------------------------------------- cards


def card_100(c, cx, cy, w, h, rot, shadow=0.38):
    c.saveState()
    c.translate(cx, cy)
    c.rotate(rot)
    if shadow:
        c.setFillColor(Color(0, 0, 0, alpha=shadow))
        c.roundRect(-w / 2 + w * .016, -h / 2 - h * .032, w, h, h * .075, fill=1, stroke=0)
    c.setFillColor(RED)
    c.roundRect(-w / 2, -h / 2, w, h, h * .075, fill=1, stroke=0)
    c.setFillColor(RED_DEEP)
    c.rect(-w / 2, -h / 2 + h * .13, w, h * .085, fill=1, stroke=0)

    lw = w * .34
    im = tinted_logo((255, 255, 255))
    lh = lw * im.height / im.width
    c.drawImage(logo_path((255, 255, 255)), -w / 2 + w * .070,
                h / 2 - lh - h * .085, lw, lh, mask="auto")
    c.setFont("D", h * .40)
    c.setFillColor(WHITE)
    c.drawCentredString(0, -h * .155, "$100")
    tracked(c, "GIFT CARD", "B", h * .055, -w / 2 + w * .070, -h / 2 + h * .255,
            h * .028, Color(1, 1, 1, alpha=.82))
    c.restoreState()


def card_20(c, cx, cy, w, h, rot, shadow=0.42):
    c.saveState()
    c.translate(cx, cy)
    c.rotate(rot)
    if shadow:
        c.setFillColor(Color(0, 0, 0, alpha=shadow))
        c.roundRect(-w / 2 + w * .017, -h / 2 - h * .041, w, h, h * .075, fill=1, stroke=0)
    c.setFillColor(FLAME)
    c.roundRect(-w / 2, -h / 2, w, h, h * .075, fill=1, stroke=0)
    tracked(c, "ON US", "B", h * .075, -w / 2 + w * .085, h / 2 - h * .215,
            h * .038, INK)
    c.setFont("D", h * .42)
    c.setFillColor(INK)
    c.drawCentredString(0, -h * .17, "$20")
    c.restoreState()


# How far the pair reaches from its centre, per unit of scale. Worked out
# from the rotated corners rather than eyeballed, so a layout can ask where
# the motif will actually land instead of being rendered to find out.
PAIR = {"up": 366.7, "down": 339.1, "left": 470.2, "right": 484.0}


def pair_box(cx, cy, scale):
    return (cx - PAIR["left"] * scale, cy - PAIR["down"] * scale,
            cx + PAIR["right"] * scale, cy + PAIR["up"] * scale)


def pair_cx(page_cx, scale):
    """The motif is wider to the right than the left, so its centre is not
    the page centre."""
    return page_cx - (PAIR["right"] - PAIR["left"]) * scale / 2


def card_pair(c, cx, cy, scale, rot_a=-7, rot_b=10, shadow=None):
    """$20 behind and up-right, $100 in front and down-left — the bonus reads
    as something tucked behind the thing you actually buy."""
    s20 = 0.42 if shadow is None else shadow
    s100 = 0.38 if shadow is None else shadow
    card_20(c, cx + 232 * scale, cy + 182 * scale,
            460 * scale, 294 * scale, rot_b, s20)
    card_100(c, cx - 96 * scale, cy - 78 * scale,
             700 * scale, 440 * scale, rot_a, s100)

# ---------------------------------------------------------------- qr


def qr_png(url, px, seed_path):
    """Snap the QR to whole pixels. A QR resampled off-grid grows soft module
    edges, and a phone at six feet in a dim dining room needs every bit of
    that edge."""
    import qrcode
    q = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_Q,
                      box_size=10, border=0)
    q.add_data(url)
    q.make(fit=True)
    m = q.get_matrix()
    n = len(m)
    box = max(1, round(px / n))
    im = Image.new("1", (n * box, n * box), 1)
    px_ = im.load()
    for r in range(n):
        for col in range(n):
            if m[r][col]:
                for dy in range(box):
                    for dx in range(box):
                        px_[col * box + dx, r * box + dy] = 0
    im = im.convert("RGB")
    im.save(seed_path)
    return seed_path, im.size[0]


def qr_block(c, url, x, y, size, label_lines, fg_label, tmp,
             quiet_ratio=0.085, card=WHITE, align="left"):
    """QR on its own white card with a real quiet zone, labels beside it."""
    path, real = qr_png(url, size, tmp)
    quiet = size * quiet_ratio
    cw = size + quiet * 2
    c.setFillColor(card)
    c.roundRect(x, y, cw, cw, cw * .06, fill=1, stroke=0)
    c.drawImage(path, x + quiet, y + quiet, size, size)
    tx = x + cw + size * 0.16
    ty = y + cw * 0.62
    for i, (txt, font, fs, track) in enumerate(label_lines):
        tracked(c, txt, font, fs, tx, ty, track, fg_label)
        ty -= fs * 1.55
    return cw

# ---------------------------------------------------------------- output


def render(c, path, name, dpi=72):
    c.showPage()
    c.save()
    stem = str(Path(path).with_suffix(""))
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-singlefile", path, stem],
                   check=True)
    png = Path(stem + ".png")
    im = Image.open(png).convert("RGB")
    im.save(png)
    print(f"  {name:28s} {im.size[0]}x{im.size[1]}  {png.stat().st_size//1024}KB")
    return png
